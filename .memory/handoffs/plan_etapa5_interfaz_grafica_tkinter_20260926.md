# Handoff Durable T16 — Plan de Triage Factual (Fase 1 Core): Etapa 5 (Interfaz Gráfica Tkinter)

- **Fecha:** 2026-09-26
- **Turno:** T16 (Fase 1 — Triage & Arquitectura)
- **Rol:** Ani Arquitecta (Tech Lead del Escuadrón Ani)
- **Pedido Original del Capitán:** "avanza"
- **Estado Previo:** Etapa 4 cerrada en T15 con 127 comprobaciones automatizadas en verde (0 fallas).
- **Entregable:** `implementation_plan.md` y este handoff durable.

---

## 1. Resumen Ejecutivo y Triage

Se ha asumido el mando del triage de Fase 1 para la **Etapa 5 (Interfaz gráfica Tkinter)** del visualizador de audio para Drift, conforme a lo establecido en `docs/RUTA_DE_TRABAJO.md` §4, `docs/ARQUITECTURA.md` §8 y `docs/MVP.md` §4.

El propósito de la Etapa 5 es materializar el principio fundacional *"sin programación para el usuario final"*, dotando al sistema de una interfaz de escritorio reactiva, liviana y desacoplada del motor de procesamiento, construida íntegramente sobre las bibliotecas estándar ya presentes en el entorno (`tkinter` con Tk 8.6 y `Pillow` con `ImageTk`), sin introducir dependencias externas.

---

## 2. Verificación Factual del Punto de Partida

### A. Repositorio y Entorno
- **Directorio de trabajo:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins`
- **Rama:** `master`
- **Punto de sincronización:** Base T15 implementada en disco con módulos `proyecto.py`, `parametros.py` (álgebra de Trama y `compensar_fondo`), `presets/` (4 presets canónicos), integración en `cli.py` y suite `test_proyecto.py`.
- **Runtimes verificados:**
  * Python 3.14.6 (`pythonw.exe` disponible para ejecución sin consola).
  * Tkinter operativo con Tk 8.6.
  * Pillow 11.1.0 con soporte `ImageTk` confirmado.
  * FFmpeg 8.0.1 verificado en `C:\ffmpeg\bin\ffmpeg.exe`.

### B. Evidencia Empírica de Pruebas (127/127 comprobaciones en verde)
1. `tests/test_analisis.py`: **36 pasadas, 0 fallas** (análisis espectral y temporal exacto, ventana causal).
2. `tests/test_render.py --export`: **36 pasadas, 0 fallas** (idempotencia de cuadro, barrido de parámetros, exportación WebM en 3 modos).
3. `tests/verificar_sincronia.py`: **9 pasadas, 0 fallas (+0 cuadros de desvío)** en los 8 ataques rítmicos.
4. `tests/test_proyecto.py`: **46 pasadas, 0 fallas** (persistencia de proyectos y presets, invariante de `#000000`, fidelidad ΔE < 1.0, avisos ante colores inalcanzables y CLI).

Total general verificado: **127 pruebas automáticas en verde, 0 fallas**. Precondiciones de la Etapa 5 completamente cumplidas.

---

## 3. Justificación de Consulta Previa (Regla 28 de SKILL.md)

No se convocó a `ani-pensadora` ni a `ani-investigadora` debido a que las especificaciones de interfaz, contratos de renderizado y esquemas de parámetros se encuentran exhaustivamente determinados y verificados en disco en `docs/ARQUITECTURA.md`, `docs/MVP.md` y `tools/visualizador/parametros.py`. Los aspectos de concurrencia y diseño de UI se han resuelto de forma directa y autónoma en el plan de arquitectura.

---

## 4. Arquitectura y Diseño Técnico de la Etapa 5

### Principio Rector: Desacoplamiento Estructural (Garantía MVP-5)
La interfaz gráfica (`tools/visualizador/gui.py`) opera como un cliente puro del motor, en pie de igualdad con `cli.py`. No contiene lógica matemática de FFT, no implementa dibujadores paralelos y no escribe video por su cuenta:
1. La vista previa utiliza estrictamente `Render.cuadro(i)`.
2. La exportación invoca a `salida.exportar(render, destino, progreso)`.
3. Los proyectos y presets se gestionan a través de `proyecto.guardar()`, `proyecto.abrir()`, etc.
4. Los parámetros se construyen y validan a través de `parametros.validar()`.

### Componentes de la Interfaz
1. **Ventana Principal (`VentanaVisualizador`):**
   - Disposición en dos paneles principales: panel izquierdo para lienzo de previsualización y transporte; panel derecho para configuración y acciones.
   - Canvas de visualización con auto-ajuste proporcional (aspect ratio 16:9).
2. **Generador Dinámico de Controles:**
   - Recorre `parametros.por_grupo(estilo)` y renderiza controles según el tipo de `Valor`:
     * Numérico con rango (`float`/`int`): `ttk.Scale` enlazado con variable de Tkinter y display numérico en vivo.
     * Booleano: `ttk.Checkbutton`.
     * Opciones: `ttk.Combobox` (modo solo lectura).
     * Color (`formato="color"`): muestra gráfica del color actual y diálogo selector `colorchooser.askcolor()`.
   - Reactividad con debouncing (50 ms) para asegurar actualización fluida sin colapsar el hilo de UI.
   - Habilitación dinámica según `parametros.tiene_efecto()`.
   - Filtrado dinámico por estilo según `v.aplica_a(estilo)`.
3. **Barra de Transporte y Scrubbing:**
   - Deslizador temporal que mapea cuadros `0 .. n_cuadros - 1` con formato `MM:SS / MM:SS`.
   - Botón de previsualización animada corta (secuencia de 60 cuadros a 30 fps) mediante bucle cooperativo `root.after()`.
4. **Exportación no Bloqueante con Cancelación Cooperativa:**
   - La exportación se ejecuta en un hilo secundario `threading.Thread`.
   - Diálogo modal de progreso con barra, porcentaje y botón de cancelación.
   - La función `progreso(hecho, total) -> bool` verifica el evento de cancelación; al cancelar devuelve `False`, terminando el subproceso FFmpeg y eliminando el archivo temporal de inmediato.
   - Al finalizar, muestra el mensaje operativo `SIGUIENTE_PASO[fondo]`.

---

## 5. Asignación de Roles y Tareas

- **Tareas 5.1 a 5.5 (Implementación técnica y suite de pruebas):** Ani Programadora (Fase 2 - Ejecución).
- **Tarea 5.6 (Auditoría de criterios de aceptación y verificación falsable):** Ani Mal Humor (Fase 3 - QA).

---

## 6. Criterios de Aceptación Falsables (5.1 a 5.6)

| # | Criterio | Método de Verificación | Condición Falsable |
|---|---|---|---|
| **5.1** | Recorrido completo sin tocar la línea de comandos | Prueba de integración funcional | Carga de audio, selección de estilo, ajuste de parámetros, guardado de proyecto y exportación ejecutados íntegramente desde la GUI. |
| **5.2** | Cuadro de vista previa idéntico al del export | `tests/test_gui.py` | Comparación pixel a pixel (`np.array_equal`) y hash SHA-256 entre el cuadro emitido para la vista previa y el entregado al pipeline de exportación. |
| **5.3** | Vista previa actualizada en < 500 ms | `tests/test_gui.py` | Benchmark con `time.perf_counter()` demostrando que la generación y reescalado de cuadro toma menos de 500 ms a media resolución. |
| **5.4** | UI no congelada durante export y cancelación cooperativa | `tests/test_gui.py` | Eventos de UI procesados durante export en hilo secundario; cancelación interrumpe el proceso, elimina el archivo parcial y restablece el estado. |
| **5.5** | 100% de los parámetros del esquema presentes en la UI | `tests/test_gui.py` | Inspección refleja de los widgets creados contra las claves de `parametros.ESQUEMA`. |
| **5.6** | Audio corrupto o inexistente avisa sin traceback | `tests/test_gui.py` | Detección de error de análisis capturada con mensaje claro al usuario en lugar de fallo no capturado. |

---

## 7. Frontera Factual

- **Archivos creados/modificados en este turno:**
  * `implementation_plan.md` (actualizado con el plan estructurado de la Etapa 5).
  * `.memory/handoffs/plan_etapa5_interfaz_grafica_tkinter_20260926.md` (este documento).
  * `.memory/log.md` (bitácora actualizada).
- **Archivos explícitamente NO tocados en este turno:**
  * Código de producto de `tools/visualizador/` (veto de Turno 1 respetado estrictamente).
  * Código de pruebas de `tests/`.
  * Bóveda canónica central o rutas externas.
