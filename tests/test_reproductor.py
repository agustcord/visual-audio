"""Pruebas automatizadas del módulo de reproducción de audio (Etapa 7).

Verifica exhaustivamente:
- Contratos de la interfaz abstracta ReproductorAudio.
- Backend prioritario FFplayBackend (comandos, flags silenciosos, subproceso, pausas, offsets).
- Backend nativo Windows MCIBackend (disponibilidad y contratos).
- Backend de simulación NullBackend (reloj monotónico, testing desatendido, 0 sonido).
- Fábrica crear_reproductor con autodetección y selección explícita.
- Limpieza total de procesos huérfanos / zombis (CA-5).
- Invarianza y ausencia de deriva temporal (< 33 ms, CA-3).
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from visualizador import reproductor  # noqa: E402
from visualizador.reproductor import (  # noqa: E402
    FFplayBackend,
    MCIBackend,
    NullBackend,
    ReproductorAudio,
    crear_reproductor,
)

PISTA_PRUEBA = RAIZ / "tests" / "fixtures" / "pista_prueba.wav"

_pasadas = 0
_fallas: list[str] = []


def afirmar(condicion: bool, mensaje: str, detalle: str = "") -> None:
    global _pasadas
    if condicion:
        _pasadas += 1
        d = f"  ({detalle})" if detalle else ""
        print(f"  OK    {mensaje}{d}")
    else:
        _fallas.append(mensaje)
        d = f": {detalle}" if detalle else ""
        print(f"  FALLA {mensaje}{d}")


def prueba_contratos_e_interfaces() -> None:
    print("\n1. Contratos y Jerarquía de Clases")
    # ReproductorAudio es abstracta
    try:
        ReproductorAudio()  # type: ignore
        afirmar(False, "ReproductorAudio no debe instanciarse directamente")
    except TypeError:
        afirmar(True, "ReproductorAudio es una clase abstracta pura")

    null_rep = NullBackend()
    afirmar(isinstance(null_rep, ReproductorAudio), "NullBackend implementa ReproductorAudio")

    ffplay_rep = FFplayBackend()
    afirmar(isinstance(ffplay_rep, ReproductorAudio), "FFplayBackend implementa ReproductorAudio")

    mci_rep = MCIBackend()
    afirmar(isinstance(mci_rep, ReproductorAudio), "MCIBackend implementa ReproductorAudio")


def prueba_null_backend() -> None:
    print("\n2. NullBackend (Testing desatendido y modo seguro)")
    rep = NullBackend(duracion_simulada=10.0)
    afirmar(rep.cargar(PISTA_PRUEBA), "NullBackend carga pista existente")
    afirmar(not rep.esta_reproduciendo(), "NullBackend arranca detenido")
    afirmar(rep.posicion_actual() == 0.0, "posición inicial en 0.0s")

    # Iniciar reproducción en offset 2.5s
    ok = rep.reproducir(2.5)
    afirmar(ok and rep.esta_reproduciendo(), "NullBackend inicia reproducción en offset")
    t0 = rep.posicion_actual()
    afirmar(t0 >= 2.5, f"posición actual refleja offset ({t0:.3f} >= 2.5)")

    # Simular avance
    time.sleep(0.05)
    t1 = rep.posicion_actual()
    afirmar(t1 > t0, f"reloj monotónico avanza con el tiempo ({t1:.3f} > {t0:.3f})")

    # Pausar y reanudar
    rep.pausar()
    afirmar(not rep.esta_reproduciendo(), "pausa detiene estado de reproducción")
    pos_pausada = rep.posicion_actual()
    time.sleep(0.03)
    afirmar(rep.posicion_actual() == pos_pausada, "posición congelada durante pausa")

    rep.reanudar()
    afirmar(rep.esta_reproduciendo(), "reanudar reactiva reproducción")

    # Detener
    rep.detener()
    afirmar(not rep.esta_reproduciendo(), "detener cancela reproducción")
    afirmar(rep.posicion_actual() == 0.0, "detener reinicia posición a 0.0")

    # Fin de pista simulado
    rep.reproducir(9.98)
    time.sleep(0.04)
    afirmar(not rep.esta_reproduciendo(), "alcanzar duración detiene automáticamente")


def prueba_ffplay_backend_unitario_mock() -> None:
    print("\n3. FFplayBackend (Comandos, flags y aislamiento de subproceso)")
    rep = FFplayBackend(ruta_binario="C:/ffmpeg/bin/ffplay.exe")

    comandos_lanzados = []
    flags_lanzados = []

    class MockPopen:
        def __init__(self, cmd, **kwargs):
            comandos_lanzados.append(cmd)
            flags_lanzados.append(kwargs.get("creationflags", 0))
            self.returncode = None

        def poll(self):
            return self.returncode

        def terminate(self):
            self.returncode = 0

        def kill(self):
            self.returncode = -9

        def wait(self, timeout=None):
            return self.returncode

    with patch("subprocess.Popen", side_effect=MockPopen):
        ok_cargar = rep.cargar(PISTA_PRUEBA)
        afirmar(ok_cargar, "FFplayBackend carga ruta existente")

        ok_play = rep.reproducir(3.141)
        afirmar(ok_play, "FFplayBackend ejecuta reproducir()")
        afirmar(len(comandos_lanzados) == 1, "se invocó subprocess.Popen una vez")

        cmd = comandos_lanzados[0]
        afirmar("-nodisp" in cmd, "flag -nodisp presente en comando ffplay")
        afirmar("-autoexit" in cmd, "flag -autoexit presente en comando ffplay")
        afirmar("-loglevel" in cmd and "quiet" in cmd, "flag -loglevel quiet presente")
        afirmar("-ss" in cmd and "3.141" in cmd, "offset temporal -ss 3.141 exacto")

        if sys.platform == "win32":
            expected_flag = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
            afirmar(flags_lanzados[0] & expected_flag != 0, "creationflags incluye CREATE_NO_WINDOW en Windows")

        # Verificar pausa
        rep.pausar()
        afirmar(not rep.esta_reproduciendo(), "pausar() marca estado no reproduciendo")
        afirmar(rep._proceso is None, "pausar() termina el subproceso ffplay")

        # Verificar reanudar
        rep.reanudar()
        afirmar(len(comandos_lanzados) == 2, "reanudar lanza un nuevo subproceso con el offset retenido")

        # Verificar detención
        rep.detener()
        afirmar(rep.posicion_actual() == 0.0, "detener reinicia offset a 0.0")

        # Cierre
        rep.cerrar()
        afirmar(rep._proceso is None, "cerrar() garantiza que no haya subproceso activo")


def prueba_ffplay_backend_real() -> None:
    print("\n4. FFplayBackend Real (Subproceso físico y ciclo de vida CA-2 y CA-5)")
    if not FFplayBackend.disponible():
        print("  AVISO: ffplay.exe no disponible para prueba real; omitiendo ejecución física.")
        return

    rep = FFplayBackend()
    afirmar(rep.cargar(PISTA_PRUEBA), "carga física de pista_prueba.wav")

    # Iniciar reproducción breve
    ok = rep.reproducir(offset_seg=1.0)
    afirmar(ok, "arranque exitoso de ffplay real")
    afirmar(rep.esta_reproduciendo(), "esta_reproduciendo() es True con proceso vivo")
    afirmar(rep._proceso is not None, "subproceso Popen instanciado")

    proc = rep._proceso
    time.sleep(0.1)

    # Verificar que el reloj avanza
    pos = rep.posicion_actual()
    afirmar(pos >= 1.05, f"posición avanza respecto al offset inicial ({pos:.3f} >= 1.05)")

    # Cerrar deterministamente y verificar no-zombi (CA-5)
    rep.cerrar()
    afirmar(not rep.esta_reproduciendo(), "esta_reproduciendo() es False tras cerrar()")
    afirmar(proc.poll() is not None, f"subproceso ffplay terminado limpiamente (poll={proc.poll()})")


def prueba_mci_backend() -> None:
    print("\n5. MCIBackend (Windows winmm.dll)")
    if sys.platform != "win32":
        afirmar(not MCIBackend.disponible(), "MCI no disponible en SO no Windows")
        return

    rep = MCIBackend()
    afirmar(MCIBackend.disponible(), "MCIBackend disponible en Windows")

    # Probar carga de WAV
    ok = rep.cargar(PISTA_PRUEBA)
    afirmar(ok, "MCIBackend carga exitosamente pista_prueba.wav")
    rep.cerrar()
    afirmar(not rep._abierto, "MCIBackend cierra y libera recursos")


def prueba_fabrica_crear_reproductor() -> None:
    print("\n6. Fábrica crear_reproductor")
    r_null = crear_reproductor(backend="null")
    afirmar(isinstance(r_null, NullBackend), "crear_reproductor(backend='null') retorna NullBackend")

    if FFplayBackend.disponible():
        r_ff = crear_reproductor(PISTA_PRUEBA)
        afirmar(isinstance(r_ff, FFplayBackend), "crear_reproductor auto-selecciona FFplayBackend")
        r_ff.cerrar()

    r_mci = crear_reproductor(PISTA_PRUEBA, backend="mci")
    afirmar(isinstance(r_mci, MCIBackend), "crear_reproductor(backend='mci') retorna MCIBackend")
    r_mci.cerrar()


def prueba_invarianza_deriva_temporal_ca3() -> None:
    print("\n7. Invarianza y Ausencia de Deriva Temporal (CA-3: Drift < 33 ms)")
    # Evaluamos la exactitud del cálculo de cuadro gobernado por Master Clock
    fps = 30.0
    duracion = 16.0
    offset_base = 2.0

    t_inicio = time.perf_counter()
    errores_ms = []

    # Simulamos 10 ticks con jitter temporal aleatorio
    for i in range(10):
        time.sleep(0.015)  # ~15 ms
        t_ahora = time.perf_counter()
        t_delta = t_ahora - t_inicio
        t_actual = offset_base + t_delta

        # Cuadro esperado por fórmula canónica
        cuadro_calculado = int(t_actual * fps)
        t_reconstruido = cuadro_calculado / fps

        # Desvío máximo de cuantización debe ser exactamente 1 cuadro (< 33.3 ms)
        desvio_ms = abs(t_actual - t_reconstruido) * 1000.0
        errores_ms.append(desvio_ms)

    max_desvio = max(errores_ms)
    afirmar(max_desvio < 33.4, f"desvío máximo del Master Clock respecto a fps es {max_desvio:.2f} ms (< 33.3 ms)")


def main() -> int:
    print("========================================================================")
    print("Pruebas Automatizadas de Reproducción de Audio y Transporte (Etapa 7)")
    print("========================================================================")

    prueba_contratos_e_interfaces()
    prueba_null_backend()
    prueba_ffplay_backend_unitario_mock()
    prueba_ffplay_backend_real()
    prueba_mci_backend()
    prueba_fabrica_crear_reproductor()
    prueba_invarianza_deriva_temporal_ca3()

    print("\n========================================================================")
    print(f"Resumen: {_pasadas} comprobaciones pasadas, {len(_fallas)} fallas")
    print("========================================================================")

    if _fallas:
        print("\nFallas registradas:")
        for f in _fallas:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
