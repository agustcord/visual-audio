#!/usr/bin/env python3
"""Genera el audio de prueba del proyecto.

Produce una pista sintética corta con estructura rítmica marcada, pensada
específicamente para probar un visualizador de audio:

  - Transientes nítidos (kick y hi-hat) para que la detección de onsets de
    Drift tenga picos claros que encontrar.
  - Separación de bandas: kick en graves, hats en agudos, bajo y acorde en
    el medio. Así un visualizador de espectro muestra algo distinto en cada
    banda en vez de una mancha uniforme.
  - Un tramo de silencio y un tramo intenso, para ver que la onda respira.
  - Duración > 4 s, que es el mínimo que Drift necesita para estimar tempo
    (`kMinAnalysisSec` en src/engine/AudioOnsets.cpp).

Es sintético a propósito: no hay material con derechos en el repositorio y
el archivo se puede regenerar de forma idéntica en cualquier máquina.

Uso:
    python generar_audio_prueba.py            # escribe pista_prueba.wav
    python generar_audio_prueba.py --bpm 128  # otro tempo
"""

from __future__ import annotations

import argparse
import math
import struct
import sys
import wave
from pathlib import Path

SAMPLE_RATE = 48_000
CANALES = 2
BITS = 16

# Estructura: 8 compases de 4/4. Cada entrada dice qué pasa en ese compás.
# "bombo"/"hat" son patrones de semicorcheas (16 por compás): 1 = golpe.
COMPASES = [
    # compás 0-1: sólo ritmo, entrada seca
    {"bombo": "1000000010000000", "hat": "0010001000100010", "bajo": False, "acorde": None},
    {"bombo": "1000000010000000", "hat": "0010101000101010", "bajo": True, "acorde": None},
    # compás 2-3: entra el acorde
    {"bombo": "1000001010000000", "hat": "0010101000101010", "bajo": True, "acorde": "menor"},
    {"bombo": "1000000010000100", "hat": "0010101010101010", "bajo": True, "acorde": "menor"},
    # compás 4: respiro, casi silencio -> la onda debe achicarse visiblemente
    {"bombo": "1000000000000000", "hat": "0000000000000000", "bajo": False, "acorde": None},
    # compás 5-7: tramo intenso
    {"bombo": "1000101010001010", "hat": "1010101010101010", "bajo": True, "acorde": "mayor"},
    {"bombo": "1000101010001010", "hat": "1010101010101010", "bajo": True, "acorde": "mayor"},
    {"bombo": "1010101010101010", "hat": "1111111111111111", "bajo": True, "acorde": "mayor"},
]

# Frecuencias de las notas usadas (Hz).
LA2, DO3, MI3, DO4, MI4, LA4 = 110.0, 130.81, 164.81, 261.63, 329.63, 440.0
ACORDES = {"menor": (LA4, DO4, MI4), "mayor": (DO4, MI4, LA4)}


def bombo(t: float) -> float:
    """Kick: seno que baja de tono rápido, con caída exponencial. Todo en graves."""
    if t < 0.0:
        return 0.0
    envolvente = math.exp(-t * 11.0)
    frecuencia = 52.0 + 95.0 * math.exp(-t * 32.0)  # el "punch" del barrido
    cuerpo = math.sin(2.0 * math.pi * frecuencia * t)
    click = math.exp(-t * 320.0) * 0.35  # transitorio para que el onset sea nítido
    return (cuerpo * envolvente + click) * 0.92


def hat(t: float, semilla: int) -> float:
    """Hi-hat: ruido pseudoaleatorio filtrado a agudos, decaimiento muy corto."""
    if t < 0.0:
        return 0.0
    envolvente = math.exp(-t * 68.0)
    # LCG determinista: el mismo archivo en cualquier máquina, sin depender de random
    estado = (semilla * 1_103_515_245 + 12_345 + int(t * SAMPLE_RATE) * 2_654_435_761) & 0x7FFFFFFF
    ruido = ((estado % 20_000) / 10_000.0) - 1.0
    # Diferenciar el ruido lo corre hacia agudos, que es donde vive un hat
    estado2 = (estado * 1_103_515_245 + 12_345) & 0x7FFFFFFF
    ruido2 = ((estado2 % 20_000) / 10_000.0) - 1.0
    return (ruido - ruido2 * 0.7) * envolvente * 0.26


def bajo(t: float, dur: float) -> float:
    """Bajo: onda con algo de cuerpo, sostenida durante el compás."""
    if t < 0.0 or t > dur:
        return 0.0
    ataque = min(1.0, t * 55.0)
    salida = min(1.0, max(0.0, (dur - t) * 22.0))
    fundamental = math.sin(2.0 * math.pi * LA2 * t)
    armonico = math.sin(2.0 * math.pi * LA2 * 2.0 * t) * 0.28
    return (fundamental + armonico) * ataque * salida * 0.3


def acorde(t: float, dur: float, notas: tuple[float, ...]) -> float:
    """Acorde: suma de senos con vibrato leve, en el registro medio."""
    if t < 0.0 or t > dur:
        return 0.0
    ataque = min(1.0, t * 12.0)
    salida = min(1.0, max(0.0, (dur - t) * 9.0))
    total = 0.0
    for i, f in enumerate(notas):
        vibrato = 1.0 + 0.004 * math.sin(2.0 * math.pi * 5.2 * t + i)
        total += math.sin(2.0 * math.pi * f * vibrato * t) * (0.8 ** i)
    return total * ataque * salida * 0.13


def sintetizar(bpm: float) -> list[tuple[float, float]]:
    """Devuelve la pista como lista de pares (izquierda, derecha) en -1..1."""
    seg_por_compas = (60.0 / bpm) * 4.0
    seg_por_paso = seg_por_compas / 16.0
    duracion = seg_por_compas * len(COMPASES)
    n = int(duracion * SAMPLE_RATE)

    # Cada evento es (instante_de_inicio, funcion_que_da_la_muestra, panorama)
    # panorama: 0.0 = centro, -1 = todo a la izquierda, +1 = todo a la derecha
    eventos: list[tuple[float, object, float]] = []
    for c, compas in enumerate(COMPASES):
        base = c * seg_por_compas
        for paso in range(16):
            inicio = base + paso * seg_por_paso
            if compas["bombo"][paso] == "1":
                eventos.append((inicio, bombo, 0.0))
            if compas["hat"][paso] == "1":
                # Hats alternando lados: da movimiento estéreo visible
                lado = 0.45 if paso % 2 == 0 else -0.45
                eventos.append((inicio, lambda t, p=paso: hat(t, p + c * 16), lado))
        if compas["bajo"]:
            eventos.append((base, lambda t, d=seg_por_compas: bajo(t, d), 0.0))
        if compas["acorde"]:
            notas = ACORDES[compas["acorde"]]
            eventos.append((base, lambda t, d=seg_por_compas, nn=notas: acorde(t, d, nn), 0.0))

    izq = [0.0] * n
    der = [0.0] * n
    for inicio, fn, pan in eventos:
        i0 = int(inicio * SAMPLE_RATE)
        # Ventana generosa: alcanza para la cola más larga (un compás entero)
        i1 = min(n, i0 + int(seg_por_compas * SAMPLE_RATE) + 1)
        gan_izq = math.sqrt((1.0 - pan) / 2.0) * math.sqrt(2.0)
        gan_der = math.sqrt((1.0 + pan) / 2.0) * math.sqrt(2.0)
        for i in range(max(0, i0), i1):
            v = fn((i - i0) / SAMPLE_RATE)
            if v:
                izq[i] += v * gan_izq
                der[i] += v * gan_der

    # Normalizar a -1 dBFS, con un limitador suave por si algún golpe se pasa
    pico = max(max(abs(v) for v in izq), max(abs(v) for v in der), 1e-9)
    objetivo = 10 ** (-1.0 / 20.0)
    escala = objetivo / pico
    return [(max(-1.0, min(1.0, l * escala)), max(-1.0, min(1.0, r * escala)))
            for l, r in zip(izq, der)]


def escribir_wav(destino: Path, muestras: list[tuple[float, float]]) -> None:
    pico_int = 2 ** (BITS - 1) - 1
    cuadro = bytearray()
    for l, r in muestras:
        cuadro += struct.pack("<hh", int(l * pico_int), int(r * pico_int))
    destino.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(CANALES)
        w.setsampwidth(BITS // 8)
        w.setframerate(SAMPLE_RATE)
        w.writeframes(bytes(cuadro))


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bpm", type=float, default=120.0, help="tempo (default: 120)")
    p.add_argument("-o", "--salida", type=Path,
                   default=Path(__file__).parent / "pista_prueba.wav",
                   help="archivo .wav de salida")
    args = p.parse_args()

    if args.bpm <= 0:
        print("error: --bpm debe ser mayor que 0", file=sys.stderr)
        return 2

    muestras = sintetizar(args.bpm)
    escribir_wav(args.salida, muestras)

    dur = len(muestras) / SAMPLE_RATE
    print(f"escrito: {args.salida}")
    print(f"  duracion    : {dur:.3f} s")
    print(f"  bpm         : {args.bpm:g}")
    print(f"  compases    : {len(COMPASES)} (4/4)")
    print(f"  formato     : {SAMPLE_RATE} Hz, {CANALES} canales, {BITS} bits PCM")
    if dur < 4.0:
        print("  AVISO: menos de 4 s, Drift no va a poder estimar el tempo",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
