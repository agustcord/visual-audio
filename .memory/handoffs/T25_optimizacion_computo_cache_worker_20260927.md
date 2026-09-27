# Handoff T25 — Optimización de Cómputo Post-MVP: Caché PCM, Worker Thread Asíncrono y Debounce Adaptativo (Bloque A)

- **Fecha:** 2026-09-27
- **Turno:** T25
- **Fase del Ciclo Core:** Fase 2 (Ejecución Técnica — Bloque A)
- **Agente:** Ani Programadora (Core Logic Multilenguaje)
- **Repositorio:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins`
- **Rama:** `master`
- **Línea Base Previa:** Commit `779a544` / Catalogación `v0.1.0-mvp` (277 comprobaciones automáticas).
- **Estado Posterior:** 309 comprobaciones automáticas pasando al 100% en verde (0 fallas, exit code 0).

---

## 📌 Pedido Original del Capitán (textual)
> "procede" (aprobación formal del Gate del Capitán sobre el Bloque A de `implementation_plan.md` tras el dictamen PASS del MVP).

---

## 1. Resumen Ejecutivo del Bloque A

Se implementó de manera íntegra y desacoplada la arquitectura de cómputo reactivo y jerarquía de caché de audio PCM en el Visualizador de Drift conforme a los lineamientos de `implementation_plan.md`:

1. **Tarea 2.1 — Caché PCM en Memoria (`analisis.py`):**
   - Se incorporó el diccionario global en memoria `_CACHE_PCM: dict[tuple[Path, float], np.ndarray]` indexado por `(ruta_audio.resolve(), mtime)`.
   - En `leer_mono(ruta)`, si el archivo ya fue decodificado y su fecha de modificación no varió, se devuelven las muestras directamente en 0 ms sin invocar `ffmpeg.exe` ni crear subprocesos.
   - Se expuso la función `limpiar_cache_pcm()` para testing y gestión de ciclo de vida.
   - **Cumplimiento CA-POST-2:** Exactamente 0 llamadas a FFmpeg al modificar sliders analíticos o de render tras la carga inicial de la pista.

2. **Tarea 2.2 — Worker Thread Asíncrono con Cola Last-Write-Wins (`gui.py`):**
   - Se implementó un worker thread secundario (`self._worker_thread`, demonizado) y una cola thread-safe de tamaño 1 (`queue.Queue(maxsize=1)`) con política estricta de descarte automático de solicitudes obsoletas (*Last-Write-Wins*).
   - El cómputo pesado de `analizar()` y `Render.cuadro(i)` corre íntegramente fuera del hilo principal de Tkinter, liberando la interfaz de cualquier bloqueo sincrónico.
   - La entrega del cuadro renderizado se despacha de forma thread-safe mediante `self.root.after_idle(self._procesar_resultados_worker)` con filtro de secuencia monotónica (`id_tarea >= self._id_render_mostrado`) que previene condiciones de carrera o sobreescritura de cuadros más recientes.
   - **Cumplimiento CA-POST-1 y CA-POST-3:** El hilo de Tkinter no se congela (latencia $\le 16$ ms por evento) y en ráfagas de 10 eventos rápidos el worker procesa a lo sumo 2 tareas (la primera y la última), descartando automáticamente las 8 intermedias.

3. **Tarea 2.3 — Debounce Adaptativo por Categoría de Parámetro (`gui.py`):**
   - Se sustituyó el debounce fijo de 50 ms por un temporizador dinámico adaptativo implementado en `_tiempo_debounce_para(nombre)`:
     * **Cosméticos / Render directo (30 ms):** `color`, `grosor_linea`, `resplandor`, `reflejo`, `tapas_pico`, `espaciado`, `compensar_fondo`, etc.
     * **Ganancia y Respuesta Dinámica (100 ms):** `sensibilidad`, `suavizado`, `caida_picos`.
     * **Analíticos Estructurales (250 ms):** `n_barras`, `frec_min`, `frec_max`, `curva_respuesta`, `fps`.
   - La UI mantiene una actualización inmediata (0 ms) de los displays numéricos adyacentes a cada slider (`_labels_display`) ante el movimiento del cursor, desacoplada del render gráfico.

---

## 2. Frontera de la Intervención Técnica (SMF)

### Archivos Modificados:
1. [`tools/visualizador/analisis.py`](file:///C:/Users/Jonatan%20Agust%C3%ADn/Desktop/Proyectos/Drift/Plugins/tools/visualizador/analisis.py):
   - Creación de `_CACHE_PCM`, función `limpiar_cache_pcm()`, y optimización de `leer_mono(ruta)`.
2. [`tools/visualizador/gui.py`](file:///C:/Users/Jonatan%20Agust%C3%ADn/Desktop/Proyectos/Drift/Plugins/tools/visualizador/gui.py):
   - Clases `_TareaRender` y `_ResultadoRender`.
   - Constantes de debounce adaptativo (`DEBOUNCE_COSMETICO_MS`, `DEBOUNCE_DINAMICA_MS`, `DEBOUNCE_ESTRUCTURAL_MS`, y conjuntos de clasificación de parámetros).
   - Inicialización del worker asíncrono y colas thread-safe en `__init__`.
   - Métodos `_tiempo_debounce_para()`, `_programar_debounce_render()`, `_encolar_tarea_worker()`, `_solicitar_render_async()`, `_bucle_worker_render()`, `_procesar_resultados_worker()`, `esperar_render_async()`.
   - Preservación de `_actualizar_vista_previa_inmediata()` sincrónico con avance de secuencia de render para garantizar invarianza en tests y scrubbing.
   - Limpieza ordenada de recursos y terminación de hilos en `_al_cerrar_ventana` y `_al_salir_proceso`.
3. [`tests/test_analisis.py`](file:///C:/Users/Jonatan%20Agust%C3%ADn/Desktop/Proyectos/Drift/Plugins/tests/test_analisis.py):
   - Adición de `criterio_post_2_cache_pcm()` validando `limpiar_cache_pcm()`, persistencia en caché, 0 llamadas a FFmpeg en lecturas repetidas y velocidad de recuperación < 5 ms (+9 comprobaciones).
4. [`tests/test_gui.py`](file:///C:/Users/Jonatan%20Agust%C3%ADn/Desktop/Proyectos/Drift/Plugins/tests/test_gui.py):
   - Adición de `criterios_post_mvp_bloque_a()` validando debounce adaptativo por parámetro, latencia de UI en hilo principal $\le 16$ ms (CA-POST-1), actualización instantánea de labels numéricos (CA-POST-5), y descarte LWW en worker thread con $\le 2$ tareas procesadas y $\ge 8$ descartadas (CA-POST-3) (+23 comprobaciones).

### Explícitamente Fuera de Alcance (NO Tocado):
- Motor binario de Drift (`drift.exe` en `C:\Program Files\Drift\`).
- Regla 13 preservada al 100%: Cero dependencias externas adicionales introducidas. Se utilizó exclusivamente la biblioteca estándar (`queue`, `threading`, `time`, `pathlib`, `tkinter`) y `numpy` / `Pillow` ya homologados.
- Tareas del Bloque B (UI visual badges "⏳ Actualizando..." y ghost frame): corresponden a Ani Frontend.

---

## 3. Matriz de Evidencia Empírica de Verificación

Se ejecutó la suite completa de 7 scripts de prueba automatizados, confirmando **309 comprobaciones en verde, 0 fallas y 0 regresiones** (exit code 0):

| Script de Prueba | Checks Previos | Checks Actuales | Estado | Detalles de Verificación |
|---|---|---|---|---|
| `tests/test_analisis.py` | 36 | **45** | **PASS** | Cobertura total de CA-POST-2: 0 llamadas a FFmpeg tras carga inicial; recuperación en 0.25 ms. |
| `tests/test_render.py --export` | 36 | **36** | **PASS** | 73 combinaciones en Barras, 73 en Espejadas, 59 en Onda; exports negro, color y transparente (alpha) intactos. |
| `tests/verificar_sincronia.py` | 8 | **8** | **PASS** | 8 ataques rítmicos alineados con desvío exacto de +0 cuadros en los tres estilos. |
| `tests/test_proyecto.py` | 46 | **46** | **PASS** | Persistencia JSON, 4 presets de fábrica y álgebra de color en modo Trama. |
| `tests/test_lanzador.py` | 44 | **44** | **PASS** | Lanzador `visualizador.bat`, arranque con `pythonw.exe`, entrypoint canónico. |
| `tests/test_reproductor.py` | 43 | **43** | **PASS** | Backends `FFplayBackend`, `MCIBackend`, `NullBackend` y Master Clock anti-deriva. |
| `tests/test_gui.py` | 64 | **87** | **PASS** | Invarianza MVP-5, transporte continuo, CA-POST-1 ($\le 16$ ms), CA-POST-3 (LWW $\le 2$ proc, $\ge 8$ desc), Debounce adaptativo. |
| **TOTAL GENERAL** | **277** | **309** | **100% PASS** | **0 fallas, 0 regresiones, exit code 0 en todos los scripts.** |

### Mediciones Falsables Observadas:
- **Latencia de UI en hilo principal (CA-POST-1):** Promedio de 8.77 ms, pico máximo de 12.50 ms (umbral máximo permitido: 16.0 ms a 60 fps).
- **Caché PCM (CA-POST-2):** Conteo de `subprocess.run` con FFmpeg en lecturas repetidas: exactamente 0. Tiempo de lectura de caché: 0.25 ms (< 5.0 ms).
- **Descarte de Tareas Obsoletas (CA-POST-3):** Ráfaga de 10 solicitudes asíncronas en < 200 ms: el worker procesó exactamente 2 tareas (la inicial en curso y la final solicitada), descartando automáticamente 8 intermedias.
- **Debounce Adaptativo:** `color` = 30 ms, `grosor_linea` = 30 ms, `sensibilidad` = 100 ms, `n_barras` = 250 ms, `fps` = 250 ms.
- **Display Numérico Inmediato (CA-POST-5):** Label actualizado a 2.90 de forma sincrónica con 0 ms de retraso.

---

## 4. Decisiones Técnicas y de Arquitectura

1. **Invarianza Monotónica de Render:** Para impedir que una tarea asíncrona vieja sobrescriba un cuadro renderizado de forma sincrónica (por ejemplo, durante scrubbing o avance cuadro a cuadro), se asignó a cada tarea un número de secuencia monotónico incremental `self._secuencia_render`. Si al despachar a la UI `res.id_tarea < self._id_render_mostrado`, el resultado se descarta.
2. **Absorción de Obsoletos en Entrada y Salida:** En `_encolar_tarea_worker`, si la cola de tamaño 1 está llena, la tarea previa se desaloja sumando al contador de descartes. Adicionalmente, al despertar el worker, si mientras tanto entraron tareas más nuevas a la cola, se extrae la última inmediatamente sin malgastar CPU en el cómputo del estado intermedio.
3. **Preservación Estricta de la Firma de `_actualizar_vista_previa_inmediata`:** Mantiene su capacidad de render sincrónico inmediato requerida para la inicialización al cargar audio, la exportación y las pruebas unitarias de invarianza estructural (MVP-5).

---

## 5. Dónde Retomar y Próximos Pasos

- **Bloque B (Maquillaje y Feedback de Experiencia de Usuario):** Ani Frontend asume la implementación del badge sutil "⏳ Actualizando..." en el canvas para cómputos $> 80$ ms, cursor de espera interactivo y preservación visual de fotograma anterior (*ghost frame* / *never blank*).
- **Fase 3 (QA y Auditoría de Aceptación):** Ani Mal Humor auditará empíricamente la suite de 309 pruebas y los umbrales de latencia.
