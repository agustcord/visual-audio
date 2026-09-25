#!/usr/bin/env python3
"""Prueba de regresión: el overlay está sincronizado con el audio.

Existe por un bug real. `showwaves` entrega los cuadros con intervalos perfectos
de 1/fps pero **etiqueta el primero en PTS 0.100 s en vez de 0**, y ese
corrimiento constante hacía que todo el overlay reaccionara 100 ms después de la
música. El generador lo corrige con `setpts=PTS-STARTPTS`; esta prueba verifica
que siga corregido.

El corrimiento **no se puede detectar** contando cuadros ni midiendo duraciones:
la cantidad de cuadros era correcta y el contenedor declaraba la duración
correcta. Sólo se ve comparando *cuándo* pasa algo en el overlay contra *cuándo*
pasa en el audio.

## Cómo mide

`tests/fixtures/pista_prueba.wav` tiene una estructura conocida, y esta prueba la
usa como sistema de referencia. A 120 BPM en 4/4 cada compás dura exactamente 2 s:

    t=0.0s   primer bombo, arranca la pista
    t=1.0s   entra el bajo (mitad del compás 0... en realidad compás 1)
    t=8.0s   compás 4: el "respiro", casi silencio
    t=10.0s  compás 5: arranca el tramo intenso

Se extrae el canal alpha del overlay, se mide cuánta superficie está dibujada en
cada cuadro, y se buscan los **saltos de energía más grandes**. Esos saltos tienen
que caer sobre los ataques conocidos.

Se usan los **ataques** y no los silencios a propósito: el borde donde entra el
tramo intenso es abrupto y medible, mientras que el comienzo del silencio es
difuso porque la cola de decaimiento del bombo ocupa unos 600 ms. Medir contra un
borde difuso da un desvío que parece un bug y no lo es — se probó, y confundía.

## Tolerancia

Un cuadro. Un ataque que ocurre en t cae en el cuadro que *contiene* t, así que
+1 cuadro de cuantización es correcto y esperable, no un error.

Uso:
    python tests\\verificar_sincronia.py
    python tests\\verificar_sincronia.py --fps 24
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
AUDIO = RAIZ / "tests" / "fixtures" / "pista_prueba.wav"

# Instantes con un ataque marcado en la pista de prueba, en segundos.
# Derivados de su estructura: 120 BPM, 4/4, compases de 2 s.
ATAQUES_ESPERADOS = [0.0, 1.0, 10.0]

MUESTRA_W, MUESTRA_H = 160, 40


def perfil_de_energia(ffmpeg: str, audio: Path, fps: int) -> list[float]:
    """Fracción de superficie dibujada en cada cuadro del overlay."""
    filtro = (
        f"[0:a]showwaves=s={MUESTRA_W}x{MUESTRA_H}:mode=cline:rate={fps}"
        f":draw=full:scale=sqrt:colors=white,setpts=PTS-STARTPTS,alphaextract[v]"
    )
    cmd = [
        ffmpeg, "-hide_banner", "-loglevel", "error", "-nostdin",
        "-i", str(audio),
        "-filter_complex", filtro,
        "-map", "[v]",
        "-f", "rawvideo", "-pix_fmt", "gray", "-",
    ]
    res = subprocess.run(cmd, capture_output=True)
    if res.returncode != 0:
        raise SystemExit(f"error: ffmpeg falló:\n{res.stderr.decode(errors='replace')}")

    por_cuadro = MUESTRA_W * MUESTRA_H
    d = res.stdout
    n = len(d) // por_cuadro
    if n == 0:
        raise SystemExit("error: ffmpeg no devolvió ningún cuadro")
    return [
        sum(1 for b in d[i * por_cuadro:(i + 1) * por_cuadro] if b > 32) / por_cuadro
        for i in range(n)
    ]


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--fps", type=int, default=30, help="cuadros por segundo (default: 30)")
    args = p.parse_args()

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        print("error: no se encontró ffmpeg en el PATH", file=sys.stderr)
        return 2
    if not AUDIO.exists():
        print(f"error: falta la pista de prueba: {AUDIO}\n"
              f"  Generala con: python tests\\fixtures\\generar_audio_prueba.py",
              file=sys.stderr)
        return 2

    energia = perfil_de_energia(ffmpeg, AUDIO, args.fps)
    n = len(energia)
    tolerancia_cuadros = 1

    # Los saltos de energía más grandes, uno por ataque esperado.
    saltos = sorted(
        ((energia[i + 1] - energia[i], i + 1) for i in range(n - 1)),
        reverse=True,
    )[:len(ATAQUES_ESPERADOS)]
    detectados = sorted(indice for _, indice in saltos)

    print(f"pista    : {AUDIO.name}")
    print(f"cuadros  : {n} a {args.fps} fps = {n / args.fps:.3f}s")
    print(f"tolerancia: {tolerancia_cuadros} cuadro ({1000.0 / args.fps:.1f} ms)\n")

    fallas = 0
    for esperado, indice in zip(ATAQUES_ESPERADOS, detectados):
        medido = indice / args.fps
        desvio_cuadros = indice - round(esperado * args.fps)
        ok = abs(desvio_cuadros) <= tolerancia_cuadros
        if not ok:
            fallas += 1
        print(f"  {'OK   ' if ok else 'FALLA'}  ataque esperado en {esperado:6.3f}s, "
              f"medido en {medido:6.3f}s  "
              f"(desvío {desvio_cuadros:+d} cuadro{'s' if abs(desvio_cuadros) != 1 else ''}, "
              f"{(medido - esperado) * 1000:+.0f} ms)")

    if fallas:
        print(f"\n{fallas} de {len(ATAQUES_ESPERADOS)} ataques fuera de tolerancia.",
              file=sys.stderr)
        print("Si el desvío es constante en todos, es un corrimiento de PTS: revisá que "
              "el generador siga aplicando setpts=PTS-STARTPTS.", file=sys.stderr)
        return 1

    print("\nSincronía OK: el overlay reacciona cuando suena la música.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
