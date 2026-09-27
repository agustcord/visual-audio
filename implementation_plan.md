# Plan de Implementación — Roadmap Post-MVP: Optimización de Rendimiento y UX Reactiva (Gate del Capitán)

## 📌 Pedido Original del Capitán (textual)
> "procede con eso que pidio mal humor. yo ya probe la app, y puedo dictaminar que funciona, por mi parte el dictame es PASS con respeto al MVP, sino no la considero una version final ya que tiene mejoras importantes por hacer. La primera, es el rendimiento, el programa tiene procesos brusco de cargar cuando se modifica una variable, siendo facil de interpretar que se \"rompio\" cuando no es asi. que programadora haga lo que pidio mal humor. pero que arquitecta docummente mvp cerrado, catalogue la version correctamente, y empiece a investigar como mmejorar este apartado, o como \"maquillar\" esta sensacion de que se rompio, para que el programa sea mas amigable con el usuario"

---

## 1. Contexto y Estado de Línea Base
- **Estado del MVP:** Formalmente cerrado y catalogado como **`v0.1.0-mvp`** con dictamen **PASS** emitido por el Capitán tras pruebas directas y con la totalidad de la suite automatizada en verde (**277 comprobaciones automáticas pasando al 100%, 0 fallas y 0 regresiones**).
- **Objetivo de este Plan:** Responder al mandato expreso del Capitán para transformar la experiencia interactiva de la aplicación, eliminando los procesos bruscos de carga ("tirones") y la sensación de que el programa "se rompió" cuando el usuario ajusta variables en la interfaz gráfica.
- **Alcance Operativo:** Modificaciones de arquitectura en `tools/visualizador/gui.py` y `tools/visualizador/analisis.py`, adición de componentes de feedback visual en el visor de Tkinter, y pruebas de verificación de latencia en `tests/test_gui.py`. Cero mutaciones de código en turno 1 (Fase 1 Triage) a la espera de la autorización en el **Gate del Capitán**.

---

## 2. Justificación de Consulta en Fase 0
De acuerdo con las Reglas de Workspace y Delegación Anidada de Ani Arquitecta, el análisis de arquitectura, ponderación de tradeoffs y formulación de contingencias técnicas se resolvió de forma autónoma e integral en este plan y en el informe durable `.memory/handoffs/T24_cierre_mvp_v010_investigacion_rendimiento_ux_20260926.md`. No se requiere consulta externa adicional para habilitar la decisión del Capitán en el Gate.

---

## 3. Plan Estructurado de Tareas por Fases y Roles

### FASE 2: EJECUCIÓN TÉCNICA

#### Bloque A: Arquitectura de Cómputo y Caché (Ani Programadora)
- **Tarea 2.1 — Implementación de Caché de Audio PCM en `analisis.py`:**
  - Crear un diccionario de caché global en memoria `_CACHE_PCM: dict[tuple[Path, float], np.ndarray]` indexado por `(ruta_audio.resolve(), mtime)`.
  - En `leer_mono(ruta)`, verificar si el audio ya fue decodificado y el archivo no mutó. Si existe en caché, devolver la referencia inmediatamente en 0 ms sin invocar `ffmpeg.exe`.
  - Erradicar las llamadas redundantes a subprocesos durante los ajustes de parámetros analíticos.

- **Tarea 2.2 — Worker Thread Asíncrono y Cola con Descarte de Obsoletos (Last-Write-Wins) en `gui.py`:**
  - Crear un hilo trabajador secundario (`self._worker_thread`) demonizado y una cola de solicitudes thread-safe de tamaño 1 (`queue.Queue(maxsize=1)` o variable atómica con cerrojo `threading.Lock`).
  - Cuando el usuario mueve un control, la solicitud de recálculo se encola. Si el worker está ocupado procesando un cuadro previo, la nueva solicitud sobrescribe a la anterior (descarte automático de estados intermedios obsoletos).
  - El cómputo pesado de `analizar()` y `Render.cuadro(i)` corre íntegramente en el worker thread, liberando al hilo principal de Tkinter de cualquier bloqueo sincrónico.
  - La entrega del cuadro renderizado hacia el canvas se despacha de forma thread-safe mediante `self.root.after_idle` o mensaje de retorno.

- **Tarea 2.3 — Debounce Adaptativo por Categoría de Parámetro en `gui.py`:**
  - Sustituir el debounce fijo de 50 ms por un temporizador dinámico según el parámetro que originó el cambio:
    * **Cosméticos / Render directo (30 ms):** `color`, `grosor_linea`, `resplandor`, `reflejo`, `tapas_pico`, `espaciado`, `compensar_fondo`.
    * **Ganancia y Respuesta Dinámica (100 ms):** `sensibilidad`, `suavizado`, `caida_picos`.
    * **Analíticos Estructurales (250 ms):** `n_barras`, `frec_min`, `frec_max`, `curva_respuesta`, `fps`.

---

#### Bloque B: Maquillaje y Feedback de Experiencia de Usuario (Ani Frontend)
- **Tarea 2.4 — Actualización Inmediata y Sincrónica de Displays Numéricos a 60 fps:**
  - En `_al_mover_slider()`, asegurar que `self._labels_display[nombre].config(text=txt)` se ejecute de inmediato y sincrónicamente ante el evento de arrastre de Tkinter, desacoplado del timer de debounce del render.
  - El usuario percibe respuesta instantánea de la interfaz bajo el puntero del ratón en todo momento.

- **Tarea 2.5 — Preservación del Fotograma Anterior (Ghost Frame / Never Blank):**
  - Garantizar que durante el tiempo de recálculo asíncrono el canvas de previsualización conserve intacto el último fotograma dibujado, prohibiendo explícitamente cualquier borrado o parpadeo a negro.

- **Tarea 2.6 — Badge Sutil de Actualización en el Visor ("⏳ Actualizando..."):**
  - Implementar un indicador visual no intrusivo en el canvas o barra de estado (badge semi-transparente en la esquina superior derecha del visor con el texto `"⏳ Actualizando..."` y cursor de espera en el canvas).
  - El badge se activa si la tarea del worker toma más de 80 ms y se oculta de inmediato al recibir y proyectar el fotograma final.
  - Erradica por completo la interpretación de que "el programa se rompió", otorgando feedback explícito de actividad en curso.

---

### FASE 3: QA Y AUDITORÍA DE ACEPTACIÓN (Ani Mal Humor)
- **Tarea 3.1 — Auditoría Empírica de Latencia y Fluidez de UI:**
  - Medir que la latencia en el hilo principal de Tkinter durante el arrastre continuo de sliders se mantenga en $\le 16$ ms (60 fps), sin eventos de ventana congelada ni mensajes de "No responde" del sistema operativo.
- **Tarea 3.2 — Verificación de Ausencia de Invocaciones Redundantes a FFmpeg:**
  - Auditar que al modificar sliders analíticos con una pista ya cargada, el contador de ejecuciones de `ffmpeg.exe` permanezca en 0 gracias a la caché PCM.
- **Tarea 3.3 — Auditoría de la Suite Integral de Pruebas (277+ checks):**
  - Ejecutar la suite completa de 7 scripts de prueba (`test_analisis.py`, `test_render.py`, `verificar_sincronia.py`, `test_proyecto.py`, `test_lanzador.py`, `test_reproductor.py`, `test_gui.py`) y nuevas pruebas para el worker y la caché, certificando 0 fallas y 0 regresiones.

---

## 4. Matriz de Criterios de Aceptación Falsables

| Criterio | Descripción | Método de Verificación Empírico | Umbral Falsable |
|---|---|---|---|
| **CA-POST-1** | Hilo principal de Tkinter no bloqueante | Medición de tiempo de bloqueo en evento `<B1-Motion>` en `gui.py` | Latencia de UI en hilo principal $\le 16$ ms; cero congelamientos perceptibles. |
| **CA-POST-2** | Caché de decodificación PCM | Conteo de llamadas a `subprocess.run` con `ffmpeg` tras cargar el audio | Exactamente 0 llamadas a FFmpeg al modificar sliders analíticos o de render. |
| **CA-POST-3** | Descarte de tareas obsoletas | Generación de ráfaga de 10 eventos de slider en < 200 ms | El worker procesa a lo sumo 2 renders (el primero y el último), descartando los 8 intermedios. |
| **CA-POST-4** | Feedback visual de actualización | Verificación de existencia del badge o estado en el canvas | El widget/texto `"⏳ Actualizando..."` se muestra si el cómputo dura $> 80$ ms y desaparece al finalizar. |
| **CA-POST-5** | Respuesta inmediata de displays numéricos | Inspección de `_labels_display` durante arrastre continuo | El label numérico se actualiza sincrónicamente con el slider (0 ms de delay). |
| **CA-POST-6** | Invarianza y preservación de suite | Ejecución secuencial de la suite completa de pruebas | 100% de comprobaciones en verde (277+ checks), 0 fallas, exit code 0. |

---

## 5. Asignación de Roles del Escuadrón Ani
- **Fase 1 (Triage & Arquitectura):** Ani Arquitecta (Tech Lead) — Diagnóstico de causa raíz, diseño de arquitectura desacoplada y formalización de plan.
- **Fase 2 (Ejecución Técnica de Cómputo y Caché):** Ani Programadora (Core Logic) — Implementación de caché PCM, worker thread asíncrono y debounce adaptativo.
- **Fase 2 (Ejecución Técnica de UX & Maquillaje):** Ani Frontend (UI/UX) — Implementación de overlay/badge de actualización, labels inmediatos a 60 fps y cursor de espera.
- **Fase 3 (QA & Auditoría Falsable):** Ani Mal Humor (Vice-Líder & QA Lead) — Medición de latencia de UI, verificación de caché y auditoría de la suite de 277+ pruebas.

---

## 6. Próximo Paso Inmediato (Gate del Capitán)
El presente plan queda registrado de forma durable en disco. Ninguna línea de código de producto ha sido modificada en este turno. Ani Recepcionista presentará este plan al Capitán para obtener su aprobación explícita antes de habilitar el pase a la Fase 2 de Ejecución Técnica.
