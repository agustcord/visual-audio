#!/usr/bin/env python3
"""Genera un overlay de visualización de audio con canal alpha, para Drift.

Toma un archivo de audio y produce un video WebM (VP9, `yuva420p`) que contiene
sólo la forma de onda sobre fondo **transparente**. El resultado se importa a
Drift y se coloca en una pista por encima del video: Drift compone la
transparencia y el tamaño, la posición y la opacidad se ajustan con sus propios
controles de clip.

Por qué así y no como un efecto de Drift: Drift no expone ningún dato de audio a
sus shaders, así que un visualizador no puede reaccionar a la música en tiempo
de render. El análisis completo está en `docs/VIABILIDAD.md`.

Ejemplos
--------
    # Lo mínimo
    python tools/generar_overlay.py tests/fixtures/pista_prueba.wav

    # Con estilo
    python tools/generar_overlay.py cancion.mp3 -o onda.webm \\
        --color "#00E5FF" --ancho 1920 --alto 360 --fps 30 --modo cline
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Modos de dibujo de `showwaves`. La descripción es para el --help.
MODOS = {
    "cline": "línea centrada, espejada arriba y abajo (la más parecida a un ecualizador)",
    "line": "una línea por columna, desde el borde inferior",
    "p2p": "picos conectados punto a punto, contorno continuo",
    "point": "un píxel por muestra, aspecto granulado",
}

# Escalas de amplitud. Con audio comprimido `lin` se ve plano; `sqrt` suele ser
# el mejor punto medio para música.
ESCALAS = {
    "lin": "lineal, fiel a la amplitud",
    "sqrt": "raíz cuadrada, levanta los pasajes suaves (recomendada)",
    "cbrt": "raíz cúbica, los levanta más",
    "log": "logarítmica, máximo contraste en lo suave",
}

RE_COLOR = re.compile(r"^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")

# Los dos contenedores con alpha que Drift produce en sus propios presets de
# exportación (`src/engine/Exporter.cpp`, tabla de presets):
#
#   vp9_alpha    -> AV_PIX_FMT_YUVA420P     en webm
#   prores_4444  -> AV_PIX_FMT_YUVA444P10LE en mov
#
# Si Drift los exporta, los sabe leer. Generamos los mismos dos y nada más.
FORMATOS = {
    "webm": "VP9 con alpha en WebM. Liviano. Es el que Drift exporta como 'vp9_alpha'",
    "mov": "ProRes 4444 en MOV. Sin pérdida y mucho más pesado, pero es el camino de "
           "alpha más robusto de Drift: lo detecta por el formato de píxel Y por una "
           "rama dedicada al codec",
}
EXTENSION = {"webm": ".webm", "mov": ".mov"}


class ErrorDeGeneracion(Exception):
    """Falla esperable y explicable: se reporta sin traceback."""


# --------------------------------------------------------------------------- #
# Utilidades de entorno
# --------------------------------------------------------------------------- #

def exigir_herramienta(nombre: str) -> str:
    ruta = shutil.which(nombre)
    if not ruta:
        raise ErrorDeGeneracion(
            f"no se encontró '{nombre}' en el PATH.\n"
            f"  Se necesita FFmpeg para generar el overlay. Instalalo o agregá su\n"
            f"  carpeta 'bin' al PATH. En esta máquina vive en C:\\ffmpeg\\bin."
        )
    return ruta


def sondear_audio(ffprobe: str, ruta: Path) -> dict:
    """Devuelve {duracion, sample_rate, canales, codec} del primer stream de audio."""
    if not ruta.exists():
        raise ErrorDeGeneracion(f"el archivo de audio no existe: {ruta}")

    cmd = [
        ffprobe, "-v", "error",
        "-select_streams", "a:0",
        "-show_entries", "stream=codec_name,sample_rate,channels",
        "-show_entries", "format=duration",
        "-of", "json", str(ruta),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        raise ErrorDeGeneracion(
            f"ffprobe no pudo leer '{ruta}':\n  {res.stderr.strip()}"
        )

    datos = json.loads(res.stdout or "{}")
    streams = datos.get("streams") or []
    if not streams:
        raise ErrorDeGeneracion(
            f"'{ruta}' no tiene ningún stream de audio.\n"
            f"  ¿Es un archivo de video sin audio, o una imagen?"
        )

    duracion = float((datos.get("format") or {}).get("duration") or 0.0)
    if duracion <= 0.0:
        raise ErrorDeGeneracion(f"'{ruta}' declara duración {duracion}; no hay nada que dibujar.")

    s = streams[0]
    return {
        "duracion": duracion,
        "sample_rate": int(s.get("sample_rate") or 0),
        "canales": int(s.get("channels") or 0),
        "codec": s.get("codec_name") or "?",
    }


# --------------------------------------------------------------------------- #
# Construcción del comando
# --------------------------------------------------------------------------- #

def argumentos_de_codec(formato: str, crf: int, cpu_used: int) -> list[str]:
    """Los argumentos de codificación de cada formato, calcados de lo que hace Drift.

    **`-auto-alt-ref 0` en VP9 no es una optimización, es obligatorio.** El propio
    exportador de Drift lo desactiva cuando el preset lleva alpha
    (`src/engine/Exporter.cpp:895-898`), con el comentario *"VP9 with an alpha plane
    cannot use automatic alternate-reference frames"*.

    Omitirlo fue el error del primer PoC. libvpx-vp9 activa alt-ref por su cuenta con
    `-deadline good`, y esos cuadros de referencia son **invisibles**: no llevan su
    paquete de alpha asociado, así que la correspondencia entre cuadro y alpha se
    desalinea. El síntoma es traicionero — muestras puntuales decodifican bien y la
    reproducción completa muestra fondo negro — y fue exactamente lo que pasó.
    """
    if formato == "webm":
        return [
            "-c:v", "libvpx-vp9",
            "-pix_fmt", "yuva420p",
            "-b:v", "0", "-crf", str(crf),
            "-row-mt", "1",
            "-deadline", "good", "-cpu-used", str(cpu_used),
            "-auto-alt-ref", "0",
            "-lag-in-frames", "0",   # sin lag no hay ventana para que aparezcan alt-refs
        ]
    # ProRes 4444: sin pérdida, sin parámetro de calidad. `-vendor apl0` se marca
    # como Apple, que es lo que espera cualquier lector de ProRes.
    return [
        "-c:v", "prores_ks",
        "-profile:v", "4444",
        "-pix_fmt", "yuva444p10le",
        "-alpha_bits", "16",
        "-vendor", "apl0",
    ]


def construir_comando(
    ffmpeg: str, audio: Path, salida: Path, *,
    duracion: float, ancho: int, alto: int, fps: int, color: str,
    modo: str, escala: str, trazo: str, formato: str,
    lienzo: tuple[int, int] | None, pad_x: int, pad_y: int,
    crf: int, cpu_used: int, sobrescribir: bool,
) -> list[str]:
    """Arma el comando de FFmpeg como lista de argumentos.

    El filtro es una sola línea porque **`showwaves` ya emite RGBA con el fondo
    transparente**. Medido: en un cuadro de 640x120 al segundo 0.4 de la pista de
    prueba, 76.790 de 76.800 píxeles salen con alpha 0, y la onda llega a alpha
    255. El color se le pasa directo con `colors=` y sale correcto.

    Eso hace innecesario todo el andamiaje que uno esperaría (dibujar en blanco,
    convertir a máscara gris, generar una fuente de color plano y combinarlas con
    `alphamerge`). Ese camino se intentó primero y además **no funciona**:
    `alphamerge` devolvía alpha 255 en todo el cuadro. La historia está en el
    handoff T2, para que nadie lo vuelva a intentar.

    Argumentos por qué:

    - `draw=full` por default, **no** el `scale` que trae FFmpeg. Con `scale`, la
      intensidad de cada columna se reparte entre las muestras que caen en ella
      (a 48 kHz y 30 fps son 1600 por columna), así que a resolución alta dibuja
      un pelo casi invisible: medido en PNG sin pérdida a 1920x320, el alpha
      máximo llegaba a **153 y ningún píxel era opaco**. Con `draw=full` el mismo
      cuadro da **max 255 y 58.419 píxeles opacos**, con la misma cantidad de
      transparentes. No era el codec: era esto.
    - Los argumentos de codec salen de `argumentos_de_codec`, que copia lo que hace
      el exportador de Drift para cada formato con alpha. Leé su docstring: hay un
      argumento de VP9 que es obligatorio y cuya ausencia produce fondo negro.
    - `setpts` corrige un corrimiento de sincronía de 100 ms. Ver el comentario en el
      armado del filtro: es el hallazgo menos obvio de todo este archivo.
    - `-an`: el overlay no lleva audio. El audio ya está en la timeline de Drift;
      duplicarlo sólo sumaría peso y riesgo de doble reproducción.
    """
    filtro = (
        f"[0:a]showwaves="
        f"s={ancho}x{alto}:"
        f"mode={modo}:"
        f"rate={fps}:"
        f"scale={escala}:"
        f"draw={trazo}:"
        f"colors={color}"
    )

    # Con `--lienzo`, la banda de onda se sitúa dentro de un cuadro del tamaño del
    # proyecto y el resto queda **transparente de verdad** (`0x00000000`, verificado:
    # la zona rellenada mide alpha 0 exacto, mínimo y máximo).
    #
    # Sirve para dos cosas. La obvia: resuelve la personalización de *posición* sin
    # tocar nada en Drift. La menos obvia: elimina toda pregunta sobre qué hace Drift
    # con un clip más chico que el lienzo — si el clip ya viene del tamaño exacto, no
    # hay escalado ni relleno que pueda meter negro donde no lo queremos.
    if lienzo:
        lienzo_w, lienzo_h = lienzo
        filtro += f",pad={lienzo_w}:{lienzo_h}:{pad_x}:{pad_y}:color=0x00000000"

    # `setpts=PTS-STARTPTS` corrige un corrimiento de sincronía, no es cosmético.
    #
    # Medido: `showwaves` entrega los 480 cuadros que corresponden a 16 s a 30 fps,
    # con intervalos exactos de 1/30, pero **etiqueta el primero en PTS 0.100 s en vez
    # de 0**, y el último en 16.067. Es un desplazamiento constante de 3 cuadros.
    #
    # Tenía dos consecuencias, y la segunda es la grave:
    #   1. `-t` recortaba los 3 cuadros de la cola (477 en vez de 480).
    #   2. **Todo el overlay quedaba 100 ms atrasado respecto de la música.** En un
    #      video musical eso se nota: la onda reacciona después del golpe.
    #
    # Rebasar los timestamps arregla las dos de una.
    filtro += ",setpts=PTS-STARTPTS"

    filtro += "[salida]"

    return [
        ffmpeg,
        "-hide_banner", "-loglevel", "error", "-nostdin",
        "-y" if sobrescribir else "-n",
        "-i", str(audio),
        "-filter_complex", filtro,
        "-map", "[salida]",
        *argumentos_de_codec(formato, crf, cpu_used),
        "-an",
        "-t", f"{duracion:.6f}",
        str(salida),
    ]


# --------------------------------------------------------------------------- #
# Verificación del resultado
# --------------------------------------------------------------------------- #

def auditar_alpha_completo(ffmpeg: str, salida: Path, formato: str,
                           muestra_w: int = 160, muestra_h: int = 90) -> dict | None:
    """Audita el canal alpha de **todos** los cuadros, no de un par de muestras.

    Esto existe por una falla concreta: la primera versión medía dos instantes y
    los dos daban bien, pero al reproducir en Drift el overlay salía con fondo
    negro. La causa era que a VP9 le faltaba `-auto-alt-ref 0`, y eso rompe el
    alpha **de algunos cuadros**, no de todos. Dos muestras no podían verlo.

    Cada cuadro se reduce a una miniatura de 64x16 antes de medir, así que el
    costo de recorrer la secuencia entera es bajo y la memoria queda acotada:
    se procesa cuadro por cuadro en vez de acumular la película.

    **El único modo de falla es el cuadro opaco**, donde no queda nada transparente:
    ahí el alpha se perdió y en Drift se ve un rectángulo negro.

    Los cuadros **vacíos** (nada dibujado) se cuentan y se informan, pero **no son una
    falla**: en un pasaje silencioso corresponde que no se dibuje nada. La primera
    versión de esta función los trataba como error y reprobaba un archivo correcto —
    confundir silencio con rotura es un falso positivo, y un verificador que cría
    lobos deja de servir.
    """
    cmd = [ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin"]
    if formato == "webm":
        # Sin esto el decodificador nativo de vp9 ignora el plano alpha en
        # silencio. Drift hace lo mismo en ClipReader.cpp:1002-1010.
        cmd += ["-c:v", "libvpx-vp9"]
    cmd += [
        "-i", str(salida),
        "-vf", f"alphaextract,scale={muestra_w}:{muestra_h}",
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]

    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0 or not res.stdout:
        return None

    por_cuadro = muestra_w * muestra_h
    datos = res.stdout
    n = len(datos) // por_cuadro
    if n == 0:
        return None

    opacos: list[int] = []
    vacios: list[int] = []
    max_global, min_global = 0, 255
    for i in range(n):
        f = datos[i * por_cuadro:(i + 1) * por_cuadro]
        mn, mx = min(f), max(f)
        max_global = max(max_global, mx)
        min_global = min(min_global, mn)
        if mn > 200:            # nada transparente en todo el cuadro
            opacos.append(i)
        elif mx < 24:           # nada dibujado en todo el cuadro
            vacios.append(i)

    return {
        "cuadros": n,
        "opacos": opacos,
        "vacios": vacios,
        "max": max_global,
        "min": min_global,
    }


def verificar_salida(ffmpeg: str, ffprobe: str, salida: Path, formato: str,
                     duracion_audio: float, fps: int) -> list[tuple[bool, str]]:
    """Comprueba los criterios PoC-1..PoC-3 de docs/PLAN_ETAPA1.md."""
    resultados: list[tuple[bool, str]] = []

    # ---- PoC-1: el archivo existe y no está vacío ----
    existe = salida.exists() and salida.stat().st_size > 0
    tam = salida.stat().st_size if salida.exists() else 0
    resultados.append((existe, f"PoC-1  archivo generado y no vacío ({tam:,} bytes)"))
    if not existe:
        return resultados

    cmd = [
        ffprobe, "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=pix_fmt,width,height,codec_name,profile",
        "-show_entries", "stream_tags=alpha_mode",
        "-show_entries", "format=duration",
        "-of", "json", str(salida),
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        resultados.append((False, f"PoC-2  ffprobe no pudo leer la salida: {res.stderr.strip()}"))
        return resultados

    datos = json.loads(res.stdout or "{}")
    streams = datos.get("streams") or []
    if not streams:
        resultados.append((False, "PoC-2  la salida no tiene stream de video"))
        return resultados

    v = streams[0]
    pix_fmt = v.get("pix_fmt", "?")

    # ---- PoC-2a: la marca de alpha, según cómo la declara cada formato ----
    #
    # WebM: el alpha de VP9 viaja como datos adicionales de cada bloque, NO en el
    # bitstream. `ffprobe` reporta `pix_fmt=yuv420p` aunque el alpha esté ahí, así
    # que mirar ese campo da un falso negativo. La marca es el tag `alpha_mode`.
    #
    # MOV/ProRes: el formato de píxel sí lo dice (`yuva444p10le`), y además Drift
    # tiene una rama dedicada que reconoce ProRes 4444 por codec y perfil.
    if formato == "webm":
        alpha_mode = (v.get("tags") or {}).get("alpha_mode")
        marca_ok = alpha_mode == "1"
        detalle = (f"alpha_mode={alpha_mode!r}, codec={v.get('codec_name')}, "
                   f"pix_fmt del bitstream={pix_fmt}")
    else:
        marca_ok = "a" in pix_fmt.replace("yuv", "").replace("gbr", "")
        detalle = (f"pix_fmt={pix_fmt}, codec={v.get('codec_name')}, "
                   f"perfil={v.get('profile')}")
    resultados.append((marca_ok, f"PoC-2a el formato declara alpha ({detalle})"))

    # ---- PoC-2b: el alpha, auditado cuadro por cuadro ----
    auditoria = auditar_alpha_completo(ffmpeg, salida, formato)
    if auditoria is None:
        resultados.append((False, "PoC-2b no se pudo decodificar el canal alpha"))
    else:
        n = auditoria["cuadros"]
        opacos, vacios = auditoria["opacos"], auditoria["vacios"]
        sanos = n - len(opacos) - len(vacios)

        # Sólo los cuadros opacos reprueban. Los vacíos son silencio, no rotura.
        ok = not opacos and sanos > 0
        msg = (f"PoC-2b sin cuadros opacos: {n - len(opacos)}/{n} conservan "
               f"transparencia (rango global {auditoria['min']}..{auditoria['max']})")
        if opacos:
            primeros = ", ".join(str(i) for i in opacos[:8])
            msg += (f"\n         {len(opacos)} cuadros OPACOS: el alpha se perdió. "
                    f"En Drift se ven como un rectángulo negro"
                    f"\n         índices: {primeros}{'…' if len(opacos) > 8 else ''}")
        if vacios:
            msg += (f"\n         nota: {len(vacios)} cuadros sin nada dibujado "
                    f"(pasajes silenciosos — esperado, no es falla)")
        resultados.append((ok, msg))

    # ---- PoC-3: duración, contada por cuadros y no por lo que declara el contenedor ----
    #
    # La duración del contenedor **miente**. Un WebM al que le faltaban 3 cuadros
    # declaraba igual 16.000 s y la comprobación pasaba con 0.0 ms de desvío; el mismo
    # contenido en MOV declaraba los 15.900 s reales y reprobaba. El dato honesto es la
    # cantidad de cuadros que realmente se decodifican, que la auditoría de alpha ya
    # cuenta de paso.
    dur_declarada = float((datos.get("format") or {}).get("duration") or 0.0)
    tolerancia = 1.0 / fps

    if auditoria is not None:
        cuadros = auditoria["cuadros"]
        dur_real = cuadros / fps
        esperados = round(duracion_audio * fps)
        delta = abs(dur_real - duracion_audio)
        nota = ""
        if abs(dur_declarada - dur_real) > tolerancia / 2:
            nota = (f"\n         (el contenedor declara {dur_declarada:.3f}s; "
                    f"manda el conteo de cuadros)")
        resultados.append((
            delta <= tolerancia,
            f"PoC-3  {cuadros} cuadros decodificados de {esperados} esperados "
            f"= {dur_real:.3f}s vs audio {duracion_audio:.3f}s "
            f"(desvío {delta * 1000:.1f} ms, tolerancia {tolerancia * 1000:.1f} ms){nota}",
        ))
    else:
        delta = abs(dur_declarada - duracion_audio)
        resultados.append((
            delta <= tolerancia,
            f"PoC-3  duración declarada {dur_declarada:.3f}s vs audio "
            f"{duracion_audio:.3f}s (desvío {delta * 1000:.1f} ms) "
            f"— no se pudieron contar los cuadros, dato menos confiable",
        ))

    return resultados


# --------------------------------------------------------------------------- #
# Interfaz de línea de comandos
# --------------------------------------------------------------------------- #

def tipo_tamano(valor: str) -> tuple[int, int]:
    """Parsea '1920x1080'."""
    m = re.match(r"^(\d+)[xX](\d+)$", valor.strip())
    if not m:
        raise argparse.ArgumentTypeError(
            f"tamaño inválido: '{valor}'. Usá ANCHOxALTO, por ejemplo '1920x1080'."
        )
    w, h = int(m.group(1)), int(m.group(2))
    if w <= 0 or h <= 0:
        raise argparse.ArgumentTypeError(f"el tamaño debe ser positivo, recibí {valor}")
    return w, h


def calcular_posicion(lienzo: tuple[int, int], ancho: int, alto: int,
                      posicion: str, margen: int) -> tuple[int, int]:
    """Dónde va la banda de onda dentro del lienzo. Devuelve (x, y) para `pad`."""
    lw, lh = lienzo
    if ancho > lw or alto > lh:
        raise ErrorDeGeneracion(
            f"la banda de onda ({ancho}x{alto}) no cabe en el lienzo ({lw}x{lh}).\n"
            f"  Bajá --ancho/--alto, o subí --lienzo."
        )
    x = (lw - ancho) // 2
    if posicion == "arriba":
        y = margen
    elif posicion == "centro":
        y = (lh - alto) // 2
    else:  # abajo
        y = lh - alto - margen
    return x, max(0, min(y, lh - alto))


def tipo_color(valor: str) -> str:
    """Acepta '#RGB', '#RRGGBB' o un nombre de color de FFmpeg."""
    if RE_COLOR.match(valor):
        return valor
    if re.match(r"^[A-Za-z]+$", valor):
        return valor  # nombre tipo 'white', 'cyan'; FFmpeg valida
    raise argparse.ArgumentTypeError(
        f"color inválido: '{valor}'. Usá '#RRGGBB' (ej. '#00E5FF') o un nombre como 'cyan'."
    )


def entero_positivo(valor: str) -> int:
    try:
        n = int(valor)
    except ValueError:
        raise argparse.ArgumentTypeError(f"'{valor}' no es un número entero")
    if n <= 0:
        raise argparse.ArgumentTypeError(f"debe ser mayor que 0, recibí {n}")
    return n


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("audio", type=Path, help="archivo de audio de entrada (wav, mp3, flac, m4a…)")
    p.add_argument("-o", "--salida", type=Path, default=None,
                   help="archivo .webm de salida (default: <audio>_overlay.webm)")

    g = p.add_argument_group("aspecto")
    g.add_argument("--color", type=tipo_color, default="#FFFFFF",
                   help="color de la onda, '#RRGGBB' o nombre (default: #FFFFFF)")
    g.add_argument("--ancho", type=entero_positivo, default=1920, help="ancho en píxeles (default: 1920)")
    g.add_argument("--alto", type=entero_positivo, default=320, help="alto en píxeles (default: 320)")
    g.add_argument("--fps", type=entero_positivo, default=30, help="cuadros por segundo (default: 30)")
    g.add_argument("--modo", choices=sorted(MODOS), default="cline",
                   help="forma de dibujo (default: cline). " +
                        "; ".join(f"{k}: {v}" for k, v in MODOS.items()))
    g.add_argument("--escala", choices=sorted(ESCALAS), default="sqrt",
                   help="escala de amplitud (default: sqrt). " +
                        "; ".join(f"{k}: {v}" for k, v in ESCALAS.items()))
    g.add_argument("--lienzo", type=tipo_tamano, default=None, metavar="ANCHOxALTO",
                   help="genera el cuadro completo del tamaño del proyecto (ej. '1920x1080') "
                        "con la banda de onda situada dentro y el resto transparente. "
                        "Sin esto, el archivo mide sólo la banda (--ancho x --alto)")
    g.add_argument("--posicion", choices=("arriba", "centro", "abajo"), default="abajo",
                   help="dónde va la banda dentro del lienzo (default: abajo). Sólo aplica con --lienzo")
    g.add_argument("--margen", type=int, default=0, metavar="PX",
                   help="separación en píxeles del borde, para --posicion arriba o abajo (default: 0)")
    g.add_argument("--trazo", choices=("full", "scale"), default="full",
                   help="grosor del trazo (default: full). full: cada muestra a "
                        "intensidad plena, onda sólida y bien visible; scale: reparte "
                        "la intensidad, queda un trazo tenue que en resoluciones "
                        "grandes casi no se ve")

    g2 = p.add_argument_group("codificación")
    g2.add_argument("--formato", choices=sorted(FORMATOS), default="webm",
                    help="formato de salida (default: webm). " +
                         "; ".join(f"{k}: {v}" for k, v in FORMATOS.items()))
    g2.add_argument("--crf", type=int, default=36, metavar="0-63",
                    help="calidad VP9: menor = mejor y más pesado (default: 36). "
                         "Medido sobre la pista de prueba de 16 s: crf 30 = 13.7 MB, "
                         "36 = 11.0 MB, 42 = 8.4 MB, 48 = 6.1 MB, sin degradación "
                         "medible del alpha en ninguno. El overlay pesa igual bastante: "
                         "cada cuadro es una ventana de onda nueva, así que la "
                         "compresión temporal no tiene de dónde agarrarse")
    g2.add_argument("--cpu-used", type=int, default=4, metavar="0-8",
                    help="velocidad de VP9: mayor = más rápido y algo peor (default: 4)")
    g2.add_argument("-n", "--no-sobrescribir", action="store_true",
                    help="fallar si el archivo de salida ya existe")

    g3 = p.add_argument_group("diagnóstico")
    g3.add_argument("--sin-verificar", action="store_true",
                    help="no comprobar el resultado al terminar")
    g3.add_argument("--mostrar-comando", action="store_true",
                    help="imprimir el comando de FFmpeg y salir sin ejecutarlo")

    return p


def main(argv: list[str] | None = None) -> int:
    args = construir_parser().parse_args(argv)

    try:
        if not 0 <= args.crf <= 63:
            raise ErrorDeGeneracion(f"--crf debe estar entre 0 y 63, recibí {args.crf}")
        if not 0 <= args.cpu_used <= 8:
            raise ErrorDeGeneracion(f"--cpu-used debe estar entre 0 y 8, recibí {args.cpu_used}")

        ffmpeg = exigir_herramienta("ffmpeg")
        ffprobe = exigir_herramienta("ffprobe")

        info = sondear_audio(ffprobe, args.audio)

        ext = EXTENSION[args.formato]
        salida = args.salida or args.audio.with_name(args.audio.stem + "_overlay" + ext)
        if salida.suffix.lower() != ext:
            raise ErrorDeGeneracion(
                f"la salida '{salida.name}' no termina en '{ext}'.\n"
                f"  El formato '{args.formato}' necesita ese contenedor para llevar el "
                f"canal alpha. Renombrá la salida o cambiá --formato."
            )
        salida.parent.mkdir(parents=True, exist_ok=True)

        pad_x, pad_y = 0, 0
        if args.lienzo:
            if args.margen < 0:
                raise ErrorDeGeneracion(f"--margen no puede ser negativo, recibí {args.margen}")
            pad_x, pad_y = calcular_posicion(args.lienzo, args.ancho, args.alto,
                                             args.posicion, args.margen)

        cmd = construir_comando(
            ffmpeg, args.audio, salida,
            duracion=info["duracion"],
            ancho=args.ancho, alto=args.alto, fps=args.fps, color=args.color,
            modo=args.modo, escala=args.escala, trazo=args.trazo, formato=args.formato,
            lienzo=args.lienzo, pad_x=pad_x, pad_y=pad_y,
            crf=args.crf, cpu_used=args.cpu_used,
            sobrescribir=not args.no_sobrescribir,
        )

        if args.mostrar_comando:
            print(subprocess.list2cmdline(cmd))
            return 0

        print(f"audio   : {args.audio.name}  "
              f"({info['duracion']:.3f}s, {info['sample_rate']} Hz, "
              f"{info['canales']} canal{'es' if info['canales'] != 1 else ''}, {info['codec']})")
        if args.lienzo:
            print(f"overlay : lienzo {args.lienzo[0]}x{args.lienzo[1]}, "
                  f"banda {args.ancho}x{args.alto} en ({pad_x},{pad_y}) [{args.posicion}]")
        else:
            print(f"overlay : {args.ancho}x{args.alto} (sólo la banda, sin lienzo)")
        print(f"estilo  : {args.fps}fps, modo={args.modo}, escala={args.escala}, "
              f"trazo={args.trazo}, color={args.color}")
        print(f"formato : {args.formato}"
              + (f" (VP9 alpha, crf {args.crf})" if args.formato == "webm"
                 else " (ProRes 4444, sin pérdida)"))
        print(f"salida  : {salida}")
        print("generando…")

        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            detalle = (res.stderr or res.stdout or "").strip()
            if "File exists" in detalle:
                raise ErrorDeGeneracion(
                    f"'{salida}' ya existe y se pidió --no-sobrescribir."
                )
            raise ErrorDeGeneracion(f"FFmpeg falló (código {res.returncode}):\n  {detalle}")

        if args.sin_verificar:
            print("listo (sin verificar).")
            return 0

        print("\nverificación:")
        resultados = verificar_salida(ffmpeg, ffprobe, salida, args.formato,
                                      info["duracion"], args.fps)
        for ok, texto in resultados:
            print(f"  {'OK  ' if ok else 'FALLA'}  {texto}")

        if not all(ok for ok, _ in resultados):
            print("\nEl overlay se generó pero no cumple todos los criterios.", file=sys.stderr)
            return 1

        print(f"\nTodo OK. Siguiente paso: importá '{salida.name}' a Drift y ponelo "
              f"en una pista por encima del video.")
        return 0

    except ErrorDeGeneracion as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\ninterrumpido.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
