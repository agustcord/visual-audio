"""Gestión de proyectos y presets: serialización, validación y persistencia.

Contratos canónicos definidos en docs/ARQUITECTURA.md §6 y docs/RUTA_DE_TRABAJO.md §4:
- Formato JSON indentado con versión explícita ("version": 1).
- Proyectos asocian audio, estilo y parámetros.
- Presets asocian estilo y parámetros, sin atarse a una pista de audio.
- Comprobación estricta de existencia física del audio al abrir proyectos.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import estilos, parametros


class ErrorDeProyecto(ValueError):
    """Error al guardar, abrir o validar un proyecto o preset."""


_DIRECTORIO_RAIZ = Path(__file__).resolve().parent.parent.parent
DIRECTORIO_PRESETS = _DIRECTORIO_RAIZ / "presets"


def guardar(ruta: Path | str, audio: Path | str, estilo: str, params: dict[str, Any]) -> None:
    """Guarda un proyecto en archivo JSON."""
    ruta = Path(ruta)
    audio_path = Path(audio)

    # Validar estilo y parámetros antes de escribir en disco
    est = estilos.obtener(estilo)
    params_validados = parametros.validar(params, estilo=est.id, permitir_desconocidos=False)

    data = {
        "version": 1,
        "audio": str(audio_path),
        "estilo": est.id,
        "params": params_validados,
    }

    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        raise ErrorDeProyecto(f"No se pudo guardar el proyecto en '{ruta}': {e}") from e


def abrir(ruta: Path | str) -> tuple[Path, str, dict[str, Any]]:
    """Abre un proyecto desde archivo JSON.

    Devuelve (audio_path, estilo_id, params).
    Levanta ErrorDeProyecto o ErrorDeParametro ante archivos faltantes, JSON corrupto,
    versión desconocida, parámetros inválidos o audio ausente.
    """
    ruta = Path(ruta)
    if not ruta.is_file():
        raise ErrorDeProyecto(f"El archivo de proyecto no existe: '{ruta}'")

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ErrorDeProyecto(f"El archivo de proyecto '{ruta}' tiene JSON mal formado: {e}") from e
    except OSError as e:
        raise ErrorDeProyecto(f"No se pudo leer el archivo de proyecto '{ruta}': {e}") from e

    if not isinstance(data, dict):
        raise ErrorDeProyecto(f"El archivo de proyecto '{ruta}' no contiene un objeto JSON válido.")

    version = data.get("version")
    if version != 1:
        raise ErrorDeProyecto(
            f"Versión de proyecto no soportada: {version!r} en '{ruta}'. Se espera 'version: 1'."
        )

    for campo in ("audio", "estilo", "params"):
        if campo not in data:
            raise ErrorDeProyecto(f"Al proyecto '{ruta}' le falta el campo obligatorio '{campo}'.")

    estilo_id = str(data["estilo"])
    try:
        estilos.obtener(estilo_id)
    except ValueError as e:
        raise ErrorDeProyecto(f"Estilo desconocido en proyecto '{ruta}': '{estilo_id}'") from e

    params_raw = data["params"]
    if not isinstance(params_raw, dict):
        raise ErrorDeProyecto(f"El campo 'params' en '{ruta}' debe ser un diccionario.")

    # Validar parámetros contra el esquema
    params_validados = parametros.validar(params_raw, estilo=estilo_id, permitir_desconocidos=False)

    # Validar existencia de la pista de audio
    audio_str = str(data["audio"])
    audio_path = Path(audio_str)
    if not audio_path.exists():
        # Probar relativo al directorio del proyecto si era relativa
        relativo = (ruta.parent / audio_path).resolve()
        if relativo.exists():
            audio_path = relativo
        else:
            raise ErrorDeProyecto(
                f"La pista de audio especificada en el proyecto no existe: '{audio_str}'"
            )

    return audio_path, estilo_id, params_validados


def guardar_preset(ruta: Path | str, estilo: str, params: dict[str, Any]) -> None:
    """Guarda un preset de estilo y parámetros (sin audio)."""
    ruta = Path(ruta)
    est = estilos.obtener(estilo)
    params_validados = parametros.validar(params, estilo=est.id, permitir_desconocidos=False)

    data = {
        "version": 1,
        "estilo": est.id,
        "params": params_validados,
    }

    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except OSError as e:
        raise ErrorDeProyecto(f"No se pudo guardar el preset en '{ruta}': {e}") from e


def abrir_preset(ruta_o_nombre: Path | str, directorio: Path | None = None) -> tuple[str, dict[str, Any]]:
    """Abre y valida un preset.

    Permite pasar una ruta a un archivo .json, o el nombre de un preset alojado en presets/.
    Devuelve (estilo_id, params).
    """
    ruta = Path(ruta_o_nombre)
    base_dir = directorio or DIRECTORIO_PRESETS

    if not ruta.is_file():
        # Intentar buscar por nombre en el directorio de presets
        candidatos = [
            base_dir / ruta.name,
            base_dir / f"{ruta.name}.json",
            base_dir / f"{ruta.stem}.json",
        ]
        encontrado = None
        for c in candidatos:
            if c.is_file():
                encontrado = c
                break
        if encontrado is not None:
            ruta = encontrado
        else:
            raise ErrorDeProyecto(f"No se encontró el archivo de preset: '{ruta_o_nombre}'")

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ErrorDeProyecto(f"El archivo de preset '{ruta}' tiene JSON mal formado: {e}") from e
    except OSError as e:
        raise ErrorDeProyecto(f"No se pudo leer el archivo de preset '{ruta}': {e}") from e

    if not isinstance(data, dict):
        raise ErrorDeProyecto(f"El archivo de preset '{ruta}' no contiene un objeto JSON válido.")

    version = data.get("version")
    if version != 1:
        raise ErrorDeProyecto(
            f"Versión de preset no soportada: {version!r} en '{ruta}'. Se espera 'version: 1'."
        )

    for campo in ("estilo", "params"):
        if campo not in data:
            raise ErrorDeProyecto(f"Al preset '{ruta}' le falta el campo obligatorio '{campo}'.")

    estilo_id = str(data["estilo"])
    try:
        estilos.obtener(estilo_id)
    except ValueError as e:
        raise ErrorDeProyecto(f"Estilo desconocido en preset '{ruta}': '{estilo_id}'") from e

    params_raw = data["params"]
    if not isinstance(params_raw, dict):
        raise ErrorDeProyecto(f"El campo 'params' en '{ruta}' debe ser un diccionario.")

    params_validados = parametros.validar(params_raw, estilo=estilo_id, permitir_desconocidos=False)

    return estilo_id, params_validados


def listar_presets(directorio: Path | None = None) -> list[str]:
    """Lista los nombres (stems) de los presets disponibles en presets/."""
    d = directorio or DIRECTORIO_PRESETS
    if not d.is_dir():
        return []
    return sorted(p.stem for p in d.glob("*.json"))
