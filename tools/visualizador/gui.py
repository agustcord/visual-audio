"""Interfaz gráfica de usuario (Tkinter) para el visualizador de audio.

Contratos canónicos definidos en docs/ARQUITECTURA.md §8, docs/MVP.md §4 y
docs/RUTA_DE_TRABAJO.md §4:
- Motor desacoplado: esta interfaz es un cliente más del motor (como cli.py).
- Formulario dinámico generado a partir de parametros.ESQUEMA sin controles cableados a mano.
- Invarianza estructural (MVP-5): la vista previa utiliza estrictamente Render.cuadro(i).
- Exportación de video asíncrona en hilo secundario con barra de progreso y cancelación cooperativa limpia.
"""

from __future__ import annotations

import math
import queue
import threading
import time
from pathlib import Path
from typing import Any, Callable
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk
from PIL import Image, ImageTk

from . import estilos, parametros, proyecto
from .analisis import Analisis, ErrorDeAnalisis, analizar
from .render import Render
from .salida import ErrorDeSalida, SIGUIENTE_PASO, exportar


def formatear_tiempo(segundos: float) -> str:
    """Convierte segundos a formato MM:SS.mmm."""
    if segundos < 0:
        segundos = 0.0
    minutos = int(segundos // 60)
    resto = segundos % 60
    return f"{minutos:02d}:{resto:06.3f}"


class VentanaVisualizador:
    """Ventana principal de la interfaz gráfica del visualizador."""

    def __init__(
        self,
        root: tk.Tk | None = None,
        audio: Path | str | None = None,
        estilo: str | None = None,
        proyecto_path: Path | str | None = None,
        preset: str | None = None,
    ) -> None:
        self._es_root_propio = root is None
        self.root = root or tk.Tk()
        self.root.title("Visualizador de audio — Drift")
        self.root.geometry("1240x780")
        self.root.minsize(960, 600)

        # Estado del motor
        self._ruta_audio: Path | None = None
        self._analisis: Analisis | None = None
        self._render: Render | None = None
        self._estilo: str = estilo or "barras"
        self._cuadro_actual: int = 0
        self._params_analisis_previo: dict[str, Any] = {}
        self._cuadro_raw_actual: Image.Image | None = None
        self._imagen_tk_referencia: ImageTk.PhotoImage | None = None
        self._ultimo_error: str | None = None

        # Control reactivo y animación
        self._timer_debounce: str | None = None
        self._reproduciendo: bool = False
        self._timer_animacion: str | None = None
        self._cuadro_fin_animacion: int = 0

        # Exportación en segundo plano
        self._hilo_export: threading.Thread | None = None
        self._evento_cancelar = threading.Event()
        self._dialogo_progreso: tk.Toplevel | None = None

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

        # Texto inicial si no hay audio
        self._dibujar_mensaje_espera("Cargá un archivo de audio (.mp3, .wav, .flac) para previsualizar")

        # Barra de transporte
        frame_transporte = ttk.LabelFrame(self._panel_izq, text="Transporte", padding=6)
        frame_transporte.grid(row=1, column=0, sticky="ew", pady=(8, 0))
        frame_transporte.columnconfigure(1, weight=1)

        # Deslizador de tiempo
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

        # Botones y etiquetas de transporte
        self.btn_prev_frame = ttk.Button(frame_transporte, text="◀ Cuadro", width=9, command=self._retroceder_un_cuadro)
        self.btn_prev_frame.grid(row=1, column=0, sticky="w", padx=2, pady=4)

        self.btn_animar = ttk.Button(frame_transporte, text="▶ Fragmento (2s)", command=self._alternar_animacion_fragmento)
        self.btn_animar.grid(row=1, column=1, sticky="w", padx=4, pady=4)

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

    def _al_cambiar_parametro(self, nombre: str) -> None:
        self._actualizar_habilitacion_dependencias()
        self._programar_debounce_render()

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
        """Carga y analiza una pista de audio. Muestra fotograma inicial de inmediato."""
        ruta_p = Path(ruta)
        self._detener_animacion()
        try:
            params = self.obtener_parametros()
            self._analisis = analizar(ruta_p, params, self._estilo)
            self._params_analisis_previo = self._extraer_params_analisis(params)
            self._ruta_audio = ruta_p
            self._render = Render(self._analisis, self._estilo, params)
            self._ultimo_error = None
        except (ErrorDeAnalisis, Exception) as e:
            self._ultimo_error = str(e)
            messagebox.showerror("Error al cargar audio", f"No se pudo cargar '{ruta_p.name}':\n\n{e}")
            return False

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

    def _programar_debounce_render(self) -> None:
        """Programa la actualización de vista previa con debounce de 50 ms."""
        if self._timer_debounce is not None:
            try:
                self.root.after_cancel(self._timer_debounce)
            except Exception:
                pass
        self._timer_debounce = self.root.after(50, self._actualizar_vista_previa)

    def _actualizar_vista_previa(self) -> None:
        self._timer_debounce = None
        self._actualizar_vista_previa_inmediata()

    def _actualizar_vista_previa_inmediata(self) -> None:
        """Genera el cuadro actual mediante Render.cuadro(i) y lo proyecta."""
        if self._analisis is None or self._ruta_audio is None:
            return

        params = self.obtener_parametros()
        params_analisis = self._extraer_params_analisis(params)

        # Si cambiaron parámetros que afectan al análisis, re-analizar
        if params_analisis != self._params_analisis_previo:
            try:
                self._analisis = analizar(self._ruta_audio, params, self._estilo)
                self._params_analisis_previo = params_analisis
                self.scale_tiempo.config(to=max(0, self._analisis.n_cuadros - 1))
            except Exception as e:
                self._ultimo_error = str(e)
                return

        # Actualizar Render si no existe o cambiaron parámetros
        self._render = Render(self._analisis, self._estilo, params)

        if not 0 <= self._cuadro_actual < self._analisis.n_cuadros:
            self._cuadro_actual = max(0, min(self._cuadro_actual, self._analisis.n_cuadros - 1))

        # Contrato de Invarianza Estructural (MVP-5): usar estrictamente Render.cuadro(i)
        cuadro_rgba = self._render.cuadro(self._cuadro_actual)
        self._cuadro_raw_actual = cuadro_rgba
        self._proyectar_en_canvas(cuadro_rgba)
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

        img_redim = img_rgba.resize((nw, nh), Image.Resampling.BILINEAR)
        base.paste(img_redim, (0, 0), img_redim)

        img_tk = ImageTk.PhotoImage(base)
        self._imagen_tk_referencia = img_tk

        self.canvas_preview.delete("all")
        x = cw // 2
        y = ch // 2
        self.canvas_preview.create_image(x, y, image=img_tk, anchor="center")

    def _al_redimensionar_canvas(self, event: Any = None) -> None:
        if self._cuadro_raw_actual is not None:
            self._proyectar_en_canvas(self._cuadro_raw_actual)
        elif self._analisis is None:
            self._dibujar_mensaje_espera("Cargá un archivo de audio (.mp3, .wav, .flac) para previsualizar")

    def _dibujar_mensaje_espera(self, mensaje: str) -> None:
        self.canvas_preview.delete("all")
        cw = max(10, self.canvas_preview.winfo_width())
        ch = max(10, self.canvas_preview.winfo_height())
        self.canvas_preview.create_text(
            cw // 2, ch // 2,
            text=mensaje,
            fill="#71717A",
            font=("TkDefaultFont", 11),
            justify="center",
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

    def _retroceder_un_cuadro(self) -> None:
        if self._analisis and self._cuadro_actual > 0:
            self._cuadro_actual -= 1
            self._var_escala_tiempo.set(self._cuadro_actual)
            self._actualizar_vista_previa_inmediata()

    def _avanzar_un_cuadro(self) -> None:
        if self._analisis and self._cuadro_actual < self._analisis.n_cuadros - 1:
            self._cuadro_actual += 1
            self._var_escala_tiempo.set(self._cuadro_actual)
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

    def _alternar_animacion_fragmento(self) -> None:
        if self._reproduciendo:
            self._detener_animacion()
        else:
            self._iniciar_animacion_fragmento()

    def _iniciar_animacion_fragmento(self) -> None:
        if self._analisis is None:
            return
        fps = self._analisis.fps
        cuadros_fragmento = 60  # 2 segundos exactos
        self._cuadro_fin_animacion = min(self._cuadro_actual + cuadros_fragmento, self._analisis.n_cuadros - 1)
        if self._cuadro_actual >= self._cuadro_fin_animacion:
            self._cuadro_actual = max(0, self._cuadro_fin_animacion - cuadros_fragmento)
            self._var_escala_tiempo.set(self._cuadro_actual)

        self._reproduciendo = True
        self.btn_animar.config(text="⏹ Detener")
        intervalo_ms = max(15, int(1000 / fps))
        self._bucle_animacion(intervalo_ms)

    def _bucle_animacion(self, intervalo_ms: int) -> None:
        if not self._reproduciendo:
            return
        if self._cuadro_actual >= self._cuadro_fin_animacion or self._cuadro_actual >= self._analisis.n_cuadros - 1:
            self._detener_animacion()
            return

        self._cuadro_actual += 1
        self._var_escala_tiempo.set(self._cuadro_actual)
        self._actualizar_vista_previa_inmediata()
        self._timer_animacion = self.root.after(intervalo_ms, lambda: self._bucle_animacion(intervalo_ms))

    def _detener_animacion(self) -> None:
        self._reproduciendo = False
        if self._timer_animacion is not None:
            try:
                self.root.after_cancel(self._timer_animacion)
            except Exception:
                pass
            self._timer_animacion = None
        self.btn_animar.config(text="▶ Fragmento (2s)")

    def obtener_cuadro_actual_raw(self) -> Image.Image | None:
        """Devuelve el cuadro RGBA sin escalar generado por Render.cuadro(i)."""
        return self._cuadro_raw_actual

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


def main(argv: list[str] | None = None, audio: Path | str | None = None,
         proyecto_path: Path | str | None = None, preset: str | None = None,
         estilo: str | None = None) -> int:
    """Punto de entrada para inicializar y ejecutar el bucle principal de la GUI."""
    root = tk.Tk()
    app = VentanaVisualizador(
        root=root,
        audio=audio,
        estilo=estilo,
        proyecto_path=proyecto_path,
        preset=preset,
    )
    root.mainloop()
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
