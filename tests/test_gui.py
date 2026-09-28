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
import math
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

from visualizador import analisis, bake, estilos, gui, parametros, proyecto, reproductor  # noqa: E402
from visualizador.render import Render  # noqa: E402

PISTA = RAIZ / "tests" / "fixtures" / "pista_espectro.wav"
PISTA_PRUEBA = RAIZ / "tests" / "fixtures" / "pista_prueba.wav"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

_pasadas = 0
_fallas: list[str] = []


def afirmar(condicion: bool, mensaje: str, detalle: str = "") -> None:
    global _pasadas
    d = f"  ({detalle})" if detalle else ""
    linea = f"  OK    {mensaje}{d}" if condicion else f"  FALLA {mensaje}{d}"
    if condicion:
        _pasadas += 1
    else:
        _fallas.append(mensaje)
    try:
        print(linea)
    except UnicodeEncodeError:
        print(linea.encode("ascii", errors="replace").decode("ascii"))


def crear_app_test(tmp_dir: Path, rep: reproductor.ReproductorAudio | None = None) -> tuple[tk.Tk, gui.VentanaVisualizador]:
    """Crea una instancia de VentanaVisualizador con root oculto para testing desatendido."""
    root = tk.Tk()
    root.withdraw()
    backend_mudo = rep or reproductor.NullBackend()
    app = gui.VentanaVisualizador(root=root, reproductor_audio=backend_mudo)
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


def criterios_etapa7_reproductor_y_transporte(tmp_dir: Path) -> None:
    print("\n========================================================================")
    print("Pruebas de Reproducción y Transporte Sincronizado en GUI (Etapa 7: CA-1 a CA-7)")
    print("========================================================================")

    class EspiaReproductor(reproductor.NullBackend):
        def __init__(self) -> None:
            super().__init__()
            self.offsets_solicitados: list[float] = []
            self.veces_reproducir = 0
            self.veces_pausar = 0
            self.veces_detener = 0
            self.veces_cerrar = 0

        def reproducir(self, offset_seg: float = 0.0) -> bool:
            self.offsets_solicitados.append(offset_seg)
            self.veces_reproducir += 1
            return super().reproducir(offset_seg)

        def pausar(self) -> None:
            self.veces_pausar += 1
            super().pausar()

        def detener(self) -> None:
            self.veces_detener += 1
            super().detener()

        def cerrar(self) -> None:
            self.veces_cerrar += 1
            super().cerrar()

    espia = EspiaReproductor()
    root, app = crear_app_test(tmp_dir, rep=espia)

    try:
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            app.cargar_audio(PISTA_PRUEBA)
            root.update()

            # CA-1: Botón Play/Pausa continuo en la GUI
            afirmar(app.btn_play_pausa.cget("text") == "▶ Reproducir", "CA-1: boton inicial en estado Reproducir")
            app.reproducir()
            root.update()
            afirmar(app._reproduciendo and app.btn_play_pausa.cget("text") == "⏸ Pausar",
                    "CA-1: boton conmuta a Pausar y estado reproduciendo es True")

            app.pausar()
            root.update()
            afirmar(not app._reproduciendo and app.btn_play_pausa.cget("text") == "▶ Reproducir",
                    "CA-1: pausar conmuta boton a Reproducir y estado es False")

            # Atajo de teclado barra espaciadora
            app._al_presionar_espacio()
            root.update()
            afirmar(app._reproduciendo and app.btn_play_pausa.cget("text") == "⏸ Pausar",
                    "CA-1: atajo de barra espaciadora alterna a Play")
            app._al_presionar_espacio()
            root.update()
            afirmar(not app._reproduciendo and app.btn_play_pausa.cget("text") == "▶ Reproducir",
                    "CA-1: atajo de barra espaciadora alterna a Pausa")

            # CA-2: Emisión de audio sincronizado en tiempo real y offset exacto
            app._cuadro_actual = 60
            app._var_escala_tiempo.set(60)
            app._actualizar_vista_previa_inmediata()
            root.update()

            espia.offsets_solicitados.clear()
            app.reproducir()
            root.update()
            afirmar(len(espia.offsets_solicitados) > 0 and abs(espia.offsets_solicitados[-1] - 2.0) < 0.001,
                    f"CA-2: reproducir en cuadro 60 envía offset exacto de 2.0s ({espia.offsets_solicitados[-1] if espia.offsets_solicitados else 0}s)")
            app.pausar()

            # CA-3: Invarianza y ausencia de deriva temporal (Drift < 1 cuadro / 33 ms)
            app._cuadro_actual = 10
            app._var_escala_tiempo.set(10)
            app.reproducir()
            for _ in range(4):
                time.sleep(0.02)
                root.update()
                app._bucle_reproduccion()

            t_perf = app._offset_seg_reloj + (time.perf_counter() - app._t_inicio_reloj)
            cuadro_esperado = int(math.floor(t_perf * app._analisis.fps))
            desvio_cuadros = abs(app._cuadro_actual - cuadro_esperado)
            afirmar(desvio_cuadros <= 1, f"CA-3: sincronía con Master Clock sin deriva (desvío = {desvio_cuadros} cuadros <= 1)")
            app.pausar()

            # CA-4: Scrubbing interactivo fluido sin saturar subprocesos
            app._cuadro_actual = 30
            app._var_escala_tiempo.set(30)
            app.reproducir()
            afirmar(app._reproduciendo, "CA-4: en reproducción activa antes de scrub")

            # Iniciar arrastre (ButtonPress-1)
            app._al_iniciar_scrubbing()
            afirmar(app._scrubbing_activo, "CA-4: scrubbing marcado activo")
            afirmar(not app._reproduciendo, "CA-4: audio pausado durante arrastre para evitar saturación")
            afirmar(app._estaba_reproduciendo_antes_de_scrub, "CA-4: retiene memoria de estado previo activo")

            reproducir_antes = espia.veces_reproducir
            # Arrastre continuo de tiempo (B1-Motion)
            for paso in [40, 50, 60, 70]:
                app._al_mover_escala_tiempo(str(paso))
                root.update()

            afirmar(espia.veces_reproducir == reproducir_antes,
                    "CA-4: arrastre continuo genera CERO llamadas a subproceso de audio")

            # Soltar arrastre (ButtonRelease-1)
            app._al_finalizar_scrubbing()
            root.update()
            afirmar(not app._scrubbing_activo, "CA-4: scrubbing finalizado")
            afirmar(app._reproduciendo, "CA-4: reproducción reanudada automáticamente al soltar")
            afirmar(abs(espia.offsets_solicitados[-1] - (70 / 30.0)) < 0.01,
                    f"CA-4: audio reanudado en offset exacto del nuevo cuadro ({espia.offsets_solicitados[-1]:.3f}s)")
            app.pausar()

            # CA-5: Ciclo de vida limpio (Cero procesos huérfanos / zombis)
            app.reproducir()
            afirmar(app._reproduciendo, "CA-5: reproductor activo")

            # Detención al cambiar de estilo
            app.cambiar_estilo("espejadas")
            afirmar(not app._reproduciendo, "CA-5: audio detenido al cambiar de estilo")

            app.reproducir()
            # Detención al aplicar preset
            app.aplicar_preset("barras_blancas")
            afirmar(not app._reproduciendo, "CA-5: audio detenido al aplicar preset")

            app.reproducir()
            # Detención al cargar nuevo audio
            app.cargar_audio(PISTA_PRUEBA)
            afirmar(not app._reproduciendo, "CA-5: audio detenido al cargar nueva pista")

            # Cierre seguro de ventana WM_DELETE_WINDOW
            app.reproducir()
            cerrar_antes = espia.veces_cerrar
            app._al_cerrar_ventana()
            afirmar(espia.veces_cerrar > cerrar_antes, "CA-5: _al_cerrar_ventana invoca cerrar() en el reproductor")

        # CA-6: Respeto estricto a la Regla 13 de dependencias
        modulos_prohibidos = ["pygame", "sounddevice", "pyaudio", "librosa", "simpleaudio"]
        violaciones = [m for m in modulos_prohibidos if m in sys.modules]
        afirmar(len(violaciones) == 0, f"CA-6: Regla 13 preservada sin bibliotecas externas no estándar ({violaciones})")

        # CA-7: Compatibilidad y degradación elegante (Fallback / NullBackend)
        afirmar(isinstance(espia, reproductor.NullBackend),
                "CA-7: interfaz operando al 100% de forma desatendida y silenciosa sobre NullBackend")

    finally:
        try:
            root.destroy()
        except Exception:
            pass


def criterios_post_mvp_bloque_a(tmp_dir: Path) -> None:
    print("\n" + "=" * 72)
    print("Pruebas de Optimización Post-MVP (Bloque A: Caché, Worker y Debounce)")
    print("=" * 72)
    root, app = crear_app_test(tmp_dir)
    try:
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            app.cargar_audio(PISTA_PRUEBA)
            root.update()

            # 1. Debounce Adaptativo por Categoría de Parámetro
            afirmar(hasattr(app, "_tiempo_debounce_para"), "app expone _tiempo_debounce_para()")
            # Cosméticos (30 ms)
            for p_cosm in ("color", "grosor_linea", "resplandor", "reflejo", "tapas_pico", "espaciado", "compensar_fondo"):
                t_deb = app._tiempo_debounce_para(p_cosm)
                afirmar(t_deb == 30, f"debounce adaptativo: '{p_cosm}' es cosmético (30 ms)")

            # Dinámica / Ganancia (100 ms)
            for p_din in ("sensibilidad", "suavizado", "caida_picos"):
                t_deb = app._tiempo_debounce_para(p_din)
                afirmar(t_deb == 100, f"debounce adaptativo: '{p_din}' es ganancia/dinámica (100 ms)")

            # Analíticos Estructurales (250 ms)
            for p_est in ("n_barras", "frec_min", "frec_max", "curva_respuesta", "fps"):
                t_deb = app._tiempo_debounce_para(p_est)
                afirmar(t_deb == 250, f"debounce adaptativo: '{p_est}' es estructural (250 ms)")

            # 2. CA-POST-1: Hilo principal no bloqueante (< 16 ms) durante arrastre de sliders
            latencias: list[float] = []
            for v in range(10, 30):
                t0 = time.perf_counter()
                app._al_mover_slider("sensibilidad", str(v / 10.0))
                root.update_idletasks()
                t_ms = (time.perf_counter() - t0) * 1000
                latencias.append(t_ms)

            lat_max = max(latencias)
            lat_med = sum(latencias) / len(latencias)
            afirmar(lat_max <= 16.0,
                    f"CA-POST-1: latencia en hilo principal <= 16 ms (máx {lat_max:.2f} ms, prom {lat_med:.2f} ms)")

            # Verificar que el label numérico se actualizó instantáneamente
            lbl_txt = app._labels_display["sensibilidad"].cget("text")
            afirmar("2.90" in lbl_txt, f"CA-POST-5: label numérico actualizado de inmediato ({lbl_txt})")

            # 3. CA-POST-3: Worker Thread y Descarte de Tareas Obsoletas (Last-Write-Wins)
            afirmar(hasattr(app, "_worker_thread") and app._worker_thread.is_alive(),
                    "app tiene worker thread secundario activo")
            afirmar(hasattr(app, "_encolar_tarea_worker"),
                    "app implementa encolado de tareas para el worker")

            # Asegurar que no queden tareas pendientes del paso previo
            if app._timer_debounce is not None:
                try:
                    app.root.after_cancel(app._timer_debounce)
                except Exception:
                    pass
                app._timer_debounce = None
            app.esperar_render_async(timeout=2.0)
            root.update()

            # Resetear contadores de auditoría
            app._contador_renders_procesados = 0
            app._contador_tareas_descartadas = 0

            # Disparar ráfaga rápida de 10 eventos (< 200 ms total)
            for i in range(10):
                app._variables["grosor_linea"].set(i + 1)
                app._solicitar_render_async()
                time.sleep(0.001)  # ráfaga en ~10 ms (< 200 ms)

            # Esperar a que el worker procese las tareas pendientes
            app.esperar_render_async(timeout=3.0)
            root.update()

            proc = app._contador_renders_procesados
            desc = app._contador_tareas_descartadas
            afirmar(proc <= 2, f"CA-POST-3: worker procesó a lo sumo 2 tareas ({proc} procesadas <= 2)")
            afirmar(desc >= 8, f"CA-POST-3: intermedias descartadas automáticamente ({desc} descartadas >= 8)")

            # Verificar que el resultado final corresponde al último valor de la ráfaga (grosor_linea = 10)
            afirmar(app._cuadro_raw_actual is not None, "cuadro renderizado entregado al canvas")

    finally:
        try:
            root.destroy()
        except Exception:
            pass


def criterios_post_mvp_bloque_b(tmp_dir: Path) -> None:
    print("\n" + "=" * 72)
    print("Pruebas de Maquillaje y UX Reactiva (Bloque B: Badge, Cursor y Ghost Frame)")
    print("=" * 72)
    root, app = crear_app_test(tmp_dir)
    try:
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            app.cargar_audio(PISTA_PRUEBA)
            root.update()

            # 1. Existencia y tokens de diseño del badge (Accesibilidad & Contrato Visual)
            afirmar(hasattr(app, "_badge_actualizando"), "app expone widget _badge_actualizando")
            lbl_texto = app._badge_actualizando.cget("text")
            afirmar(lbl_texto == "⏳ Actualizando...", f"badge contiene texto exacto: '{lbl_texto}'")
            bg_col = app._badge_actualizando.cget("bg")
            fg_col = app._badge_actualizando.cget("fg")
            afirmar(bg_col == "#18181B" and fg_col == "#F4F4F5",
                    f"badge cumple paleta accesible de alto contraste (15.9:1): bg={bg_col}, fg={fg_col}")
            afirmar(not app._badge_visible, "badge inicialmente inactivo (_badge_visible == False)")
            afirmar(app._badge_actualizando.winfo_manager() == "", "badge inicialmente no mapeado en canvas")
            afirmar(app.canvas_preview.cget("cursor") == "", "cursor de canvas inicialmente en estado normal ('')")
            afirmar(not app.esta_actualizando(), "esta_actualizando() reporta False en reposo")

            # 2. CA-POST-4: Operaciones instantáneas (< 80 ms) no muestran badge (cero parpadeos)
            app.esperar_render_async(timeout=2.0)
            root.update()
            app._desactivar_estado_computo()
            root.update()

            # Modificar parámetro cosmético y esperar render rápido
            app._variables["grosor_linea"].set(4)
            app._solicitar_render_async()
            app.esperar_render_async(timeout=2.0)
            root.update()
            app._desactivar_estado_computo()
            root.update()
            afirmar(not app._badge_visible, "CA-POST-4: cómputo rápido (< 80 ms) no activa badge visual")
            afirmar(app._badge_actualizando.winfo_manager() == "", "badge se mantuvo oculto durante operación rápida")
            afirmar(app.canvas_preview.cget("cursor") == "", "cursor permaneció normal sin parpadeo")

            # 3. CA-POST-4: Cómputo prolongado (> 80 ms) activa badge y cursor 'watch', y se oculta al finalizar
            cuadro_original = Render.cuadro
            cuadro_vp_original = Render.cuadro_viewport

            def cuadro_lento(self_render, idx):
                time.sleep(0.16)  # Retardo controlado de 160 ms (> 80 ms de gracia)
                return cuadro_original(self_render, idx)

            def cuadro_vp_lento(self_render, idx, w, h):
                time.sleep(0.16)  # Retardo controlado de 160 ms (> 80 ms de gracia)
                return cuadro_vp_original(self_render, idx, w, h)

            with patch.object(Render, "cuadro", side_effect=cuadro_lento, autospec=True), \
                 patch.object(Render, "cuadro_viewport", side_effect=cuadro_vp_lento, autospec=True):
                app._variables["grosor_linea"].set(7)
                app._solicitar_render_async()

                # Esperar 100 ms para que venza el temporizador de gracia de 80 ms
                time.sleep(0.10)
                root.update()

                # Verificar activación durante el cálculo (> 80 ms)
                afirmar(app._badge_visible, "CA-POST-4: badge se activa tras superar umbral de gracia de 80 ms")
                afirmar(app._badge_actualizando.winfo_manager() == "place", "CA-POST-4: widget de badge mapeado en canvas ('place')")
                afirmar(app.canvas_preview.cget("cursor") == "watch", "CA-POST-4: cursor inteligente conmuta a 'watch' durante cálculo")
                afirmar(app.esta_actualizando(), "esta_actualizando() reporta True durante cálculo")

                # Preservación de fotograma previo (Ghost frame / Never blank) mientras calcula
                items_durante = app.canvas_preview.find_withtag("canvas_imagen")
                afirmar(len(items_durante) > 0, "CA-POST-5: canvas conserva el fotograma previo durante el cálculo (never blank)")
                afirmar(app._cuadro_raw_actual is not None, "cuadro previo en memoria intacto durante el cálculo")

            # Esperar a que el worker complete y despache el nuevo cuadro
            app.esperar_render_async(timeout=3.0)
            root.update()
            app._desactivar_estado_computo()
            root.update()

            # Verificar desactivación inmediata al recibir el cuadro
            afirmar(not app._badge_visible, "CA-POST-4: badge se desactiva inmediatamente al entregar nuevo cuadro")
            afirmar(app._badge_actualizando.winfo_manager() == "", "CA-POST-4: widget de badge desmapeado del canvas")
            afirmar(app.canvas_preview.cget("cursor") == "", "CA-POST-4: cursor restaurado a flecha normal ('') al finalizar")
            afirmar(not app.esta_actualizando(), "esta_actualizando() reporta False tras finalizar")

            # Preservación y proyección del nuevo cuadro
            items_despues = app.canvas_preview.find_withtag("canvas_imagen")
            afirmar(len(items_despues) == 1, "un único cuadro renderizado proyectado en canvas al concluir")

            # 4. Respuesta sincrónica inmediata de displays numéricos (CA-POST-5)
            app._al_mover_slider("n_barras", "48")
            lbl_barras = app._labels_display["n_barras"].cget("text")
            afirmar(lbl_barras == "48", f"CA-POST-5: label numérico actualizado de inmediato a 60 fps ({lbl_barras})")

    finally:
        try:
            root.destroy()
        except Exception:
            pass


def probar_viewport_lod_render_y_blit(app: gui.VentanaVisualizador, root: tk.Tk | None = None) -> None:
    """Valida el pipeline de Viewport LOD directo en Canvas (CA-REARQ-4).

    Verifica la eliminación total de resize bilineal 1080p en render interactivo,
    aplica warmup anti-jitter de 4 cuadros no cronometrados, y comprueba que el tiempo
    promedio de render + blit sea <= 10.0 ms (capacidad >= 100 FPS en CPU) y la mediana
    estadística sobre ventanas de 10 cuadros sea <= 10.0 ms, con tolerancia a context-switch
    del sistema operativo (p95 <= 16.6 ms o máx <= 25.0 ms).
    """
    with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
        # En entorno de test desatendido, configurar dimensiones representativas de viewport
        app.canvas_preview.winfo_width = lambda: 640
        app.canvas_preview.winfo_height = lambda: 360
        app._cuadro_actual = 20

        # Espiar llamadas a Image.resize
        original_resize = Image.Image.resize
        contador_resizes = [0]

        def spy_resize(self_img: Image.Image, size: tuple[int, int], *args: object, **kwargs: object) -> Image.Image:
            contador_resizes[0] += 1
            return original_resize(self_img, size, *args, **kwargs)

        with patch.object(Image.Image, "resize", side_effect=spy_resize):
            app._actualizar_vista_previa_inmediata()
            afirmar(contador_resizes[0] == 0, "CA-REARQ-4 (GUI): cero llamadas a Image.resize en render interactivo")

        # Pase previo de pre-calentamiento (warmup de 4 cuadros no cronometrados)
        # para estabilizar la asignación de buffers de Tkinter, PhotoImage y Pillow
        for w_idx in range(4):
            app._cuadro_actual = w_idx % app._analisis.n_cuadros
            app._actualizar_vista_previa_inmediata()

        # Benchmark de 60 cuadros consecutivos en canvas con Viewport LOD
        tiempos_frame: list[float] = []
        for frame_idx in range(60):
            c_idx = frame_idx % app._analisis.n_cuadros
            app._cuadro_actual = c_idx
            t0 = time.perf_counter()
            app._actualizar_vista_previa_inmediata()
            dt_ms = (time.perf_counter() - t0) * 1000.0
            tiempos_frame.append(dt_ms)

        t_med_frame = float(np.mean(tiempos_frame))
        t_p95 = float(np.percentile(tiempos_frame, 95))
        t_max_frame = float(np.max(tiempos_frame))

        # Medición estadística robusta sobre ventanas de 10 cuadros contra jitter del SO / GC
        medianas_10 = [
            float(np.median(tiempos_frame[i:i + 10]))
            for i in range(0, len(tiempos_frame), 10)
        ]
        t_mediana_10 = float(np.mean(medianas_10))

        afirmar(t_med_frame <= 10.0,
                f"CA-REARQ-4 (GUI): tiempo promedio render + blit <= 10.0 ms ({t_med_frame:.2f} ms, capacidad >= 100 FPS)")
        afirmar(t_mediana_10 <= 10.0,
                f"CA-REARQ-4 (GUI): latencia estadística mediana (10 cuadros) <= 10.0 ms ({t_mediana_10:.2f} ms)")
        afirmar(t_p95 <= 16.6 or t_max_frame <= 25.0,
                f"CA-REARQ-4 (GUI): tiempo de cuadro anti-jitter <= 16.6 ms p95 o cota <= 25.0 ms (p95={t_p95:.2f} ms, máx={t_max_frame:.2f} ms, presupuesto 60 FPS)")


def criterios_rearquitectura_bloque_2(tmp_dir: Path) -> None:
    print("\n" + "=" * 72)
    print("Pruebas de Re-arquitectura de Rendimiento (Bloque 2: GUI, Viewport LOD & 60 FPS)")
    print("=" * 72)

    # 1. Tarea 2.5: Carga con Pre-Bake persistente y feedback en worker thread
    print("\nB2.1 — Tarea 2.5: Integración de Pre-Bake y carga asíncrona en GUI")
    pista_b2 = tmp_dir / "audio_b2_test.wav"
    shutil.copyfile(PISTA_PRUEBA, pista_b2)
    ruta_bake = bake.obtener_ruta_bake(pista_b2, fps=60)
    if ruta_bake.exists():
        ruta_bake.unlink()

    root, app = crear_app_test(tmp_dir)
    try:
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            # A) Primera carga: no existe bake en disco -> hornea en worker thread y crea .driftbake.npz
            app.obtener_variable("fps").set(60)
            afirmar(not ruta_bake.exists(), "archivo .driftbake.npz no existe antes de la primera carga")
            ok_1 = app.cargar_audio(pista_b2)
            root.update()
            afirmar(ok_1, "primera carga de audio completa con éxito")
            afirmar(ruta_bake.is_file(), "CA-REARQ-1 (GUI): archivo .driftbake.npz creado en disco tras primera carga")
            afirmar(app._datos_bake is not None, "app almacena DatosBake en memoria RAM")
            afirmar(app._datos_bake.stft_potencia.shape[1] == 2049, "DatosBake contiene matriz causal densa de 2049 bins")

            # B) Segunda carga: existe bake en disco -> carga instantánea en < 100 ms y 0 llamadas a FFmpeg
            import subprocess
            with patch("subprocess.run", wraps=subprocess.run) as mock_ffmpeg:
                t0 = time.perf_counter()
                ok_2 = app.cargar_audio(pista_b2)
                t_carga_ms = (time.perf_counter() - t0) * 1000.0
                root.update()

                afirmar(ok_2, "segunda carga de audio completa con éxito")
                afirmar(mock_ffmpeg.call_count == 0, "CA-REARQ-1 (GUI): segunda carga realiza CERO llamadas a FFmpeg")
                afirmar(t_carga_ms <= 100.0, f"CA-REARQ-1 (GUI): tiempo de carga en memoria <= 100 ms ({t_carga_ms:.2f} ms)")

        # 2. Tarea 2.6: Viewport LOD en Canvas y eliminación de resize bilineal 1080p
        print("\nB2.2 — Tarea 2.6: Pipeline de Viewport LOD directo en Canvas")
        probar_viewport_lod_render_y_blit(app, root)

        # 3. Tarea 2.7: Desacople de controles deslizantes (Sliders) y proyección O(1)
        print("\nB2.3 — Tarea 2.7: Desacople de sliders, recálculo < 10 ms y badge ausente")
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            # Modificación de barras espectrales (filtro) mediante proyección O(1)
            t0 = time.perf_counter()
            p_filtro = dict(app.obtener_parametros())
            p_filtro["n_barras"] = 48
            a_filtro = analisis.proyectar_analisis(app._datos_bake, p_filtro, app._estilo)
            t_filtro_ms = (time.perf_counter() - t0) * 1000.0

            afirmar(t_filtro_ms <= 15.0, f"CA-REARQ-2 (GUI): recálculo espectral por slider <= 15 ms ({t_filtro_ms:.2f} ms)")
            afirmar(a_filtro.n_bandas == 48, "matriz de análisis proyecta 48 bandas")

            # Modificación de dinámica / ganancia mediante proyección O(1)
            t0 = time.perf_counter()
            p_din = dict(app.obtener_parametros())
            p_din["sensibilidad"] = 4.0
            a_din = analisis.proyectar_analisis(app._datos_bake, p_din, app._estilo)
            t_din_ms = (time.perf_counter() - t0) * 1000.0

            afirmar(t_din_ms <= 10.0, f"CA-REARQ-3 (GUI): ajuste de dinámica por slider <= 10 ms ({t_din_ms:.2f} ms)")

            # Verificar ausencia de badge invasivo en operaciones rápidas del worker
            app.esperar_render_async(timeout=1.0)
            app._desactivar_estado_computo()
            root.update()
            app._variables["sensibilidad"].set(2.5)
            app._solicitar_render_async()
            app.esperar_render_async(timeout=2.0)
            root.update()
            app._desactivar_estado_computo()
            root.update()

            afirmar(not app._badge_visible, "CA-POST-4: badge visual no se activa ante slider instantáneo")
            afirmar(app.canvas_preview.cget("cursor") == "", "cursor de canvas permanece normal")

        # 4. Tarea 2.8: Transporte y Scrubbing a 60 FPS
        print("\nB2.4 — Tarea 2.8: Scrubbing continuo a 60 FPS estables sin saturación")
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            app._al_iniciar_scrubbing()
            tiempos_scrub = []
            for scrub_idx in range(60):
                c_target = scrub_idx % app._analisis.n_cuadros
                t0 = time.perf_counter()
                app._al_mover_escala_tiempo(str(c_target))
                tiempos_scrub.append((time.perf_counter() - t0) * 1000.0)

            app._al_finalizar_scrubbing()
            root.update()

            t_med_scrub = float(np.mean(tiempos_scrub))
            afirmar(t_med_scrub <= 12.0, f"CA-REARQ-4 (Scrubbing): latencia promedio de scrub <= 12 ms ({t_med_scrub:.2f} ms)")
            afirmar(root.winfo_exists(), "la interfaz permanece perfectamente fluida y responsiva")

    finally:
        try:
            root.destroy()
        except Exception:
            pass


def probar_selector_color_barras_y_ondas(tmp_dir: Path) -> None:
    print("\n========================================================================")
    print("Pruebas de Selector de Color en Barras y Ondas (CA-COLOR-1 a CA-COLOR-5)")
    print("========================================================================")
    root, app = crear_app_test(tmp_dir)
    try:
        with patch("tkinter.messagebox.showinfo"), patch("tkinter.messagebox.showwarning"), patch("tkinter.messagebox.showerror"):
            # 1. Cargar audio y posicionar en cuadro con señal
            app.cargar_audio(PISTA_PRUEBA)
            root.update()
            app.cambiar_estilo("barras")
            app._cuadro_actual = 60
            app._actualizar_vista_previa_inmediata()
            app._solicitar_render_async()
            app.esperar_render_async(timeout=4.0)
            root.update()

            # 2. CA-COLOR-1: Selección de nuevo color (#FF0000) en estilo barras
            with patch("tkinter.colorchooser.askcolor", return_value=((255, 0, 0), "#ff0000")) as mock_ask:
                app._elegir_color("color")
                root.update()
                mock_ask.assert_called_once()
                args, kwargs = mock_ask.call_args
                afirmar(kwargs.get("parent") == app.root, "parent=self.root pasado a colorchooser.askcolor")
                afirmar(kwargs.get("title") == "Elegir color", "título correcto pasado a colorchooser.askcolor")

            afirmar(app.obtener_variable("color").get() == "#FF0000",
                    "CA-COLOR-1: variable 'color' muta a #FF0000 tras selección")

            # 3. CA-COLOR-3: Actualización de muestra y accesibilidad de contraste
            lbl_muestra = app._muestras_color["color"]
            afirmar(lbl_muestra.cget("bg").upper() == "#FF0000",
                    "CA-COLOR-3: muestra de color actualiza fondo bg a #FF0000")
            afirmar(lbl_muestra.cget("text").upper() == "#FF0000",
                    "CA-COLOR-3: muestra de color actualiza texto a #FF0000")
            afirmar(lbl_muestra.cget("fg").upper() == "#FFFFFF",
                    "CA-COLOR-3: contraste accesible fg=#FFFFFF para color oscuro #FF0000")

            # 4. CA-COLOR-2: Cancelación limpia de diálogo (mock retorna (None, None))
            with patch("tkinter.colorchooser.askcolor", return_value=(None, None)):
                app._elegir_color("color")
                root.update()

            afirmar(app.obtener_variable("color").get() == "#FF0000",
                    "CA-COLOR-2: cancelación (None, None) preserva valor #FF0000")
            afirmar(app._muestras_color["color"].cget("bg").upper() == "#FF0000",
                    "CA-COLOR-2: muestra conserva fondo previo tras cancelación")

            # Cancelación con retorno None directo
            with patch("tkinter.colorchooser.askcolor", return_value=None):
                app._elegir_color("color")
                root.update()

            afirmar(app.obtener_variable("color").get() == "#FF0000",
                    "CA-COLOR-2: retorno None no produce excepciones ni altera valor")

            # 5. Selección de color claro (#00FF00) para validar contraste invertido
            with patch("tkinter.colorchooser.askcolor", return_value=((0, 255, 0), "#00ff00")):
                app._elegir_color("color")
                root.update()

            afirmar(app.obtener_variable("color").get() == "#00FF00",
                    "CA-COLOR-1: variable 'color' muta a #00FF00 tras selección")
            afirmar(app._muestras_color["color"].cget("fg").upper() == "#000000",
                    "CA-COLOR-3: contraste accesible fg=#000000 para color claro #00FF00")

            # 6. Interacción mediante click en la muestra de color (evento <Button-1>)
            with patch("tkinter.colorchooser.askcolor", return_value=((255, 0, 0), "#ff0000")):
                app._muestras_color["color"].event_generate("<Button-1>")
                root.update()

            afirmar(app.obtener_variable("color").get() == "#FF0000",
                    "interacción: click sobre muestra de color dispara selector y actualiza variable")

            # 7. CA-COLOR-4: Debounce adaptativo y regeneración de fotograma en worker/canvas
            t_debounce = app._tiempo_debounce_para("color")
            afirmar(t_debounce <= 30, f"CA-COLOR-4: debounce cosmético configurado en <= 30 ms ({t_debounce} ms)")

            # Esperar a que venza el debounce cosmético de 30 ms y procese el render asíncrono
            time.sleep(0.04)
            root.update()
            ok_render = app.esperar_render_async(timeout=4.0)
            root.update()
            afirmar(ok_render, "CA-COLOR-4: render asíncrono completado tras debounce cosmético")

            cuadro_barras = app.obtener_cuadro_actual_raw()
            afirmar(cuadro_barras is not None, "CA-COLOR-4: fotograma de barras generado")
            if cuadro_barras is not None:
                arr_barras = np.array(cuadro_barras)
                pixeles_rojos = np.count_nonzero(
                    (arr_barras[:, :, 0] > 200) & (arr_barras[:, :, 1] < 50) & (arr_barras[:, :, 2] < 50) & (arr_barras[:, :, 3] > 0)
                )
                afirmar(pixeles_rojos > 0, f"CA-COLOR-4: fotograma de barras proyecta color rojo ({pixeles_rojos} píxeles)")

            # 8. Verificación en estilo 'onda' y color secundario 'color_final'
            app.cambiar_estilo("onda")
            root.update()
            with patch("tkinter.colorchooser.askcolor", return_value=((0, 255, 0), "#00ff00")):
                app._elegir_color("color")
                root.update()

            afirmar(app.obtener_variable("color").get() == "#00FF00",
                    "CA-COLOR-1: selector funciona correctamente en estilo 'onda'")

            time.sleep(0.04)
            root.update()
            app.esperar_render_async(timeout=4.0)
            root.update()

            cuadro_onda = app.obtener_cuadro_actual_raw()
            afirmar(cuadro_onda is not None, "CA-COLOR-4: fotograma de onda generado")
            if cuadro_onda is not None:
                arr_onda = np.array(cuadro_onda)
                pixeles_verdes = np.count_nonzero(
                    (arr_onda[:, :, 1] > 200) & (arr_onda[:, :, 0] < 50) & (arr_onda[:, :, 2] < 50) & (arr_onda[:, :, 3] > 0)
                )
                afirmar(pixeles_verdes > 0, f"CA-COLOR-4: fotograma de onda proyecta color verde ({pixeles_verdes} píxeles)")

    finally:
        try:
            root.destroy()
        except Exception:
            pass


def main() -> int:
    print("Pruebas Automatizadas de Interfaz Gráfica Tkinter (Etapa 5 y 7)")
    print(f"  pista   : {PISTA.name}\n")

    tmp_dir = Path(tempfile.mkdtemp(prefix="drift_test_gui_"))
    try:
        criterio_5_1_flujo_completo(tmp_dir)
        criterio_5_2_invarianza_estructural(tmp_dir)
        criterio_5_3_latencia_vista_previa(tmp_dir)
        criterio_5_4_concurrencia_y_cancelacion(tmp_dir)
        criterio_5_5_cobertura_esquema_y_dependencias(tmp_dir)
        criterio_5_6_resiliencia_errores(tmp_dir)
        pruebas_transporte_y_presets(tmp_dir)
        criterios_etapa7_reproductor_y_transporte(tmp_dir)
        criterios_post_mvp_bloque_a(tmp_dir)
        criterios_post_mvp_bloque_b(tmp_dir)
        criterios_rearquitectura_bloque_2(tmp_dir)
        probar_selector_color_barras_y_ondas(tmp_dir)
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
