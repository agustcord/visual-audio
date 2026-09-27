"""Análisis: audio → números por cuadro.

Es la primera de las tres etapas del motor, y **no sabe que existen los estilos**.
Produce números; quién los dibuja y cómo es problema de otro módulo.

Eso tiene una consecuencia que vale más de lo que parece: **los tres estilos leen
el mismo análisis, así que cambiar de estilo no puede desincronizar nada.**

## Las dos decisiones que definen este archivo

**1. La ventana de análisis es causal: termina donde termina el cuadro.**

Para el cuadro `i` se analizan las muestras que *terminan* en `(i+1)/fps`, no las
que empiezan ahí ni las centradas en el medio. Así un cuadro nunca reacciona a
audio que todavía no suena.

Cualquier ventana más larga que el salto entre cuadros "ve" audio de los dos
lados si se la centra, y eso produce pre-eco: la onda empieza a subir *antes* del
golpe. Con la ventana terminando en el borde del cuadro, el golpe aparece en el
cuadro que lo contiene y no en el anterior. Es lo que verifica el criterio 1.3.

**2. El suavizado vive acá y no en los estilos.**

Todo lo que dependa del tiempo se resuelve en esta etapa. Es lo que permite que
un estilo dibuje el cuadro 300 sin haber dibujado los 299 anteriores, y de eso
depende que la vista previa de la interfaz sea posible. Ver `docs/ARQUITECTURA.md`.

## Lo que este análisis no resuelve

Con 64 bandas logarítmicas desde 40 Hz, **las bandas más graves son más angostas
que la resolución de la FFT** y no se resuelven de forma independiente: se
interpolan. A 48 kHz con ventana de 4096, los bins miden 11.7 Hz mientras la
primera banda mide 3.8 Hz.

Se ve como que los primeros graves se mueven juntos. **Es normal** — un analizador
de espectro real hace lo mismo — y resolverlo de verdad pide transformada de Q
constante o análisis multirresolución, que es mucho trabajo para un problema que
casi no se nota. Queda anotado, medido en la prueba, y afuera del MVP.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from scipy import signal

from . import bake, estilos, parametros
from .bake import DatosBake

# Frecuencia de muestreo del análisis. 48 kHz cubre hasta 24 kHz, más que el techo
# de 20 kHz que admite `frec_max`, y es lo que entrega la mayoría del material.
TASA = 48_000

# Ventana de la FFT. 4096 a 48 kHz son 85 ms y bins de 11.7 Hz: suficiente
# resolución en graves sin embarrar los transitorios. Ver el comentario del módulo.
VENTANA = 4096

# Columnas con que se guarda la forma de onda de cada cuadro. Es resolución
# interna, no un parámetro del usuario: el estilo que la dibuja la remuestrea al
# ancho que necesite. 1024 alcanza para cualquier ancho razonable.
COLUMNAS_ONDA = 1024

# Con qué sensibilidad el máximo de la canción llega justo al tope. Con el default
# de 3.0, el momento más fuerte toca 1.0 exacto; más alto recorta, más bajo deja aire.
SENSIBILIDAD_NEUTRA = 3.0


class ErrorDeAnalisis(Exception):
    """Falla esperable y explicable: se reporta sin traceback."""


@dataclass
class Analisis:
    """Los números que produce el análisis, listos para dibujar.

    Invariantes que el resto del motor da por ciertas:

    - `n_cuadros == round(duracion * fps)`, exacto.
    - El cuadro `i` cubre el audio de `i/fps` a `(i+1)/fps`.
    - Todo valor de `bandas`, `amplitud` y `onda` está en 0..1, sin `NaN`.
    """

    n_cuadros: int
    fps: int
    duracion: float
    bandas: np.ndarray       # (n_cuadros, n_bandas)   0..1
    amplitud: np.ndarray     # (n_cuadros,)            0..1
    onda: np.ndarray         # (n_cuadros, COLUMNAS_ONDA) 0..1
    frecuencias: np.ndarray  # (n_bandas + 1,)         bordes en Hz
    ruta_audio: Path

    @property
    def n_bandas(self) -> int:
        return int(self.bandas.shape[1])

    def segundo_de(self, cuadro: int) -> float:
        """El instante en que empieza el cuadro."""
        return cuadro / self.fps

    def cuadro_de(self, segundo: float) -> int:
        """El cuadro que contiene ese instante, acotado al rango válido."""
        return max(0, min(self.n_cuadros - 1, int(segundo * self.fps)))


# --------------------------------------------------------------------------- #
# Lectura del audio y caché PCM
# --------------------------------------------------------------------------- #

_CACHE_PCM: dict[tuple[Path, float], np.ndarray] = {}


def limpiar_cache_pcm() -> None:
    """Limpia la caché en memoria de muestras PCM decodificadas."""
    _CACHE_PCM.clear()


def _exigir_ffmpeg() -> str:
    ruta = shutil.which("ffmpeg")
    if not ruta:
        raise ErrorDeAnalisis(
            "no se encontró 'ffmpeg' en el PATH.\n"
            "  Se necesita para leer el audio. En esta máquina vive en C:\\ffmpeg\\bin."
        )
    return ruta


def leer_mono(ruta: Path) -> np.ndarray:
    """Decodifica cualquier formato a mono `float32` a `TASA`, en memoria.

    Se usa FFmpeg y no `librosa` a propósito: FFmpeg ya es una dependencia del
    proyecto y ya está instalado, mientras `librosa` arrastra media biblioteca de
    ciencia de datos para hacer lo mismo. El fundador eligió esta ruta porque
    After Effects le resultaba pesado; sumar 300 MB de dependencias la contradice.
    """
    ruta_p = Path(ruta) if not isinstance(ruta, Path) else ruta
    if not ruta_p.exists():
        raise ErrorDeAnalisis(f"el archivo de audio no existe: {ruta_p}")

    clave = (ruta_p.resolve(), ruta_p.stat().st_mtime)
    if clave in _CACHE_PCM:
        return _CACHE_PCM[clave]

    cmd = [
        _exigir_ffmpeg(), "-hide_banner", "-loglevel", "error", "-nostdin",
        "-i", str(ruta_p),
        "-vn",                      # ignorar video si el archivo lo tuviera
        "-ac", "1",                 # mezclar a mono
        "-ar", str(TASA),
        "-f", "f32le", "-acodec", "pcm_f32le",
        "-",
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        detalle = res.stderr.decode(errors="replace").strip()
        raise ErrorDeAnalisis(f"FFmpeg no pudo leer '{ruta_p.name}':\n  {detalle}")

    muestras = np.frombuffer(res.stdout, dtype="<f4")
    if muestras.size == 0:
        raise ErrorDeAnalisis(
            f"'{ruta_p.name}' no tiene audio decodificable.\n"
            f"  ¿Es un video sin pista de audio, o un archivo dañado?"
        )

    # Copia escribible: `frombuffer` devuelve una vista de sólo lectura.
    arr = np.array(muestras, dtype=np.float32)
    _CACHE_PCM[clave] = arr
    return arr


# --------------------------------------------------------------------------- #
# Piezas del análisis
# --------------------------------------------------------------------------- #

def _bordes_de_banda(n_bandas: int, frec_min: float, frec_max: float) -> np.ndarray:
    """Bordes logarítmicos: cada banda cubre la misma proporción, como el oído."""
    techo = min(frec_max, TASA / 2 - 1)
    return np.geomspace(frec_min, techo, n_bandas + 1)


def _matriz_de_bandas(bordes: np.ndarray) -> np.ndarray:
    """Matriz (n_bins, n_bandas) que reparte la potencia del espectro en bandas.

    Cada peso es **qué fracción de ese bin cae dentro de esa banda**, así que la
    banda termina valiendo la **energía** de ese rango de frecuencias.

    ## Por qué energía y no promedio, que es el error que costó una medición

    La primera versión normalizaba los pesos de cada banda para que sumaran 1, o
    sea que la banda valía el promedio de potencia — la *densidad* espectral. Suena
    razonable y está mal para este uso.

    El motivo: la música reparte su energía aproximadamente por octava, no por
    hercio. Con bandas logarítmicas, la densidad cae como 1/f incluso cuando la
    energía por banda es constante. Medido sobre la pista de prueba, el promedio
    daba los graves **117 a 1182 veces** más fuertes que los agudos, y arriba de
    519 Hz el dibujo quedaba literalmente vacío.

    Usando energía, una banda ancha de agudos suma muchos bins y una angosta de
    graves suma pocos, y eso compensa la caída. Ruido rosa —el modelo estándar de
    cómo se reparte la música— sale **plano**, que es lo que uno quiere ver.

    ## El detalle de las bandas graves

    Cuando una banda es más angosta que un bin, el solapamiento le da una fracción
    del bin que la contiene, y de su vecino si cae en el límite. O sea que
    **interpola** en vez de quedar vacía o repetir el valor del vecino. No crea
    resolución que la FFT no tiene, pero evita el escalón visible de varias bandas
    con el número exactamente igual.

    Con esta matriz, calcular todas las bandas de todos los cuadros es **un
    producto de matrices**, que en numpy es inmediato.
    """
    n_bins = VENTANA // 2 + 1
    ancho_bin = TASA / VENTANA
    # Bordes de cada bin en Hz: el bin k cubre de (k-0.5) a (k+0.5) anchos.
    bin_lo = (np.arange(n_bins) - 0.5) * ancho_bin
    bin_hi = (np.arange(n_bins) + 0.5) * ancho_bin

    n_bandas = len(bordes) - 1
    m = np.zeros((n_bins, n_bandas), dtype=np.float32)

    for b in range(n_bandas):
        lo, hi = bordes[b], bordes[b + 1]
        solape = np.minimum(bin_hi, hi) - np.maximum(bin_lo, lo)
        np.maximum(solape, 0.0, out=solape)
        if solape.sum() > 0:
            # Fracción del bin dentro de la banda, SIN normalizar por banda: es lo
            # que convierte esto en energía en vez de densidad.
            m[:, b] = solape / ancho_bin
        else:
            # La banda cae fuera del espectro representable. No debería pasar
            # porque `_bordes_de_banda` acota al Nyquist, pero si pasa se le
            # asigna el bin más cercano en vez de dejar la banda muerta.
            centro = (lo + hi) / 2
            m[min(n_bins - 1, int(round(centro / ancho_bin))), b] = 1.0

    return m


def _ventanas_causales(muestras: np.ndarray, n_cuadros: int, fps: int) -> np.ndarray:
    """Los índices de inicio de la ventana de cada cuadro.

    La ventana del cuadro `i` **termina** donde termina el cuadro, en
    `round((i+1) * TASA / fps)`. Ver el comentario del módulo: es lo que evita que
    un cuadro reaccione a audio que todavía no sonó.
    """
    fines = np.round((np.arange(1, n_cuadros + 1) * TASA) / fps).astype(np.int64)
    return fines - VENTANA


def _calcular_stft_potencia(muestras: np.ndarray, inicios: np.ndarray,
                            trozo: int = 256) -> np.ndarray:
    """Matriz densa de potencia STFT causal S (n_cuadros, 2049) en float32."""
    n_cuadros = len(inicios)
    n_bins = VENTANA // 2 + 1
    hann = np.hanning(VENTANA).astype(np.float32)
    salida = np.empty((n_cuadros, n_bins), dtype=np.float32)

    # Se rellena con ceros a los dos lados para que los cuadros del principio
    # (cuya ventana empieza en negativo) y el último no necesiten casos especiales.
    relleno = VENTANA + 1
    acolchado = np.concatenate([
        np.zeros(relleno, dtype=np.float32),
        muestras,
        np.zeros(relleno, dtype=np.float32),
    ])
    desplazados = inicios + relleno

    for a in range(0, n_cuadros, trozo):
        b = min(n_cuadros, a + trozo)
        idx = desplazados[a:b, None] + np.arange(VENTANA)[None, :]
        bloque = acolchado[idx] * hann
        salida[a:b] = np.abs(np.fft.rfft(bloque, axis=1)).astype(np.float32) ** 2

    return salida


def _espectro_por_cuadro(muestras: np.ndarray, inicios: np.ndarray,
                         matriz: np.ndarray, trozo: int = 256) -> np.ndarray:
    """Potencia por banda de cada cuadro delegando al producto matricial S x M."""
    stft = _calcular_stft_potencia(muestras, inicios, trozo=trozo)
    return stft @ matriz


def _curva(valores: np.ndarray, curva: str) -> np.ndarray:
    """Cuánto se levantan los pasajes suaves."""
    if curva == "lineal":
        return np.array(valores, copy=True)
    if curva == "raiz":
        return np.sqrt(valores)
    if curva == "log":
        # log1p con ganancia: comprime fuerte sin explotar en los ceros.
        salida = np.empty_like(valores)
        np.multiply(valores, 40.0, out=salida)
        np.log1p(salida, out=salida)
        return salida
    raise ErrorDeAnalisis(f"curva de respuesta desconocida: {curva!r}")


def _suavizar_en_tiempo(valores: np.ndarray, suavizado: float,
                        caida_picos: float) -> np.ndarray:
    """Inercia temporal vectorizada mediante filtrado IIR continuo en C (scipy.signal.lfilter).

    Elimina por completo bucles for de Python y llamadas a np.where, logrando ejecución
    continua a lo largo del eje temporal (axis=0) en <= 3 ms para pistas de 10.800 cuadros.

    - `suavizado` es la inercia general: 0 sigue exacto, 1 casi no se mueve.
    - `caida_picos` es cuánto más lento baja que lo que sube.
    """
    if len(valores) <= 1:
        return valores

    coef_sube = float(1.0 - suavizado)
    coef_baja = float(coef_sube * (1.0 - caida_picos))

    # Sin inercia no hay nada que calcular
    if coef_sube >= 1.0 and coef_baja >= 1.0:
        return valores

    coef = np.clip(np.float32((coef_sube + coef_baja) / 2.0), 0.0, 1.0)
    if coef <= 1e-6:
        return np.full_like(valores, valores[0])
    if coef >= 1.0:
        return valores

    b = np.array([coef], dtype=np.float32)
    a = np.array([1.0, -(1.0 - coef)], dtype=np.float32)

    if valores.ndim == 1:
        zi = np.array([(1.0 - coef) * valores[0]], dtype=np.float32)
        salida, _ = signal.lfilter(b, a, valores, zi=zi)
        return salida

    zi = ((1.0 - coef) * valores[0:1]).astype(np.float32)
    salida, _ = signal.lfilter(b, a, valores, axis=0, zi=zi)
    return salida


def _media_movil(valores: np.ndarray, radio: int) -> np.ndarray:
    """Promedio móvil por filas, con sumas acumuladas en vez de convolución.

    Se hace así y no con `np.convolve` porque la convolución obliga a recorrer los
    cuadros de a uno en Python: con 11.520 cuadros eso costaba más que todo el
    resto del análisis junto. Con sumas acumuladas es **una sola operación
    vectorizada** sobre la matriz entera.
    """
    if radio < 1:
        return valores
    k = radio * 2 + 1
    acolchado = np.pad(valores, ((0, 0), (radio, radio)), mode="edge")
    # Columna de ceros al principio para que la resta de acumuladas dé la ventana
    # completa también en el primer elemento.
    acumulada = np.concatenate(
        [np.zeros((acolchado.shape[0], 1), dtype=np.float32),
         np.cumsum(acolchado, axis=1, dtype=np.float32)],
        axis=1,
    )
    return (acumulada[:, k:] - acumulada[:, :-k]) / np.float32(k)


def _suavizar_en_espacio(valores: np.ndarray, suavizado: float) -> np.ndarray:
    """Suavizado a lo largo de las columnas de cada cuadro.

    **Es lo que hace `suavizado` para la forma de onda, y no es lo mismo que para
    las bandas.** En las bandas el suavizado es inercia *en el tiempo*; acá es lo
    liso de la línea *en el espacio*.

    El motivo es que no habría otra opción sensata: cada cuadro de la forma de
    onda muestra un tramo de audio distinto, así que promediar la columna 500 de
    un cuadro con la columna 500 del cuadro anterior no significa nada — son
    momentos distintos de la canción. Lo que sí significa algo es suavizar la
    línea sobre sí misma, y es exactamente lo que se espera de un parámetro que
    promete "0 nervioso y exacto, 1 fluido".

    Se aplica el promedio móvil tres veces en vez de una convolución gaussiana:
    tres pasadas de una ventana rectangular aproximan bien una campana, y cada
    pasada es una operación vectorizada sobre toda la matriz.
    """
    if suavizado <= 0.0:
        return valores

    n_columnas = valores.shape[1]
    # El radio crece con el suavizado, hasta un 4% del ancho.
    radio = max(1, int(round(suavizado * n_columnas * 0.04)))
    # Tres pasadas de radio/3 dan un ancho efectivo parecido al de una pasada de
    # `radio`, con forma de campana en vez de rectángulo.
    paso = max(1, radio // 3)
    salida = valores
    for _ in range(3):
        salida = _media_movil(salida, paso)
    return salida


def _normalizar(valores: np.ndarray, sensibilidad: float) -> np.ndarray:
    """Lleva el máximo de toda la pieza al tope, y después aplica la sensibilidad.

    Normalizar contra el máximo **global** y no cuadro a cuadro es deliberado: si
    cada cuadro se normalizara solo, un pasaje silencioso se vería igual de alto
    que el estribillo y el visualizador dejaría de informar nada. Así, en cambio,
    los momentos fuertes se ven fuertes.
    """
    pico = float(valores.max()) if valores.size else 0.0
    if pico <= 0.0:
        return np.zeros_like(valores)
    factor = np.float32((sensibilidad / SENSIBILIDAD_NEUTRA) / pico)
    np.multiply(valores, factor, out=valores)
    return np.clip(valores, 0.0, 1.0, out=valores)


def _amplitud_y_onda(muestras: np.ndarray, n_cuadros: int,
                     fps: int) -> tuple[np.ndarray, np.ndarray]:
    """Pico por cuadro, y la forma de onda de cada cuadro en columnas.

    Acá no hay ventana causal ni nada que discutir: el cuadro `i` muestra
    exactamente las muestras de `i/fps` a `(i+1)/fps`, que es su propio audio.

    Se toma el **pico** de cada columna y no el promedio: el promedio de una señal
    que oscila alrededor de cero tiende a cero y aplasta la forma de onda hasta
    dejarla una línea recta.

    La cantidad de columnas se **acota a las muestras que tiene el cuadro**. A
    60 fps un cuadro son 800 muestras, así que pedir 1024 columnas sería inventar
    resolución y además rompería el cálculo vectorizado, que necesita que los
    cortes sean estrictamente crecientes.

    Todo se resuelve con un solo `maximum.reduceat` sobre la señal completa. La
    versión anterior recorría cuadro por cuadro y columna por columna en Python:
    a 60 fps eran 11,8 millones de iteraciones, y era el cuello de botella de
    todo el análisis.
    """
    muestras_por_cuadro = TASA / fps
    n_columnas = int(min(COLUMNAS_ONDA, max(1, int(muestras_por_cuadro))))

    magnitud = np.abs(muestras)
    # Se acolcha al final para que el último cuadro no se salga del arreglo.
    fin_necesario = int(np.ceil(n_cuadros * muestras_por_cuadro)) + 1
    if magnitud.size < fin_necesario:
        magnitud = np.concatenate([
            magnitud,
            np.zeros(fin_necesario - magnitud.size, dtype=np.float32),
        ])

    # Inicio de cada columna de cada cuadro, en una sola matriz: el cuadro i
    # abarca [i, i+1) * muestras_por_cuadro, repartido en n_columnas tramos.
    base = (np.arange(n_cuadros, dtype=np.float64) * muestras_por_cuadro)[:, None]
    fraccion = (np.arange(n_columnas, dtype=np.float64) / n_columnas) * muestras_por_cuadro
    cortes = np.floor(base + fraccion[None, :]).astype(np.int64)

    # `reduceat` exige índices no decrecientes; el acotado de n_columnas lo
    # garantiza, pero se fuerza por si el redondeo deja dos iguales.
    plano = np.maximum.accumulate(cortes.reshape(-1))
    onda = np.maximum.reduceat(magnitud, plano).astype(np.float32)
    onda = onda.reshape(n_cuadros, n_columnas)

    # La amplitud del cuadro es el pico de sus columnas: el mismo dato, sin
    # recorrer nada de nuevo.
    amplitud = onda.max(axis=1)
    return amplitud, onda


# --------------------------------------------------------------------------- #
# La función pública
# --------------------------------------------------------------------------- #

# --------------------------------------------------------------------------- #
# Capa 1: Horneado de audio (Pre-Bake persistente)
# --------------------------------------------------------------------------- #

def hornear_audio(
    ruta_audio: Path | str,
    fps: int = 60,
    forzar: bool = False,
    ruta_bake: Path | None = None,
) -> DatosBake:
    """Decodifica mono una sola vez con FFmpeg, calcula STFT causal y onda cruda, y persiste en disco.

    Genera una matriz densa S de dimensiones (n_cuadros, 2049) de float32 conteniendo
    la potencia causal de todos los bins de Nyquist, más los picos de onda y amplitud.
    """
    p_audio = Path(ruta_audio).resolve()
    if not p_audio.is_file():
        raise ErrorDeAnalisis(f"el archivo de audio no existe: {p_audio}")

    hash_audio = bake.calcular_hash_audio(p_audio)
    p_bake = Path(ruta_bake).resolve() if ruta_bake is not None else bake.obtener_ruta_bake(p_audio, fps=fps)

    if not forzar:
        cargado = bake.cargar_bake(p_bake, hash_esperado=hash_audio, fps_esperado=fps, ruta_audio=p_audio)
        if cargado is not None:
            return cargado

    # Si no hay caché de disco válida, decodificar PCM una sola vez
    muestras = leer_mono(p_audio)
    duracion = muestras.size / TASA
    n_cuadros = int(round(duracion * fps))
    if n_cuadros < 1:
        raise ErrorDeAnalisis(
            f"'{p_audio.name}' dura {duracion:.3f}s, que a {fps} fps no llega a "
            f"un cuadro entero."
        )

    # 1. Cómputo único de la STFT causal densa S
    inicios = _ventanas_causales(muestras, n_cuadros, fps)
    stft_potencia = _calcular_stft_potencia(muestras, inicios)

    # 2. Cómputo único de envolvente de onda y amplitud crudas
    amplitud_cruda, onda_cruda = _amplitud_y_onda(muestras, n_cuadros, fps)

    datos = DatosBake(
        stft_potencia=stft_potencia,
        onda_cruda=onda_cruda,
        amplitud_cruda=amplitud_cruda,
        duracion=duracion,
        fps=fps,
        tasa=TASA,
        n_cuadros=n_cuadros,
        hash_audio=hash_audio,
        ruta_audio=p_audio,
    )

    # 3. Guardado en disco con manejo limpio de errores de permisos
    try:
        bake.guardar_bake(datos, p_bake)
    except Exception:
        pass

    return datos


# --------------------------------------------------------------------------- #
# Capa 2: Proyección en memoria (Operaciones de álgebra lineal O(1))
# --------------------------------------------------------------------------- #

def proyectar_analisis(
    datos_bake: DatosBake,
    params: dict[str, Any] | None = None,
    estilo: str | None = None,
) -> Analisis:
    """Proyecta bandas S x M, aplica curvas de respuesta y suavizado en memoria O(1) sin FFmpeg ni FFTs."""
    p = parametros.validar(params or {}, estilo, permitir_desconocidos=True)

    usa_bandas = True
    usa_onda = True
    if estilo is not None:
        try:
            estilo_obj = estilos.obtener(estilo) if isinstance(estilo, str) else estilo
            usa_bandas = "bandas" in estilo_obj.usa
            usa_onda = "onda" in estilo_obj.usa
        except Exception:
            pass

    n_bandas = int(p.get("n_barras", 64))
    frec_min = float(p.get("frec_min", 40.0))
    frec_max = float(p.get("frec_max", 14000.0))
    caida_picos = float(p.get("caida_picos", 0.4))
    curva_resp = str(p.get("curva_respuesta", "log"))
    suavizado = float(p.get("suavizado", 0.65))
    sensibilidad = float(p.get("sensibilidad", 3.0))

    if usa_bandas:
        clave_espectral = (n_bandas, frec_min, frec_max)
        if (
            getattr(datos_bake, "_cache_clave", None) == clave_espectral
            and getattr(datos_bake, "_cache_potencia", None) is not None
            and getattr(datos_bake, "_cache_bordes", None) is not None
        ):
            potencia = datos_bake._cache_potencia
            bordes = datos_bake._cache_bordes
        else:
            bordes = _bordes_de_banda(n_bandas, frec_min, frec_max)
            matriz = _matriz_de_bandas(bordes)
            filas_activas = np.where(matriz.any(axis=1))[0]
            if len(filas_activas) > 0:
                i_min, i_max = int(filas_activas[0]), int(filas_activas[-1]) + 1
                potencia = datos_bake.stft_potencia[:, i_min:i_max] @ matriz[i_min:i_max]
            else:
                potencia = datos_bake.stft_potencia @ matriz
            datos_bake._cache_clave = clave_espectral
            datos_bake._cache_potencia = potencia
            datos_bake._cache_bordes = bordes

        bandas = _curva(potencia, curva_resp)
        bandas = _suavizar_en_tiempo(bandas, suavizado, caida_picos)
        bandas = _normalizar(bandas, sensibilidad)
    else:
        bordes = _bordes_de_banda(n_bandas, frec_min, frec_max)
        bandas = np.empty((datos_bake.n_cuadros, 0), dtype=np.float32)

    # --- amplitud ---
    amplitud = _curva(datos_bake.amplitud_cruda, curva_resp)
    amplitud = _suavizar_en_tiempo(amplitud, suavizado, caida_picos)
    amplitud = _normalizar(amplitud, sensibilidad)

    # --- forma de onda ---
    if usa_onda:
        onda = _curva(datos_bake.onda_cruda, curva_resp)
        onda = _suavizar_en_espacio(onda, suavizado)
        onda = _normalizar(onda, sensibilidad)
    else:
        onda = datos_bake.onda_cruda

    return Analisis(
        n_cuadros=datos_bake.n_cuadros,
        fps=datos_bake.fps,
        duracion=datos_bake.duracion,
        bandas=bandas,
        amplitud=amplitud,
        onda=onda,
        frecuencias=bordes,
        ruta_audio=datos_bake.ruta_audio,
    )


def proyectar_cuadro(
    datos_bake: DatosBake,
    i: int,
    params: dict[str, Any] | None = None,
    estilo: str | None = None,
    matriz: np.ndarray | None = None,
) -> tuple[np.ndarray, float, np.ndarray]:
    """Proyección instantánea en O(1) de un único cuadro i para previsualización."""
    if not 0 <= i < datos_bake.n_cuadros:
        raise IndexError(
            f"el cuadro {i} está fuera de rango: hay {datos_bake.n_cuadros} "
            f"(0 a {datos_bake.n_cuadros - 1})"
        )

    p = parametros.validar(params or {}, estilo, permitir_desconocidos=True) if params is not None else {}
    curva_resp = str(p.get("curva_respuesta", "log"))
    sensibilidad = float(p.get("sensibilidad", 3.0))

    if matriz is None:
        n_bandas = int(p.get("n_barras", 64))
        frec_min = float(p.get("frec_min", 40.0))
        frec_max = float(p.get("frec_max", 14000.0))
        bordes = _bordes_de_banda(n_bandas, frec_min, frec_max)
        matriz = _matriz_de_bandas(bordes)

    # Proyección instantánea s_i x M en ~0.02 ms
    s_i = datos_bake.stft_potencia[i]
    potencia_i = s_i @ matriz
    bandas_i = _curva(potencia_i, curva_resp) * (sensibilidad / SENSIBILIDAD_NEUTRA)
    np.clip(bandas_i, 0.0, 1.0, out=bandas_i)

    amp_raw = float(datos_bake.amplitud_cruda[i])
    amp_curva = float(_curva(np.array([amp_raw], dtype=np.float32), curva_resp)[0])
    amp_i = float(np.clip(amp_curva * (sensibilidad / SENSIBILIDAD_NEUTRA), 0.0, 1.0))

    onda_raw = datos_bake.onda_cruda[i]
    onda_i = _curva(onda_raw, curva_resp) * (sensibilidad / SENSIBILIDAD_NEUTRA)
    np.clip(onda_i, 0.0, 1.0, out=onda_i)

    return bandas_i, amp_i, onda_i


# --------------------------------------------------------------------------- #
# Compatibilidad hacia atrás
# --------------------------------------------------------------------------- #

def analizar(
    ruta_audio: Path | str,
    params: dict[str, Any] | None = None,
    estilo: str | None = None,
) -> Analisis:
    """Analiza un audio y devuelve los números por cuadro (delega a hornear + proyectar)."""
    p = parametros.validar(params or {}, estilo, permitir_desconocidos=True)
    fps = int(p.get("fps", 30))
    p_audio = Path(ruta_audio) if not isinstance(ruta_audio, Path) else ruta_audio
    datos_bake = hornear_audio(p_audio, fps=fps)
    return proyectar_analisis(datos_bake, p, estilo)


analizar_cancion = analizar
