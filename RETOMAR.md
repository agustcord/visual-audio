# Dónde retomar

**Documento vivo.** Cada agente lo actualiza al cerrar su turno. Si contradice a otro documento, gana la bitácora `.memory/log.md` — pero entonces alguien tiene que arreglar este archivo.

**Última actualización:** 2026-09-27, dictamen FAIL del Capitán en optimización post-MVP (turno T27), agente Ani Arquitecta (Tech Lead).

---

## 🚦 Estado: etapas 1 a 6 cerradas. Etapa 7 completada y MVP formalmente CERRADO (v0.1.0-mvp) con PASS formal del Capitán. Intento de optimización post-MVP (rendimiento y maquillaje): ❌ RECHAZADO / DICTAMEN FAIL FORMAL DEL CAPITÁN. NO APROBADO.

### 🛑 Dictamen Textual del Capitán (T27):
> *"declaro fail, el rendimiento es bajo. se sigue trabando, las maquillaje no se aprecian. declara el fail en la docummentación y en donde consideres asi no se cree que esta aprobado, luego convoca a investigadora, y que investigue como es el estandar de la industria, y como manejan este tipo de herramientas"*

**Veredicto del Fundador:**
- **El rendimiento sigue siendo bajo:** los cálculos y recálculos siguen demandando tiempo excesivo.
- **Se sigue trabando:** la interfaz de usuario se congela y sufre tirones perceptibles durante el ajuste interactivo de controles.
- **El maquillaje no se aprecia:** las mitigaciones visuales (badge "⏳ Actualizando...", cursor de espera y retención de frame previo) no compensan la lentitud subyacente ni se aprecian de forma efectiva en el uso real.
- **Estado formal:** La entrega técnica de rendimiento y UX post-MVP (T25-T26) queda formalmente en estado **FAIL** y **NO ESTÁ APROBADA**.

La aplicación conserva el MVP de línea base (v0.1.0-mvp) con reproducción sincronizada, y el código de T25-T26 activo pero calificado como FAIL por el Fundador:
- **Caché PCM en memoria (`tools/visualizador/analisis.py`):** Indexada por ruta y mtime (recuperación en 0.25 ms sin llamadas a FFmpeg en recálculo).
- **Worker thread asíncrono con cola Last-Write-Wins (`tools/visualizador/gui.py`):** Desacople de cómputo en hilo secundario.
- **Debounce adaptativo por parámetro (`tools/visualizador/gui.py`):** 30 ms cosmético, 100 ms dinámica, 250 ms estructural.
- **Feedback visual y badge reactivo (`tools/visualizador/gui.py`):** Badge "⏳ Actualizando..." y cursor "watch" (insuficientes según dictamen del Capitán).
- **Preservación de fotograma previo (*Ghost Frame / Never Blank*):** Proyección por tags.
- **Reproductor de audio desacoplado:** `tools/visualizador/reproductor.py` con interfaz abstracta y backend prioritario `FFplayBackend`.
- **Transporte continuo y sincronizado en GUI:** Botón Play/Pausa y barra espaciadora.
- **Master Clock monotónico y time-delta:** Sincronización gobernada por `time.perf_counter()`.
- **Lanzador de escritorio:** `visualizador.bat` en la raíz sin consola de fondo.
- **Proyectos y presets:** `tools/visualizador/proyecto.py` con 4 presets de fábrica y `compensar_fondo`.
- **Suite de pruebas:** 331 comprobaciones automáticas pasando al 100% en verde (pruebas técnicas sintéticas válidas, pero experiencia real calificada FAIL por el Fundador).

### Lo que el fundador decidió en el punto de control y turnos previos

| Tema | Decisión del fundador |
|---|---|
| **Dictamen MVP (Etapa 7)** | ✅ **PASS formal del MVP (v0.1.0-mvp)** dictaminado por el Capitán en T22/T23 ("yo ya probe la app, y puedo dictaminar que funciona, por mi parte el dictame es PASS con respeto al MVP"). Formalizado y catalogado en T24 como v0.1.0-mvp. |
| **Rendimiento y UX Post-MVP** | ❌ **FAIL formal del Capitán (T27)** ("declaro fail, el rendimiento es bajo. se sigue trabando, las maquillaje no se aprecian... asi no se cree que esta aprobado"). La optimización y el maquillaje implementados en T25-T26 **NO ESTÁN APROBADOS**. |
| **Reproductor y Play continuo** | ✅ Solicitado en T20 y completado en T21: botón Play/Pausa, audio sincronizado y scrubbing |
| **Aspecto de barras** | ✅ Aprobado en T10: *"Sobre los estilos y variables, para esta primer version me parece bien"* |
| **Composición** | **Trama (Screen)** sobre fondo negro. Chroma Key descartado como default por limitaciones en Drift 0.6.0 |
| **Color** | Compensación matemática con `compensar_fondo` (`docs/COLOR_EN_TRAMA.md`), y preset de barras blancas inmune |
| **Puerta de entrada** | **`visualizador.bat` para el MVP** (T11). Ejecutable `.exe` con PyInstaller post-MVP |
| **Distribución** | ❌ **No es objetivo de este proyecto** (Regla 16 de la ruta) |

---

## Lo primero que tiene que hacer el próximo agente

**FASE 0 — INVESTIGACIÓN DE ESTÁNDAR DE LA INDUSTRIA (Ani Investigadora):**
Por orden taxativa del Capitán tras dictaminar FAIL en el intento de optimización local post-MVP, convocar a **Ani Investigadora** para investigar a fondo:
1. **Cómo es el estándar de la industria** en previsualización interactiva de audio-reactividad (ej. Adobe After Effects con plugins como Trapcode Sound Keys o Spectrum, DaVinci Resolve / Fairlight, Blender Audio Visualizer, TouchDesigner, Sonic Visualiser, plugins de audio VST/AU con FFT reactivo, herramientas WebGL/Shader).
2. **Cómo manejan este tipo de herramientas el render y el rendimiento:**
   - ¿Calculan la FFT bajo demanda o hacen pre-render / pre-análisis completo en caché de espectrograma?
   - ¿Usan LOD (Level of Detail) o representaciones reducidas de barras/puntos durante la interacción en tiempo real?
   - ¿Delegan la proyección a aceleración por hardware / GPU (OpenGL/DirectX/Vulkan) en vez de Canvas por software en CPU (Tkinter)?
   - ¿Cómo sincronizan el audio continuo con el timeline sin tirones ni latencias perceptibles?
3. Generar un informe durable de investigación técnica en `.memory/wiki/Investigacion_estandar_industria_audio_reactividad.md` para fundamentar la futura re-arquitectura del motor visual.

---

## Probarlo ahora mismo

```powershell
# 1. Abrir la interfaz gráfica interactiva (doble clic o desde terminal):
.\visualizador.bat

# 2. Consultar estilos, presets y parámetros por CLI:
.\visualizador.bat --listar

# 3. Exportar un video directamente por CLI:
.\visualizador.bat tests\fixtures\pista_espectro.wav -o build\prueba.webm --preset barras_neon

# 4. Correr la suite completa de pruebas (331 comprobaciones):
python tests\test_analisis.py
python tests\test_render.py --export
python tests\verificar_sincronia.py
python tests\test_proyecto.py
python tests\test_lanzador.py
python tests\test_reproductor.py
python tests\test_gui.py
```

---

## Organización del código y documentación

| Documento | Contenido |
|---|---|
| [`docs/GUIA_DE_USO.md`](docs/GUIA_DE_USO.md) | Guía de uso completa para el usuario final (lanzador, GUI, Drift) |
| [`docs/COMO_USAR.md`](docs/COMO_USAR.md) | Referencia paso a paso de uso y composición |
| [`docs/RUTA_DE_TRABAJO.md`](docs/RUTA_DE_TRABAJO.md) | Tabla de etapas, criterios de salida y reglas de trabajo |
| [`docs/MVP.md`](docs/MVP.md) | Especificación y criterios de aceptación del MVP |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Contratos de código y desacoplamiento de componentes |
| [`docs/COLOR_EN_TRAMA.md`](docs/COLOR_EN_TRAMA.md) | Fundamentos matemáticos y mediciones de la fusión Trama |

---

## Datos operativos verificados

- **Drift:** `C:\Program Files\Drift\drift.exe`, versión 0.6.0 — **sólo lectura**.
- **FFmpeg:** `C:\ffmpeg\bin\ffmpeg.exe` 8.0.1 en PATH.
- **Python:** 3.14.6 con `pythonw.exe`, `python.exe` y `py.exe` en PATH.
- **Lanzador:** `visualizador.bat` probado con espacios y rutas absolutas.
