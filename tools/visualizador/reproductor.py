"""Módulo desacoplado de reproducción de audio para el visualizador de Drift.

Provee una arquitectura de backends intercambiables para reproducción de audio
sincronizada sin agregar dependencias externas de Python (Regla 13):
- ReproductorAudio: Interfaz base abstracta que define el contrato común.
- FFplayBackend: Backend primario universal usando ffplay.exe en subproceso silencioso.
- MCIBackend: Backend nativo de Windows (winmm.dll) como fallback para MP3/WAV.
- NullBackend: Backend mudo para testing automatizado, entornos headless y modo seguro.
"""

from __future__ import annotations

import abc
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Posibles ubicaciones canónicas de ffplay en el sistema
RUTAS_FFPLAY_CONOCIDAS = [
    Path(r"C:\ffmpeg\bin\ffplay.exe"),
    Path(r"C:\ffmpeg\bin\ffplay"),
]


class ReproductorAudio(abc.ABC):
    """Contrato base abstracto para los motores de reproducción de audio."""

    def __init__(self) -> None:
        self._ruta_audio: Path | None = None

    @abc.abstractmethod
    def cargar(self, ruta_audio: Path | str) -> bool:
        """Carga una pista de audio para su reproducción."""
        ...

    @abc.abstractmethod
    def reproducir(self, offset_seg: float = 0.0) -> bool:
        """Inicia la reproducción desde el segundo indicado (offset_seg)."""
        ...

    def play(self, desde_segundo: float = 0.0) -> bool:
        """Alias de reproducir para compatibilidad de nomenclatura."""
        return self.reproducir(offset_seg=desde_segundo)

    @abc.abstractmethod
    def pausar(self) -> None:
        """Pausa la reproducción reteniendo la posición actual."""
        ...

    def pause(self) -> None:
        """Alias de pausar."""
        self.pausar()

    @abc.abstractmethod
    def reanudar(self) -> None:
        """Reanuda la reproducción desde la posición pausada."""
        ...

    def resume(self) -> None:
        """Alias de reanudar."""
        self.reanudar()

    @abc.abstractmethod
    def detener(self) -> None:
        """Detiene la reproducción y reinicia la posición a cero."""
        ...

    def stop(self) -> None:
        """Alias de detener."""
        self.detener()

    @abc.abstractmethod
    def esta_reproduciendo(self) -> bool:
        """Indica si el audio se está reproduciendo activamente en este instante."""
        ...

    def is_playing(self) -> bool:
        """Alias de esta_reproduciendo."""
        return self.esta_reproduciendo()

    @abc.abstractmethod
    def posicion_actual(self) -> float:
        """Devuelve la posición temporal actual de la reproducción en segundos."""
        ...

    def get_pos(self) -> float:
        """Alias de posicion_actual."""
        return self.posicion_actual()

    @abc.abstractmethod
    def cerrar(self) -> None:
        """Libera de forma determinista todos los recursos y subprocesos."""
        ...

    def __del__(self) -> None:
        try:
            self.cerrar()
        except Exception:
            pass


class FFplayBackend(ReproductorAudio):
    """Backend prioritario basado en ffplay.exe ejecutado en segundo plano sin ventana.

    Utiliza los flags -nodisp -autoexit -ss <offset> -loglevel quiet y
    subprocess.CREATE_NO_WINDOW en Windows para garantizar silencio de consola y cero ventanas.
    """

    def __init__(self, ruta_binario: Path | str | None = None) -> None:
        super().__init__()
        self._binario = self._localizar_binario(ruta_binario)
        self._proceso: subprocess.Popen[Any] | None = None
        self._offset_base: float = 0.0
        self._tiempo_inicio_perf: float = 0.0
        self._reproduciendo: bool = False
        self._pausado: bool = False

    @classmethod
    def disponible(cls, ruta_binario: Path | str | None = None) -> bool:
        """Verifica si ffplay.exe existe y es ejecutable en el sistema."""
        try:
            binario = cls._localizar_binario(ruta_binario)
            return binario is not None and Path(binario).is_file()
        except Exception:
            return False

    @staticmethod
    def _localizar_binario(preferido: Path | str | None = None) -> Path | None:
        if preferido:
            p = Path(preferido)
            if p.is_file():
                return p

        # 1. Probar PATH general del sistema
        which_path = shutil.which("ffplay")
        if which_path:
            return Path(which_path)

        # 2. Probar rutas conocidas estándar en Windows
        for ruta in RUTAS_FFPLAY_CONOCIDAS:
            if ruta.is_file():
                return ruta

        return None

    def cargar(self, ruta_audio: Path | str) -> bool:
        self.detener()
        p = Path(ruta_audio)
        if not p.is_file():
            return False
        self._ruta_audio = p
        self._offset_base = 0.0
        return True

    def reproducir(self, offset_seg: float = 0.0) -> bool:
        if self._ruta_audio is None or not self._ruta_audio.is_file():
            return False
        if self._binario is None:
            return False

        self._matar_proceso()

        offset_seg = max(0.0, offset_seg)
        # Comando canónico ffplay silencioso sin interfaz gráfica
        cmd = [
            str(self._binario),
            "-nodisp",
            "-autoexit",
            "-ss",
            f"{offset_seg:.3f}",
            "-loglevel",
            "quiet",
            str(self._ruta_audio),
        ]

        flags = 0
        if sys.platform == "win32":
            # Bandera de Windows para prevenir la apertura de cualquier ventana de consola
            flags |= getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

        try:
            self._proceso = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=flags,
            )
            self._offset_base = offset_seg
            self._tiempo_inicio_perf = time.perf_counter()
            self._reproduciendo = True
            self._pausado = False
            return True
        except Exception:
            self._proceso = None
            self._reproduciendo = False
            self._pausado = False
            return False

    def pausar(self) -> None:
        if self._reproduciendo and self._proceso is not None:
            # En ffplay en modo headless, pausar de forma determinista y sin tuberías
            # frágiles consiste en congelar la posición actual y finalizar el subproceso.
            self._offset_base = self.posicion_actual()
            self._matar_proceso()
            self._reproduciendo = False
            self._pausado = True

    def reanudar(self) -> None:
        if self._pausado and self._ruta_audio is not None:
            self.reproducir(self._offset_base)

    def detener(self) -> None:
        self._matar_proceso()
        self._offset_base = 0.0
        self._reproduciendo = False
        self._pausado = False

    def esta_reproduciendo(self) -> bool:
        if not self._reproduciendo or self._proceso is None:
            return False
        if self._proceso.poll() is not None:
            # El subproceso finalizó naturalmente (fin de archivo o error)
            self._reproduciendo = False
            return False
        return True

    def posicion_actual(self) -> float:
        if self.esta_reproduciendo():
            delta = time.perf_counter() - self._tiempo_inicio_perf
            return self._offset_base + delta
        return self._offset_base

    def _matar_proceso(self) -> None:
        if self._proceso is not None:
            if self._proceso.poll() is None:
                try:
                    self._proceso.terminate()
                    self._proceso.wait(timeout=0.2)
                except (subprocess.TimeoutExpired, Exception):
                    try:
                        self._proceso.kill()
                        self._proceso.wait(timeout=0.2)
                    except Exception:
                        pass
            self._proceso = None

    def cerrar(self) -> None:
        self.detener()


class MCIBackend(ReproductorAudio):
    """Backend nativo para Windows mediante la API winmm.dll (MCI).

    Ofrece latencia ultra-baja para archivos WAV y MP3 sin necesidad de binarios externos.
    Nota: WinMM no admite nativamente contenedores FLAC u OGG sin filtros DirectShow.
    """

    def __init__(self) -> None:
        super().__init__()
        self._alias = f"drift_mci_{id(self)}"
        self._abierto: bool = False
        self._reproduciendo: bool = False
        self._pausado: bool = False
        self._offset_base: float = 0.0
        self._tiempo_inicio_perf: float = 0.0

    @classmethod
    def disponible(cls) -> bool:
        return sys.platform == "win32"

    def _enviar(self, comando: str) -> tuple[int, str]:
        if not self.disponible():
            return 1, "MCI no soportado fuera de Windows"
        try:
            import ctypes
            buffer = ctypes.create_unicode_buffer(256)
            err = ctypes.windll.winmm.mciSendStringW(comando, buffer, 255, 0)
            return err, buffer.value
        except Exception as e:
            return 1, str(e)

    def cargar(self, ruta_audio: Path | str) -> bool:
        self.cerrar()
        p = Path(ruta_audio).resolve()
        if not p.is_file():
            return False

        # MCI maneja bien WAV y MP3
        ext = p.suffix.lower()
        if ext not in (".wav", ".mp3"):
            return False

        cmd = f'open "{p}" type mpegvideo alias {self._alias}'
        err, _ = self._enviar(cmd)
        if err != 0:
            return False

        self._enviar(f"set {self._alias} time format milliseconds")
        self._ruta_audio = p
        self._abierto = True
        self._offset_base = 0.0
        return True

    def reproducir(self, offset_seg: float = 0.0) -> bool:
        if not self._abierto:
            return False

        offset_seg = max(0.0, offset_seg)
        ms = int(round(offset_seg * 1000))
        err, _ = self._enviar(f"play {self._alias} from {ms}")
        if err != 0:
            return False

        self._offset_base = offset_seg
        self._tiempo_inicio_perf = time.perf_counter()
        self._reproduciendo = True
        self._pausado = False
        return True

    def pausar(self) -> None:
        if self._abierto and self._reproduciendo:
            self._offset_base = self.posicion_actual()
            self._enviar(f"pause {self._alias}")
            self._reproduciendo = False
            self._pausado = True

    def reanudar(self) -> None:
        if self._abierto and self._pausado:
            err, _ = self._enviar(f"resume {self._alias}")
            if err == 0:
                self._tiempo_inicio_perf = time.perf_counter()
                self._reproduciendo = True
                self._pausado = False

    def detener(self) -> None:
        if self._abierto:
            self._enviar(f"stop {self._alias}")
        self._offset_base = 0.0
        self._reproduciendo = False
        self._pausado = False

    def esta_reproduciendo(self) -> bool:
        if not self._abierto or not self._reproduciendo:
            return False
        err, resp = self._enviar(f"status {self._alias} mode")
        if err == 0 and resp.strip().lower() == "playing":
            return True
        self._reproduciendo = False
        return False

    def posicion_actual(self) -> float:
        if not self._abierto:
            return self._offset_base
        err, resp = self._enviar(f"status {self._alias} position")
        if err == 0 and resp.strip().isdigit():
            return int(resp.strip()) / 1000.0
        if self._reproduciendo:
            delta = time.perf_counter() - self._tiempo_inicio_perf
            return self._offset_base + delta
        return self._offset_base

    def cerrar(self) -> None:
        if self._abierto:
            self._enviar(f"close {self._alias}")
            self._abierto = False
        self._reproduciendo = False
        self._pausado = False
        self._offset_base = 0.0


class NullBackend(ReproductorAudio):
    """Backend simulado silencioso para testing desatendido y modo seguro.

    Mantiene el avance temporal mediante time.perf_counter() sin emitir ningún sonido
    por los parlantes ni crear procesos en el sistema operativo.
    """

    def __init__(self, duracion_simulada: float = 3600.0) -> None:
        super().__init__()
        self._duracion = duracion_simulada
        self._offset_base: float = 0.0
        self._tiempo_inicio_perf: float = 0.0
        self._reproduciendo: bool = False
        self._pausado: bool = False

    def cargar(self, ruta_audio: Path | str) -> bool:
        self.detener()
        self._ruta_audio = Path(ruta_audio)
        self._offset_base = 0.0
        return True

    def reproducir(self, offset_seg: float = 0.0) -> bool:
        self._offset_base = max(0.0, offset_seg)
        self._tiempo_inicio_perf = time.perf_counter()
        self._reproduciendo = True
        self._pausado = False
        return True

    def pausar(self) -> None:
        if self._reproduciendo:
            self._offset_base = self.posicion_actual()
            self._reproduciendo = False
            self._pausado = True

    def reanudar(self) -> None:
        if self._pausado:
            self.reproducir(self._offset_base)

    def detener(self) -> None:
        self._offset_base = 0.0
        self._reproduciendo = False
        self._pausado = False

    def esta_reproduciendo(self) -> bool:
        if not self._reproduciendo:
            return False
        if self.posicion_actual() >= self._duracion:
            self._reproduciendo = False
            return False
        return True

    def posicion_actual(self) -> float:
        if self._reproduciendo:
            delta = time.perf_counter() - self._tiempo_inicio_perf
            return min(self._duracion, self._offset_base + delta)
        return self._offset_base

    def cerrar(self) -> None:
        self.detener()


def crear_reproductor(
    ruta_audio: Path | str | None = None,
    backend: str | None = None,
) -> ReproductorAudio:
    """Fábrica que instancia el mejor reproductor de audio disponible.

    Parámetros:
    - ruta_audio: Pista opcional para inferir compatibilidad de códec.
    - backend: Selección forzada ('ffplay', 'mci', 'null') o None para auto-detección.
    """
    if backend == "null":
        rep = NullBackend()
        if ruta_audio:
            rep.cargar(ruta_audio)
        return rep

    if backend == "ffplay":
        rep = FFplayBackend()
        if ruta_audio:
            rep.cargar(ruta_audio)
        return rep

    if backend == "mci":
        rep = MCIBackend()
        if ruta_audio:
            rep.cargar(ruta_audio)
        return rep

    # Auto-detección:
    # 1. FFplayBackend es prioritario y universal (soporta todos los formatos y seek exacto)
    if FFplayBackend.disponible():
        rep = FFplayBackend()
        if ruta_audio:
            rep.cargar(ruta_audio)
        return rep

    # 2. MCIBackend si estamos en Windows y es WAV o MP3
    if ruta_audio:
        ext = Path(ruta_audio).suffix.lower()
        if ext in (".wav", ".mp3") and MCIBackend.disponible():
            rep = MCIBackend()
            if rep.cargar(ruta_audio):
                return rep

    # 3. Fallback de seguridad mudo
    rep = NullBackend()
    if ruta_audio:
        rep.cargar(ruta_audio)
    return rep
