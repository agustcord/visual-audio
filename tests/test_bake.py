#!/usr/bin/env python3
"""Pruebas del subsistema de Pre-Bake, Proyección Matricial O(1) y Viewport LOD.

Criterios de Aceptación:
  CA-REARQ-1: Pre-Bake persistente en disco (.driftbake.npz), segunda carga <= 100 ms con 0 llamadas a FFmpeg.
  CA-REARQ-2: Proyección matricial S x M en memoria <= 15 ms.
  CA-REARQ-3: Recálculo de dinámica y curvas en <= 5 ms.
  CA-REARQ-4: Render Viewport LOD directo a resolución de visor <= 10 ms por cuadro.
  Invarianza: cuadro_viewport proporcional a cuadro maestro, y compatibilidad hacia atrás con analizar / analizar_cancion.
"""

from __future__ import annotations

import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
import subprocess

import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from visualizador import analisis, bake, consola, parametros, render  # noqa: E402

consola.preparar()

PISTA = RAIZ / "tests" / "fixtures" / "pista_prueba.wav"

_fallas: list[str] = []
_pasadas = 0


def afirmar(condicion: bool, titulo: str, detalle: str = "") -> None:
    global _pasadas
    if condicion:
        _pasadas += 1
        print(f"  OK    {titulo}" + (f"  ({detalle})" if detalle else ""))
    else:
        _fallas.append(titulo)
        print(f"  FALLA {titulo}" + (f"  ({detalle})" if detalle else ""))


# --------------------------------------------------------------------------- #
# 1. Pruebas Unitarias del Módulo bake.py
# --------------------------------------------------------------------------- #

def test_bake_unitario() -> None:
    print("\n1. Módulo bake.py — Persistencia, hash SHA-256 e invalidación")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        pista_tmp = tmp_path / "audio_test.wav"
        shutil.copyfile(PISTA, pista_tmp)

        # 1.1 Cálculo de hash consistente
        h1 = bake.calcular_hash_audio(pista_tmp)
        h2 = bake.calcular_hash_audio(pista_tmp)
        afirmar(isinstance(h1, str) and len(h1) == 64, "hash SHA-256 de 64 caracteres hex")
        afirmar(h1 == h2, "hash determinista para el mismo archivo")

        # 1.2 Invalidación ante cambio de mtime
        time.sleep(0.05)
        os.utime(pista_tmp, (time.time() + 10, time.time() + 10))
        h3 = bake.calcular_hash_audio(pista_tmp)
        afirmar(h1 != h3, "hash cambia al modificarse mtime")

        # 1.3 Obtención de ruta bake
        ruta_bake = bake.obtener_ruta_bake(pista_tmp)
        afirmar(ruta_bake.name == "audio_test.driftbake.npz", "nombre canónico <stem>.driftbake.npz", str(ruta_bake.name))
        afirmar(ruta_bake.parent == pista_tmp.parent, "ruta bake vive en el mismo directorio del audio")

        # 1.4 Guardado y carga de DatosBake sintético
        n_cuadros = 120
        datos_sint = bake.DatosBake(
            stft_potencia=np.ones((n_cuadros, 2049), dtype=np.float32) * 0.5,
            onda_cruda=np.ones((n_cuadros, 800), dtype=np.float32) * 0.25,
            amplitud_cruda=np.ones((n_cuadros,), dtype=np.float32) * 0.75,
            duracion=2.0,
            fps=60,
            tasa=48000,
            n_cuadros=n_cuadros,
            hash_audio=h3,
            ruta_audio=pista_tmp,
            version_formato=bake.VERSION_BAKE,
        )
        ruta_guardada = bake.guardar_bake(datos_sint, ruta_bake)
        afirmar(ruta_guardada.exists(), "archivo .driftbake.npz generado en disco")

        datos_cargados = bake.cargar_bake(ruta_bake, hash_esperado=h3, fps_esperado=60)
        afirmar(datos_cargados is not None, "cargar_bake recupera DatosBake válidos")
        if datos_cargados:
            afirmar(datos_cargados.n_cuadros == n_cuadros, "n_cuadros coincide")
            afirmar(datos_cargados.fps == 60, "fps coincide")
            afirmar(np.array_equal(datos_cargados.stft_potencia, datos_sint.stft_potencia), "stft_potencia idéntico bit a bit")
            afirmar(np.array_equal(datos_cargados.amplitud_cruda, datos_sint.amplitud_cruda), "amplitud_cruda idéntica bit a bit")
            afirmar(np.array_equal(datos_cargados.onda_cruda, datos_sint.onda_cruda), "onda_cruda idéntica bit a bit")

        # 1.5 Rechazo ante hash no coincidente
        datos_rechazados = bake.cargar_bake(ruta_bake, hash_esperado="hash_falso_invalido", fps_esperado=60)
        afirmar(datos_rechazados is None, "cargar_bake retorna None ante hash desactualizado")

        # 1.6 Rechazo ante fps no coincidente
        datos_rechazados_fps = bake.cargar_bake(ruta_bake, hash_esperado=h3, fps_esperado=30)
        afirmar(datos_rechazados_fps is None, "cargar_bake retorna None ante fps distinto")

        # 1.7 Manejo limpio ante archivo corrupto (sin excepción no controlada)
        ruta_corrupta = tmp_path / "corrupto.driftbake.npz"
        ruta_corrupta.write_bytes(b"PK\x03\x04 corrupt data truncate")
        datos_corruptos = bake.cargar_bake(ruta_corrupta, hash_esperado=None)
        afirmar(datos_corruptos is None, "cargar_bake maneja limpiamente archivo npz corrupto")


# --------------------------------------------------------------------------- #
# 2. Criterio CA-REARQ-1: Persistencia e Inmediatez de Pre-Bake
# --------------------------------------------------------------------------- #

def test_criterio_ca_rearq_1() -> None:
    print("\n2. CA-REARQ-1: Persistencia e inmediatez de Pre-Bake (<= 100 ms, 0 FFmpeg)")

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        pista_tmp = tmp_path / "cancion_real.wav"
        shutil.copyfile(PISTA, pista_tmp)

        ruta_bake = bake.obtener_ruta_bake(pista_tmp, fps=60)
        afirmar(not ruta_bake.exists(), "archivo bake no existe antes del primer análisis")

        # Primera carga: debe hornear y guardar en disco
        with patch("subprocess.run", wraps=subprocess.run) as mock_ffmpeg:
            datos_1 = analisis.hornear_audio(pista_tmp, fps=60)
            afirmar(ruta_bake.exists(), "CA-REARQ-1: se crea <audio>.driftbake.npz en primera carga")
            afirmar(mock_ffmpeg.call_count >= 1, "primera carga decodifica con FFmpeg")
            afirmar(datos_1.stft_potencia.shape[1] == 2049, "matriz causal contiene 2049 bins de frecuencia")

        # Calentamiento de FS para aislar inspección inicial de Windows Defender en tempfile
        with patch("subprocess.run", wraps=subprocess.run) as mock_ffmpeg:
            analisis.limpiar_cache_pcm()
            _ = analisis.hornear_audio(pista_tmp, fps=60)

            # Medición robusta con mediana de 3 lecturas sucesivas desde disco
            tiempos_lectura = []
            for _ in range(3):
                analisis.limpiar_cache_pcm()
                t0 = time.perf_counter()
                datos_2 = analisis.hornear_audio(pista_tmp, fps=60)
                tiempos_lectura.append((time.perf_counter() - t0) * 1000.0)

            afirmar(mock_ffmpeg.call_count == 0, "CA-REARQ-1: segunda carga realiza CERO (0) llamadas a FFmpeg")
            t_carga_mediana = float(np.median(tiempos_lectura))
            afirmar(t_carga_mediana <= 100.0, f"CA-REARQ-1: tiempo de carga directa (mediana 3 lecturas) <= 100 ms ({t_carga_mediana:.2f} ms)")
            afirmar(datos_2.n_cuadros == datos_1.n_cuadros, "mismos cuadros cargados desde bake")
            afirmar(np.array_equal(datos_1.stft_potencia, datos_2.stft_potencia), "datos de STFT idénticos bit a bit")


# --------------------------------------------------------------------------- #
# 3. Criterio CA-REARQ-2 y CA-REARQ-3: Proyección Matricial O(1) y Dinámica
# --------------------------------------------------------------------------- #

def test_criterios_ca_rearq_2_y_3() -> None:
    print("\n3. CA-REARQ-2 y CA-REARQ-3: Proyección Matricial (<= 15 ms) y Dinámica (<= 5 ms)")

    # Hornear una vez
    datos_bake = analisis.hornear_audio(PISTA, fps=60)

    # CA-REARQ-2: Proyección matricial S x M ante cambios estructurales de barras/frecuencia
    tiempos_proy = []
    for _ in range(10):
        t0 = time.perf_counter()
        a_proy = analisis.proyectar_analisis(
            datos_bake,
            {"n_barras": 64, "frec_min": 50.0, "frec_max": 12000.0, "fps": 60},
            estilo="barras",
        )
        tiempos_proy.append((time.perf_counter() - t0) * 1000.0)

    t_proy_med = float(np.mean(tiempos_proy))
    afirmar(t_proy_med <= 15.0, f"CA-REARQ-2: proyección matricial completa <= 15 ms ({t_proy_med:.2f} ms promedio)")
    afirmar(a_proy.bandas.shape == (datos_bake.n_cuadros, 64), "matriz de bandas proyectada con dimensiones correctas")
    afirmar(np.isfinite(a_proy.bandas).all(), "bandas proyectadas válidas y finitas")

    # CA-REARQ-3: Recálculo de dinámica y curvas
    tiempos_din = []
    for _ in range(10):
        t0 = time.perf_counter()
        a_din = analisis.proyectar_analisis(
            datos_bake,
            {"sensibilidad": 4.5, "curva_respuesta": "raiz", "suavizado": 0.5, "caida_picos": 0.6, "fps": 60},
            estilo="barras",
        )
        tiempos_din.append((time.perf_counter() - t0) * 1000.0)

    t_din_med = float(np.mean(tiempos_din))
    afirmar(t_din_med <= 5.0, f"CA-REARQ-3: recálculo de dinámica y curvas ultra-rápido ({t_din_med:.2f} ms promedio)")

    # Proyección O(1) de fotograma individual
    bordes = analisis._bordes_de_banda(64, 40.0, 14000.0)
    matriz = analisis._matriz_de_bandas(bordes)
    t0 = time.perf_counter()
    for _ in range(100):
        bandas_i, amp_i, onda_i = analisis.proyectar_cuadro(datos_bake, 50, matriz=matriz)
    t_cuadro_us = ((time.perf_counter() - t0) / 100) * 1_000_000.0
    afirmar(t_cuadro_us <= 100.0, f"proyección O(1) de cuadro individual en < 100 µs ({t_cuadro_us:.1f} µs)")
    afirmar(len(bandas_i) == 64, "cuadro individual proyecta 64 barras")
    afirmar(0.0 <= amp_i <= 1.0, "amplitud de cuadro en 0..1")

    # 3.2 Benchmark explícito sobre canción estándar de 3 min (10.800 cuadros @ 60 fps)
    print("  --- Benchmark de estrés (10.800 cuadros / 3 min @ 60 fps) ---")
    n_estres = 10800
    datos_estres = bake.DatosBake(
        stft_potencia=np.ones((n_estres, 2049), dtype=np.float32) * 0.5,
        onda_cruda=np.ones((n_estres, 800), dtype=np.float32) * 0.25,
        amplitud_cruda=np.ones((n_estres,), dtype=np.float32) * 0.75,
        duracion=180.0,
        fps=60,
        tasa=48000,
        n_cuadros=n_estres,
        hash_audio="hash_estres_10800",
        ruta_audio=PISTA,
        version_formato=bake.VERSION_BAKE,
    )

    # CA-REARQ-2 en 10.800 cuadros: recálculo completo de bandas (S x M) ante cambio de barras/frecuencia
    tiempos_proy_10800 = []
    for _ in range(10):
        t0 = time.perf_counter()
        a_proy_10800 = analisis.proyectar_analisis(
            datos_estres,
            {"n_barras": 48, "frec_min": 50.0, "frec_max": 12000.0, "fps": 60},
            estilo="barras",
        )
        tiempos_proy_10800.append((time.perf_counter() - t0) * 1000.0)
    t_proy_10800_med = float(np.mean(tiempos_proy_10800))
    afirmar(t_proy_10800_med <= 15.0,
            f"CA-REARQ-2 (10.800 cuadros): proyección matricial completa <= 15 ms ({t_proy_10800_med:.2f} ms promedio)")
    afirmar(a_proy_10800.bandas.shape == (10800, 48), "matriz de bandas en estrés (10800, 48)")

    # CA-REARQ-3 en 10.800 cuadros: recálculo de dinámica y curvas con caché espectral activa
    tiempos_din_10800 = []
    for _ in range(10):
        t0 = time.perf_counter()
        a_din_10800 = analisis.proyectar_analisis(
            datos_estres,
            {"n_barras": 48, "frec_min": 50.0, "frec_max": 12000.0, "sensibilidad": 4.5, "curva_respuesta": "raiz", "suavizado": 0.5, "caida_picos": 0.6, "fps": 60},
            estilo="barras",
        )
        tiempos_din_10800.append((time.perf_counter() - t0) * 1000.0)
    t_din_10800_med = float(np.mean(tiempos_din_10800))
    afirmar(t_din_10800_med <= 5.0,
            f"CA-REARQ-3 (10.800 cuadros): recálculo de dinámica y curvas <= 5 ms ({t_din_10800_med:.2f} ms promedio)")

    # Proyección O(1) de cuadro en pista de 10.800 cuadros
    bordes_estres = analisis._bordes_de_banda(48, 50.0, 12000.0)
    matriz_estres = analisis._matriz_de_bandas(bordes_estres)
    t0 = time.perf_counter()
    for _ in range(100):
        b_i, a_i, o_i = analisis.proyectar_cuadro(datos_estres, 5000, matriz=matriz_estres)
    t_cuadro_estres_us = ((time.perf_counter() - t0) / 100) * 1_000_000.0
    afirmar(t_cuadro_estres_us <= 100.0,
            f"proyección O(1) de cuadro en 10.800 cuadros < 100 µs ({t_cuadro_estres_us:.1f} µs)")


# --------------------------------------------------------------------------- #
# 4. Criterio CA-REARQ-4: Viewport LOD en render.py
# --------------------------------------------------------------------------- #

def test_criterio_ca_rearq_4() -> None:
    print("\n4. CA-REARQ-4: Render Viewport LOD directo a resolución de visor (<= 10 ms)")

    a = analisis.analizar(PISTA, {"fps": 30})
    r = render.Render(a, "barras", {
        "lienzo_ancho": 1920,
        "lienzo_alto": 1080,
        "ancho": 1920,
        "alto": 320,
        "x": 0,
        "y": 700,
        "resplandor": 0.5,
        "resplandor_radio": 18.0,
        "fps": 30,
    })

    # 4.1 Invarianza de cuadro maestro para exportación
    cuadro_maestro = r.cuadro(30)
    afirmar(cuadro_maestro.size == (1920, 1080), "Render.cuadro(i) genera a resolución completa (1920x1080)")

    # 4.2 cuadro_viewport genera directamente a resolución destino
    vp_w, vp_h = 640, 360
    cuadro_vp = r.cuadro_viewport(30, vp_w, vp_h)
    afirmar(cuadro_vp.size == (vp_w, vp_h), f"cuadro_viewport genera a resolución de visor exacto ({vp_w}x{vp_h})")

    # 4.3 Benchmark de rendimiento Viewport LOD
    tiempos_vp = []
    for _ in range(20):
        t0 = time.perf_counter()
        img = r.cuadro_viewport(30, vp_w, vp_h)
        tiempos_vp.append((time.perf_counter() - t0) * 1000.0)

    t_vp_med = float(np.mean(tiempos_vp))
    afirmar(t_vp_med <= 10.0, f"CA-REARQ-4: render Viewport LOD <= 10 ms por cuadro ({t_vp_med:.2f} ms promedio)")

    # 4.4 Proporción geométrica respetada
    # En escala 1/3 (640x360 vs 1920x1080), la zona ocupada por barras se reduce proporcionalmente
    arr_maestro = np.array(cuadro_maestro)
    arr_vp = np.array(cuadro_vp)
    pixeles_maestro = np.count_nonzero(arr_maestro[:, :, 3] > 0)
    pixeles_vp = np.count_nonzero(arr_vp[:, :, 3] > 0)
    afirmar(pixeles_maestro > 0 and pixeles_vp > 0, "ambos cuadros contienen píxeles renderizados")
    # A 1/3 de escala en cada dimensión, el área es ~1/9 (0.111x)
    ratio = pixeles_vp / pixeles_maestro
    afirmar(0.05 <= ratio <= 0.20, f"proporción de cobertura de píxeles consistente con escala LOD ({ratio:.3f})")

    # 4.5 Soporte de estilo Onda en cuadro_viewport
    r_onda = render.Render(a, "onda", {
        "lienzo_ancho": 1920,
        "lienzo_alto": 1080,
        "ancho": 1920,
        "alto": 320,
        "x": 0,
        "y": 700,
        "grosor_linea": 6,
        "fps": 30,
    })
    cuadro_onda_vp = r_onda.cuadro_viewport(30, vp_w, vp_h)
    afirmar(cuadro_onda_vp.size == (vp_w, vp_h), "cuadro_viewport funciona para estilo onda")


# --------------------------------------------------------------------------- #
# 5. Compatibilidad hacia atrás (analizar y analizar_cancion)
# --------------------------------------------------------------------------- #

def test_compatibilidad_retro() -> None:
    print("\n5. Compatibilidad hacia atrás — analizar(...) y analizar_cancion(...)")

    a1 = analisis.analizar(PISTA, {"fps": 30, "n_barras": 32})
    afirmar(isinstance(a1, analisis.Analisis), "analizar(...) retorna instancia de Analisis")
    afirmar(a1.bandas.shape[1] == 32, "analizar(...) respeta parámetros recibidos")

    afirmar(hasattr(analisis, "analizar_cancion"), "analisis expone analizar_cancion")
    a2 = analisis.analizar_cancion(PISTA, {"fps": 30, "n_barras": 32})
    afirmar(isinstance(a2, analisis.Analisis), "analizar_cancion(...) retorna instancia de Analisis")
    afirmar(np.array_equal(a1.bandas, a2.bandas), "analizar y analizar_cancion producen resultados idénticos")


# --------------------------------------------------------------------------- #

def main() -> int:
    if not PISTA.exists():
        print(f"error: falta pista de prueba: {PISTA}", file=sys.stderr)
        return 2

    print("Pruebas de Pre-Bake Persistente, Proyección O(1) y Viewport LOD (Bloque 1)")
    print(f"  pista   : {PISTA.name}")

    test_bake_unitario()
    test_criterio_ca_rearq_1()
    test_criterios_ca_rearq_2_y_3()
    test_criterio_ca_rearq_4()
    test_compatibilidad_retro()

    print(f"\n{_pasadas} comprobaciones pasadas, {len(_fallas)} fallas")
    if _fallas:
        print("\nFallaron:", file=sys.stderr)
        for f in _fallas:
            print(f"  - {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
