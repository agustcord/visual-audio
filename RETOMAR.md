# Dónde retomar

**Documento vivo.** Cada agente lo actualiza al cerrar su turno. Si contradice a otro documento, gana la bitácora `.memory/log.md` — pero entonces alguien tiene que arreglar este archivo.

**Última actualización:** 2026-09-27, consolidación post-MVP (turnos T25-T26), agente Ani Programadora (Core Logic Multilenguaje).

---

## 🚦 Estado: etapas 1 a 6 cerradas. Etapa 7 completada y MVP formalmente CERRADO (v0.1.0-mvp) con PASS formal del Capitán. Optimizaciones de rendimiento y UX post-MVP completadas (T25-T26). 331 comprobaciones automáticas pasando al 100% en verde.

La aplicación cuenta con reproducción de audio sincronizada, controles de transporte interactivos y optimizaciones de rendimiento/UX post-MVP:
- **Caché PCM en memoria (`tools/visualizador/analisis.py`):** Indexada por ruta y mtime, elimina el 100% de llamadas redundantes a FFmpeg al modificar sliders o parámetros tras la carga inicial (CA-POST-2, recuperación en 0.25 ms).
- **Worker thread asíncrono con cola Last-Write-Wins (`tools/visualizador/gui.py`):** Desacopla íntegramente el cómputo pesado de `analizar()` y `Render.cuadro(i)` del hilo principal de Tkinter. En ráfagas de cambios rápidos procesa a lo sumo 2 tareas y descarta automáticamente las intermedias obsoletas (CA-POST-1 y CA-POST-3, latencia en hilo de UI <= 16 ms).
- **Debounce adaptativo por parámetro (`tools/visualizador/gui.py`):** 30 ms para ajustes cosméticos/render, 100 ms para ganancia/dinámica y 250 ms para alteraciones analíticas estructurales, manteniendo actualización instantánea (0 ms) de los displays numéricos adyacentes a cada slider bajo el ratón (CA-POST-5).
- **Feedback visual y badge reactivo (`tools/visualizador/gui.py`):** Widget `_badge_actualizando` ("⏳ Actualizando...") con tokens accesibles (15.9:1 de contraste), temporizador de gracia de 80 ms para evitar parpadeos en operaciones rápidas, y cursor inteligente `"watch"` durante cálculos pesados (CA-POST-4).
- **Preservación de fotograma previo (*Ghost Frame / Never Blank*):** Proyección atómica en canvas mediante tags; el visor nunca parpadea a negro durante los recálculos en segundo plano (CA-POST-5).
- **Reproductor de audio desacoplado:** `tools/visualizador/reproductor.py` con interfaz abstracta `ReproductorAudio`, backend prioritario universal `FFplayBackend` (`ffplay.exe` silencioso con flags `-nodisp -autoexit -ss <offset> -loglevel quiet` y `CREATE_NO_WINDOW`), fallback `MCIBackend` (Windows winmm.dll) y `NullBackend` (testing desatendido y modo seguro sin sonido).
- **Transporte continuo y sincronizado en GUI:** Botón toggle `"▶ Reproducir"` / `"⏸ Pausar"` y atajo con la barra espaciadora (`<space>`).
- **Master Clock monotónico y time-delta:** Sincronización audiovisual gobernada por `time.perf_counter()` con frame-skipping automático para erradicar cualquier deriva temporal acumulativa (deriva < 33 ms).
- **Scrubbing interactivo del slider:** Pausa y aísla el audio durante el arrastre manual con el mouse para evitar saturar el sistema operativo, actualizando en tiempo real la proyección gráfica y reanudando la pista en el offset exacto al soltar el mouse.
- **Prevención de procesos zombis:** Detención determinista al cambiar de audio, proyecto, preset, exportar o cerrar la ventana (`WM_DELETE_WINDOW` y hook `atexit`).
- **Lanzador de escritorio:** `visualizador.bat` en la raíz ejecuta la aplicación mediante `pythonw.exe` sin dejar consola negra de fondo en Windows.
- **Proyectos y presets:** `tools/visualizador/proyecto.py` con 4 presets de fábrica en `presets/` y compensación matemática `compensar_fondo` para fidelidad de color en modo Trama.
- **Suite de pruebas completa:** 331 comprobaciones automáticas pasando al 100% en verde con 0 fallas y 0 regresiones.

### Lo que el fundador decidió en el punto de control y turnos previos

| Tema | Decisión del fundador |
|---|---|
| **Dictamen MVP (Etapa 7)** | ✅ **PASS formal del MVP (v0.1.0-mvp)** dictaminado por el Capitán en T22/T23 ("yo ya probe la app, y puedo dictaminar que funciona, por mi parte el dictame es PASS con respeto al MVP"). Formalizado y catalogado en T24 como v0.1.0-mvp. |
| **Rendimiento y UX Post-MVP** | ✅ Solicitado por el Capitán tras el cierre del MVP ("La primera, es el rendimiento... o como 'maquillar' esta sensacion de que se rompio, para que el programa sea mas amigable con el usuario"). Completado en T25 (Bloque A) y T26 (Bloque B) con dictamen PASS en Fase 3 QA. |
| **Reproductor y Play continuo** | ✅ Solicitado en T20 y completado en T21: botón Play/Pausa, audio sincronizado y scrubbing |
| **Aspecto de barras** | ✅ Aprobado en T10: *"Sobre los estilos y variables, para esta primer version me parece bien"* |
| **Composición** | **Trama (Screen)** sobre fondo negro. Chroma Key descartado como default por limitaciones en Drift 0.6.0 |
| **Color** | Compensación matemática con `compensar_fondo` (`docs/COLOR_EN_TRAMA.md`), y preset de barras blancas inmune |
| **Puerta de entrada** | **`visualizador.bat` para el MVP** (T11). Ejecutable `.exe` con PyInstaller post-MVP |
| **Distribución** | ❌ **No es objetivo de este proyecto** (Regla 16 de la ruta) |

---

## Lo primero que tiene que hacer el próximo agente

**Ciclo actual cerrado con éxito y suite en verde (331 comprobaciones):**
- El MVP `v0.1.0-mvp` cuenta con dictamen PASS formal del Capitán.
- El ciclo de optimización de rendimiento post-MVP (T25: Worker thread, caché PCM, debounce adaptativo) y maquillaje UX (T26: Badge visual "⏳ Actualizando...", cursor inteligente, ghost frame y displays a 60 fps) está 100% implementado, verificado y auditado por Ani Mal Humor en QA (Fase 3).
- **Próximos pasos a definir por el Capitán:** Consultar al Capitán qué rumbo desea priorizar a continuación (e.g. empaquetado `.exe` con PyInstaller, nuevos estilos como espectro circular, o integración con futuras versiones de Drift).

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
