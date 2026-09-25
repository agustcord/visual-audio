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

def construir_comando(
    ffmpeg: str, audio: Path, salida: Path, *,
    duracion: float, ancho: int, alto: int, fps: int, color: str,
    modo: str, escala: str, trazo: str, crf: int, cpu_used: int, sobrescribir: bool,
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
    - `libvpx-vp9` + `yuva420p`: es la combinación de codec y formato con alpha
      que Drift sabe decodificar. `ClipReader.cpp:1002-1010` fuerza el
      decodificador `libvpx-vp9` justamente porque los decodificadores nativos
      de vp9 ignoran el plano alpha de WebM.
    - `-t` con la duración exacta del audio: `showwaves` se pasa unos cuadros
      (medido: 16.100 s para un audio de 16.000 s, o sea 100 ms de más).
    - `-an`: el overlay no lleva audio. El audio ya está en la timeline de Drift;
      duplicarlo sólo sumaría peso y riesgo de doble reproducción.
    """
    tamano = f"{ancho}x{alto}"

    filtro = (
        f"[0:a]showwaves="
        f"s={tamano}:"
        f"mode={modo}:"
        f"rate={fps}:"
        f"scale={escala}:"
        f"draw={trazo}:"
        f"colors={color}"
        f"[salida]"
    )

    return [
        ffmpeg,
        "-hide_banner", "-loglevel", "error", "-nostdin",
        "-y" if sobrescribir else "-n",
        "-i", str(audio),
        "-filter_complex", filtro,
        "-map", "[salida]",
        "-c:v", "libvpx-vp9",
        "-pix_fmt", "yuva420p",
        "-b:v", "0", "-crf", str(crf),   # calidad constante
        "-row-mt", "1",                  # multihilo por filas
        "-deadline", "good", "-cpu-used", str(cpu_used),
        "-an",
        "-t", f"{duracion:.6f}",
        str(salida),
    ]


# --------------------------------------------------------------------------- #
# Verificación del resultado
# --------------------------------------------------------------------------- #

def medir_alpha(ffmpeg: str, salida: Path, segundo: float) -> tuple[int, int, int, int] | None:
    """Decodifica un cuadro y devuelve (min, max, n_transparentes, n_total) del alpha.

    Fuerza `-c:v libvpx-vp9` **antes** de `-i`, que es lo que hay que hacer para
    que el plano alpha de un WebM se decodifique: el decodificador nativo de vp9
    lo ignora en silencio. Drift hace exactamente lo mismo
    (`src/engine/ClipReader.cpp:1002-1010`), así que esta medición se parece a lo
    que va a ver Drift, no a un caso de laboratorio.
    """
    cmd = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
        "-c:v", "libvpx-vp9",
        "-ss", f"{segundo:.3f}",
        "-i", str(salida),
        "-vf", "alphaextract",
        "-frames:v", "1",
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0 or not res.stdout:
        return None
    d = res.stdout
    return min(d), max(d), sum(1 for b in d if b < 8), len(d)


def verificar_salida(ffmpeg: str, ffprobe: str, salida: Path,
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
        "-show_entries", "stream=pix_fmt,width,height,codec_name",
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

    # ---- PoC-2: canal alpha real ----
    #
    # Ojo con la trampa: en un WebM, el alpha de VP9 viaja como datos
    # adicionales de cada bloque, NO en el bitstream principal. Por eso
    # `ffprobe` reporta `pix_fmt=yuv420p` incluso cuando el alpha está ahí, y
    # mirar ese campo da un falso negativo. Lo verificamos de dos maneras
    # independientes: la marca del contenedor, y una decodificación real.
    alpha_mode = (v.get("tags") or {}).get("alpha_mode")
    marca_ok = alpha_mode == "1"
    resultados.append((
        marca_ok,
        f"PoC-2a el contenedor declara alpha (alpha_mode={alpha_mode!r}, "
        f"codec={v.get('codec_name')}, pix_fmt del bitstream={v.get('pix_fmt')})",
    ))

    # Se mide en dos instantes: uno cualquiera y uno pasada la mitad, para no
    # aprobar por casualidad con un cuadro en silencio.
    medidas = [(t, medir_alpha(ffmpeg, salida, t))
               for t in (min(0.5, duracion_audio / 2), duracion_audio * 0.7)]
    for segundo, m in medidas:
        if m is None:
            resultados.append((False, f"PoC-2b no se pudo decodificar el alpha en t={segundo:.2f}s"))
            continue
        mn, mx, transp, total = m
        # Un overlay útil tiene zonas transparentes Y zonas opacas. Todo opaco
        # significa que el alpha se perdió; todo transparente, que no se dibujó nada.
        varia = mx > 200 and transp > total * 0.1
        resultados.append((
            varia,
            f"PoC-2b alpha varía en t={segundo:.2f}s "
            f"(min={mn}, max={mx}, transparentes={transp:,}/{total:,} = "
            f"{100.0 * transp / total:.1f}%)",
        ))

    # ---- PoC-3: duración dentro de un frame ----
    dur_salida = float((datos.get("format") or {}).get("duration") or 0.0)
    tolerancia = 1.0 / fps
    delta = abs(dur_salida - duracion_audio)
    resultados.append((
        delta <= tolerancia,
        f"PoC-3  duración {dur_salida:.3f}s vs audio {duracion_audio:.3f}s "
        f"(desvío {delta * 1000:.1f} ms, tolerancia {tolerancia * 1000:.1f} ms)",
    ))

    return resultados


# --------------------------------------------------------------------------- #
# Interfaz de línea de comandos
# --------------------------------------------------------------------------- #

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
    g.add_argument("--trazo", choices=("full", "scale"), default="full",
                   help="grosor del trazo (default: full). full: cada muestra a "
                        "intensidad plena, onda sólida y bien visible; scale: reparte "
                        "la intensidad, queda un trazo tenue que en resoluciones "
                        "grandes casi no se ve")

    g2 = p.add_argument_group("codificación")
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

        salida = args.salida or args.audio.with_name(args.audio.stem + "_overlay.webm")
        if salida.suffix.lower() != ".webm":
            print(f"aviso: la salida '{salida.name}' no termina en .webm; "
                  f"VP9 con alpha necesita el contenedor WebM.", file=sys.stderr)
        salida.parent.mkdir(parents=True, exist_ok=True)

        cmd = construir_comando(
            ffmpeg, args.audio, salida,
            duracion=info["duracion"],
            ancho=args.ancho, alto=args.alto, fps=args.fps, color=args.color,
            modo=args.modo, escala=args.escala, trazo=args.trazo,
            crf=args.crf, cpu_used=args.cpu_used,
            sobrescribir=not args.no_sobrescribir,
        )

        if args.mostrar_comando:
            print(subprocess.list2cmdline(cmd))
            return 0

        print(f"audio   : {args.audio.name}  "
              f"({info['duracion']:.3f}s, {info['sample_rate']} Hz, "
              f"{info['canales']} canal{'es' if info['canales'] != 1 else ''}, {info['codec']})")
        print(f"overlay : {args.ancho}x{args.alto} @ {args.fps}fps, "
              f"modo={args.modo}, escala={args.escala}, trazo={args.trazo}, "
              f"color={args.color}")
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
        resultados = verificar_salida(ffmpeg, ffprobe, salida, info["duracion"], args.fps)
        for ok, texto in resultados:
            print(f"  {'OK  ' if ok else 'FALLA'}  {texto}")

        if not all(ok for ok, _ in resultados):
            print("\nEl overlay se generó pero no cumple todos los criterios.", file=sys.stderr)
            return 1

        print("\nTodo OK. Siguiente paso: importá el .webm a Drift y ponelo en una "
              "pista por encima del video.")
        return 0

    except ErrorDeGeneracion as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\ninterrumpido.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
