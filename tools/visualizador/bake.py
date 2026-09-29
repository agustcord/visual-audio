"""Persistencia y caché de Pre-Bake para análisis de audio (.audiobake.npz).

Almacena la matriz densa de STFT causal S (2049 bins float32) y la envolvente
de onda cruda en disco de forma comprimida. Permite reabrir o reanalizar
pistas con cero llamadas a FFmpeg y consultas en tiempo constante O(1).
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

# Versión del formato de serialización. Si la estructura interna cambia,
# las versiones anteriores se descartan e invalidan transparentemente.
VERSION_BAKE = 1

# Tamaño del bloque inicial del archivo de audio para el hash SHA-256 (64 KB).
BLOQUE_HASH_BYTES = 64 * 1024


class ErrorDeBake(Exception):
    """Error al hornear o recuperar el análisis persistido."""


@dataclass
class DatosBake:
    """Datos densos de pre-análisis de audio en memoria o cargados de disco."""

    stft_potencia: np.ndarray    # (n_cuadros, 2049) float32 — espectro causal
    onda_cruda: np.ndarray       # (n_cuadros, n_col) float32 — picos de onda por columna
    amplitud_cruda: np.ndarray   # (n_cuadros,) float32 — pico absoluto por cuadro
    duracion: float              # duración en segundos
    fps: int                     # cuadros por segundo analizados
    tasa: int                    # tasa de muestreo PCM (típicamente 48000 Hz)
    n_cuadros: int               # cantidad total de cuadros
    hash_audio: str              # suma de verificación SHA-256 del audio original
    ruta_audio: Path             # ruta del archivo de audio fuente
    version_formato: int = VERSION_BAKE

    # Cache volátil en RAM para acelerar recálculo de dinámica (CA-REARQ-3)
    _cache_clave: tuple[int, float, float] | None = None
    _cache_potencia: np.ndarray | None = None
    _cache_bordes: np.ndarray | None = None

    @property
    def n_bins(self) -> int:
        return int(self.stft_potencia.shape[1])


def calcular_hash_audio(ruta: Path | str) -> str:
    """Calcula la suma de verificación SHA-256 para validación de caché.

    Combina los primeros 64 KB del archivo + tamaño total en bytes + marca
    de tiempo de modificación (mtime). Si el audio es alterado o reemplazado,
    el hash cambia e invalida la caché automáticamente.
    """
    p = Path(ruta).resolve()
    if not p.is_file():
        raise FileNotFoundError(f"el archivo de audio no existe: {p}")

    stat = p.stat()
    hasher = hashlib.sha256()

    # Incorporar tamaño y marca de tiempo
    hasher.update(str(stat.st_size).encode("utf-8"))
    mtime_val = getattr(stat, "st_mtime_ns", stat.st_mtime)
    hasher.update(str(mtime_val).encode("utf-8"))

    # Incorporar los primeros 64 KB de contenido
    with open(p, "rb") as f:
        bloque = f.read(BLOQUE_HASH_BYTES)
        hasher.update(bloque)

    return hasher.hexdigest()


def obtener_ruta_bake(ruta_audio: Path | str, fps: int = 60) -> Path:
    """Retorna la ruta canónica del archivo .audiobake.npz junto al audio original.

    Para fps estándar (60) usa: `<audio_stem>.audiobake.npz`.
    Para otros fps incluye el sufijo: `<audio_stem>_{fps}fps.audiobake.npz`.
    """
    p = Path(ruta_audio)
    if fps == 60:
        nombre_bake = f"{p.stem}.audiobake.npz"
    else:
        nombre_bake = f"{p.stem}_{fps}fps.audiobake.npz"
    return p.parent / nombre_bake


def guardar_bake(datos: DatosBake, ruta_bake: Path | str) -> Path:
    """Guarda DatosBake en disco comprimido (.audiobake.npz) con escritura atómica."""
    destino = Path(ruta_bake).resolve()
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".tmp.npz")

    meta: dict[str, Any] = {
        "version_formato": VERSION_BAKE,
        "tasa": int(datos.tasa),
        "fps": int(datos.fps),
        "duracion": float(datos.duracion),
        "n_cuadros": int(datos.n_cuadros),
        "hash_audio": str(datos.hash_audio),
        "ruta_audio": str(datos.ruta_audio),
    }

    try:
        np.savez_compressed(
            temporal,
            stft_potencia=np.asarray(datos.stft_potencia, dtype=np.float32),
            onda_cruda=np.asarray(datos.onda_cruda, dtype=np.float32),
            amplitud_cruda=np.asarray(datos.amplitud_cruda, dtype=np.float32),
            metadatos=np.array(json.dumps(meta)),
        )
        temporal.replace(destino)
        return destino
    except Exception as e:
        if temporal.exists():
            try:
                temporal.unlink()
            except OSError:
                pass
        raise ErrorDeBake(f"no se pudo guardar el archivo de pre-bake '{destino}': {e}") from e


def cargar_bake(
    ruta_bake: Path | str,
    hash_esperado: str | None = None,
    fps_esperado: int | None = None,
    ruta_audio: Path | None = None,
) -> DatosBake | None:
    """Carga un archivo .audiobake.npz en memoria RAM si es válido.

    Retorna None sin levantar excepción si el archivo no existe, está corrupto,
    tiene una versión antigua o no coincide el hash o fps esperado.
    """
    p = Path(ruta_bake).resolve()
    if not p.is_file():
        return None

    try:
        with np.load(p, allow_pickle=False) as data:
            if "metadatos" not in data:
                return None
            meta_json = str(data["metadatos"])
            meta = json.loads(meta_json)

            # Validar versión
            if meta.get("version_formato") != VERSION_BAKE:
                return None

            # Validar hash de audio
            if hash_esperado is not None and meta.get("hash_audio") != hash_esperado:
                return None

            # Validar fps
            if fps_esperado is not None and int(meta.get("fps", 0)) != int(fps_esperado):
                return None

            stft = np.array(data["stft_potencia"], dtype=np.float32)
            onda = np.array(data["onda_cruda"], dtype=np.float32)
            amp = np.array(data["amplitud_cruda"], dtype=np.float32)
            duracion = float(meta.get("duracion", 0.0))
            fps = int(meta.get("fps", 60))
            tasa = int(meta.get("tasa", 48000))
            n_cuadros = int(meta.get("n_cuadros", len(amp)))
            hash_audio = str(meta.get("hash_audio", ""))

            audio_path = ruta_audio or Path(meta.get("ruta_audio", ""))

            return DatosBake(
                stft_potencia=stft,
                onda_cruda=onda,
                amplitud_cruda=amp,
                duracion=duracion,
                fps=fps,
                tasa=tasa,
                n_cuadros=n_cuadros,
                hash_audio=hash_audio,
                ruta_audio=audio_path,
                version_formato=VERSION_BAKE,
            )
    except Exception:
        # Cualquier fallo de lectura (archivo truncado, zip dañado, json mal formado)
        # se descarta limpiamente para forzar re-horneado.
        return None
