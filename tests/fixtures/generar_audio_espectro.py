#!/usr/bin/env python3
"""Genera la pista de prueba de espectro completo.

## Por qué existe, además de `pista_prueba.wav`

La otra pista sirve para medir **ritmo y sincronía**: tiene transitorios nítidos y
un compás de silencio, y sobre ella se verifica que el dibujo reaccione en el
cuadro correcto.

Lo que no sirve para medir es **el aspecto de un espectro**, porque no tiene ningún
instrumento entre 500 Hz y 2 kHz: sus acordes llegan hasta 440 Hz y los hi-hats
están arriba de 4 kHz. Medido en la etapa 1, el perfil del espectro queda vacío en
toda esa franja. Con ese material las barras del medio salen planas, y eso se lee
como un defecto del dibujo cuando en realidad es del audio.

Esta pista llena el espectro a propósito, con instrumentos repartidos para que
**cada tercio del rango tenga algo que mostrar**:

    50–150 Hz     bombo, con barrido de tono descendente
    110–440 Hz    bajo, con sus armónicos
    250–520 Hz    acorde sostenido
    700–2500 Hz   melodía principal  ← la franja que faltaba
    200 Hz–16 kHz redoblante de banda ancha  ← rellena todo el medio
    4–16 kHz      hi-hats

## Estructura

Ocho compases de 4/4 a 120 BPM, 2 segundos cada uno, 16 segundos en total. Los
instrumentos entran de a uno para poder aislar qué banda mueve cada cosa:

    compás 0  (0–2 s)    bombo y hats
    compás 1  (2–4 s)    + bajo
    compás 2  (4–6 s)    + acorde
    compás 3  (6–8 s)    + melodía
    compás 4  (8–10 s)   respiro: un solo bombo
    compás 5  (10–12 s)  todo, denso
    compás 6  (12–14 s)  todo, con redoblante en contratiempo
    compás 7  (14–16 s)  todo en semicorcheas

Uso:
    python generar_audio_espectro.py
    python generar_audio_espectro.py --bpm 128
"""

from __future__ import annotations

import argparse
import sys
import wave
from pathlib import Path

import numpy as np

TASA = 48_000
CANALES = 2
BITS = 16
SEMILLA = 20260925   # fija, para que el archivo sea reproducible al byte

# Notas de la melodía, en Hz. Una escala pentatónica de La, que suena bien sin
# saber nada de armonía y cubre justo la franja que faltaba.
MELODIA_HZ = [880.0, 1046.5, 1318.5, 1567.98, 1760.0, 2093.0, 2349.3]

# Notas del acorde sostenido, en el registro medio.
ACORDE_HZ = [261.63, 329.63, 392.0, 523.25]


def envolvente(n: int, ataque_ms: float, caida: float, tasa: int = TASA) -> np.ndarray:
    """Ataque lineal corto y caída exponencial. `caida` es el factor por segundo."""
    t = np.arange(n) / tasa
    subida = np.clip(t / max(ataque_ms / 1000.0, 1e-6), 0.0, 1.0)
    return (subida * np.exp(-t * caida)).astype(np.float32)


def bombo(dur: float, tasa: int = TASA) -> np.ndarray:
    """Barrido de tono descendente con un click al principio, todo en graves."""
    n = int(dur * tasa)
    t = np.arange(n) / tasa
    frec = 50.0 + 100.0 * np.exp(-t * 30.0)
    fase = 2 * np.pi * np.cumsum(frec) / tasa
    cuerpo = np.sin(fase) * envolvente(n, 1.0, 11.0)
    click = np.exp(-t * 300.0) * 0.3
    return ((cuerpo + click) * 0.9).astype(np.float32)


def hat(dur: float, rng: np.random.Generator, tasa: int = TASA) -> np.ndarray:
    """Ruido diferenciado dos veces: eso lo empuja bien arriba, donde vive un hat."""
    n = int(dur * tasa)
    ruido = rng.standard_normal(n + 2).astype(np.float32)
    agudo = np.diff(np.diff(ruido))
    return (agudo * envolvente(n, 0.2, 70.0) * 0.18).astype(np.float32)


def redoblante(dur: float, rng: np.random.Generator, tasa: int = TASA) -> np.ndarray:
    """Ruido de banda ancha más un tono de cuerpo.

    Es el instrumento que llena el medio del espectro, que era el agujero de la
    otra pista. El ruido se diferencia **una sola** vez: con dos quedaría tan
    agudo como un hat, y con ninguna quedaría demasiado grave.
    """
    n = int(dur * tasa)
    ruido = rng.standard_normal(n + 1).astype(np.float32)
    medio = np.diff(ruido)
    t = np.arange(n) / tasa
    cuerpo = np.sin(2 * np.pi * 185.0 * t) * np.exp(-t * 22.0) * 0.35
    return ((medio * 0.5 + cuerpo) * envolvente(n, 0.5, 14.0) * 0.55).astype(np.float32)


def bajo(dur: float, frec: float, tasa: int = TASA) -> np.ndarray:
    """Fundamental con dos armónicos, sostenido."""
    n = int(dur * tasa)
    t = np.arange(n) / tasa
    onda = (np.sin(2 * np.pi * frec * t)
            + 0.35 * np.sin(2 * np.pi * frec * 2 * t)
            + 0.12 * np.sin(2 * np.pi * frec * 3 * t))
    salida = np.clip(t / 0.01, 0, 1) * np.clip((dur - t) / 0.05, 0, 1)
    return (onda * salida * 0.3).astype(np.float32)


def acorde(dur: float, tasa: int = TASA) -> np.ndarray:
    """Varias notas sostenidas con un vibrato leve, en el registro medio."""
    n = int(dur * tasa)
    t = np.arange(n) / tasa
    total = np.zeros(n, dtype=np.float32)
    for i, f in enumerate(ACORDE_HZ):
        vibrato = 1.0 + 0.003 * np.sin(2 * np.pi * 5.0 * t + i)
        total += np.sin(2 * np.pi * f * vibrato * t) * (0.75 ** i)
    forma = np.clip(t / 0.08, 0, 1) * np.clip((dur - t) / 0.12, 0, 1)
    return (total * forma * 0.11).astype(np.float32)


def nota_melodia(dur: float, frec: float, tasa: int = TASA) -> np.ndarray:
    """Nota con ataque de púa y un armónico, en la franja de 700 a 2500 Hz."""
    n = int(dur * tasa)
    t = np.arange(n) / tasa
    onda = np.sin(2 * np.pi * frec * t) + 0.3 * np.sin(2 * np.pi * frec * 2 * t)
    return (onda * envolvente(n, 2.0, 6.0) * 0.22).astype(np.float32)


# Patrones por compás. Los de bombo, hat y redoblante son semicorcheas (16 por
# compás); `bajo`, `acorde` y `melodia` dicen si el instrumento suena en el compás.
COMPASES = [
    # 0: entrada seca
    {"bombo": "1000000010000000", "hat": "0010001000100010", "redo": "0000000000000000",
     "bajo": False, "acorde": False, "melodia": False},
    # 1: entra el bajo
    {"bombo": "1000000010000000", "hat": "0010101000101010", "redo": "0000000010000000",
     "bajo": True, "acorde": False, "melodia": False},
    # 2: entra el acorde
    {"bombo": "1000001010000000", "hat": "0010101000101010", "redo": "0000000010000000",
     "bajo": True, "acorde": True, "melodia": False},
    # 3: entra la melodia
    {"bombo": "1000000010000100", "hat": "0010101010101010", "redo": "0000000010000000",
     "bajo": True, "acorde": True, "melodia": True},
    # 4: respiro, un solo bombo. Control negativo.
    {"bombo": "1000000000000000", "hat": "0000000000000000", "redo": "0000000000000000",
     "bajo": False, "acorde": False, "melodia": False},
    # 5-7: todo
    {"bombo": "1000101010001010", "hat": "1010101010101010", "redo": "0000100000001000",
     "bajo": True, "acorde": True, "melodia": True},
    {"bombo": "1000101010001010", "hat": "1010101010101010", "redo": "0010001000100010",
     "bajo": True, "acorde": True, "melodia": True},
    {"bombo": "1010101010101010", "hat": "1111111111111111", "redo": "0000100000001000",
     "bajo": True, "acorde": True, "melodia": True},
]

BAJO_HZ = [110.0, 110.0, 146.83, 110.0, 110.0, 110.0, 130.81, 110.0]


def sintetizar(bpm: float) -> tuple[np.ndarray, np.ndarray]:
    """Devuelve los dos canales, cada uno en -1..1."""
    rng = np.random.default_rng(SEMILLA)
    seg_compas = (60.0 / bpm) * 4.0
    seg_paso = seg_compas / 16.0
    n_total = int(np.ceil(seg_compas * len(COMPASES) * TASA)) + TASA  # + cola

    izq = np.zeros(n_total, dtype=np.float32)
    der = np.zeros(n_total, dtype=np.float32)

    def sumar(inicio_s: float, señal: np.ndarray, pan: float = 0.0) -> None:
        """Mezcla `señal` en `inicio_s`, con paneo de potencia constante."""
        i0 = int(inicio_s * TASA)
        i1 = min(n_total, i0 + señal.size)
        if i1 <= i0:
            return
        trozo = señal[: i1 - i0]
        g_izq = np.sqrt((1.0 - pan) / 2.0) * np.sqrt(2.0)
        g_der = np.sqrt((1.0 + pan) / 2.0) * np.sqrt(2.0)
        izq[i0:i1] += trozo * g_izq
        der[i0:i1] += trozo * g_der

    for c, compas in enumerate(COMPASES):
        base = c * seg_compas

        for paso in range(16):
            t = base + paso * seg_paso
            if compas["bombo"][paso] == "1":
                sumar(t, bombo(0.5))
            if compas["hat"][paso] == "1":
                # Los hats alternan lados: da movimiento estéreo visible.
                sumar(t, hat(0.09, rng), 0.45 if paso % 2 == 0 else -0.45)
            if compas["redo"][paso] == "1":
                sumar(t, redoblante(0.28, rng), 0.12)

        if compas["bajo"]:
            sumar(base, bajo(seg_compas, BAJO_HZ[c]))
        if compas["acorde"]:
            sumar(base, acorde(seg_compas))
        if compas["melodia"]:
            # Ocho corcheas por compás, recorriendo la escala.
            for paso in range(8):
                frec = MELODIA_HZ[(c * 3 + paso) % len(MELODIA_HZ)]
                sumar(base + paso * seg_paso * 2, nota_melodia(seg_paso * 2 * 0.9, frec),
                      -0.2 if paso % 2 else 0.2)

    # Recortar a la duración exacta de los compases y normalizar a -1 dBFS.
    n_final = int(round(seg_compas * len(COMPASES) * TASA))
    izq, der = izq[:n_final], der[:n_final]
    pico = max(float(np.abs(izq).max()), float(np.abs(der).max()), 1e-9)
    escala = (10 ** (-1.0 / 20.0)) / pico
    return np.clip(izq * escala, -1, 1), np.clip(der * escala, -1, 1)


def escribir_wav(destino: Path, izq: np.ndarray, der: np.ndarray) -> None:
    entrelazado = np.empty(izq.size * 2, dtype="<i2")
    entrelazado[0::2] = (izq * 32767).astype("<i2")
    entrelazado[1::2] = (der * 32767).astype("<i2")
    destino.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destino), "wb") as w:
        w.setnchannels(CANALES)
        w.setsampwidth(BITS // 8)
        w.setframerate(TASA)
        w.writeframes(entrelazado.tobytes())


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--bpm", type=float, default=120.0, help="tempo (default: 120)")
    p.add_argument("-o", "--salida", type=Path,
                   default=Path(__file__).parent / "pista_espectro.wav")
    args = p.parse_args()

    if args.bpm <= 0:
        print("error: --bpm debe ser mayor que 0", file=sys.stderr)
        return 2

    izq, der = sintetizar(args.bpm)
    escribir_wav(args.salida, izq, der)

    dur = izq.size / TASA
    print(f"escrito: {args.salida}")
    print(f"  duracion  : {dur:.3f} s")
    print(f"  bpm       : {args.bpm:g}   compases: {len(COMPASES)} (4/4)")
    print(f"  formato   : {TASA} Hz, {CANALES} canales, {BITS} bits PCM")
    print(f"  cobertura : 50 Hz a 16 kHz, sin huecos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
