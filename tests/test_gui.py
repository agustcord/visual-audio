"""Pruebas automatizadas de la interfaz gráfica Tkinter (Etapa 5).

Verifica formalmente los Criterios de Aceptación 5.1 a 5.6:
- 5.1: Recorrido completo sin tocar la línea de comandos (cargar, elegir, ajustar, guardar, exportar).
- 5.2: Invarianza estructural (MVP-5): el cuadro de la vista previa es idéntico bit a bit al exportador.
- 5.3: La vista previa se actualiza en menos de 500 ms a media resolución.
- 5.4: La interfaz no se congela durante el export, y la cancelación cooperativa funciona y limpia.
- 5.5: El 100% de los valores del esquema aparecen en la interfaz y responden a dependencias.
- 5.6: Un audio corrupto o inexistente emite aviso claro sin traceback.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path
from unittest.mock import patch
import tkinter as tk
from tkinter import ttk
import numpy as np
from PIL import Image

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from visualizador import estilos, gui, parametros, proyecto  # noqa: E402
from visualizador.render import Render  # noqa: E402

PISTA = RAIZ / "tests" / "fixtures" / "pista_espectro.wav"
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


def crear_app_test(tmp_dir: Path) -> tuple[tk.Tk, gui.VentanaVisualizador]:
    """Crea una instancia de VentanaVisualizador con root oculto para testing desatendido."""
    root = tk.Tk()
    root.withdraw()
    app = gui.VentanaVisualizador(root=root)
    root.update()
    return root, app


def criterio_5_1_flujo_completo(tmp_dir: Path) -> None:
    print("\n5.1  Recorrido completo sin tocar la línea de comandos")
    root, app = crear_app_test(tmp_dir)
    try:
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            # 1. Cargar audio
            ok_audio = app.cargar_audio(PISTA_PRUEBA)
            root.update()
            afirmar(ok_audio, "carga de audio exitosa desde la interfaz")
            afirmar(app._analisis is not None and app._analisis.n_cuadros > 0,
                    f"audio analizado correctamente con {app._analisis.n_cuadros if app._analisis else 0} cuadros")

            # 2. Elegir estilo
            app.cambiar_estilo("onda")
            root.update()
            afirmar(app._estilo == "onda", "cambio de estilo a 'onda' en la interfaz")

            # 3. Ajustar valores
            app.obtener_variable("grosor_linea").set(8)
            app.obtener_variable("color").set("#FF0055")
            app._actualizar_vista_previa_inmediata()
            root.update()
            p_actuales = app.obtener_parametros()
            afirmar(p_actuales["grosor_linea"] == 8 and p_actuales["color"] == "#FF0055",
                    "ajuste de parámetros reflejado en el estado de la interfaz")

            # 4. Guardar proyecto
            ruta_proy = tmp_dir / "flujo_proy.json"
            ok_guardar = app.guardar_proyecto(ruta_proy)
            afirmar(ok_guardar and ruta_proy.is_file(), "guardado de proyecto en archivo JSON")

            # 5. Reabrir proyecto
            ok_reabrir = app.cargar_proyecto(ruta_proy)
            root.update()
            afirmar(ok_reabrir, "reapertura de proyecto desde archivo JSON")
            p_reabiertos = app.obtener_parametros()
            afirmar(p_reabiertos["color"] == "#FF0055" and p_reabiertos["grosor_linea"] == 8,
                    "parámetros recuperados con fidelidad del proyecto guardado")

            # 6. Exportar video (usando tamaño reducido para agilizar prueba)
            app.obtener_variable("lienzo_ancho").set(480)
            app.obtener_variable("lienzo_alto").set(270)
            app.obtener_variable("ancho").set(480)
            app.obtener_variable("alto").set(80)
            app.obtener_variable("x").set(0)
            app.obtener_variable("y").set(170)
            app._actualizar_vista_previa_inmediata()
            root.update()

            ruta_video = tmp_dir / "flujo_video.webm"
            finalizado = [False]
            error_exp = [None]

            def cb_fin(escrito: Path | None, err: Exception | None) -> None:
                finalizado[0] = True
                error_exp[0] = err

            app.exportar_video_async(ruta_video, callback_finalizado=cb_fin)

            t_espera = 0.0
            while not finalizado[0] and t_espera < 15.0:
                root.update()
                time.sleep(0.05)
                t_espera += 0.05

            det_err = f"error: {error_exp[0]}" if error_exp[0] else ""
            afirmar(finalizado[0] and error_exp[0] is None, "exportación de video completada sin excepciones", det_err)
            afirmar(ruta_video.is_file() and ruta_video.stat().st_size > 0,
                    f"archivo de video WebM generado en disco ({ruta_video.stat().st_size if ruta_video.is_file() else 0} bytes)")

    finally:
        root.destroy()


def criterio_5_2_invarianza_estructural(tmp_dir: Path) -> None:
    print("\n5.2  Invarianza estructural: cuadro de vista previa idéntico al del export (MVP-5)")
    root, app = crear_app_test(tmp_dir)
    try:
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            app.cargar_audio(PISTA)
            root.update()

            for estilo_nom in ("barras", "onda", "espejadas"):
                app.cambiar_estilo(estilo_nom)
                app._cuadro_actual = 60
                app._actualizar_vista_previa_inmediata()
                root.update()

                cuadro_gui = app.obtener_cuadro_actual_raw()
                afirmar(cuadro_gui is not None, f"{estilo_nom}: vista previa genera cuadro raw RGBA")

                # Generar cuadro de referencia directamente desde Render
                render_ref = Render(app._analisis, app._estilo, app.obtener_parametros())
                cuadro_ref = render_ref.cuadro(60)

                # Generar cuadro desde el iterador cuadros() que utiliza salida.exportar()
                cuadro_export = next(render_ref.cuadros(desde=60, hasta=61))

                arr_gui = np.array(cuadro_gui)
                arr_ref = np.array(cuadro_ref)
                arr_exp = np.array(cuadro_export)

                iguales_ref = np.array_equal(arr_gui, arr_ref)
                iguales_exp = np.array_equal(arr_gui, arr_exp)

                hash_gui = hashlib.sha256(cuadro_gui.tobytes()).hexdigest()
                hash_exp = hashlib.sha256(cuadro_export.tobytes()).hexdigest()

                afirmar(iguales_ref, f"{estilo_nom}: array RGBA de vista previa idéntico al de Render.cuadro(i)")
                afirmar(iguales_exp, f"{estilo_nom}: array RGBA de vista previa idéntico al de cuadros() para export")
                afirmar(hash_gui == hash_exp, f"{estilo_nom}: hash SHA-256 idéntico ({hash_gui[:12]})")

    finally:
        root.destroy()


def criterio_5_3_latencia_vista_previa(tmp_dir: Path) -> None:
    print("\n5.3  La vista previa se actualiza en menos de 500 ms")
    root, app = crear_app_test(tmp_dir)
    try:
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            app.cargar_audio(PISTA)
            root.update()

            tiempos: list[float] = []
            for i in (10, 50, 100, 150, 200):
                app._cuadro_actual = i
                t0 = time.perf_counter()
                app._actualizar_vista_previa_inmediata()
                root.update()
                t1 = time.perf_counter()
                tiempos.append(t1 - t0)

            t_max = max(tiempos)
            t_medio = sum(tiempos) / len(tiempos)

            afirmar(t_max < 0.500,
                    f"tiempo máximo de render y proyección menor a 500 ms",
                    f"máx {t_max * 1000:.1f} ms, promedio {t_medio * 1000:.1f} ms")

    finally:
        root.destroy()


def criterio_5_4_concurrencia_y_cancelacion(tmp_dir: Path) -> None:
    print("\n5.4  La interfaz no se congela durante el export, y cancelar funciona")
    root, app = crear_app_test(tmp_dir)
    try:
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            app.cargar_audio(PISTA)
            app.obtener_variable("lienzo_ancho").set(960)
            app.obtener_variable("lienzo_alto").set(540)
            app._actualizar_vista_previa_inmediata()
            root.update()

            ruta_salida = tmp_dir / "video_a_cancelar.webm"
            finalizado = [False]
            err_resultado = [None]

            def cb_fin(escrito: Path | None, err: Exception | None) -> None:
                finalizado[0] = True
                err_resultado[0] = err

            app.exportar_video_async(ruta_salida, callback_finalizado=cb_fin)

            # Esperar a que arranque el subproceso y el hilo esté activo
            for _ in range(30):
                root.update()
                if getattr(app, "_hilo_export", None) and app._hilo_export.is_alive():
                    break
                time.sleep(0.01)

            # Cancelar exportación
            app.cancelar_exportacion()

            # Dar tiempo a que el hilo termine y limpie el archivo
            t_espera = 0.0
            while not finalizado[0] and t_espera < 10.0:
                root.update()
                time.sleep(0.05)
                t_espera += 0.05

            afirmar(finalizado[0], "hilo de exportación terminó tras señalizar cancelación", f"err={err_resultado[0]}")
            afirmar(not ruta_salida.exists(), "el archivo incompleto fue eliminado del disco")
            afirmar(root.winfo_exists(), "la interfaz gráfica sigue viva y respondiendo")

    finally:
        root.destroy()


def criterio_5_5_cobertura_esquema_y_dependencias(tmp_dir: Path) -> None:
    print("\n5.5  100% de los valores del esquema presentes en la interfaz")
    root, app = crear_app_test(tmp_dir)
    try:
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            total_esquema = len(parametros.ESQUEMA)
            presentes = 0
            for nombre, def_val in parametros.ESQUEMA.items():
                if nombre in app._variables and nombre in app._filas_parametro and app.obtener_widget(nombre):
                    presentes += 1

            afirmar(presentes == total_esquema,
                    f"todos los valores de ESQUEMA tienen control en la UI ({presentes}/{total_esquema})")

            # Comprobar reactividad de dependencias
            # Caso 1: resplandor_radio depende de resplandor
            app.obtener_variable("resplandor").set(0.0)
            app._actualizar_habilitacion_dependencias()
            widgets_radio = app.obtener_widget("resplandor_radio")
            scale_radio = next((w for w in widgets_radio if isinstance(w, ttk.Scale)), None)
            afirmar(scale_radio is not None and str(scale_radio.cget("state")) == "disabled",
                    "resplandor_radio deshabilitado cuando resplandor == 0.0")

            app.obtener_variable("resplandor").set(0.5)
            app._actualizar_habilitacion_dependencias()
            afirmar(scale_radio is not None and str(scale_radio.cget("state")) == "normal",
                    "resplandor_radio habilitado cuando resplandor > 0.0")

            # Caso 2: color_final depende de degradado
            app.obtener_variable("degradado").set("ninguno")
            app._actualizar_habilitacion_dependencias()
            widgets_cf = app.obtener_widget("color_final")
            btn_cf = next((w for w in widgets_cf if isinstance(w, ttk.Button)), None)
            afirmar(btn_cf is not None and str(btn_cf.cget("state")) == "disabled",
                    "color_final deshabilitado cuando degradado == 'ninguno'")

            app.obtener_variable("degradado").set("vertical")
            app._actualizar_habilitacion_dependencias()
            afirmar(btn_cf is not None and str(btn_cf.cget("state")) == "normal",
                    "color_final habilitado cuando degradado != 'ninguno'")

    finally:
        root.destroy()


def criterio_5_6_resiliencia_errores(tmp_dir: Path) -> None:
    print("\n5.6  Audio corrupto o inexistente avisa sin traceback")
    root, app = crear_app_test(tmp_dir)
    try:
        avisos_error: list[str] = []

        def mock_showerror(titulo: str, mensaje: str) -> None:
            avisos_error.append(f"{titulo}: {mensaje}")

        with patch("tkinter.messagebox.showerror", side_effect=mock_showerror):
            # 1. Archivo inexistente
            ruta_inexistente = tmp_dir / "fantasma_no_existe_404.wav"
            ok_inexistente = app.cargar_audio(ruta_inexistente)
            root.update()

            afirmar(not ok_inexistente, "cargar_audio devuelve False ante archivo inexistente")
            afirmar(app._ultimo_error is not None and "no existe" in app._ultimo_error,
                    f"error registrado limpiamente: {app._ultimo_error}")
            afirmar(len(avisos_error) >= 1, "diálogo de error emitido ante archivo inexistente")

            # 2. Archivo corrupto (bytes aleatorios)
            ruta_corrupta = tmp_dir / "corrupto.mp3"
            with open(ruta_corrupta, "wb") as f:
                f.write(b"ESTO NO ES UN ARCHIVO DE AUDIO VALIDO 1234567890")

            avisos_error.clear()
            ok_corrupto = app.cargar_audio(ruta_corrupta)
            root.update()

            afirmar(not ok_corrupto, "cargar_audio devuelve False ante audio corrupto")
            afirmar(app._ultimo_error is not None and len(avisos_error) >= 1,
                    f"error de análisis capturado y dialogado: {app._ultimo_error}")
            afirmar(root.winfo_exists(), "la interfaz permanece estable y operativa tras el error")

    finally:
        root.destroy()


def pruebas_transporte_y_presets(tmp_dir: Path) -> None:
    print("\nExtra  Transporte, scrubbing, animación de fragmento y presets")
    root, app = crear_app_test(tmp_dir)
    try:
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            app.cargar_audio(PISTA)
            root.update()

            # Avance y retroceso de cuadro
            ini = app._cuadro_actual
            app._avanzar_un_cuadro()
            root.update()
            afirmar(app._cuadro_actual == ini + 1, "avanzar cuadro incrementa en 1")

            app._retroceder_un_cuadro()
            root.update()
            afirmar(app._cuadro_actual == ini, "retroceder cuadro decrementa en 1")

            # Presets
            for pre in ("barras_neon", "onda_suave"):
                ok_pre = app.aplicar_preset(pre)
                root.update()
                afirmar(ok_pre, f"preset '{pre}' aplicado exitosamente desde la UI")

            # Animación de fragmento
            app._iniciar_animacion_fragmento()
            afirmar(app._reproduciendo, "fragmento animado inicia reproducción cooperativa")
            for _ in range(5):
                root.update()
                time.sleep(0.04)
            app._detener_animacion()
            afirmar(not app._reproduciendo, "fragmento animado se detiene limpiamente")

    finally:
        root.destroy()


def main() -> int:
    print("Pruebas Automatizadas de Interfaz Gráfica Tkinter (Etapa 5)")
    print(f"  pista   : {PISTA.name}\n")

    tmp_dir = Path(tempfile.mkdtemp(prefix="drift_test_etapa5_"))
    try:
        criterio_5_1_flujo_completo(tmp_dir)
        criterio_5_2_invarianza_estructural(tmp_dir)
        criterio_5_3_latencia_vista_previa(tmp_dir)
        criterio_5_4_concurrencia_y_cancelacion(tmp_dir)
        criterio_5_5_cobertura_esquema_y_dependencias(tmp_dir)
        criterio_5_6_resiliencia_errores(tmp_dir)
        pruebas_transporte_y_presets(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n{_pasadas} comprobaciones pasadas, {len(_fallas)} fallas\n")
    if _fallas:
        print("Fallas:")
        for f in _fallas:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
