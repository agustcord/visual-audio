# Dónde retomar

**Documento vivo.** Cada agente lo actualiza al cerrar su turno. Si contradice a otro documento, gana la bitácora `.memory/log.md` — pero entonces alguien tiene que arreglar este archivo.

**Última actualización:** 2026-09-26, turno T24, agente Ani Arquitecta (Fase 1 Triage / Cierre de MVP v0.1.0-mvp & Roadmap Post-MVP).

---

## 🚦 Estado: etapas 1 a 6 cerradas. Etapa 7 completada y MVP formalmente CERRADO (v0.1.0-mvp) con PASS formal del Capitán. 277 comprobaciones automáticas pasando al 100% en verde.

La aplicación cuenta con reproducción de audio sincronizada y controles de transporte interactivos:
- **Reproductor de audio desacoplado:** `tools/visualizador/reproductor.py` con interfaz abstracta `ReproductorAudio`, backend prioritario universal `FFplayBackend` (`ffplay.exe` silencioso con flags `-nodisp -autoexit -ss <offset> -loglevel quiet` y `CREATE_NO_WINDOW`), fallback `MCIBackend` (Windows winmm.dll) y `NullBackend` (testing desatendido y modo seguro sin sonido).
- **Transporte continuo y sincronizado en GUI:** Botón toggle `"▶ Reproducir"` / `"⏸ Pausar"` y atajo con la barra espaciadora (`<space>`).
- **Master Clock monotónico y time-delta:** Sincronización audiovisual gobernada por `time.perf_counter()` con frame-skipping automático para erradicar cualquier deriva temporal acumulativa (deriva < 33 ms).
- **Scrubbing interactivo del slider:** Pausa y aísla el audio durante el arrastre manual con el mouse para evitar saturar el sistema operativo, actualizando en tiempo real la proyección gráfica y reanudando la pista en el offset exacto al soltar el mouse.
- **Prevención de procesos zombis:** Detención determinista al cambiar de audio, proyecto, preset, exportar o cerrar la ventana (`WM_DELETE_WINDOW` y hook `atexit`).
- **Lanzador de escritorio:** `visualizador.bat` en la raíz ejecuta la aplicación mediante `pythonw.exe` sin dejar consola negra de fondo en Windows.
- **Proyectos y presets:** `tools/visualizador/proyecto.py` con 4 presets de fábrica en `presets/` y compensación matemática `compensar_fondo` para fidelidad de color en modo Trama.
- **Suite de pruebas completa:** 277 comprobaciones automáticas pasando al 100% en verde con 0 fallas y 0 regresiones.

### Lo que el fundador decidió en el punto de control y turnos previos

| Tema | Decisión del fundador |
|---|---|
| **Dictamen MVP (Etapa 7)** | ✅ **PASS formal del MVP (v0.1.0-mvp)** dictaminado por el Capitán en T22/T23 ("yo ya probe la app, y puedo dictaminar que funciona, por mi parte el dictame es PASS con respeto al MVP"). Formalizado y catalogado en T24 como v0.1.0-mvp con 277 comprobaciones automáticas. Apertura prioritaria de optimización de rendimiento y UX post-MVP. |
| **Reproductor y Play continuo** | ✅ Solicitado en T20 y completado en T21: botón Play/Pausa, audio sincronizado y scrubbing |
| **Aspecto de barras** | ✅ Aprobado en T10: *"Sobre los estilos y variables, para esta primer version me parece bien"* |
| **Composición** | **Trama (Screen)** sobre fondo negro. Chroma Key descartado como default por limitaciones en Drift 0.6.0 |
| **Color** | Compensación matemática con `compensar_fondo` (`docs/COLOR_EN_TRAMA.md`), y preset de barras blancas inmune |
| **Puerta de entrada** | **`visualizador.bat` para el MVP** (T11). Ejecutable `.exe` con PyInstaller post-MVP |
| **Distribución** | ❌ **No es objetivo de este proyecto** (Regla 16 de la ruta) |

---

## Lo primero que tiene que hacer el próximo agente

**Aprobación del Gate del Capitán & Ejecución del Roadmap Post-MVP:**
- Presentar al Capitán el `implementation_plan.md` con las optimizaciones de rendimiento y UX (desacople multihilo, jerarquía de caché FFT/PCM y feedback visual).
- Tras el Gate de aprobación del Capitán:
  1. **Ani Programadora:** Implementar worker thread en `gui.py`, jerarquía de caché en `analisis.py` / `gui.py` y debounce adaptativo por parámetro.
  2. **Ani Frontend:** Implementar overlay de actualización ("⏳ Actualizando..."), actualización inmediata de displays numéricos y cursor de espera.
  3. **Ani Mal Humor:** Auditar latencia de UI (< 16 ms), certificar ausencia de congelamientos y validar suite de 277+ comprobaciones sin regresiones.

---

## Probarlo ahora mismo

```powershell
# 1. Abrir la interfaz gráfica interactiva (doble clic o desde terminal):
.\visualizador.bat

# 2. Consultar estilos, presets y parámetros por CLI:
.\visualizador.bat --listar

# 3. Exportar un video directamente por CLI:
.\visualizador.bat tests\fixtures\pista_espectro.wav -o build\prueba.webm --preset barras_neon

# 4. Correr la suite completa de pruebas (277 comprobaciones):
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
