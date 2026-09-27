"""Interfaz gráfica de usuario (Tkinter) para el visualizador de audio.

Contratos canónicos definidos en docs/ARQUITECTURA.md §8, docs/MVP.md §4 y
docs/RUTA_DE_TRABAJO.md §4:
- Motor desacoplado: esta interfaz es un cliente más del motor (como cli.py).
- Formulario dinámico generado a partir de parametros.ESQUEMA sin controles cableados a mano.
- Invarianza estructural (MVP-5): la vista previa utiliza estrictamente Render.cuadro(i).
- Exportación de video asíncrona en hilo secundario con barra de progreso y cancelación cooperativa limpia.
"""

from __future__ import annotations

import atexit
import math
import queue
import threading
import time
from pathlib import Path
from typing import Any, Callable
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk
from PIL import Image, ImageTk

from . import analisis, bake, estilos, parametros, proyecto, reproductor
from .analisis import Analisis, ErrorDeAnalisis, analizar, hornear_audio, proyectar_analisis
from .bake import DatosBake, cargar_bake, obtener_ruta_bake, calcular_hash_audio
from .render import Render
from .reproductor import ReproductorAudio, crear_reproductor
from .salida import ErrorDeSalida, SIGUIENTE_PASO, exportar


def formatear_tiempo(segundos: float) -> str:
    """Convierte segundos a formato MM:SS.mmm."""
    if segundos < 0:
        segundos = 0.0
    minutos = int(segundos // 60)
    resto = segundos % 60
    return f"{minutos:02d}:{resto:06.3f}"


# Tiempos de debounce adaptativo y feedback visual (Bloques A y B / CA-POST-1 a CA-POST-5)
DEBOUNCE_COSMETICO_MS: int = 30
DEBOUNCE_DINAMICA_MS: int = 100
DEBOUNCE_ESTRUCTURAL_MS: int = 250
TIEMPO_GRACIA_BADGE_MS: int = 80

PARAMS_COSMETICOS: set[str] = {
    "color", "color_final", "color_fondo", "fondo", "grosor_linea",
    "resplandor", "resplandor_radio", "reflejo", "reflejo_opacidad",
    "reflejo_desenfoque", "tapas_pico", "espaciado", "compensar_fondo",
    "lienzo_ancho", "lienzo_alto", "x", "y", "ancho", "alto", "relleno",
    "tipo_linea", "redondeo", "degradado", "modo_fusion",
}
PARAMS_DINAMICA: set[str] = {
    "sensibilidad", "suavizado", "caida_picos",
}
PARAMS_ESTRUCTURALES: set[str] = {
    "n_barras", "frec_min", "frec_max", "curva_respuesta", "fps",
}


class _TareaRender:
    """Solicitud inmutable enviada al worker thread de render."""
    __slots__ = ("id_tarea", "ruta_audio", "estilo", "params", "cuadro", "ancho_vp", "alto_vp", "callback")

    def __init__(
        self,
        id_tarea: int,
        ruta_audio: Path,
        estilo: str,
        params: dict[str, Any],
        cuadro: int,
        ancho_vp: int = 0,
        alto_vp: int = 0,
        callback: Callable[[], None] | None = None,
    ) -> None:
        self.id_tarea = id_tarea
        self.ruta_audio = ruta_audio
        self.estilo = estilo
        self.params = params
        self.cuadro = cuadro
        self.ancho_vp = ancho_vp
        self.alto_vp = alto_vp
        self.callback = callback


class _ResultadoRender:
    """Resultado generado por el worker thread listo para despachar a la UI."""
    __slots__ = ("id_tarea", "analisis", "render", "params_analisis", "cuadro_rgba", "error", "callback")

    def __init__(
        self,
        id_tarea: int,
        analisis: Analisis | None,
        render: Render | None,
        params_analisis: dict[str, Any],
        cuadro_rgba: Image.Image | None,
        error: Exception | None = None,
        callback: Callable[[], None] | None = None,
    ) -> None:
        self.id_tarea = id_tarea
        self.analisis = analisis
        self.render = render
        self.params_analisis = params_analisis
        self.cuadro_rgba = cuadro_rgba
        self.error = error
        self.callback = callback


class VentanaVisualizador:
    """Ventana principal de la interfaz gráfica del visualizador."""

    def __init__(
        self,
        root: tk.Tk | None = None,
        audio: Path | str | None = None,
        estilo: str | None = None,
        proyecto_path: Path | str | None = None,
        preset: str | None = None,
        reproductor_audio: ReproductorAudio | None = None,
    ) -> None:
        self._es_root_propio = root is None
        self.root = root or tk.Tk()
        self.root.title("Visualizador de audio — Drift")
        self.root.geometry("1240x780")
        self.root.minsize(960, 600)

        # Estado del motor
        self._ruta_audio: Path | None = None
        self._datos_bake: DatosBake | None = None
        self._analisis: Analisis | None = None
        self._render: Render | None = None
        self._estilo: str = estilo or "barras"
        self._cuadro_actual: int = 0
        self._params_analisis_previo: dict[str, Any] = {}
        self._cuadro_raw_actual: Image.Image | None = None
        self._imagen_tk_referencia: ImageTk.PhotoImage | None = None
        self._ultimo_error: str | None = None

        # Motor de reproducción de audio y sincronización audiovisual
        self._reproductor: ReproductorAudio = reproductor_audio or crear_reproductor()
        self._t_inicio_reloj: float = 0.0
        self._offset_seg_reloj: float = 0.0
        self._scrubbing_activo: bool = False
        self._estaba_reproduciendo_antes_de_scrub: bool = False

        # Control reactivo y animación
        self._timer_debounce: str | None = None
        self._reproduciendo: bool = False
        self._timer_animacion: str | None = None
        self._cuadro_fin_animacion: int = 0

        # Worker thread secundario asíncrono y cola Last-Write-Wins (Bloque A / CA-POST-1 y CA-POST-3)
        self._secuencia_render: int = 0
        self._id_render_mostrado: int = 0
        self._contador_tareas_descartadas: int = 0
        self._contador_renders_procesados: int = 0
        self._cola_worker: queue.Queue[_TareaRender | None] = queue.Queue(maxsize=1)
        self._cola_resultados: queue.Queue[_ResultadoRender] = queue.Queue()
        self._evento_cerrar_worker = threading.Event()
        self._worker_ocupado: bool = False
        self._worker_thread = threading.Thread(
            target=self._bucle_worker_render,
            daemon=True,
            name="WorkerRenderAsync",
        )
        self._worker_thread.start()
 
        # Feedback visual de actualización y cursor inteligente (Bloque B / CA-POST-4)
        self._timer_badge_gracia: str | None = None
        self._timer_chequeo_resultados: str | None = None
        self._badge_visible: bool = False
        self._calculo_en_progreso: bool = False

        # Exportación en segundo plano
        self._hilo_export: threading.Thread | None = None
        self._evento_cancelar = threading.Event()
        self._dialogo_progreso: tk.Toplevel | None = None

        # Protocolos de ciclo de vida y prevención de procesos huérfanos (CA-5)
        self.root.protocol("WM_DELETE_WINDOW", self._al_cerrar_ventana)
        self.root.bind("<Destroy>", self._al_destruir_root, add="+")
        try:
            atexit.register(self._al_salir_proceso)
        except Exception:
            pass

        # Atajo global de teclado para Play / Pausa
        self.root.bind("<space>", self._al_presionar_espacio)

        # Estructuras de datos para variables y widgets de parámetros
        self._variables: dict[str, tk.Variable] = {}
        self._labels_display: dict[str, ttk.Label] = {}
        self._muestras_color: dict[str, tk.Label] = {}
        self._filas_parametro: dict[str, ttk.Frame] = {}
        self._widgets_por_parametro: dict[str, list[tk.Widget]] = {}

        self._inicializar_variables()
        self._construir_interfaz()

        # Cargas iniciales si se pasaron argumentos
        if proyecto_path:
            self.cargar_proyecto(proyecto_path)
        else:
            if preset:
                self.aplicar_preset(preset)
            if audio:
                self.cargar_audio(audio)

    # ----------------------------------------------------------------------- #
    # Construcción de la Interfaz
    # ----------------------------------------------------------------------- #

    def _inicializar_variables(self) -> None:
        """Inicializa una variable Tkinter por cada parámetro del ESQUEMA."""
        for nombre, def_val in parametros.ESQUEMA.items():
            if def_val.formato == "color":
                var = tk.StringVar(self.root, value=str(def_val.default))
            elif def_val.opciones:
                var = tk.StringVar(self.root, value=str(def_val.default))
            elif def_val.tipo is bool:
                var = tk.BooleanVar(self.root, value=bool(def_val.default))
            elif def_val.tipo is int:
                var = tk.IntVar(self.root, value=int(def_val.default))
            else:
                var = tk.DoubleVar(self.root, value=float(def_val.default))
            self._variables[nombre] = var

    def _construir_interfaz(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # PanedWindow divisor principal
        self._paned = ttk.PanedWindow(self.root, orient="horizontal")
        self._paned.grid(row=0, column=0, sticky="nsew")

        # --- Panel Izquierdo: Visualización y Transporte ---
        self._panel_izq = ttk.Frame(self._paned, padding=8)
        self._paned.add(self._panel_izq, weight=3)
        self._construir_panel_izquierdo()

        # --- Panel Derecho: Control y Parámetros ---
        self._panel_der = ttk.Frame(self._paned, padding=8)
        self._paned.add(self._panel_der, weight=2)
        self._construir_panel_derecho()

    def _construir_panel_izquierdo(self) -> None:
        self._panel_izq.columnconfigure(0, weight=1)
        self._panel_izq.rowconfigure(0, weight=1)
        self._panel_izq.rowconfigure(1, weight=0)

        # Área de visualización del lienzo
        frame_canvas = ttk.Frame(self._panel_izq)
        frame_canvas.grid(row=0, column=0, sticky="nsew")
        frame_canvas.columnconfigure(0, weight=1)
        frame_canvas.rowconfigure(0, weight=1)

        self.canvas_preview = tk.Canvas(frame_canvas, bg="#111114", highlightthickness=0)
        self.canvas_preview.grid(row=0, column=0, sticky="nsew")
        self.canvas_preview.bind("<Configure>", self._al_redimensionar_canvas)

        # Badge sutil de actualización ("⏳ Actualizando...") en canvas_preview (Bloque B / CA-POST-4)
        self._badge_actualizando = tk.Label(
            self.canvas_preview,
            text="⏳ Actualizando...",
            bg="#18181B",
            fg="#F4F4F5",
            font=("TkDefaultFont", 9, "bold"),
            highlightbackground="#3F3F46",
            highlightcolor="#3F3F46",
            highlightthickness=1,
            bd=0,
            padx=10,
            pady=4,
        )
        self._badge_visible = False

        # Texto inicial si no hay audio
        self._dibujar_mensaje_espera("Cargá un archivo de audio (.mp3, .wav, .flac) para previsualizar")

        # Barra de transporte
        frame_transporte = ttk.LabelFrame(self._panel_izq, text="Transporte", padding=6)
        frame_transporte.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        frame_transporte.columnconfigure(1, weight=1)

        # Deslizador de tiempo interactivo con scrubbing
        self._var_escala_tiempo = tk.DoubleVar(value=0.0)
        self.scale_tiempo = ttk.Scale(
            frame_transporte,
            orient="horizontal",
            from_=0,
            to=0,
            variable=self._var_escala_tiempo,
            command=self._al_mover_escala_tiempo,
        )
        self.scale_tiempo.grid(row=0, column=0, columnspan=4, sticky="ew", padx=4, pady=2)
        self.scale_tiempo.bind("<ButtonPress-1>", self._al_iniciar_scrubbing)
        self.scale_tiempo.bind("<B1-Motion>", self._al_arrastrar_scrubbing)
        self.scale_tiempo.bind("<ButtonRelease-1>", self._al_finalizar_scrubbing)

        # Botones y etiquetas de transporte
        self.btn_prev_frame = ttk.Button(frame_transporte, text="◀ Cuadro", width=9, command=self._retroceder_un_cuadro)
        self.btn_prev_frame.grid(row=1, column=0, sticky="w", padx=2, pady=4)

        self.btn_play_pausa = ttk.Button(frame_transporte, text="▶ Reproducir", command=self._alternar_reproduccion)
        self.btn_play_pausa.grid(row=1, column=1, sticky="w", padx=4, pady=4)
        self.btn_animar = self.btn_play_pausa  # Alias de compatibilidad hacia atrás

        self.btn_next_frame = ttk.Button(frame_transporte, text="Cuadro ▶", width=9, command=self._avanzar_un_cuadro)
        self.btn_next_frame.grid(row=1, column=2, sticky="w", padx=2, pady=4)

        self.lbl_tiempo = ttk.Label(frame_transporte, text="00:00.000 / 00:00.000 (0 / 0)", font=("TkDefaultFont", 9, "bold"))
        self.lbl_tiempo.grid(row=1, column=3, sticky="e", padx=4, pady=4)

    def _construir_panel_derecho(self) -> None:
        self._panel_der.columnconfigure(0, weight=1)
        self._panel_der.rowconfigure(3, weight=1)

        # 1. Barra de acciones principales (Archivos y Proyectos)
        frame_acciones = ttk.Frame(self._panel_der)
        frame_acciones.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        frame_acciones.columnconfigure(0, weight=1)
        frame_acciones.columnconfigure(1, weight=1)
        frame_acciones.columnconfigure(2, weight=1)

        btn_cargar_audio = ttk.Button(frame_acciones, text="Cargar Audio", command=self._dialogo_cargar_audio)
        btn_cargar_audio.grid(row=0, column=0, sticky="ew", padx=2, pady=2)

        btn_abrir_proy = ttk.Button(frame_acciones, text="Abrir Proyecto", command=self._dialogo_abrir_proyecto)
        btn_abrir_proy.grid(row=0, column=1, sticky="ew", padx=2, pady=2)

        btn_guardar_proy = ttk.Button(frame_acciones, text="Guardar Proyecto", command=self._dialogo_guardar_proyecto)
        btn_guardar_proy.grid(row=0, column=2, sticky="ew", padx=2, pady=2)

        # 2. Barra de Presets y Estilos
        frame_estilo_preset = ttk.LabelFrame(self._panel_der, text="Estilo y Preset", padding=6)
        frame_estilo_preset.grid(row=1, column=0, sticky="ew", pady=(0, 6))
        frame_estilo_preset.columnconfigure(1, weight=1)

        # Selector de Estilo
        ttk.Label(frame_estilo_preset, text="Estilo:").grid(row=0, column=0, sticky="w", padx=4, pady=2)
        nombres_estilos = [e.id for e in estilos.disponibles()]
        self._combo_estilos = ttk.Combobox(
            frame_estilo_preset,
            values=nombres_estilos,
            state="readonly",
        )
        self._combo_estilos.set(self._estilo)
        self._combo_estilos.grid(row=0, column=1, columnspan=2, sticky="ew", padx=4, pady=2)
        self._combo_estilos.bind("<<ComboboxSelected>>", self._al_cambiar_estilo)

        # Selector de Preset
        ttk.Label(frame_estilo_preset, text="Preset:").grid(row=1, column=0, sticky="w", padx=4, pady=2)
        presets_disp = proyecto.listar_presets()
        self._combo_presets = ttk.Combobox(
            frame_estilo_preset,
            values=presets_disp,
            state="readonly",
        )
        if presets_disp:
            self._combo_presets.set(presets_disp[0])
        self._combo_presets.grid(row=1, column=1, sticky="ew", padx=4, pady=2)

        btn_aplicar_pre = ttk.Button(frame_estilo_preset, text="Aplicar", width=8, command=self._al_pulsar_aplicar_preset)
        btn_aplicar_pre.grid(row=1, column=2, sticky="e", padx=2, pady=2)

        btn_guardar_pre = ttk.Button(frame_estilo_preset, text="Guardar Preset...", command=self._dialogo_guardar_preset)
        btn_guardar_pre.grid(row=2, column=1, columnspan=2, sticky="e", padx=2, pady=(2, 0))

        # 3. Contenedor scrollable vertical para el formulario dinámico
        frame_scroll = ttk.Frame(self._panel_der)
        frame_scroll.grid(row=3, column=0, sticky="nsew", pady=(0, 6))
        frame_scroll.columnconfigure(0, weight=1)
        frame_scroll.rowconfigure(0, weight=1)

        self._canvas_form = tk.Canvas(frame_scroll, borderwidth=0, highlightthickness=0)
        self._scrollbar_form = ttk.Scrollbar(frame_scroll, orient="vertical", command=self._canvas_form.yview)
        self._frame_form_interior = ttk.Frame(self._canvas_form)

        self._frame_form_interior.bind(
            "<Configure>",
            lambda e: self._canvas_form.configure(scrollregion=self._canvas_form.bbox("all")),
        )

        self._canvas_window = self._canvas_form.create_window((0, 0), window=self._frame_form_interior, anchor="nw")
        self._canvas_form.bind(
            "<Configure>",
            lambda e: self._canvas_form.itemconfig(self._canvas_window, width=e.width),
        )
        self._canvas_form.configure(yscrollcommand=self._scrollbar_form.set)

        self._canvas_form.grid(row=0, column=0, sticky="nsew")
        self._scrollbar_form.grid(row=0, column=1, sticky="ns")

        # Scroll con rueda del mouse
        def _scroll_mouse(event: tk.Event) -> None:
            if event.delta:
                self._canvas_form.yview_scroll(int(-1 * (event.delta / 120)), "units")

        self._canvas_form.bind_all("<MouseWheel>", _scroll_mouse)

        # Generar controles dinámicos según ESQUEMA
        self._generar_formulario_dinamico()

        # 4. Botón inferior destacado: Exportar Video
        btn_exportar = ttk.Button(
            self._panel_der,
            text="🎬  Exportar Video (WebM)",
            command=self._dialogo_exportar_video,
        )
        btn_exportar.grid(row=4, column=0, sticky="ew", ipady=6, pady=(4, 0))

    def _generar_formulario_dinamico(self) -> None:
        """Crea las secciones y controles del formulario leyendo parametros.ESQUEMA."""
        # Secciones por grupo
        for grupo_id, grupo_titulo in parametros.GRUPOS.items():
            labelframe = ttk.LabelFrame(self._frame_form_interior, text=grupo_titulo, padding=6)
            labelframe.pack(fill="x", expand=True, padx=4, pady=4)
            labelframe.columnconfigure(0, weight=1)

            # Buscar parámetros de este grupo
            for nombre, def_val in parametros.ESQUEMA.items():
                if def_val.grupo != grupo_id:
                    continue

                fila = ttk.Frame(labelframe)
                fila.pack(fill="x", expand=True, pady=2)
                fila.columnconfigure(1, weight=1)
                self._filas_parametro[nombre] = fila
                self._widgets_por_parametro[nombre] = []

                var = self._variables[nombre]

                # Generación polimórfica según tipo y formato
                if def_val.formato == "color":
                    lbl = ttk.Label(fila, text=def_val.etiqueta, width=16, anchor="w")
                    lbl.grid(row=0, column=0, sticky="w", padx=(0, 4))
                    self._widgets_por_parametro[nombre].append(lbl)

                    c_frame = ttk.Frame(fila)
                    c_frame.grid(row=0, column=1, sticky="ew")
                    c_frame.columnconfigure(0, weight=1)

                    muestra = tk.Label(
                        c_frame,
                        text=str(var.get()),
                        bg=str(var.get()),
                        fg="#FFFFFF" if self._es_color_oscuro(str(var.get())) else "#000000",
                        width=10,
                        relief="solid",
                        borderwidth=1,
                        cursor="hand2",
                    )
                    muestra.grid(row=0, column=0, sticky="ew", padx=(0, 4))
                    self._muestras_color[nombre] = muestra
                    self._widgets_por_parametro[nombre].append(muestra)

                    btn_color = ttk.Button(
                        c_frame,
                        text="Elegir...",
                        width=8,
                        command=lambda n=nombre: self._elegir_color(n),
                    )
                    btn_color.grid(row=0, column=1, sticky="e")
                    self._widgets_por_parametro[nombre].append(btn_color)

                    # Click en la muestra también dispara selector de color
                    muestra.bind("<Button-1>", lambda e, n=nombre: self._elegir_color(n))

                elif def_val.opciones:
                    lbl = ttk.Label(fila, text=def_val.etiqueta, width=16, anchor="w")
                    lbl.grid(row=0, column=0, sticky="w", padx=(0, 4))
                    self._widgets_por_parametro[nombre].append(lbl)

                    combo = ttk.Combobox(
                        fila,
                        textvariable=var,
                        values=list(def_val.opciones),
                        state="readonly",
                    )
                    combo.grid(row=0, column=1, sticky="ew")
                    combo.bind("<<ComboboxSelected>>", lambda e, n=nombre: self._al_cambiar_parametro(n))
                    self._widgets_por_parametro[nombre].append(combo)

                elif def_val.tipo is bool:
                    chk = ttk.Checkbutton(
                        fila,
                        text=def_val.etiqueta,
                        variable=var,
                        command=lambda n=nombre: self._al_cambiar_parametro(n),
                    )
                    chk.grid(row=0, column=0, columnspan=2, sticky="w")
                    self._widgets_por_parametro[nombre].append(chk)

                else:  # float o int con mínimo y máximo
                    lbl = ttk.Label(fila, text=def_val.etiqueta, width=16, anchor="w")
                    lbl.grid(row=0, column=0, sticky="w", padx=(0, 4))
                    self._widgets_por_parametro[nombre].append(lbl)

                    val_ini = var.get()
                    formato_txt = f"{int(round(val_ini))} {def_val.unidad}" if def_val.tipo is int else f"{float(val_ini):.2f} {def_val.unidad}"
                    lbl_val = ttk.Label(fila, text=formato_txt.strip(), width=9, anchor="e")
                    lbl_val.grid(row=0, column=2, sticky="e", padx=(4, 0))
                    self._labels_display[nombre] = lbl_val
                    self._widgets_por_parametro[nombre].append(lbl_val)

                    scale = ttk.Scale(
                        fila,
                        from_=def_val.minimo if def_val.minimo is not None else 0.0,
                        to=def_val.maximo if def_val.maximo is not None else 1.0,
                        variable=var,
                        orient="horizontal",
                        command=lambda v, n=nombre: self._al_mover_slider(n, v),
                    )
                    scale.grid(row=0, column=1, sticky="ew")
                    self._widgets_por_parametro[nombre].append(scale)

        self._actualizar_visibilidad_por_estilo()
        self._actualizar_habilitacion_dependencias()

    # ----------------------------------------------------------------------- #
    # Reactividad y Gestión de Parámetros
    # ----------------------------------------------------------------------- #

    @staticmethod
    def _es_color_oscuro(hex_str: str) -> bool:
        """Determina si un color hexadecimal es oscuro para elegir contraste de texto."""
        try:
            r, g, b = parametros.a_rgb(hex_str)
            lum = 0.299 * r + 0.587 * g + 0.114 * b
            return lum < 128
        except Exception:
            return True

    def _elegir_color(self, nombre: str) -> None:
        actual = str(self._variables[nombre].get())
        nuevo, _ = colorchooser.askcolor(color=actual, title=f"Elegir {nombre}")
        if nuevo:
            hex_mayus = nuevo.upper()
            self._variables[nombre].set(hex_mayus)
            self._actualizar_muestra_color(nombre, hex_mayus)
            self._al_cambiar_parametro(nombre)

    def _actualizar_muestra_color(self, nombre: str, hex_val: str) -> None:
        if nombre in self._muestras_color:
            lbl = self._muestras_color[nombre]
            lbl.config(
                text=hex_val,
                bg=hex_val,
                fg="#FFFFFF" if self._es_color_oscuro(hex_val) else "#000000",
            )

    def _al_mover_slider(self, nombre: str, valor_str: str) -> None:
        def_val = parametros.ESQUEMA[nombre]
        try:
            val_f = float(valor_str)
        except ValueError:
            return

        if def_val.tipo is int:
            val_int = int(round(val_f))
            self._variables[nombre].set(val_int)
            txt = f"{val_int} {def_val.unidad}".strip()
        else:
            txt = f"{val_f:.2f} {def_val.unidad}".strip()

        if nombre in self._labels_display:
            self._labels_display[nombre].config(text=txt)

        self._al_cambiar_parametro(nombre)

    def _al_cambiar_parametro(self, nombre: str | None = None) -> None:
        self._actualizar_habilitacion_dependencias()
        self._programar_debounce_render(nombre)

    def _actualizar_habilitacion_dependencias(self) -> None:
        """Habilita o deshabilita controles según parametros.tiene_efecto()."""
        params_actuales = self.obtener_parametros()
        for nombre, widgets in self._widgets_por_parametro.items():
            activo = parametros.tiene_efecto(params_actuales, nombre)
            nuevo_estado = "normal" if activo else "disabled"
            for w in widgets:
                if isinstance(w, ttk.Combobox):
                    w.config(state="readonly" if activo else "disabled")
                elif isinstance(w, (ttk.Button, ttk.Scale, ttk.Checkbutton, tk.Label)):
                    try:
                        w.config(state=nuevo_estado)
                    except tk.TclError:
                        pass

    def _actualizar_visibilidad_por_estilo(self) -> None:
        """Muestra u oculta controles según apliquen al estilo activo."""
        for nombre, fila in self._filas_parametro.items():
            def_val = parametros.ESQUEMA[nombre]
            if def_val.aplica_a(self._estilo):
                fila.pack(fill="x", expand=True, pady=2)
            else:
                fila.pack_forget()

    def obtener_parametros(self, solo_estilo_activo: bool = False) -> dict[str, Any]:
        """Obtiene un diccionario con los valores tipados de los parámetros."""
        resultado: dict[str, Any] = {}
        for nombre, var in self._variables.items():
            def_val = parametros.ESQUEMA[nombre]
            if solo_estilo_activo and not def_val.aplica_a(self._estilo):
                continue
            val_raw = var.get()
            if def_val.tipo is int:
                resultado[nombre] = int(round(float(val_raw)))
            elif def_val.tipo is float:
                resultado[nombre] = float(val_raw)
            elif def_val.tipo is bool:
                resultado[nombre] = bool(val_raw)
            else:
                resultado[nombre] = str(val_raw)
        return resultado

    def establecer_parametros(self, params: dict[str, Any]) -> None:
        """Asigna parámetros a la interfaz y actualiza widgets."""
        for nombre, valor in params.items():
            if nombre in self._variables:
                def_val = parametros.ESQUEMA[nombre]
                self._variables[nombre].set(valor)
                if def_val.formato == "color":
                    self._actualizar_muestra_color(nombre, str(valor))
                elif def_val.tipo in (int, float) and nombre in self._labels_display:
                    txt = f"{int(round(float(valor)))} {def_val.unidad}" if def_val.tipo is int else f"{float(valor):.2f} {def_val.unidad}"
                    self._labels_display[nombre].config(text=txt.strip())

        self._actualizar_visibilidad_por_estilo()
        self._actualizar_habilitacion_dependencias()
        self._programar_debounce_render()

    def obtener_variable(self, nombre: str) -> tk.Variable:
        """Acceso a la variable Tkinter asociada a un parámetro."""
        return self._variables[nombre]

    def obtener_widget(self, nombre: str) -> list[tk.Widget]:
        """Acceso a la lista de widgets asociados a un parámetro."""
        return self._widgets_por_parametro.get(nombre, [])

    def cambiar_estilo(self, nuevo_estilo: str) -> None:
        """Cambia el estilo de renderizado y refresca controles."""
        self.detener_reproduccion()
        estilos.obtener(nuevo_estilo)  # valida existencia
        self._estilo = nuevo_estilo
        self._combo_estilos.set(nuevo_estilo)
        self._actualizar_visibilidad_por_estilo()
        self._actualizar_habilitacion_dependencias()
        self._render = None
        self._actualizar_vista_previa()

    def _al_cambiar_estilo(self, event: Any = None) -> None:
        nuevo = self._combo_estilos.get()
        if nuevo != self._estilo:
            self.cambiar_estilo(nuevo)

    # ----------------------------------------------------------------------- #
    # Carga de Audio, Proyectos y Presets
    # ----------------------------------------------------------------------- #

    def _dialogo_cargar_audio(self) -> None:
        archivo = filedialog.askopenfilename(
            title="Seleccionar archivo de audio",
            filetypes=[
                ("Archivos de audio", "*.mp3 *.wav *.flac *.m4a *.ogg"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if archivo:
            self.cargar_audio(archivo)

    def cargar_audio(self, ruta: Path | str) -> bool:
        """Carga y analiza una pista de audio mediante Pre-Bake persistente (.driftbake.npz).

        Si el archivo .driftbake.npz existe y es válido, realiza carga instantánea (< 100 ms, 0 FFmpeg).
        Si no existe, hornea asíncronamente en worker thread con feedback claro en la interfaz
        ('Horneando análisis de audio...') sin bloquear el hilo principal de eventos de Tkinter.
        """
        ruta_p = Path(ruta).resolve()
        self.detener_reproduccion()

        if not ruta_p.is_file():
            err_msg = f"el archivo de audio no existe: {ruta_p}"
            self._ultimo_error = err_msg
            messagebox.showerror("Error al cargar audio", f"No se pudo cargar '{ruta_p.name}':\n\n{err_msg}")
            return False

        try:
            params = self.obtener_parametros()
            fps = int(params.get("fps", 60))
            hash_audio = bake.calcular_hash_audio(ruta_p)
            ruta_bake = bake.obtener_ruta_bake(ruta_p, fps=fps)
            datos_bake = bake.cargar_bake(ruta_bake, hash_esperado=hash_audio, fps_esperado=fps, ruta_audio=ruta_p)
        except Exception as e:
            self._ultimo_error = str(e)
            messagebox.showerror("Error al cargar audio", f"No se pudo cargar '{ruta_p.name}':\n\n{e}")
            return False

        # Si no existe bake válido en disco, hornear asíncronamente en worker thread con feedback
        if datos_bake is None:
            self._dibujar_mensaje_espera("Horneando análisis de audio...")
            try:
                self.canvas_preview.config(cursor="watch")
            except Exception:
                pass
            self.root.update_idletasks()

            resultado: list[Any] = [None, None]
            evento = threading.Event()

            def _hilo_hornear() -> None:
                try:
                    resultado[0] = analisis.hornear_audio(ruta_p, fps=fps)
                except Exception as ex:
                    resultado[1] = ex
                finally:
                    evento.set()

            t = threading.Thread(target=_hilo_hornear, daemon=True, name="WorkerHornearAudio")
            t.start()

            while not evento.is_set():
                try:
                    self.root.update()
                except Exception:
                    break
                time.sleep(0.01)

            try:
                self.canvas_preview.config(cursor="")
            except Exception:
                pass

            if resultado[1] is not None:
                err = resultado[1]
                self._ultimo_error = str(err)
                self._dibujar_mensaje_espera("Error al analizar audio")
                messagebox.showerror("Error al cargar audio", f"No se pudo cargar '{ruta_p.name}':\n\n{err}")
                return False

            datos_bake = resultado[0]

        if datos_bake is None:
            self._ultimo_error = f"No se obtuvieron datos de análisis para '{ruta_p.name}'"
            return False

        try:
            self._datos_bake = datos_bake
            self._analisis = proyectar_analisis(datos_bake, params, self._estilo)
            self._params_analisis_previo = self._extraer_params_analisis(params)
            self._ruta_audio = ruta_p
            self._render = Render(self._analisis, self._estilo, params)
            self._ultimo_error = None
        except Exception as e:
            self._ultimo_error = str(e)
            messagebox.showerror("Error al cargar audio", f"No se pudo cargar '{ruta_p.name}':\n\n{e}")
            return False

        # Cargar pista en el reproductor de audio desacoplado
        self._reproductor.cargar(ruta_p)
        self._offset_seg_reloj = 0.0

        # Actualizar transporte
        total_cuadros = self._analisis.n_cuadros
        self.scale_tiempo.config(to=max(0, total_cuadros - 1))
        self._cuadro_actual = 0
        self._var_escala_tiempo.set(0)
        self.root.title(f"Visualizador de audio — {ruta_p.name}")

        # Renderizar fotograma inicial por defecto de inmediato
        self._actualizar_vista_previa_inmediata()
        return True

    def _extraer_params_analisis(self, params: dict[str, Any]) -> dict[str, Any]:
        """Filtra los parámetros que alteran el resultado de Analisis."""
        claves_analisis = {"fps", "n_barras", "frec_min", "frec_max", "curva_respuesta", "suavizado", "caida_picos", "sensibilidad"}
        return {k: params[k] for k in claves_analisis if k in params}

    def _dialogo_abrir_proyecto(self) -> None:
        archivo = filedialog.askopenfilename(
            title="Abrir Proyecto",
            filetypes=[("Proyectos Visualizador", "*.json"), ("Archivos JSON", "*.json")],
        )
        if archivo:
            self.cargar_proyecto(archivo)

    def cargar_proyecto(self, ruta: Path | str) -> bool:
        """Carga un archivo de proyecto JSON y actualiza el estado completo."""
        self.detener_reproduccion()
        try:
            audio_path, estilo_id, params = proyecto.abrir(ruta)
            self._estilo = estilo_id
            self._combo_estilos.set(estilo_id)
            self.establecer_parametros(params)
            ok = self.cargar_audio(audio_path)
            self._ultimo_error = None
            return ok
        except (proyecto.ErrorDeProyecto, parametros.ErrorDeParametro, Exception) as e:
            self._ultimo_error = str(e)
            messagebox.showerror("Error al abrir proyecto", f"No se pudo abrir el proyecto:\n\n{e}")
            return False

    def _dialogo_guardar_proyecto(self) -> None:
        if not self._ruta_audio:
            messagebox.showwarning("Atención", "Debés cargar un audio antes de guardar el proyecto.")
            return

        sugerido = f"{self._ruta_audio.stem}_proyecto.json"
        archivo = filedialog.asksaveasfilename(
            title="Guardar Proyecto",
            initialfile=sugerido,
            defaultextension=".json",
            filetypes=[("Proyectos Visualizador", "*.json")],
        )
        if archivo:
            self.guardar_proyecto(archivo)

    def guardar_proyecto(self, ruta: Path | str) -> bool:
        """Persiste la configuración y la pista activa en disco."""
        if not self._ruta_audio:
            return False
        try:
            params = self.obtener_parametros(solo_estilo_activo=True)
            proyecto.guardar(ruta, self._ruta_audio, self._estilo, params)
            messagebox.showinfo("Proyecto guardado", f"Proyecto guardado con éxito en:\n{ruta}")
            return True
        except (proyecto.ErrorDeProyecto, Exception) as e:
            self._ultimo_error = str(e)
            messagebox.showerror("Error al guardar", f"No se pudo guardar el proyecto:\n\n{e}")
            return False

    def _al_pulsar_aplicar_preset(self) -> None:
        nombre = self._combo_presets.get()
        if nombre:
            self.aplicar_preset(nombre)

    def aplicar_preset(self, nombre_o_ruta: str) -> bool:
        """Aplica un preset de fábrica o archivo personalizado."""
        self.detener_reproduccion()
        try:
            estilo_id, params = proyecto.abrir_preset(nombre_o_ruta)
            self._estilo = estilo_id
            self._combo_estilos.set(estilo_id)
            self.establecer_parametros(params)
            self._actualizar_vista_previa()
            return True
        except (proyecto.ErrorDeProyecto, Exception) as e:
            messagebox.showerror("Error al aplicar preset", f"No se pudo aplicar el preset '{nombre_o_ruta}':\n\n{e}")
            return False

    def _dialogo_guardar_preset(self) -> None:
        archivo = filedialog.asksaveasfilename(
            title="Guardar Preset",
            initialdir=str(proyecto.DIRECTORIO_PRESETS),
            defaultextension=".json",
            filetypes=[("Presets Visualizador", "*.json")],
        )
        if archivo:
            self.guardar_preset(archivo)

    def guardar_preset(self, ruta: Path | str) -> bool:
        """Guarda los parámetros activos como un preset reutilizable."""
        try:
            params = self.obtener_parametros(solo_estilo_activo=True)
            proyecto.guardar_preset(ruta, self._estilo, params)
            self._combo_presets.config(values=proyecto.listar_presets())
            messagebox.showinfo("Preset guardado", f"Preset guardado con éxito en:\n{ruta}")
            return True
        except (proyecto.ErrorDeProyecto, Exception) as e:
            self._ultimo_error = str(e)
            messagebox.showerror("Error al guardar preset", f"No se pudo guardar el preset:\n\n{e}")
            return False

    # ----------------------------------------------------------------------- #
    # Área de Vista Previa, Scrubbing y Transporte
    # ----------------------------------------------------------------------- #

    def _tiempo_debounce_para(self, nombre: str | None) -> int:
        """Determina la latencia de debounce adaptativo según el tipo de parámetro."""
        if not nombre:
            return 50
        if nombre in PARAMS_COSMETICOS:
            return DEBOUNCE_COSMETICO_MS
        if nombre in PARAMS_DINAMICA:
            return DEBOUNCE_DINAMICA_MS
        if nombre in PARAMS_ESTRUCTURALES:
            return DEBOUNCE_ESTRUCTURAL_MS
        return 50

    def _programar_debounce_render(self, nombre: str | None = None) -> None:
        """Programa la actualización de vista previa con debounce adaptativo por parámetro."""
        if self._timer_debounce is not None:
            try:
                self.root.after_cancel(self._timer_debounce)
            except Exception:
                pass
            self._timer_debounce = None
        ms = self._tiempo_debounce_para(nombre)
        self._timer_debounce = self.root.after(ms, self._al_vencer_debounce)

    def _al_vencer_debounce(self) -> None:
        self._timer_debounce = None
        self._solicitar_render_async()

    def _encolar_tarea_worker(self, tarea: _TareaRender) -> None:
        """Encola una tarea en el worker descartando la tarea previa si aún no se procesó (LWW)."""
        while True:
            try:
                self._cola_worker.put_nowait(tarea)
                break
            except queue.Full:
                try:
                    descartada = self._cola_worker.get_nowait()
                    if descartada is not None:
                        self._contador_tareas_descartadas += 1
                except queue.Empty:
                    pass

    def esta_actualizando(self) -> bool:
        """Indica si hay un cálculo asíncrono en curso o el badge visual está activo."""
        return self._worker_ocupado or self._calculo_en_progreso or self._badge_visible

    def _mostrar_badge_actualizando(self) -> None:
        """Muestra el badge visual sutil en el visor y conmuta cursor a espera ('watch')."""
        if not hasattr(self, "canvas_preview") or not self.canvas_preview.winfo_exists():
            return
        self._badge_visible = True
        if hasattr(self, "_badge_actualizando") and self._badge_actualizando.winfo_exists():
            self._badge_actualizando.place(relx=1.0, rely=0.0, anchor="ne", x=-14, y=14)
            self._badge_actualizando.lift()
        try:
            self.canvas_preview.config(cursor="watch")
        except Exception:
            pass

    def _ocultar_badge_actualizando(self) -> None:
        """Oculta el badge visual y restaura el cursor normal ('')."""
        self._badge_visible = False
        if hasattr(self, "_badge_actualizando") and self._badge_actualizando.winfo_exists():
            try:
                self._badge_actualizando.place_forget()
            except Exception:
                pass
        if hasattr(self, "canvas_preview") and self.canvas_preview.winfo_exists():
            try:
                self.canvas_preview.config(cursor="")
            except Exception:
                pass

    def _al_vencer_gracia_badge(self) -> None:
        """Disparado por el timer de gracia tras 80 ms si el cálculo continúa activo."""
        self._timer_badge_gracia = None
        # Solo activar si el cálculo realmente sigue pendiente y no se ha entregado el cuadro
        if self._calculo_en_progreso and self._id_render_mostrado < self._secuencia_render:
            self._mostrar_badge_actualizando()
        else:
            self._calculo_en_progreso = False

    def _desactivar_estado_computo(self) -> None:
        """Cancela timer de gracia pendiente, oculta el badge y restaura cursor normal."""
        self._calculo_en_progreso = False
        if self._timer_badge_gracia is not None:
            try:
                self.root.after_cancel(self._timer_badge_gracia)
            except Exception:
                pass
            self._timer_badge_gracia = None
        if hasattr(self, "_timer_chequeo_resultados") and self._timer_chequeo_resultados is not None:
            try:
                self.root.after_cancel(self._timer_chequeo_resultados)
            except Exception:
                pass
            self._timer_chequeo_resultados = None
        self._ocultar_badge_actualizando()

    def _programar_chequeo_resultados(self) -> None:
        """Programa sondeo proactivo periódico en el hilo principal para despachar resultados del worker."""
        if getattr(self, "_timer_chequeo_resultados", None) is None and self._calculo_en_progreso:
            self._timer_chequeo_resultados = self.root.after(20, self._al_timer_chequeo_resultados)

    def _al_timer_chequeo_resultados(self) -> None:
        self._timer_chequeo_resultados = None
        self._procesar_resultados_worker()
        if self._calculo_en_progreso or not self._cola_resultados.empty():
            self._programar_chequeo_resultados()

    def _solicitar_render_async(self, callback: Callable[[], None] | None = None) -> int:
        """Encola una solicitud de render asíncrono en el worker thread."""
        if self._ruta_audio is None:
            return 0
        self._secuencia_render += 1
        id_tarea = self._secuencia_render
        params = self.obtener_parametros()
        cw = max(10, self.canvas_preview.winfo_width()) if hasattr(self, "canvas_preview") else 0
        ch = max(10, self.canvas_preview.winfo_height()) if hasattr(self, "canvas_preview") else 0
        tarea = _TareaRender(
            id_tarea=id_tarea,
            ruta_audio=self._ruta_audio,
            estilo=self._estilo,
            params=params,
            cuadro=self._cuadro_actual,
            ancho_vp=cw,
            alto_vp=ch,
            callback=callback,
        )

        # Activar estado de cómputo en progreso y programar temporizador de gracia (80 ms)
        self._calculo_en_progreso = True
        if self._timer_badge_gracia is None and not self._badge_visible:
            self._timer_badge_gracia = self.root.after(
                TIEMPO_GRACIA_BADGE_MS,
                self._al_vencer_gracia_badge,
            )
        self._programar_chequeo_resultados()

        self._encolar_tarea_worker(tarea)
        return id_tarea

    def _bucle_worker_render(self) -> None:
        """Bucle continuo del worker thread secundario asíncrono."""
        worker_datos_bake: DatosBake | None = None
        worker_analisis: Analisis | None = None
        worker_params_analisis: dict[str, Any] = {}
        worker_ruta_audio: Path | None = None
        worker_fps: int = 60

        while not self._evento_cerrar_worker.is_set():
            try:
                tarea = self._cola_worker.get(timeout=0.1)
            except queue.Empty:
                continue

            if tarea is None or self._evento_cerrar_worker.is_set():
                break

            self._worker_ocupado = True
            try:
                # Si llegaron solicitudes más recientes mientras se despertaba, absorber la última directamente
                while not self._cola_worker.empty():
                    try:
                        mas_nueva = self._cola_worker.get_nowait()
                        if mas_nueva is not None:
                            self._contador_tareas_descartadas += 1
                            tarea = mas_nueva
                    except queue.Empty:
                        break

                self._contador_renders_procesados += 1
                id_tarea = tarea.id_tarea
                params = tarea.params
                estilo = tarea.estilo
                ruta = tarea.ruta_audio
                cuadro = tarea.cuadro

                try:
                    params_analisis = self._extraer_params_analisis(params)
                    fps_param = int(params.get("fps", 60))

                    if worker_datos_bake is None or worker_ruta_audio != ruta or worker_fps != fps_param:
                        worker_datos_bake = hornear_audio(ruta, fps=fps_param)
                        worker_ruta_audio = ruta
                        worker_fps = fps_param
                        worker_analisis = None

                    necesita_analisis = (
                        worker_analisis is None
                        or params_analisis != worker_params_analisis
                    )
                    if necesita_analisis:
                        worker_analisis = proyectar_analisis(worker_datos_bake, params, estilo)
                        worker_params_analisis = params_analisis

                    render = Render(worker_analisis, estilo, params)
                    c_idx = max(0, min(cuadro, worker_analisis.n_cuadros - 1))

                    cw = getattr(tarea, "ancho_vp", 0)
                    ch = getattr(tarea, "alto_vp", 0)
                    if cw > 0 and ch > 0:
                        cuadro_rgba = render.cuadro_viewport(c_idx, cw, ch)
                    else:
                        cuadro_rgba = render.cuadro(c_idx)

                    res = _ResultadoRender(
                        id_tarea=id_tarea,
                        analisis=worker_analisis,
                        render=render,
                        params_analisis=worker_params_analisis,
                        cuadro_rgba=cuadro_rgba,
                        error=None,
                        callback=tarea.callback,
                    )
                except Exception as e:
                    res = _ResultadoRender(
                        id_tarea=id_tarea,
                        analisis=worker_analisis,
                        render=None,
                        params_analisis=worker_params_analisis,
                        cuadro_rgba=None,
                        error=e,
                        callback=tarea.callback,
                    )

                self._cola_resultados.put(res)
                try:
                    self.root.after_idle(self._procesar_resultados_worker)
                except Exception:
                    pass
            finally:
                self._worker_ocupado = False

    def _procesar_resultados_worker(self) -> None:
        """Procesa en el hilo principal de Tkinter los resultados despachados por el worker."""
        try:
            if not self.root.winfo_exists():
                return
        except Exception:
            return

        ultimo_res: _ResultadoRender | None = None
        while True:
            try:
                res = self._cola_resultados.get_nowait()
                if res.id_tarea >= self._id_render_mostrado:
                    if ultimo_res is None or res.id_tarea > ultimo_res.id_tarea:
                        ultimo_res = res
            except queue.Empty:
                break

        if ultimo_res is None:
            if not self._worker_ocupado and self._cola_worker.empty() and self._cola_resultados.empty():
                self._desactivar_estado_computo()
            return

        if ultimo_res.error is not None:
            self._ultimo_error = str(ultimo_res.error)
            if not self._worker_ocupado and self._cola_worker.empty() and self._cola_resultados.empty():
                self._desactivar_estado_computo()
            if ultimo_res.callback:
                ultimo_res.callback()
            return

        if ultimo_res.id_tarea >= self._id_render_mostrado:
            self._id_render_mostrado = ultimo_res.id_tarea
            if self._id_render_mostrado >= self._secuencia_render:
                if self._timer_badge_gracia is not None:
                    try:
                        self.root.after_cancel(self._timer_badge_gracia)
                    except Exception:
                        pass
                    self._timer_badge_gracia = None
                self._calculo_en_progreso = False

            if ultimo_res.analisis is not None:
                self._analisis = ultimo_res.analisis
                self._params_analisis_previo = ultimo_res.params_analisis
                try:
                    if self.scale_tiempo.winfo_exists():
                        self.scale_tiempo.config(to=max(0, self._analisis.n_cuadros - 1))
                except Exception:
                    pass
            if ultimo_res.render is not None:
                self._render = ultimo_res.render

            if ultimo_res.cuadro_rgba is not None:
                self._cuadro_raw_actual = ultimo_res.cuadro_rgba
                self._proyectar_en_canvas(ultimo_res.cuadro_rgba)
                self._actualizar_indicador_tiempo()

        # Si el worker no tiene más tareas pendientes en cola o la última tarea ya fue entregada,
        # desactivar estado de cómputo y ocultar feedback visual de inmediato
        if (self._id_render_mostrado >= self._secuencia_render) or (
            not self._worker_ocupado and self._cola_worker.empty() and self._cola_resultados.empty()
        ):
            self._desactivar_estado_computo()

        if ultimo_res.callback:
            ultimo_res.callback()

    def esperar_render_async(self, timeout: float = 2.0) -> bool:
        """Espera a que el worker complete tareas pendientes. Útil para tests y sincronización."""
        t_limite = time.perf_counter() + timeout
        while time.perf_counter() < t_limite:
            try:
                self._procesar_resultados_worker()
                self.root.update_idletasks()
            except Exception:
                break
            if not self._worker_ocupado and self._cola_worker.empty() and self._cola_resultados.empty():
                time.sleep(0.01)
                try:
                    self._procesar_resultados_worker()
                    self.root.update_idletasks()
                except Exception:
                    break
                if not self._worker_ocupado and self._cola_worker.empty() and self._cola_resultados.empty():
                    self._desactivar_estado_computo()
                    return True
            time.sleep(0.005)
        return False

    def _actualizar_vista_previa(self) -> None:
        """Actualiza la vista previa solicitando render asíncrono al worker."""
        if self._timer_debounce is not None:
            try:
                self.root.after_cancel(self._timer_debounce)
            except Exception:
                pass
            self._timer_debounce = None
        self._solicitar_render_async()

    def _actualizar_vista_previa_inmediata(self) -> None:
        """Genera el cuadro actual mediante Viewport LOD o Render.cuadro(i) y lo proyecta."""
        if self._analisis is None or self._ruta_audio is None:
            return

        # Invalidar renders asíncronos previos en vuelo y desactivar feedback
        self._secuencia_render += 1
        self._id_render_mostrado = self._secuencia_render
        self._desactivar_estado_computo()

        params = self.obtener_parametros()
        params_analisis = self._extraer_params_analisis(params)

        # Si cambiaron parámetros que afectan al análisis, re-proyectar en memoria O(1)
        if params_analisis != self._params_analisis_previo:
            try:
                if self._datos_bake is not None:
                    self._analisis = proyectar_analisis(self._datos_bake, params, self._estilo)
                else:
                    self._analisis = analizar(self._ruta_audio, params, self._estilo)
                self._params_analisis_previo = params_analisis
                self.scale_tiempo.config(to=max(0, self._analisis.n_cuadros - 1))
            except Exception as e:
                self._ultimo_error = str(e)
                return

        # Actualizar Render si no existe o cambiaron parámetros
        if (
            self._render is None
            or self._render.analisis is not self._analisis
            or getattr(self, "_params_render_previo", None) != params
        ):
            self._render = Render(self._analisis, self._estilo, params)
            self._params_render_previo = params

        if not 0 <= self._cuadro_actual < self._analisis.n_cuadros:
            self._cuadro_actual = max(0, min(self._cuadro_actual, self._analisis.n_cuadros - 1))

        # Viewport LOD nativo (CA-REARQ-4): renderizado directo a resolución física del Canvas (< 8 ms)
        cw = max(10, self.canvas_preview.winfo_width())
        ch = max(10, self.canvas_preview.winfo_height())
        cuadro_vp = self._render.cuadro_viewport(self._cuadro_actual, cw, ch)
        self._cuadro_raw_actual = None  # Se computa bajo demanda en obtener_cuadro_actual_raw()
        self._proyectar_en_canvas(cuadro_vp)
        self._actualizar_indicador_tiempo()

    def _proyectar_en_canvas(self, img_rgba: Image.Image) -> None:
        cw = max(10, self.canvas_preview.winfo_width())
        ch = max(10, self.canvas_preview.winfo_height())
        lw, lh = img_rgba.size

        factor = min(cw / lw, ch / lh)
        nw = max(1, int(lw * factor))
        nh = max(1, int(lh * factor))

        # Determinar composición de fondo según parámetro activo
        modo_fondo = str(self._variables.get("fondo", tk.StringVar(value="negro")).get())
        if modo_fondo == "negro":
            base = Image.new("RGBA", (nw, nh), (0, 0, 0, 255))
        elif modo_fondo == "color":
            color_fondo_hex = self._variables.get("color_fondo", tk.StringVar(value="#FF00FF")).get()
            try:
                rgb = parametros.a_rgb(color_fondo_hex)
            except Exception:
                rgb = (255, 0, 255)
            base = Image.new("RGBA", (nw, nh), (*rgb, 255))
        else:  # transparente
            base = Image.new("RGBA", (nw, nh), (18, 18, 20, 255))

        # Viewport LOD: Si la imagen ya tiene la resolución destino, omitir resize bilineal en CPU
        if (lw, lh) == (nw, nh):
            img_final = img_rgba
        else:
            img_final = img_rgba.resize((nw, nh), Image.Resampling.BILINEAR)

        base.paste(img_final, (0, 0), img_final)

        img_tk = ImageTk.PhotoImage(base)
        self._imagen_tk_referencia = img_tk

        x = cw // 2
        y = ch // 2

        # Preservación de fotograma previo (Ghost frame / Never blank):
        # Dibujamos el nuevo cuadro y luego removemos el anterior para evitar
        # cualquier cuadro negro o parpadeo intermedio en el canvas.
        item_nuevo = self.canvas_preview.create_image(x, y, image=img_tk, anchor="center", tags="canvas_imagen")
        for item_id in self.canvas_preview.find_withtag("canvas_imagen"):
            if item_id != item_nuevo:
                self.canvas_preview.delete(item_id)
        self.canvas_preview.delete("mensaje_espera")

        if hasattr(self, "_badge_actualizando") and self._badge_visible:
            self._badge_actualizando.lift()

    def _al_redimensionar_canvas(self, event: Any = None) -> None:
        if self._render is not None and self._analisis is not None:
            self._actualizar_vista_previa_inmediata()
        elif self._analisis is None:
            self._dibujar_mensaje_espera("Cargá un archivo de audio (.mp3, .wav, .flac) para previsualizar")

    def _dibujar_mensaje_espera(self, mensaje: str) -> None:
        self.canvas_preview.delete("all")
        cw = max(10, self.canvas_preview.winfo_width())
        ch = max(10, self.canvas_preview.winfo_height())
        self.canvas_preview.create_text(
            cw // 2, ch // 2,
            text=mensaje,
            fill="#A1A1AA",
            font=("TkDefaultFont", 11),
            justify="center",
            tags="mensaje_espera",
        )

    def _al_mover_escala_tiempo(self, valor_str: str) -> None:
        if self._analisis is None:
            return
        try:
            nuevo_cuadro = int(round(float(valor_str)))
        except ValueError:
            return
        if nuevo_cuadro != self._cuadro_actual:
            self._cuadro_actual = max(0, min(nuevo_cuadro, self._analisis.n_cuadros - 1))
            self._actualizar_vista_previa_inmediata()
            if not self._reproduciendo and not self._scrubbing_activo:
                self._offset_seg_reloj = self._analisis.segundo_de(self._cuadro_actual)

    def _retroceder_un_cuadro(self) -> None:
        if self._analisis and self._cuadro_actual > 0:
            self.detener_reproduccion()
            self._cuadro_actual -= 1
            self._var_escala_tiempo.set(self._cuadro_actual)
            self._offset_seg_reloj = self._analisis.segundo_de(self._cuadro_actual)
            self._actualizar_vista_previa_inmediata()

    def _avanzar_un_cuadro(self) -> None:
        if self._analisis and self._cuadro_actual < self._analisis.n_cuadros - 1:
            self.detener_reproduccion()
            self._cuadro_actual += 1
            self._var_escala_tiempo.set(self._cuadro_actual)
            self._offset_seg_reloj = self._analisis.segundo_de(self._cuadro_actual)
            self._actualizar_vista_previa_inmediata()

    def _actualizar_indicador_tiempo(self) -> None:
        if self._analisis is None:
            self.lbl_tiempo.config(text="00:00.000 / 00:00.000 (0 / 0)")
            return
        t_actual = self._analisis.segundo_de(self._cuadro_actual)
        t_total = self._analisis.duracion
        self.lbl_tiempo.config(
            text=f"{formatear_tiempo(t_actual)} / {formatear_tiempo(t_total)} ({self._cuadro_actual + 1} / {self._analisis.n_cuadros})"
        )

    # ----------------------------------------------------------------------- #
    # Reproducción Sincronizada con Master Clock y Scrubbing
    # ----------------------------------------------------------------------- #

    def _al_presionar_espacio(self, event: Any = None) -> str | None:
        """Atajo de barra espaciadora para alternar Play/Pausa."""
        w_focus = self.root.focus_get()
        if isinstance(w_focus, (tk.Entry, ttk.Entry)):
            return None
        self._alternar_reproduccion()
        return "break"

    def _alternar_reproduccion(self) -> None:
        """Alterna el estado de reproducción continua entre Play y Pausa."""
        if self._reproduciendo:
            self.pausar()
        else:
            self.reproducir()

    def reproducir(self) -> bool:
        """Inicia o reanuda la reproducción sincronizada con audio continuo."""
        if self._analisis is None or self._ruta_audio is None:
            return False

        # Si el cursor está en el último cuadro o final de pista, reiniciar al cuadro 0
        if self._cuadro_actual >= self._analisis.n_cuadros - 1:
            self._cuadro_actual = 0
            self._var_escala_tiempo.set(0)

        offset_seg = self._analisis.segundo_de(self._cuadro_actual)

        # Cargar la pista en el reproductor e iniciar audio en el offset exacto
        self._reproductor.cargar(self._ruta_audio)
        self._reproductor.reproducir(offset_seg)

        # Inicializar Master Clock monotónico de alta resolución
        self._offset_seg_reloj = offset_seg
        self._t_inicio_reloj = time.perf_counter()
        self._reproduciendo = True

        self.btn_play_pausa.config(text="⏸ Pausar")
        self._bucle_reproduccion()
        return True

    def pausar(self) -> None:
        """Pausa la reproducción continua y detiene el subproceso de audio."""
        self._reproduciendo = False
        if self._timer_animacion is not None:
            try:
                self.root.after_cancel(self._timer_animacion)
            except Exception:
                pass
            self._timer_animacion = None

        self._reproductor.pausar()
        self.btn_play_pausa.config(text="▶ Reproducir")

    def detener_reproduccion(self) -> None:
        """Detiene completamente la reproducción y reinicia los timers."""
        self._reproduciendo = False
        if self._timer_animacion is not None:
            try:
                self.root.after_cancel(self._timer_animacion)
            except Exception:
                pass
            self._timer_animacion = None

        self._reproductor.detener()
        self.btn_play_pausa.config(text="▶ Reproducir")

    def _bucle_reproduccion(self) -> None:
        """Bucle de animación gobernado por Master Clock monotónico y time-delta."""
        if not self._reproduciendo or self._analisis is None:
            return

        # 1. Consultar tiempo del Master Clock monotónico
        t_delta = time.perf_counter() - self._t_inicio_reloj
        t_actual = self._offset_seg_reloj + t_delta

        # 2. Comprobar si se alcanzó el fin de la pista o el reproductor finalizó
        if t_actual >= self._analisis.duracion or not self._reproductor.esta_reproduciendo():
            self._cuadro_actual = self._analisis.n_cuadros - 1
            self._var_escala_tiempo.set(self._cuadro_actual)
            self._actualizar_vista_previa_inmediata()
            self.detener_reproduccion()
            return

        # 3. Calcular cuadro objetivo con frame-skipping automático
        cuadro_calculado = int(math.floor(t_actual * self._analisis.fps))
        cuadro_objetivo = max(0, min(cuadro_calculado, self._analisis.n_cuadros - 1))

        if cuadro_objetivo != self._cuadro_actual:
            self._cuadro_actual = cuadro_objetivo
            self._var_escala_tiempo.set(cuadro_objetivo)
            self._actualizar_vista_previa_inmediata()

        # 4. Programar siguiente tick (~15 ms para ~60 fps de refresco visual)
        self._timer_animacion = self.root.after(15, self._bucle_reproduccion)

    def _al_iniciar_scrubbing(self, event: Any = None) -> None:
        """Al presionar sobre el slider: silenciar audio y aislar órdenes al sistema."""
        self._scrubbing_activo = True
        self._estaba_reproduciendo_antes_de_scrub = self._reproduciendo
        if self._reproduciendo:
            self.pausar()

    def _al_arrastrar_scrubbing(self, event: Any = None) -> None:
        """Durante el arrastre del slider: actualizar exclusivamente la imagen visual."""
        pass

    def _al_finalizar_scrubbing(self, event: Any = None) -> None:
        """Al soltar el slider: reanudar audio en el offset exacto si estaba reproduciendo."""
        self._scrubbing_activo = False
        if self._analisis is not None:
            self._offset_seg_reloj = self._analisis.segundo_de(self._cuadro_actual)
        if self._estaba_reproduciendo_antes_de_scrub:
            self._estaba_reproduciendo_antes_de_scrub = False
            self.reproducir()

    # Métodos de compatibilidad hacia atrás
    def _alternar_animacion_fragmento(self) -> None:
        self._alternar_reproduccion()

    def _iniciar_animacion_fragmento(self) -> None:
        self.reproducir()

    def _detener_animacion(self) -> None:
        self.detener_reproduccion()

    def obtener_cuadro_actual_raw(self) -> Image.Image | None:
        """Devuelve el cuadro RGBA sin escalar generado por Render.cuadro(i)."""
        if self._cuadro_raw_actual is not None:
            return self._cuadro_raw_actual
        if self._render is not None and 0 <= self._cuadro_actual < self._render.n_cuadros:
            return self._render.cuadro(self._cuadro_actual)
        return None

    # ----------------------------------------------------------------------- #
    # Exportación Asíncrona con Cancelación Cooperativa
    # ----------------------------------------------------------------------- #

    def _dialogo_exportar_video(self) -> None:
        if not self._ruta_audio or self._analisis is None:
            messagebox.showwarning("Atención", "Debés cargar un archivo de audio antes de exportar.")
            return

        modo_fondo = str(self._variables.get("fondo", tk.StringVar(value="negro")).get())
        extension = ".webm"
        sugerido = f"{self._ruta_audio.stem}_visual{extension}"

        destino = filedialog.asksaveasfilename(
            title="Exportar Video",
            initialfile=sugerido,
            defaultextension=extension,
            filetypes=[("Video WebM", "*.webm")],
        )
        if destino:
            self.exportar_video_async(Path(destino))

    def exportar_video_async(
        self,
        destino: Path | str,
        callback_finalizado: Callable[[Path | None, Exception | None], None] | None = None,
    ) -> None:
        """Inicia la exportación en un hilo secundario con diálogo de progreso."""
        self.detener_reproduccion()
        if not self._ruta_audio or self._analisis is None:
            if callback_finalizado:
                callback_finalizado(None, RuntimeError("No hay audio cargado"))
            return

        destino_p = Path(destino)
        params = self.obtener_parametros()
        render_export = Render(self._analisis, self._estilo, params)
        total_cuadros = render_export.n_cuadros

        self._evento_cancelar.clear()

        # Construir diálogo de progreso modal
        dlg = tk.Toplevel(self.root)
        dlg.title("Exportando Video")
        dlg.geometry("420x180")
        dlg.resizable(False, False)
        try:
            if self.root.winfo_viewable():
                dlg.transient(self.root)
                dlg.grab_set()
        except tk.TclError:
            pass

        lbl_tit = ttk.Label(dlg, text="Exportando video para Drift...", font=("TkDefaultFont", 10, "bold"))
        lbl_tit.pack(pady=(16, 6))

        lbl_estado = ttk.Label(dlg, text=f"0%  (0 / {total_cuadros} cuadros)")
        lbl_estado.pack(pady=4)

        prog_bar = ttk.Progressbar(dlg, orient="horizontal", length=350, mode="determinate", maximum=total_cuadros)
        prog_bar.pack(pady=6)

        btn_cancelar = ttk.Button(dlg, text="Cancelar", command=lambda: self.cancelar_exportacion(btn_cancelar))
        btn_cancelar.pack(pady=(8, 0))

        self._dialogo_progreso = dlg

        cola: queue.Queue[tuple[str, Any]] = queue.Queue()

        def progreso_cb(hecho: int, total: int) -> bool:
            if self._evento_cancelar.is_set():
                return False
            cola.put(("progreso", (hecho, total)))
            return True

        def tarea_hilo() -> None:
            escrito: Path | None = None
            error_resultado: Exception | None = None
            try:
                escrito = exportar(render_export, destino_p, progreso=progreso_cb)
            except ErrorDeSalida as e:
                error_resultado = e
            except Exception as e:
                error_resultado = e
            cola.put(("fin", (escrito, error_resultado)))

        self._hilo_export = threading.Thread(target=tarea_hilo, daemon=True)
        self._hilo_export.start()

        def _procesar_mensajes_cola() -> None:
            fin_recibido = False
            escrito_final: Path | None = None
            error_final: Exception | None = None

            while True:
                try:
                    tipo, payload = cola.get_nowait()
                except queue.Empty:
                    break

                if tipo == "progreso":
                    hecho, total = payload
                    if dlg.winfo_exists():
                        prog_bar["value"] = hecho
                        pct = int(hecho * 100 / total) if total > 0 else 0
                        lbl_estado.config(text=f"{pct}%  ({hecho} / {total} cuadros)")
                elif tipo == "fin":
                    fin_recibido = True
                    escrito_final, error_final = payload

            if fin_recibido:
                if dlg.winfo_exists():
                    try:
                        dlg.grab_release()
                    except Exception:
                        pass
                    dlg.destroy()
                self._dialogo_progreso = None

                if callback_finalizado:
                    callback_finalizado(escrito_final, error_final)

                if error_final is not None:
                    if self._evento_cancelar.is_set():
                        messagebox.showinfo("Exportación cancelada", "El proceso fue cancelado y el archivo parcial se eliminó.")
                    else:
                        messagebox.showerror("Error en exportación", f"Ocurrió un error al exportar:\n\n{error_final}")
                elif escrito_final is not None:
                    fondo = str(params.get("fondo", "negro"))
                    consejo = SIGUIENTE_PASO.get(fondo, "")
                    messagebox.showinfo("Exportación exitosa", f"Video exportado con éxito:\n{escrito_final}\n\n{consejo}")
            else:
                self.root.after(30, _procesar_mensajes_cola)

        self.root.after(30, _procesar_mensajes_cola)

    def cancelar_exportacion(self, btn: ttk.Button | None = None) -> None:
        """Señaliza la cancelación cooperativa inmediata de la exportación."""
        self._evento_cancelar.set()
        if btn and btn.winfo_exists():
            btn.config(text="Cancelando...", state="disabled")

    # ----------------------------------------------------------------------- #
    # Ciclo de Vida Limpio y Cero Procesos Zombis (CA-5)
    # ----------------------------------------------------------------------- #

    def _al_cerrar_ventana(self) -> None:
        """Manejador de WM_DELETE_WINDOW para liberar recursos y cerrar subprocesos e hilos."""
        self.detener_reproduccion()
        if self._timer_debounce is not None:
            try:
                self.root.after_cancel(self._timer_debounce)
            except Exception:
                pass
            self._timer_debounce = None
        if self._timer_badge_gracia is not None:
            try:
                self.root.after_cancel(self._timer_badge_gracia)
            except Exception:
                pass
            self._timer_badge_gracia = None
        if hasattr(self, "_timer_chequeo_resultados") and self._timer_chequeo_resultados is not None:
            try:
                self.root.after_cancel(self._timer_chequeo_resultados)
            except Exception:
                pass
            self._timer_chequeo_resultados = None
        self._ocultar_badge_actualizando()
        self._evento_cerrar_worker.set()
        try:
            self._cola_worker.put_nowait(None)
        except Exception:
            pass
        if hasattr(self, "_reproductor") and self._reproductor is not None:
            self._reproductor.cerrar()
        if self._dialogo_progreso and self._dialogo_progreso.winfo_exists():
            self.cancelar_exportacion()
        self.root.destroy()

    def _al_destruir_root(self, event: Any = None) -> None:
        """Manejador del evento <Destroy> para apagar el worker thread al destruir root."""
        if event is not None and getattr(event, "widget", None) != self.root:
            return
        self._evento_cerrar_worker.set()
        try:
            self._cola_worker.put_nowait(None)
        except Exception:
            pass
        if hasattr(self, "_reproductor") and self._reproductor is not None:
            try:
                self._reproductor.cerrar()
            except Exception:
                pass

    def _al_salir_proceso(self) -> None:
        """Hook atexit para garantizar terminación absoluta de cualquier proceso ffplay o hilo."""
        try:
            self._evento_cerrar_worker.set()
        except Exception:
            pass
        try:
            if hasattr(self, "_reproductor") and self._reproductor is not None:
                self._reproductor.cerrar()
        except Exception:
            pass


def main(argv: list[str] | None = None, audio: Path | str | None = None,
         proyecto_path: Path | str | None = None, preset: str | None = None,
         estilo: str | None = None, reproductor_audio: ReproductorAudio | None = None) -> int:
    """Punto de entrada para inicializar y ejecutar el bucle principal de la GUI."""
    root = tk.Tk()
    app = VentanaVisualizador(
        root=root,
        audio=audio,
        estilo=estilo,
        proyecto_path=proyecto_path,
        preset=preset,
        reproductor_audio=reproductor_audio,
    )
    root.mainloop()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
