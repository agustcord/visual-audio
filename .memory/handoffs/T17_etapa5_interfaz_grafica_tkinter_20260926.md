# Handoff Durable T17 — Etapa 5: Interfaz Gráfica Tkinter

- **Fecha:** 2026-09-26
- **Turno:** T17 (Fase 2 — Ejecución Core)
- **Rol:** Ani Programadora (Core Logic Multilenguaje)
- **Pedido Original del Capitán:** "procede"
- **Commit Base:** `7c77176` (Etapas 1 a 4 completadas)
- **Rama:** `master`

---

## 1. Resumen Ejecutivo

Se implementó de forma completa, reactiva y desacoplada la **Etapa 5 (Interfaz Gráfica Tkinter)** del visualizador de audio Drift conforme a `docs/ARQUITECTURA.md` §8, `docs/MVP.md` §4 y `implementation_plan.md`.

Se añadieron y mutaron los siguientes componentes:
1. **Cliente GUI Desacoplado (`tools/visualizador/gui.py`)**:
   - Ventana principal `VentanaVisualizador` estructurada en panel izquierdo (visor y transporte) y panel derecho (controles y parámetros dinámicos).
   - Formulario de parámetros generado polimórficamente a partir de `parametros.ESQUEMA` (sliders continuos/discretos con displays numéricos y unidades, comboboxes readonly, checkbuttons y muestras/selectores de color).
   - Reactividad con temporizador debouncing de 50 ms y habilitación/deshabilitación dinámica basada en `parametros.tiene_efecto(params, nombre)`.
   - Filtrado dinámico de visibilidad según el estilo seleccionado (`def_val.aplica_a(estilo)`).
   - Carga inmediata de audio con proyección del fotograma inicial por defecto ("ver una onda de inmediato", pedido por el fundador).
   - Gestión integral de proyectos (.json) y presets de fábrica o personalizados.
   - Área de vista previa reactiva garantizando Invarianza Estructural (MVP-5) al consumir exclusivamente `Render.cuadro(i)`.
   - Transporte temporal con scrubbing milimétrico, avance/retroceso de cuadros y reproducción animada de fragmentos de 2 segundos (60 cuadros a 30 fps) de forma cooperativa sin congelar la interfaz.
   - Exportación de video asíncrona en hilo secundario comunicada con la UI mediante cola thread-safe (`queue.Queue`), diálogo modal con barra de progreso, porcentaje y conteo de cuadros, y cancelación cooperativa que interrumpe FFmpeg y elimina el archivo incompleto en disco de inmediato.
2. **Integración CLI / Entrypoint (`tools/visualizador/cli.py`)**:
   - Incorpora el flag `--gui` y la regla por omisión: al invocar la aplicación sin argumentos de exportación directa, se lanza la interfaz gráfica interactiva.
3. **Suite de Pruebas Automatizadas de la GUI (`tests/test_gui.py`)**:
   - 42 comprobaciones automatizadas y desatendidas validando exhaustivamente los criterios 5.1 a 5.6.

La suite general del proyecto se incrementó a **169 comprobaciones automatizadas en verde, con 0 fallas y 0 regresiones**.

---

## 2. Detalle de Archivos y Mutaciones de Estado

### A. Módulo GUI (`tools/visualizador/gui.py`)
- **Arquitectura**: Desacoplada del motor de render; actúa como cliente idéntico en jerarquía a `cli.py`.
- **Formulario dinámico**:
  - Lee `parametros.ESQUEMA` y agrupa por secciones visuales (`ttk.LabelFrame`): "Reacción al audio", "Forma", "Posición y tamaño", "Color" y "Salida".
  - Genera widgets polimórficos (`ttk.Scale`, `ttk.Combobox`, `ttk.Checkbutton`, selector hexadecimal de color con muestra gráfica contrastante).
  - Gestiona `solo_estilo_activo` al serializar proyectos o presets para prevenir colisiones de parámetros cruzados.
- **Invarianza Estructural (MVP-5 / Criterio 5.2)**:
  - La previsualización obtiene los datos directamente de `Render.cuadro(self._cuadro_actual)`. El arreglo RGBA es idéntico bit a bit al exportador.
- **Exportación asíncrona y cancelación**:
  - Emplea `threading.Thread` desacoplado y `queue.Queue` thread-safe para transmitir el avance a la UI, erradicando cualquier riesgo de deadlock en Tcl/Tk.
  - Al pulsar "Cancelar", se señaliza `threading.Event`, haciendo que `salida.exportar()` interrumpa la tubería a FFmpeg, destruya el archivo parcial incompleto (`.unlink(missing_ok=True)`) y restaure la UI limpiamente.

### B. Módulo CLI (`tools/visualizador/cli.py`)
- Se agregó el argumento `--gui` al parser.
- Si se detecta invocación sin argumentos o con flag `--gui`, se delega la ejecución en `gui.main(...)` propagando opciones iniciales si estuvieran presentes.

### C. Suite de Pruebas (`tests/test_gui.py`)
Implementa 42 comprobaciones que validan:
- **5.1 (Recorrido completo)**: Carga de audio, cambio de estilo, mutación de parámetros, persistencia en proyecto, reapertura fiel y exportación WebM completa en disco.
- **5.2 (Invarianza estructural MVP-5)**: Verificación pixel a pixel de arreglos RGBA y hashes SHA-256 idénticos entre la vista previa y el exportador para estilos Barras, Onda y Espejadas.
- **5.3 (Latencia < 500 ms)**: Medición empírica con `time.perf_counter()` del ciclo de renderizado y proyección (promedio 24-28 ms, máximo < 35 ms).
- **5.4 (Concurrencia y cancelación)**: Exportación en hilo secundario sin congelar la UI; cancelación cooperativa inmediata con eliminación confirmada del archivo residual en disco.
- **5.5 (Cobertura de esquema)**: Verificación del 100% (30/30) de los parámetros del esquema y comprobación de la reactividad de dependencias (`resplandor_radio` condicionado por `resplandor`, `color_final` por `degradado`).
- **5.6 (Resiliencia ante errores)**: Captura limpia de audio inexistente y archivos de audio corruptos mediante avisos controlados sin excepciones no capturadas.
- **Extra**: Avance/retroceso de cuadros, aplicación de presets desde UI y reproducción de fragmentos animados.

---

## 3. Evidencia Empírica de Verificación

Resultados observables tras ejecutar la suite completa en Windows (Python 3.14.6, Tkinter 8.6, FFmpeg 8.0.1):

1. `python tests/test_analisis.py`:
   - **36 comprobaciones pasadas, 0 fallas** (análisis espectral causal, curvas logarítmicas, normalización).
2. `python tests/test_render.py --export`:
   - **36 comprobaciones pasadas, 0 fallas** (renderizado determinista, barrido de parámetros, exportación WebM en negro, color y transparente con alpha).
3. `python tests/verificar_sincronia.py`:
   - **9 comprobaciones pasadas, 0 fallas (+0 cuadros de desvío)** en ataques rítmicos.
4. `python tests/test_proyecto.py`:
   - **46 comprobaciones pasadas, 0 fallas** (persistencia de proyectos, presets, validación estricta, compensación de color sobre fondos oscuros ΔE < 1.0, advertencias explícitas de saturación).
5. `python tests/test_gui.py`:
   - **42 comprobaciones pasadas, 0 fallas** (criterios 5.1 a 5.6 certificados).

**Total de la suite:** **169 comprobaciones pasadas, 0 fallas, 0 regresiones**.

---

## 4. Estado y Próximos Pasos

- **Etapa 5:** Implementada al 100% y verificada con pruebas automatizadas en disco.
- **Pase a Fase 3 (QA Lead — Ani Mal Humor):** Auditoría formal "pedido vs entregado" de la Etapa 5 y validación de los criterios 5.1 a 5.6.
- **Próxima Etapa de Producto:** Etapa 6 (Integración, empaquetado `.bat` con `pythonw.exe` y actualización de documentación final).
