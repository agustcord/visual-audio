#!/usr/bin/env python3
"""Pruebas del análisis de audio — criterios 1.1 a 1.4 de la etapa 1.

Sin dependencias nuevas: se ejecuta directo y devuelve 0 o 1.

    python tests\\test_analisis.py

## Cómo se verifica que las bandas están bien repartidas

La parte interesante es el criterio 1.4. Verificarlo con música **no sirve**: si el
perfil del espectro sale desparejo no se puede saber si el análisis está mal o si
la canción simplemente no tiene nada en esa zona. De hecho la pista de prueba del
proyecto no tiene ningún instrumento entre 500 Hz y 2 kHz, así que mirarla ahí no
dice nada.

Entonces se usa **ruido rosa generado acá mismo**, que tiene una respuesta correcta
conocida: su energía se reparte por igual en cada octava, que es como se reparte la
música. Con bandas logarítmicas y pesos por energía, el ruido rosa tiene que salir
**plano**. Si sale inclinado, el reparto de bandas está mal, y se sabe en qué
dirección.

El ruido blanco se usa como control opuesto: tiene que salir **subiendo**, porque
sus bandas altas son más anchas y por lo tanto acumulan más energía.
"""

from __future__ import annotations

import struct
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from visualizador import analisis, consola, parametros  # noqa: E402

consola.preparar()

PISTA = RAIZ / "tests" / "fixtures" / "pista_prueba.wav"

# Ataques conocidos de la pista de prueba. A 120 BPM en 4/4 cada compás dura 2 s;
# el bombo del compás 5 cae en 10.0 s, justo después del compás de casi silencio,
# así que es el borde más nítido de toda la pista.
GOLPE_TRAS_SILENCIO = 10.0
ARRANQUE_SILENCIO = 8.0

_fallas: list[str] = []
_pasadas = 0


def afirmar(condicion: bool, titulo: str, detalle: str = "") -> None:
    global _pasadas
    if condicion:
        _pasadas += 1
        print(f"  OK    {titulo}" + (f"  ({detalle})" if detalle else ""))
    else:
        _fallas.append(titulo)
        print(f"  FALLA {titulo}" + (f"  ({detalle})" if detalle else ""))


def escribir_wav(destino: Path, mono: np.ndarray, tasa: int = 48_000) -> None:
    pico = np.abs(mono).max()
    if pico > 0:
        mono = mono / pico * 0.89   # -1 dBFS, igual que la pista del proyecto
    enteros = (mono * 32767).astype("<i2")
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(tasa)
        w.writeframes(enteros.tobytes())


def ruido(tipo: str, segundos: float = 6.0, tasa: int = 48_000) -> np.ndarray:
    """Ruido blanco o rosa, determinista.

    El rosa se arma en el dominio de la frecuencia: ruido blanco escalado por
    1/sqrt(f), que da densidad espectral proporcional a 1/f — la definición de
    ruido rosa.
    """
    rng = np.random.default_rng(12345)
    n = int(segundos * tasa)
    blanco = rng.standard_normal(n).astype(np.float64)
    if tipo == "blanco":
        return blanco

    espectro = np.fft.rfft(blanco)
    frecs = np.fft.rfftfreq(n, 1.0 / tasa)
    escala = np.ones_like(frecs)
    escala[1:] = 1.0 / np.sqrt(frecs[1:])
    return np.fft.irfft(espectro * escala, n=n)


# --------------------------------------------------------------------------- #

def criterio_1_1() -> None:
    """La cantidad de cuadros es exactamente round(duracion * fps)."""
    print("\n1.1  Cantidad de cuadros exacta, en 24 / 25 / 30 / 60 fps")
    for fps in (24, 25, 30, 60):
        a = analisis.analizar(PISTA, {"fps": fps})
        esperado = round(a.duracion * fps)
        afirmar(a.n_cuadros == esperado, f"{fps} fps",
                f"{a.n_cuadros} cuadros, esperado {esperado}")
        afirmar(a.bandas.shape[0] == a.n_cuadros
                and a.amplitud.shape[0] == a.n_cuadros
                and a.onda.shape[0] == a.n_cuadros,
                f"{fps} fps: las tres salidas tienen la misma cantidad de cuadros")

        # Las columnas de la forma de onda no pueden ser más que las muestras que
        # tiene el cuadro: pedir más sería inventar resolución.
        muestras_por_cuadro = analisis.TASA / fps
        afirmar(a.onda.shape[1] <= muestras_por_cuadro + 1,
                f"{fps} fps: las columnas de la onda no exceden las muestras del cuadro",
                f"{a.onda.shape[1]} columnas para {muestras_por_cuadro:.0f} muestras")


def criterio_1_2() -> None:
    """Todo en 0..1, sin NaN ni infinitos, con cualquier combinación de valores."""
    print("\n1.2  Valores en 0..1, sin NaN ni infinitos")
    combinaciones = [
        ({}, "defaults"),
        ({"sensibilidad": 0.5, "suavizado": 0.0, "caida_picos": 0.0}, "todo al mínimo"),
        ({"sensibilidad": 10.0, "suavizado": 1.0, "caida_picos": 1.0}, "todo al máximo"),
        ({"curva_respuesta": "lineal"}, "curva lineal"),
        ({"curva_respuesta": "log"}, "curva log"),
        ({"n_barras": 5}, "5 barras"),
        ({"n_barras": 240}, "240 barras"),
        ({"frec_min": 20.0, "frec_max": 20000.0}, "espectro completo"),
        ({"frec_min": 1000.0, "frec_max": 1100.0}, "banda angosta"),
    ]
    for params, nombre in combinaciones:
        a = analisis.analizar(PISTA, params)
        ok = True
        for etiqueta, arr in (("bandas", a.bandas), ("amplitud", a.amplitud), ("onda", a.onda)):
            if not np.isfinite(arr).all() or arr.min() < 0.0 or arr.max() > 1.0:
                ok = False
                print(f"        {etiqueta}: min={arr.min()} max={arr.max()} "
                      f"finitos={np.isfinite(arr).all()}")
        afirmar(ok, nombre)


def criterio_1_3() -> None:
    """El análisis está alineado con el audio, y no reacciona antes de tiempo."""
    print("\n1.3  Alineación temporal: nada de pre-eco")
    # Sin inercia, para medir la alineación cruda y no la del suavizado.
    a = analisis.analizar(PISTA, {"suavizado": 0.0, "caida_picos": 0.0})
    energia = a.bandas.sum(axis=1)
    fps = a.fps

    cuadro_golpe = int(round(GOLPE_TRAS_SILENCIO * fps))

    # El golpe de 10.0 s viene después de casi dos segundos de silencio, así que
    # el cuadro que lo contiene tiene que ser el PRIMERO con energía. Que los
    # cuatro anteriores estén en cero es la prueba de que la ventana es causal:
    # con una ventana centrada, el análisis "vería" el golpe antes de que suene.
    antes = energia[cuadro_golpe - 4:cuadro_golpe]
    afirmar(float(antes.max()) < 0.01,
            "los cuadros previos al golpe están en silencio",
            f"máximo {antes.max():.4f} en los 4 cuadros anteriores")
    afirmar(float(energia[cuadro_golpe]) > 0.5,
            "el cuadro que contiene el golpe ya tiene energía",
            f"{energia[cuadro_golpe]:.3f}")

    # El salto más grande de toda la pista tiene que caer en ese cuadro o en el
    # siguiente — un cuadro de cuantización es correcto y esperable.
    saltos = np.diff(energia)
    cuadro_salto = int(np.argmax(saltos)) + 1
    desvio = cuadro_salto - cuadro_golpe
    afirmar(0 <= desvio <= 1,
            "el salto de energía más grande cae en el cuadro del golpe",
            f"cuadro {cuadro_salto} vs {cuadro_golpe} esperado, desvío {desvio:+d}")

    # Y el compás de casi silencio tiene que verse como tal.
    c0 = int(round(ARRANQUE_SILENCIO * fps))
    c1 = int(round(GOLPE_TRAS_SILENCIO * fps))
    tramo_silencio = energia[c0 + 20:c1].mean()      # +20 salta la cola del bombo
    tramo_intenso = energia[c1:c1 + 60].mean()
    afirmar(tramo_intenso > tramo_silencio * 10,
            "el compás de silencio se distingue del intenso",
            f"silencio {tramo_silencio:.4f} vs intenso {tramo_intenso:.4f}")


def criterio_1_4() -> None:
    """Las bandas reparten el espectro. Se mide con señales de respuesta conocida."""
    print("\n1.4  Reparto del espectro, medido con ruido de respuesta conocida")

    with tempfile.TemporaryDirectory() as tmp:
        rutas = {}
        for tipo in ("rosa", "blanco"):
            ruta = Path(tmp) / f"{tipo}.wav"
            escribir_wav(ruta, ruido(tipo))
            rutas[tipo] = ruta

        params = {"suavizado": 0.0, "caida_picos": 0.0, "curva_respuesta": "lineal",
                  "n_barras": 32, "frec_min": 60.0, "frec_max": 12000.0}

        rosa = analisis.analizar(rutas["rosa"], params).bandas.mean(axis=0)
        blanco = analisis.analizar(rutas["blanco"], params).bandas.mean(axis=0)

        # Ruido rosa: energía por octava constante → bandas logarítmicas planas.
        # Se compara el tercio grave contra el tercio agudo.
        n = len(rosa)
        rosa_grave, rosa_agudo = rosa[:n // 3].mean(), rosa[-n // 3:].mean()
        relacion_rosa = rosa_grave / max(rosa_agudo, 1e-12)
        afirmar(0.4 < relacion_rosa < 2.5,
                "el ruido rosa sale plano (graves ≈ agudos)",
                f"graves/agudos = {relacion_rosa:.2f}x, aceptable entre 0.4 y 2.5")

        # Ruido blanco: densidad plana, pero las bandas agudas son más anchas y
        # acumulan más energía → tiene que subir. Es el control opuesto: si el
        # rosa sale plano por casualidad, el blanco no saldría subiendo.
        blanco_grave, blanco_agudo = blanco[:n // 3].mean(), blanco[-n // 3:].mean()
        afirmar(blanco_agudo > blanco_grave * 2,
                "el ruido blanco sale subiendo, como corresponde",
                f"agudos/graves = {blanco_agudo / max(blanco_grave, 1e-12):.2f}x")

    # Sobre la pista musical: los graves no pueden tapar todo el resto.
    a = analisis.analizar(PISTA)
    f = a.frecuencias
    graves = [i for i in range(a.n_bandas) if f[i + 1] <= 150]
    agudos = [i for i in range(a.n_bandas) if f[i] >= 3000]
    intenso = a.bandas[420:480]
    relacion = intenso[:, graves].mean() / max(intenso[:, agudos].mean(), 1e-12)
    afirmar(relacion < 40,
            "en la pista musical los graves no tapan a los agudos",
            f"graves/agudos = {relacion:.1f}x en el tramo intenso")

    # Y las bandas graves, aunque la FFT no las resuelva, no pueden ser idénticas.
    fila = a.bandas[430][:8]
    repetidos = sum(1 for i in range(len(fila) - 1) if abs(fila[i] - fila[i + 1]) < 1e-9)
    afirmar(repetidos == 0,
            "las bandas graves se interpolan en vez de repetirse",
            f"{repetidos} pares idénticos entre las 8 primeras")


def validacion_de_parametros() -> None:
    """El esquema falla en vez de corregir en silencio."""
    print("\nExtra  El esquema de parámetros rechaza lo inválido")
    casos = [
        ({"sensibilidad": 99.0}, "sensibilidad por encima del máximo"),
        ({"sensibilidad": -1.0}, "sensibilidad negativa"),
        ({"curva_respuesta": "cuadratica"}, "curva inexistente"),
        ({"frec_min": 5000.0, "frec_max": 1000.0}, "frec_min mayor que frec_max"),
        ({"no_existe": 1}, "parámetro desconocido"),
        ({"n_barras": 3}, "menos barras que el mínimo"),
    ]
    for params, nombre in casos:
        try:
            parametros.validar(params)
        except parametros.ErrorDeParametro:
            afirmar(True, nombre)
        else:
            afirmar(False, nombre, "no falló y debería haber fallado")

    # Y acepta lo válido, completando lo que falte.
    completo = parametros.validar({"sensibilidad": 5.0})
    afirmar(completo["sensibilidad"] == 5.0 and completo["suavizado"] == 0.65,
            "completa los valores que faltan con sus defaults")


def main() -> int:
    if not PISTA.exists():
        print(f"error: falta la pista de prueba: {PISTA}\n"
              f"  Generala con: python tests\\fixtures\\generar_audio_prueba.py",
              file=sys.stderr)
        return 2

    print("Pruebas del análisis de audio")
    print(f"  pista   : {PISTA.name}")
    print(f"  ventana : {analisis.VENTANA} muestras a {analisis.TASA} Hz "
          f"({analisis.VENTANA / analisis.TASA * 1000:.0f} ms, "
          f"bins de {analisis.TASA / analisis.VENTANA:.1f} Hz)")

    criterio_1_1()
    criterio_1_2()
    criterio_1_3()
    criterio_1_4()
    validacion_de_parametros()

    print(f"\n{_pasadas} comprobaciones pasadas, {len(_fallas)} fallas")
    if _fallas:
        print("\nFallaron:", file=sys.stderr)
        for f in _fallas:
            print(f"  - {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
