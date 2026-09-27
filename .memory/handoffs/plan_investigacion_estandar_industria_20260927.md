# Plan de Implementación — Triage Post-FAIL & Estructuración de Fase 0: Investigación de Estándar de la Industria

## 📌 Pedido Original del Capitán (textual)
> "declaro fail, el rendimiento es bajo. se sigue trabando, las maquillaje no se aprecian. declara el fail en la docummentación y en donde consideres asi no se cree que esta aprobado, luego convoca a investigadora, y que investigue como es el estandar de la industria, y como manejan este tipo de herramientas"

---

## 1. Estado y Dictamen Factual del Capitán
- **Línea Base del MVP:** La versión base del MVP permanece formalmente cerrada y catalogada como **`v0.1.0-mvp`** con dictamen **PASS** emitido por el Capitán en T22/T23/T24 (con controles de transporte, reproducción sincronizada y 277 comprobaciones base).
- **Intento de Optimización Post-MVP (T25-T26):** ❌ **DICTAMEN FAIL FORMAL DEL CAPITÁN (RECHAZADO)**.
- **Motivos Factuales del Rechazo:**
  1. *El rendimiento es bajo:* Los tiempos de procesamiento y respuesta siguen siendo excesivos para el flujo de trabajo interactivo.
  2. *Se sigue trabando:* La interfaz de usuario experimenta tirones y congelamientos al manipular variables y sliders.
  3. *El maquillaje no se aprecia:* El badge de actualización visual (`_badge_actualizando`), el cursor inteligente y la retención del frame previo no mitigan la sensación de lentitud ni se aprecian de forma efectiva en el uso real.
- **Estado Administrativo y Técnico:** **NO APROBADO**. Se prohíbe dar por cerrada o aprobada la optimización superficial previa. Queda documentado explícitamente en `RETOMAR.md`, `docs/RUTA_DE_TRABAJO.md`, `README.md`, `.memory/log.md` y este plan.

---

## 2. Diagnóstico de Arquitectura y Justificación de la Fase 0
El enfoque implementado en los turnos T25 y T26 atacó el problema mediante mitigaciones locales sobre la arquitectura existente:
- Caché de muestras PCM en memoria (evitando re-invocar a FFmpeg).
- Worker thread asíncrono con descarte Last-Write-Wins (LWW) en Tkinter.
- Debounce adaptativo de eventos por categoría.
- Feedback cosmético ("maquillaje" visual con badge y cursor).

Si bien los 331 tests técnicos automatizados pasaron al 100% en condiciones sintéticas, **la prueba en el mundo real por parte del Fundador dictaminó FAIL inapelable**. El análisis por software de FFT continua en CPU junto con el renderizado pixel a pixel en Pillow y su transferencia a un `Canvas` de Tkinter posee cuellos de botella intrínsecos de tasa de refresco, contención del GIL y velocidad de blitting.

Intentar parches incrementales a ciegas sin contrastar con las soluciones ya resueltas en el software profesional constituiría una quema improductiva de recursos. Por mandato explícito del Capitán, se abre la **Fase 0: Investigación de Estándar de la Industria**, convocando a **Ani Investigadora**.

---

## 3. Estructuración de la Fase 0: Investigación de Estándar de la Industria

### Rol Asignado
- **Ani Investigadora** (Investigación Factual & Ingeniería Inversa / Benchmarking).

### Alcance Estricto de la Investigación
La investigación debe responder con hechos empíricos, documentación técnica y análisis de arquitectura a las siguientes interrogantes clave:

1. **Estándares y Patrones de la Industria en Herramientas Profesionales:**
   - **Adobe After Effects:** ¿Cómo opera el efecto nativo *Audio Spectrum / Audio Waveform* y el plugin estándar de la industria *Trapcode Sound Keys*? ¿Pre-calculan keyframes de audio (*Convert Audio to Keyframes*), operan por GPU o analizan en streaming?
   - **DaVinci Resolve / Fairlight:** ¿Cómo procesa y dibuja los analizadores de espectro en tiempo real a 60 fps sin bloquear la GUI del editor?
   - **Blender:** ¿Cómo funciona la herramienta *Bake Sound to F-Curves* en el Graph Editor y cómo se desacopla el cálculo del audio del render de la animación?
   - **Herramientas de cabecera en visualización y VJing:** TouchDesigner, Sonic Visualiser, MilkDrop / ProjectM, plugins VST de análisis espectral (FabFilter Pro-Q, Voxengo SPAN).

2. **Pipeline de Cómputo y Datos (Audio Engine):**
   - **Pre-análisis (Baking) vs. Análisis en Vuelo:** ¿Las herramientas profesionales analizan el audio completo de una sola vez al importar la pista (generando una matriz densa de FFT / espectrograma en memoria o disco), o ejecutan transformadas de Fourier bajo demanda durante la interacción?
   - **Estructura de Datos:** ¿Cómo organizan los datos espectrales (bloques de frecuencias, ventanas temporales, texturas de espectrograma 1D/2D) para que la consulta por timestamp sea $O(1)$ sin recálculo?

3. **Pipeline de Renderizado y Despliegue Visual (Graphics Engine):**
   - **Aceleración por Hardware:** ¿Qué rol juega el renderizado por GPU (OpenGL, DirectX, Vulkan, Metal o shaders GLSL) frente al render por CPU en memoria RAM (como Pillow + Canvas Tkinter)?
   - **Estrategias de Interactividad y LOD (Level of Detail):** ¿Cómo mantienen fluidez de 60 fps mientras el usuario arrastra sliders? ¿Reducen la cantidad de muestras en modo interactivo y refinan en reposo? ¿Separan la geometría de las barras del sombreado/color mediante shaders?

4. **Aplicabilidad Directa al Proyecto Drift:**
   - Cuáles de estos patrones son directamente implementables en Python sobre Windows sin violar las reglas de oro del proyecto (Regla 13: sin dependencias pesadas innecesarias; mantener ligereza; compatibilidad con el pipeline de Drift 0.6.0 Trama).

---

## 4. Criterios de Aceptación Falsables para la Fase 0

| ID | Criterio | Método de Verificación | Umbral Falsable |
|---|---|---|---|
| **CA-INV-1** | Relevamiento de al menos 4 herramientas de referencia de la industria | Inspección del informe con citas técnicas de After Effects/Trapcode, DaVinci/Fairlight, Blender y plugins VST/herramientas dedicadas | El informe detalla la arquitectura de al menos 4 referentes consolidados con citas de documentación o código fuente abierto. |
| **CA-INV-2** | Análisis comparativo de pipeline de audio (Pre-bake vs Streaming FFT) | Exposición explícita de costos en RAM, tiempo de inicio y latencia interactiva de ambos enfoques | Presenta tabla cuantitativa y trade-offs claros entre análisis previo integral vs análisis por cuadro. |
| **CA-INV-3** | Análisis de pipeline de visualización (CPU Canvas vs GPU Shaders / Aceleración) | Diagnóstico técnico de los cuellos de botella de Tkinter/Pillow y opciones viables en Python | Diagnóstico factual de límites de FPS en CPU y opciones livianas de aceleración sin bloat de dependencias. |
| **CA-INV-4** | Propuestas arquitectónicas concretas para la re-arquitectura de Drift Visualizador | Sección de recomendaciones accionables orientadas a eliminar tirones y lograr 60 fps reales | Al menos 2 propuestas técnicas fundamentadas y adaptadas al entorno del proyecto. |
| **CA-INV-5** | Registro durable en la Bóveda del proyecto | Verificación física de la nota de wiki y handoff en `$VAULT` | Archivo `.memory/wiki/Investigacion_estandar_industria_audio_reactividad.md` creado y enlazado en MOCs. |

---

## 5. Entregables Esperados de la Fase 0
1. **Nota Canónica en Bóveda:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\wiki\Investigacion_estandar_industria_audio_reactividad.md`
2. **Handoff Durable:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\handoffs\T28_investigacion_estandar_industria_audio_reactividad_YYYYMMDD.md`
3. **Entrada en Bitácora:** Actualización de `log.md` y MOC de handoffs.

---

## 6. Próximo Paso y Gobernanza
Una vez completada la investigación por Ani Investigadora, Ani Arquitecta convocará a Ani Pensadora para evaluar los tradeoffs de las alternativas relevadas, y diseñará el nuevo Plan de Re-arquitectura Técnica, el cual se someterá formalmente al **Gate del Capitán** antes de escribir cualquier nueva línea de código.
