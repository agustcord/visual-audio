# Dónde retomar

**Documento vivo.** Cada agente lo actualiza al cerrar su turno. Si contradice a otro documento, gana la bitácora `.memory/log.md` — pero entonces alguien tiene que arreglar este archivo.

**Última actualización:** 2026-09-27, Consolidación de Selector de Color de Barras y Ondas y Suite de 407 Tests (Turno T41), agente Ani Programadora.

---

## 🚦 Estado: etapas 1 a 6 cerradas. Etapa 7 completada y MVP formalmente CERRADO (v0.1.0-mvp). Re-arquitectura de Rendimiento: PASS ROTUNDO. Corrección de Selector de Color en GUI: CERTIFICADA CON PASS DE QA (Ani Mal Humor) Y CONSOLIDADA. Suite integral al 100% en verde (407 comprobaciones automáticas, 0 fallas, exit code 0).
### 🎯 Ciclo Core Activo: Consolidación Final y Cierre de Sesión completados tras dictamen PASS de QA en T41.

### ⚖️ Decisión y Pendiente Estratégico: Publicación en GitHub bajo Licencia No Comercial
- **Instrucción textual del Capitán:** *"Ok, entonces lo publiqueremos en github pero solo para uso no comercial, es decir nadie puede vender o integrarlo en un producto comercial. si puede usarlo de forma gratuita. Declara eso un pendiente"*.
- **Catalogación:** Pendiente estratégico para la fase de distribución pública. Se publicará bajo licencia restrictiva no comercial (ej. PolyForm Noncommercial 1.0.0 o CC BY-NC 4.0), habilitando el uso libre y 100% gratuito para personas creadoras, músicos y editores de video, pero prohibiendo expresamente su venta o integración en software privativo/comercial.

### 🎨 Corrección Implementada: Selector de Color de Barras y Ondas en GUI
- **Solución implementada:** En `tools/visualizador/gui.py:535-555`, `_elegir_color` desempaca con seguridad `resultado[1]` de `colorchooser.askcolor(color=actual, parent=self.root, title=f"Elegir {nombre}")`, descarta limpiamente cancelaciones (`None`), actualiza la muestra visual con contraste dinámico (`_actualizar_muestra_color`) y notifica reactividad con debounce cosmético de 30 ms vía `_al_modificar_parametro(nombre, es_cosmetico=True)`.
- **Pruebas añadidas:** Función `probar_selector_color_barras_y_ondas` en `tests/test_gui.py` con 19 comprobaciones automáticas pasando al 100% (CA-COLOR-1 a CA-COLOR-5).
- **Dictamen Formal de QA (Ani Mal Humor):** **PASS** certificado tras auditar en disco la resolución de los criterios CA-COLOR-1 a CA-COLOR-5 y certificar la suite integral de 407 comprobaciones en verde.

---

### 🏆 Dictamen y Cierre de Versión Previa (PASS Rotundo de Re-arquitectura)
- **Veredicto del Fundador / Capitán:** *"mientras mal humor da su revision. Yo ya hice la mia. por mi parte doy un pass! asi que si qa da pass, el veredicto es un pass rotundo"*.
- **Veredicto Formal de QA (Ani Mal Humor):** **PASS** certificado tras verificar la resolución de los criterios CA-REARQ-1 a CA-REARQ-6 y CA-ESTAB-1 a CA-ESTAB-4.
- **Determinismo Absoluto Certificado:**
  - `tests/test_gui.py`: **147 comprobaciones automáticas** pasando al 100% en verde con exit code 0.
  - `tests/test_bake.py`: **45 comprobaciones automáticas** pasando al 100% en verde (medianas de ~32 ms contra umbral $\le 100$ ms y 0 llamadas a FFmpeg).
- **Rendimiento de Cómputo y Suavizado:** Aceleración a **2,65 ms** en el suavizado temporal vectorizado con `scipy.signal.lfilter` (18,1x aceleración vs bucle secuencial), proyección espectral de bandas en **6,77 ms** ($\le 15$ ms) y recálculo dinámico en **3,44 ms** ($\le 5$ ms) sobre 10.800 cuadros (3 min @ 60 fps).
- **Renderizado Interactivo Viewport LOD:** Rendimiento de render Pillow directo a canvas en **7,62 ms** (capacidad $\ge 100$ FPS), mediana en **7,57 ms**, $p95 = 10,37$ ms y latencia de scrubbing en **6,48 ms** a 60 fps estables.

---

### 🚀 Resumen del Avance de la Re-arquitectura de Rendimiento (`implementation_plan.md`):
1. **Fase 0 — Investigación Estándar de la Industria (T28, Ani Investigadora):** Relevamiento de 4 referentes (After Effects, DaVinci, Blender, TouchDesigner), diagnóstico de cuello de botella de FFT (1.25s) y render Pillow 1080p (61.6 ms, 16.2 FPS max). Nota: `.memory/wiki/Investigacion_estandar_industria_audio_reactividad.md`.
2. **Fase 1 — Triage y Planificación (T29, Ani Arquitecta):** Plan de Pre-Bake persistente `.driftbake.npz`, proyecciones matriciales $O(1)$, Viewport-Native LOD y presupuesto de 60 FPS. Documento: `implementation_plan.md`.
3. **Fase 2 — Ejecución Bloque 1 (T30, Ani Programadora):** Implementación de `tools/visualizador/bake.py` (hash SHA-256, `np.savez_compressed`), refactorización de `analisis.py` (`hornear_audio`, `proyectar_analisis` $O(1)$ en 4.59 ms) y `render.py` (`cuadro_viewport` en 2.33 ms). Handoff: `T30_motor_audio_bake_proyeccion_lod_20260927.md`.
4. **Fase 2 — Ejecución Bloque 2 (T31, Ani Frontend):** Integración completa en `tools/visualizador/gui.py` y `tests/test_gui.py`: Pre-Bake, Viewport LOD directo en Canvas, invarianza estructural (MVP-5), sliders $O(1)$, scrubbing a 60 fps y ciclo de vida limpio. Handoff: `T31_integracion_gui_viewport_lod_60fps_20260927.md`.
5. **Fase 5 — Plan de Corrección tras QA FAIL (T32, Ani Arquitecta):** Plan de vectorización IIR con SciPy y estabilización contractual de UI. Handoff: `T32_plan_correccion_suavizado_vectorizado_20260927.md`.
6. **Fase 5 — Corrección Bloque 1 (T34, Ani Programadora):** Vectorización con `scipy.signal.lfilter` continuo (2,65 ms, 18,1x aceleración), proyección en 6,77 ms ($\le 15$ ms) y dinámica en 3,44 ms ($\le 5$ ms) sobre 10.800 cuadros (3 min @ 60 fps). Aserción formal y benchmark explícito en `test_bake.py`. Handoff: `T34_correccion_suavizado_vectorizado_20260927.md`.
7. **Fase 5 — Corrección Bloque 2 (T35, Ani Frontend):** Armonización de `tests/test_gui.py` con CA-REARQ-4 ($\le 10,0\text{ ms}$, medido 8,72 ms), warmup anti-jitter de 4 cuadros no cronometrados, evaluación estadística con mediana de ventanas de 10 cuadros ($\le 10,0\text{ ms}$, medido 8,96 ms) y tolerancia p95 $\le 16,6\text{ ms}$ (11,84 ms) / cota $\le 25,0\text{ ms}$ (12,78 ms). Handoff: `T35_armonizacion_test_gui_lod_20260927.md`.
8. **Fase 5 — Estabilización Determinista Bloques A y B (T36, T37, T38, Ani Arquitecta, Ani Frontend, Ani Programadora):** Erradicación de condición de carrera en timer de gracia de 80 ms (`gui.py` / `test_gui.py`) y aislamiento de escaneo en frío de Windows Defender mediante warmup de FS y evaluación de mediana en 3 lecturas (`test_bake.py`). Certificación de 10/10 deterministas en ambas suites. Handoffs: `T36_plan_correccion_estabilidad_tests_20260927.md`, `T37_correccion_frontend_estabilidad_timer_20260927.md`, `T38_correccion_programadora_estabilidad_bake_20260927.md`.
9. **Cierre y Consolidación (T39, Ani Programadora):** Formalización de PASS rotundo, actualización canónica y commit consolidado en Git con working tree clean.
10. **Fase 1 Triage & Plan (T40, Ani Arquitecta):** Registro formal del pendiente de publicación bajo licencia no comercial en GitHub, aislamiento de causa raíz del bug de selección de color en `gui.py:537`, redacción de `implementation_plan.md` y handoff `T40_triage_publicacion_nocomercial_y_fix_color_barras_20260927.md`.
11. **Fase 2 Ejecución Técnica (T41, Ani Frontend):** Corrección de `_elegir_color` en `gui.py`, reactividad cosmética de 30 ms con `_al_modificar_parametro`, adición de pruebas `probar_selector_color_barras_y_ondas` en `test_gui.py`, y certificación de suite total con 407 checks en verde (exit code 0). Handoff: `T41_correccion_selector_color_barras_20260927.md`.
12. **Fase 3 QA & Consolidación Final (T41, Ani Mal Humor / Ani Programadora):** Auditoría en disco de los criterios CA-COLOR-1 a CA-COLOR-5 con dictamen PASS emitido por Ani Mal Humor, formalización en `RETOMAR.md` y consolidación atómica en Git.

---

## Lo primero que tiene que hacer el próximo agente

El ciclo de corrección del selector de color de barras y ondas y el registro del pendiente estratégico de publicación no comercial han concluido exitosamente con dictamen **PASS** de QA y consolidación atómica en Git (407 comprobaciones automáticas al 100% en verde, exit code 0, working tree limpio).

El próximo agente debe:
1. Atender la siguiente prioridad o directiva funcional que indique el Capitán (ej. abordar la redacción de `LICENSE.md` / `README.md` bajo licencia no comercial cuando se prepare la distribución pública en GitHub, o nuevas características en la etapa 7 de validación / post-MVP).
2. Mantener la suite integral de 407 comprobaciones en verde ante cualquier nuevo cambio.


---

## Probarlo ahora mismo

```powershell
# 1. Abrir la interfaz gráfica interactiva (doble clic o desde terminal):
.\visualizador.bat

# 2. Consultar estilos, presets y parámetros por CLI:
.\visualizador.bat --listar

# 3. Exportar un video directamente por CLI:
.\visualizador.bat tests\fixtures\pista_espectro.wav -o build\prueba.webm --preset barras_neon

# 4. Correr la suite completa de pruebas consolidadas (407 comprobaciones en verde):
python -m tests.test_bake
python -m tests.test_analisis
python -m tests.test_render --export
python -m tests.test_proyecto
python -m tests.test_reproductor
python -m tests.test_lanzador
python -m tests.verificar_sincronia
python -m tests.test_gui
```

---

## Organización del código y documentación

| Documento | Contenido |
|---|---|
| [`implementation_plan.md`](implementation_plan.md) | Plan canónico de re-arquitectura de rendimiento (Pre-Bake y LOD) |
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
- **NumPy:** 2.5.1 en entorno activo.
- **Pillow:** 12.3.0 en entorno activo.
- **SciPy:** 1.18.0 en entorno activo (utilizado para filtrado vectorizado IIR `lfilter`).
- **Lanzador:** `visualizador.bat` probado con espacios y rutas absolutas.
