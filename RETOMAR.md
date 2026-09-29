# Dónde retomar

**Documento vivo.** Cada agente lo actualiza al cerrar su turno. Si contradice a otro documento, gana la bitácora `.memory/log.md` — pero entonces alguien tiene que arreglar este archivo.

**Última actualización:** 2026-09-29, Plan de Publicación en GitHub bajo Licencia No Comercial (Turno T46), agente Ani Arquitecta.

---

## 🚦 Estado: etapas 1 a 6 cerradas. Etapa 7 completada y MVP formalmente CERRADO (v0.1.0-mvp). Identidad Visual "Visual Audio" y Salto Visual Dark Zinc COMPLETADOS Y CERTIFICADOS CON PASS POR QA (Turnos T44 y T45, 462 comprobaciones en verde).
### 🎯 Ciclo Core Activo: Fase 1 (Triage & Plan) de Publicación en GitHub bajo Licencia No Comercial COMPLETADA (Turno T46). En espera del Gate de Aprobación del Capitán.

### 📦 Plan Rector de Publicación en GitHub bajo Licencia No Comercial Entregado (T46)
- **Documento rector:** `implementation_plan.md` y handoff `T46_plan_publicacion_github_licencia_nocomercial_20260929.md`.
- **Marco legal:** Adopción formal de **PolyForm Noncommercial License 1.0.0** (`LICENSE`) con preámbulo *Creator-Friendly Clarification* (uso 100% libre y gratuito para músicos y creadores de video en redes; prohibición taxativa de venta del software o integración como complemento de productos comerciales).
- **Vitrina pública:** Rediseño completo de `README.md` público (encabezado con logo y badges, propuesta de valor, galería de capturas de pantalla, guía de instalación paso a paso en Windows con Python/FFmpeg/pip, comandos de arranque GUI y CLI, y flujo de composición en Drift en modo Trama).
- **Empaquetado y distribución:** Formalización de `requirements.txt` (`numpy>=1.24.0`, `pillow>=10.0.0`, `scipy>=1.10.0`) y `pyproject.toml` (PEP 517/621).
- **Galería oficial de screenshots:** Estrategia para generar y almacenar en `assets/screenshots/` capturas en alta fidelidad de la GUI con los 3 estilos (`barras`, `onda`, `espejadas`) y tema Dark Zinc.
- **Higiene:** Cero rutas locales absolutas y `.gitignore` optimizado para GitHub.
- **Estado de código:** Cero líneas de producto modificadas en este turno (respeto estricto a la frontera de Fase 1).

### 🎨 Modernización de UI y Salto Visual "Visual Audio" Implementados y Certificados (T44 y T45)
- **Implementación (T44 - Ani Frontend):** `tools/visualizador/gui.py` con tokens `TOKENS_DISENO` (Dark Zinc 950/900/800), conmutación a tema ttk `'clam'`, iconos oficiales (`visual_audio.ico` e `visual_audio_512.png`), título formal "Visual Audio", transporte DAW (Play cian, Consolas monoespaciada) y frame swap $O(1)$ en canvas.
- **Auditoría Formal de QA (T45 - Ani Mal Humor):** **PASS** rotundo certificado sobre los criterios CA-IDENT-1 a CA-IDENT-6 (contraste WCAG AAA/AA verificado, Viewport LOD en 8.65 ms, suite completa de 462 comprobaciones automáticas en verde). Handoff: `.memory/handoffs/T45_qa_auditoria_identidad_visual_audio_20260928.md`.

### 🎨 Identidad Gráfica y Assets de Marca Entregados: "Visual Audio" (T42)
- **Directiva de marca:** Nombre oficial "Visual Audio". 100% código paramétrico (cero IA).
- **SVG maestro vectorial:** `assets/logo/visual_audio_logo.svg` (512x512, squircle zinc-900/950, barras estéreo simétricas y onda fluida en cian `#06b6d4` a violeta `#8b5cf6`).
- **Animación interactiva HyperFrames:** `assets/logo/preview_animacion.html` (composición determinista GSAP con timeline de 6.00s, scrubber en tiempo real, velocidad 0.5x..2.0x, bucle y navegación por teclado).
- **Iconos compilados:** `assets/logo/visual_audio_512.png` y `assets/logo/visual_audio.ico` (multi-resolución Windows: 16x16 a 256x256) generados con `assets/logo/compilar_iconos.py`.

### ⚖️ Decisión y Mandato del Capitán: Publicación en GitHub bajo Licencia No Comercial
- **Instrucción textual del Capitán:** *"quedo muy bien. arme todo para publicar en github de manera publica, descripcion, instalación, capturas. licencia libre de uso, siempre y cuiando no se venda el software o se use como complemento de un producto comercial"*.
- **Resolución de arquitectura (T46):** Planificada la publicación con PolyForm Noncommercial 1.0.0, vitrina pública de primer nivel y distribución limpia sin ataduras a rutas privadas.

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
13. **Fase 2 Ejecución Técnica (T42, Ani Frontend):** Creación de la identidad visual de marca "Visual Audio": logo SVG paramétrico (`visual_audio_logo.svg`), animación HyperFrames GSAP interactiva (`preview_animacion.html`) e iconos compilados (`visual_audio.ico` y `visual_audio_512.png`). Suite integral con 415 comprobaciones al 100% en verde. Handoff: `T42_diseno_logo_vectorial_animacion_visual_audio_20260927.md`.
14. **Fase 1 Triage & Plan (T43, Ani Arquitecta):** Plan estructurado de modernización de UI y salto visual en `implementation_plan.md`: tokens Dark Zinc 950/900/800 + Cian/Violeta, tema `'clam'` en `ttk.Style` para sobreescribir uxtheme de Windows, vinculación de icono y título formal "Visual Audio", transporte DAW con tipografía monoespaciada Consolas y presupuesto de 60 fps intacto. Handoff: `T43_plan_redisenio_identidad_visual_audio_20260927.md`.
15. **Fase 2 Ejecución Técnica (T44, Ani Frontend):** Implementación de tokens de diseño `TOKENS_DISENO`, estilos ttk 'clam', iconos oficiales, styling DAW y frame swap $O(1)$ en `gui.py` y `test_gui.py`. 462 comprobaciones en verde. Handoff: `T44_ejecucion_frontend_salto_visual_audio_20260928.md`.
16. **Fase 3 QA & Auditoría de Cumplimiento (T45, Ani Mal Humor):** Certificación formal de veredicto PASS sobre CA-IDENT-1 a CA-IDENT-6 (contraste WCAG AAA/AA, Viewport LOD 8.65 ms, 462/462 checks en verde). Handoff: `T45_qa_auditoria_identidad_visual_audio_20260928.md`.
17. **Fase 1 Triage & Plan de Publicación en GitHub (T46, Ani Arquitecta):** Plan rector de publicación en GitHub bajo PolyForm Noncommercial 1.0.0, vitrina pública de `README.md`, empaquetado (`requirements.txt`, `pyproject.toml`) y capturas de pantalla de la GUI oficial. Handoff: `T46_plan_publicacion_github_licencia_nocomercial_20260929.md`.

---

## Lo primero que tiene que hacer el próximo agente

Nos encontramos en el **🚦 GATE DEL CAPITÁN** del ciclo de trabajo del Escuadrón Ani.

1. **Ani Recepcionista:** Presentar el plan estructurado `implementation_plan.md` al Capitán y aguardar su aprobación explícita ("procede" o "apruebo"). **Nadie ejecuta en producción ni publica hasta su aprobación formal.**
2. **Con el plan aprobado por el Capitán (Fase 2):** Ani Recepcionista derivará la ejecución técnica:
   - **Ani Escritora / Ani Frontend:** Redacción de `LICENSE` (PolyForm Noncommercial 1.0.0 + preámbulo para creadores) y el nuevo `README.md` público.
   - **Ani Programadora:** Generación de `requirements.txt` y `pyproject.toml`.
   - **Ani Frontend:** Generación de capturas de pantalla de la GUI oficial en `assets/screenshots/`.
   - **Ani DevOps:** Verificación de `.gitignore` para GitHub y ejecución limpia de la suite.
3. **Fase 3 (QA):** Ani Recepcionista derivará a **Ani Mal Humor** para auditar en disco los criterios falsables CA-PUB-1 a CA-PUB-7.
4. Mantener la suite consolidada de 462 comprobaciones al 100% en verde.


---

## Probarlo ahora mismo

```powershell
# 1. Abrir la animación interactiva HyperFrames del logo en el navegador:
Start-Process assets\logo\preview_animacion.html

# 2. Recompilar los assets de icono (visual_audio.ico y visual_audio_512.png):
python assets\logo\compilar_iconos.py

# 3. Abrir la interfaz gráfica interactiva (doble clic o desde terminal):
.\visualizador.bat

# 4. Consultar estilos, presets y parámetros por CLI:
.\visualizador.bat --listar

# 5. Exportar un video directamente por CLI:
.\visualizador.bat tests\fixtures\pista_espectro.wav -o build\prueba.webm --preset barras_neon

# 6. Correr la suite completa de pruebas consolidadas (462 comprobaciones en verde):
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
