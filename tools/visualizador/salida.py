"""Salida: cuadros → archivo de video para Drift.

Los cuadros van por **entrada estándar a FFmpeg**, sin escribir imágenes
intermedias: cinco mil PNG en disco para después borrarlos no aporta nada y llena
el disco.

## Los parámetros de codificación no se inventaron acá

Salen de `tools/generar_overlay.py`, que es el generador de la prueba de concepto y
está verificado contra Drift. Incluye cosas que no son obvias y que costó
descubrir:

- **`-auto-alt-ref 0` y `-lag-in-frames 0` para VP9 con alpha.** El propio
  exportador de Drift lo desactiva cuando el preset lleva alpha, con el comentario
  de que VP9 con plano alpha no puede usar cuadros de referencia alternativos.
- **El modo transparente sólo sirve en Drift 0.7.0 o superior.** La 0.6.0 descarta
  el canal alpha y compone el clip como un rectángulo negro. Verificado contra el
  binario instalado: los presets de exportación con alpha no existen ahí.

## Los tres modos de fondo

| modo | qué produce | cómo se usa en Drift |
|---|---|---|
| `negro` | fondo negro sólido | modo de fusión **Trama** |
| `color` | fondo de un color plano | efecto **Chroma Key** |
| `transparente` | canal alpha | directo, **necesita 0.7.0+** |

Los dos primeros se componen en Python contra un color y se mandan en RGB, que
además pesa menos de la mitad que el alpha porque VP9 comprime mucho mejor sin el
plano extra.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any, Callable

from PIL import Image

from . import parametros
from .render import Render

# Calidad → crf de VP9. Medido sobre 16 s a 1080p con el generador de la PoC:
# crf 30 daba 13.7 MB, 36 daba 11.0 y 42 daba 8.4, sin degradación medible del
# alpha en ninguno.
CRF = {"alta": 30, "media": 36, "baja": 44}

# Consejo que se imprime al terminar, según el modo. Vale más acá que en la
# documentación: es el momento en que la persona va a ir a Drift.
SIGUIENTE_PASO = {
    "negro": "En tu editor de video: importalo, ponelo en una pista por encima del video, y "
             "poné el modo de fusión en «Trama».",
    "color": "En tu editor de video: importalo, pista por encima del video con fusión Normal, "
             "agregale el efecto «Chroma Key», poné Key Colour en el tono de tu "
             "fondo y subí Tolerance.",
    "transparente": "En tu editor de video: importalo y ponelo en una pista por encima. OJO: "
                    "esto NECESITA un editor que soporte canal alpha. Si no es compatible, el canal alpha "
                    "se descarta y vas a ver un rectángulo negro.",
}


class ErrorDeSalida(Exception):
    """Falla esperable y explicable: se reporta sin traceback."""


def _exigir_ffmpeg() -> str:
    ruta = shutil.which("ffmpeg")
    if not ruta:
        raise ErrorDeSalida(
            "no se encontró 'ffmpeg' en el PATH.\n"
            "  Se necesita para codificar el video. En esta máquina vive en "
            "C:\\ffmpeg\\bin."
        )
    return ruta


def extension_de(modo_fondo: str) -> str:
    """Todos los modos salen en WebM; la función existe para que quede explícito."""
    return ".webm"


def _argumentos_de_codec(con_alpha: bool, crf: int) -> list[str]:
    args = [
        "-c:v", "libvpx-vp9",
        "-pix_fmt", "yuva420p" if con_alpha else "yuv420p",
        "-b:v", "0", "-crf", str(crf),
        "-row-mt", "1",
        "-deadline", "good", "-cpu-used", "4",
    ]
    if con_alpha:
        # No es opcional: sin esto el plano alpha se desalinea de los cuadros.
        # El exportador de Drift hace lo mismo.
        args += ["-auto-alt-ref", "0", "-lag-in-frames", "0"]
    return args


def exportar(render: Render, destino: Path,
             progreso: Callable[[int, int], bool] | None = None) -> Path:
    """Codifica todos los cuadros al archivo.

    `progreso(hecho, total)` se llama a medida que avanza y puede devolver `False`
    para cancelar. Sin eso, un render de tres minutos deja la interfaz congelada
    sin decir nada, que es de las peores cosas que puede hacer un programa.

    Devuelve la ruta escrita.
    """
    p: dict[str, Any] = render.p
    modo = str(p["fondo"])
    con_alpha = modo == "transparente"
    crf = CRF[str(p["calidad"])]

    destino = destino.with_suffix(extension_de(modo))
    destino.parent.mkdir(parents=True, exist_ok=True)

    ancho, alto = render.tamano
    fps = render.analisis.fps
    total = render.n_cuadros

    # Los cuadros salen SIEMPRE en RGBA, incluso cuando el fondo va a ser sólido.
    #
    # Aplastar el dibujo contra el fondo en Python costaba, por cuadro, una copia
    # del lienzo entero más un `paste` con máscara más la conversión a bytes: tres
    # recorridos de dos millones de píxeles. **Lo hace FFmpeg con un `overlay`**,
    # que está optimizado para exactamente eso, y de paso Pillow entrega los bytes
    # RGBA sin conversión porque es su formato nativo acá.
    entrada = [
        "-f", "rawvideo", "-pix_fmt", "rgba",
        "-s", f"{ancho}x{alto}", "-r", str(fps), "-i", "-",
        "-i", str(render.analisis.ruta_audio),
    ]

    filtro: list[str] = []
    if not con_alpha:
        relleno = "black" if modo == "negro" else str(p["color_fondo"])
        # La fuente `color` lleva duración explícita: sin eso es infinita y
        # `-shortest` no la corta cuando la salida viene de un `filter_complex`.
        # Ya pasó en la prueba de concepto y generó 21 MB de un audio de 16 s.
        duracion = total / fps + 1.0
        filtro = [
            "-filter_complex",
            f"color=c={relleno}:s={ancho}x{alto}:r={fps}:d={duracion:.6f}[fondo];"
            f"[fondo][0:v]overlay=0:0:format=auto:shortest=1[v]",
        ]

    cmd = [
        _exigir_ffmpeg(), "-hide_banner", "-loglevel", "error", "-nostdin", "-y",
        *entrada,
        *filtro,
        *_argumentos_de_codec(con_alpha, crf),
        "-map", "0:v" if con_alpha else "[v]",
        "-map", "1:a",
        "-af", "loudnorm=I=-14:TP=-1",
        str(destino),
    ]

    cancelado = False

    proceso = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        assert proceso.stdin is not None
        for i, cuadro in enumerate(render.cuadros()):
            proceso.stdin.write(cuadro.tobytes())
            if progreso is not None and not progreso(i + 1, total):
                cancelado = True
                break
        proceso.stdin.close()
    except BrokenPipeError:
        # FFmpeg se murió antes de tiempo. Su stderr dice por qué.
        pass
    finally:
        salida_error = proceso.stderr.read().decode(errors="replace") if proceso.stderr else ""
        codigo = proceso.wait()

    if cancelado:
        destino.unlink(missing_ok=True)
        raise ErrorDeSalida("export cancelado; el archivo incompleto se borró")

    if codigo != 0:
        raise ErrorDeSalida(
            f"FFmpeg falló al codificar (código {codigo}):\n  {salida_error.strip()}"
        )

    return destino
