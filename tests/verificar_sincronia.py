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
usa como sistema de referencia. Se mide cuánta superficie está dibujada en cada
cuadro, se buscan los **saltos más grandes**, y se verifica que cada uno caiga
sobre un evento real de la pista.

**La rejilla de eventos se deriva del propio generador de la pista**, importando sus
patrones. Así la prueba y la pista no pueden separarse: si alguien cambia un patrón,
la rejilla cambia con él.

## Un error de método que esta prueba ya tuvo, y cómo se corrigió

La primera versión exigía que **tres instantes elegidos a mano** (0.0, 1.0 y 10.0 s)
fueran los tres saltos más grandes. Funcionaba con el generador de la prueba de
concepto, que dibuja amplitud, y **fallaba con el motor propio**, que dibuja
espectro — porque el momento en que entra el bajo (2.0 s) es un salto enorme de
energía espectral y apenas se nota en la amplitud.

Los dos tenían razón: los dos instantes son ataques reales. Lo que estaba mal era la
prueba, que había convertido el comportamiento de **un** método de medición en la
definición de lo correcto.

La formulación robusta es la de ahora: **cada salto detectado tiene que caer sobre
algún evento conocido**, sin exigir cuál. Igual detecta un corrimiento, porque los
eventos de la pista están separados 0.25 s como mínimo y un desfase de 100 ms deja
todos los saltos fuera de la rejilla.

## Tolerancia

Un cuadro. Un ataque que ocurre en `t` cae en el cuadro que *contiene* `t`, así que
+1 cuadro de cuantización es correcto y esperable, no un error.

Uso:
    python tests\\verificar_sincronia.py                     # motor propio, barras
    python tests\\verificar_sincronia.py --estilo espejadas
    python tests\\verificar_sincronia.py --motor ffmpeg      # el de la PoC
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
AUDIO = RAIZ / "tests" / "fixtures" / "pista_prueba.wav"

sys.path.insert(0, str(RAIZ / "tools"))
sys.path.insert(0, str(RAIZ / "tests" / "fixtures"))
from visualizador import consola  # noqa: E402

consola.preparar()


def rejilla_de_eventos(bpm: float = 120.0) -> list[float]:
    """Todos los instantes en que pasa algo en la pista de prueba.

    Se derivan de los patrones del generador de la pista, importándolos: si alguien
    cambia un patrón, esta rejilla cambia con él y la prueba sigue midiendo contra
    la verdad.

    Cuentan como evento los golpes de bombo y los comienzos de compás, que es donde
    entran el bajo y el acorde.
    """
    import generar_audio_prueba as pista

    seg_compas = (60.0 / bpm) * 4.0
    seg_paso = seg_compas / 16.0
    eventos = set()
    for c, compas in enumerate(pista.COMPASES):
        base = c * seg_compas
        eventos.add(round(base, 6))                     # comienzo de compás
        for paso, hay in enumerate(compas["bombo"]):
            if hay == "1":
                eventos.add(round(base + paso * seg_paso, 6))
    return sorted(eventos)

MUESTRA_W, MUESTRA_H = 160, 40

# Cuántos de los saltos más grandes se comprueban contra la rejilla de eventos.
# Ocho cubre la pista entera en vez de un momento afortunado.
N_SALTOS = 8


def perfil_del_motor_propio(audio: Path, fps: int, estilo: str) -> list[float]:
    """Lo mismo, pero midiendo los cuadros que dibuja nuestro motor.

    Mide **el dibujo**, no el análisis: se cuentan los píxeles pintados de cada
    cuadro renderizado. Así la prueba cubre toda la cadena —análisis, estilo,
    posicionado— y no sólo los números.

    Se renderiza a un lienzo chico porque lo que interesa es *cuándo* aparece la
    tinta, no a qué resolución.
    """
    import numpy as np
    from visualizador.analisis import analizar
    from visualizador.render import Render

    p = {
        "fps": fps, "lienzo_ancho": 320, "lienzo_alto": 180,
        "ancho": 320, "alto": 120, "x": 0, "y": 40,
        # Sin inercia ni adornos: se mide la alineación cruda, no la del suavizado.
        "suavizado": 0.0, "caida_picos": 0.0, "resplandor": 0.0, "reflejo": 0.0,
        "tapas_pico": False,
        "relleno": True,
    }
    render = Render(analizar(audio, p, estilo), estilo, p)
    perfil = []
    for i in range(render.n_cuadros):
        alfa = np.asarray(render.cuadro(i).getchannel("A"), dtype=np.float32)
        perfil.append(float((alfa > 32).sum()) / alfa.size)
    return perfil


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
    p.add_argument("--motor", default="propio", choices=("propio", "ffmpeg"),
                   help="qué se mide: 'propio' renderiza con nuestro motor (default); "
                        "'ffmpeg' usa el generador de la prueba de concepto, que sigue "
                        "existiendo como modo rápido")
    p.add_argument("--estilo", default="barras",
                   help="estilo a medir con el motor propio (default: barras)")
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

    if args.motor == "propio":
        energia = perfil_del_motor_propio(AUDIO, args.fps, args.estilo)
    else:
        energia = perfil_de_energia(ffmpeg, AUDIO, args.fps)

    n = len(energia)
    tolerancia_cuadros = 1
    rejilla = rejilla_de_eventos()

    print(f"pista    : {AUDIO.name}")
    print(f"motor    : {args.motor}" + (f" ({args.estilo})" if args.motor == "propio" else ""))
    print(f"cuadros  : {n} a {args.fps} fps = {n / args.fps:.3f}s")
    print(f"eventos  : {len(rejilla)} en la pista, derivados de su generador")
    print(f"tolerancia: {tolerancia_cuadros} cuadro ({1000.0 / args.fps:.1f} ms)\n")

    # Los saltos más grandes. Se miran varios para que la prueba cubra la pista
    # entera y no sólo un momento afortunado.
    saltos = sorted(((energia[i + 1] - energia[i], i + 1) for i in range(n - 1)),
                    reverse=True)[:N_SALTOS]

    fallas = 0
    for delta, indice in sorted(saltos, key=lambda s: s[1]):
        medido = indice / args.fps
        # El evento más cercano de la rejilla.
        evento = min(rejilla, key=lambda e: abs(e - medido))
        desvio = round((medido - evento) * args.fps)
        ok = 0 <= desvio <= tolerancia_cuadros
        if not ok:
            fallas += 1
        print(f"  {'OK   ' if ok else 'FALLA'}  salto en {medido:6.3f}s "
              f"(+{delta:.3f})  evento más cercano {evento:6.3f}s  "
              f"desvío {desvio:+d} cuadro{'s' if abs(desvio) != 1 else ''}")

    # Además, el salto más grande de toda la pista tiene que ser el de 10.0 s: es el
    # único que viene después de casi dos segundos de silencio, así que no hay
    # medición razonable en la que no sea el mayor.
    mayor = max(saltos)[1] / args.fps
    esperado_mayor = 10.0
    desvio_mayor = round((mayor - esperado_mayor) * args.fps)
    ok_mayor = 0 <= desvio_mayor <= tolerancia_cuadros
    if not ok_mayor:
        fallas += 1
    print(f"\n  {'OK   ' if ok_mayor else 'FALLA'}  el salto MÁS GRANDE cae en "
          f"{mayor:.3f}s; se espera el tramo intenso en {esperado_mayor:.3f}s "
          f"(desvío {desvio_mayor:+d})")

    if fallas:
        print(f"\n{fallas} comprobaciones fuera de tolerancia.", file=sys.stderr)
        print("Si el desvío es el mismo en todas, es un corrimiento constante: revisá "
              "que el análisis use la ventana causal y que el generador de la PoC siga "
              "aplicando setpts=PTS-STARTPTS.", file=sys.stderr)
        return 1

    print("\nSincronía OK: el dibujo reacciona cuando suena la música.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
