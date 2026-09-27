# Handoff Triage — Etapa 7: Plan de Reproducción de Audio Sincronizada y Control Play/Pausa en la GUI

- **Fecha:** 2026-09-26
- **Turno:** T20 (Triage de Fase 1)
- **Agente:** Ani Arquitecta (Tech Lead)
- **Fase del Ciclo Core:** 1 (Triage & Planificación)
- **Rama:** `master`
- **Estado de Pruebas:** 213 comprobaciones en verde en la línea base (0 fallas, 0 regresiones).
- **Entregables:** `implementation_plan.md` y este handoff durable.

---

## 1. Pedido Original del Capitán (textual)
> "la app no tiene un boton de play, solo un muestro de 2 segundo. tambien debería tener un reproductor, para saber si las ondas que generan me gusta como encaja con el sonido"

---

## 2. Resumen Ejecutivo del Triage Técnico
1. **Problema Diagnosticado:**
   La barra de transporte actual de `tools/visualizador/gui.py` cuenta únicamente con el botón `▶ Fragmento (2s)` que avanza 60 cuadros a 30 fps de forma puramente visual y muda, sin emitir audio. Esto impide al fundador calibrar el encaje rítmico y estético de las ondas con la música.

2. **Dictamen de Razonamiento Profundo (Ani Pensadora):**
   - Se convocó a Ani Pensadora en Fase 0 (`.memory/handoffs/pensadora_20260926_reproductor_audio.md`).
   - Se descartó `winsound` por falta de seek y soporte exclusivo de WAV.
   - Se evaluó empíricamente Windows MCI (`winmm.dll`): reproduce WAV/MP3 pero falla con código 263 ante FLAC/OGG.
   - Se ratificó el uso prioritario de `ffplay.exe` (verificado en `C:\ffmpeg\bin\ffplay.exe`) con flags silenciosos `-nodisp -autoexit -ss <offset> -loglevel quiet` y `creationflags=subprocess.CREATE_NO_WINDOW`, preservando al 100% la Regla 13 (cero dependencias externas adicionales en Python).
   - Se determinó que el **Master Clock** debe ser un reloj monotónico sintético de alta precisión (`time.perf_counter()`) coordinado con el audio backend, aplicando time-delta con frame-skipping automático para erradicar cualquier deriva temporal (*drift*) en el event loop de Tkinter.
   - Se diseñó el aislamiento del scrubbing con el slider (`<ButtonPress-1>`, `<B1-Motion>`, `<ButtonRelease-1>`) para actualizar el fotograma visual durante el arrastre sin saturar el sistema operativo con llamadas de subproceso.
   - Se especificó la captura del protocolo `WM_DELETE_WINDOW` y el registro de `atexit.register` para evitar procesos huérfanos o zombis.

3. **Arquitectura y Tareas Desglosadas:**
   - **Tarea 1:** Módulo desacoplado `tools/visualizador/reproductor.py` con interfaz abstracta `ReproductorAudio`, backend prioritario `FFplayBackend`, y fallbacks `MCIBackend` y `NullBackend`.
   - **Tarea 2:** Reemplazo de `btn_animar` por `btn_play_pausa` ("▶ Play" / "⏸ Pausa"), atajo de barra espaciadora (`<space>`), bucle de sincronización con time-delta y control de scrubbing en `tools/visualizador/gui.py`.
   - **Tarea 3:** Suite de pruebas automatizadas `tests/test_reproductor.py` y ampliación de `tests/test_gui.py` con 7 criterios de aceptación falsables (CA-1 a CA-7).
   - **Tarea 4:** Actualización de documentación de usuario (`docs/GUIA_DE_USO.md`, `docs/COMO_USAR.md`, `README.md`, `RETOMAR.md`, `docs/RUTA_DE_TRABAJO.md`).

4. **Asignación de Roles:**
   - Ejecución técnica: Ani Programadora.
   - Auditoría y QA: Ani Mal Humor.
   - Triage y Tech Lead: Ani Arquitecta.

5. **Regla SMF y Cero Modificaciones en Turno 1:**
   No se modificó ninguna línea de código de producto en este turno. El plan queda a la espera del Gate de aprobación del Capitán.
