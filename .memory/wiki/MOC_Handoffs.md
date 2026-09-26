---
tipo: "MOC"
estado: "activo"
relacionado: ["index"]
---

# Registro de handoffs

Índice del registro de auditoría del proyecto. Cada turno de agente deja **un** handoff acá y **una** entrada en [[log]] que lo cita.

**Ubicación única:** `.memory/handoffs/`. Si alguna nota vieja cita `handoffs/X.md` sin el prefijo `.memory/`, resolvé a `.memory/handoffs/X.md`.

**Convención de nombre:** `T<N>_<tema>_<YYYYMMDD>.md`, donde `N` es el número de turno correlativo del proyecto.

**El conteo no se tipea acá** — se deriva:

```powershell
(Get-ChildItem "$PWD\.memory\handoffs" -File -Filter *.md).Count
```

## Handoffs

| Turno | Handoff | Fecha | Qué cerró |
|---|---|---|---|
| T1 | [[T1_registro_y_viabilidad_20260925]] | 2026-09-25 | Registro del proyecto en la bóveda, `git init`, investigación de viabilidad, plan y presupuesto de la Etapa 1 (pendiente del Gate) |
| T2 | [[T2_gate_audio_y_poc_20260925]] | 2026-09-25 | Gate del fundador registrado (camino A), audio de prueba del proyecto, generador de overlay con PoC-1..3 verificados |
| T3 | [[T3_poc5_fallo_y_sincronia_20260925]] | 2026-09-25 | **PoC-5 falló** (Drift no honró el alpha). Tres hipótesis descartadas con evidencia, experimento de tres brazos preparado, desincronización de 100 ms encontrada y corregida, verificación reescrita |
| T4 | [[T4_causa_raiz_version_20260925]] | 2026-09-25 | **Causa raíz: Drift 0.6.0 no soporta canal alpha** (el soporte está en 0.7.0 sin publicar). Dos rutas que funcionan con herramientas propias de Drift, y el archivo pesa menos de la mitad |
| T5 | — *(sin handoff propio; su registro vive en `docs/DECISION_MOTOR_DE_DIBUJO.md` y en la bitácora)* | 2026-09-25 | Cuatro preguntas del fundador respondidas; PoC-5 reinterpretada (falló la redacción, no el objetivo); decisión del motor de dibujo propio planteada con evidencia comparada |
| T6 | [[T6_definicion_mvp_20260925]] | 2026-09-25 | Investigación de siete herramientas del mercado y **definición del MVP**: tres estilos, ~25 valores, interfaz de escritorio, nueve criterios falsables. Presupuesto honesto de 10 turnos, pendiente de aprobación |
| T7 | [[T7_gate2_y_ruta_de_trabajo_20260925]] | 2026-09-25 | **Gate 2**: MVP, presupuesto y resolución aprobados. Creadas la **ruta de trabajo** (siete etapas con criterios verificables, quince reglas, punto de control del fundador) y la **arquitectura** (seis contratos). El punto de entrada del proyecto pasó a ser la ruta |
| T8 | [[T8_etapa1_analisis_20260925]] | 2026-09-25 | **Etapa 1 cerrada: el análisis de audio.** 36 comprobaciones en verde. La medición del criterio 1.4 encontró un error de diseño real (densidad en vez de energía: los graves tapaban hasta 1182x y el espectro quedaba vacío arriba de 519 Hz). Ventana causal con desvío 0. Rendimiento de 14,4 s a 1,3 s |
| T9 | [[T9_etapa2_motor_y_barras_20260925]] | 2026-09-25 | **Etapa 2 cerrada en 1 de 2 turnos: motor de dibujo y Barras** (más Espejadas, que salió gratis). 19 comprobaciones en verde. Default de curva cambiado a `log` con evidencia. Rendimiento de 545 s a 250 s tras perfilar. El proyecto queda en el **punto de control del fundador** |
| T10 | [[T10_gate_aspecto_y_color_20260925]] | 2026-09-25 | **Punto de control aprobado**: aspecto y parámetros conformes, **Trama** elegida y Chroma Key descartado. El corrimiento de color de Trama medido en ΔE76 sobre 30 combinaciones: el fondo pasa **exacto**, el blanco es exacto en todo metraje, y la compensación da ΔE 0.0 sobre metraje oscuro. Se resolvió la disyuntiva 0.6 vs 0.7 sin elegir. Pendiente derivado `compensar_fondo` a la etapa 4. **Sin código de producto** |
| T11 | [[T11_como_se_abre_la_herramienta_20260925]] | 2026-09-25 | **Cómo se lanza la herramienta**, que era un punto ciego: el MVP prometía "sin programación" y no decía cómo se abre. **`.bat` en el MVP** (etapa 6, criterios 6.4 y 6.5, con `pythonw.exe` verificado en disco), **`.exe` post-MVP**, y **distribuir a terceros fuera de objetivos** como regla 16 nueva. Sin código |
| T12 | [[plan_triage_drift_plugins_20260926]] | 2026-09-26 | **Triage de Fase 1 Core**: Estado actual del proyecto verificado factual (55/55 pruebas en verde, rama master limpia), plan estructurado de la Etapa 3 (Estilo Onda) y preparación para Gate del Capitán. Sin código |

## Qué debe contener un handoff

1. **Quién y cuándo.** Agente, fecha, número de turno.
2. **Frontera declarada.** Qué archivos se tocaron y, explícitamente, **qué no se tocó**. Esto es lo que permite al siguiente agente confiar en el terreno.
3. **Lo que se verificó vs. lo que se infirió.** Con el comando o la cita de archivo:línea.
4. **Decisiones tomadas y por qué.** Incluidas las que se decidió *no* tomar.
5. **Dónde retomar.** El próximo paso concreto.
6. **Lo que quedó abierto.** Preguntas al fundador, riesgos, deuda.
