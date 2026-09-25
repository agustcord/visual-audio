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

## Qué debe contener un handoff

1. **Quién y cuándo.** Agente, fecha, número de turno.
2. **Frontera declarada.** Qué archivos se tocaron y, explícitamente, **qué no se tocó**. Esto es lo que permite al siguiente agente confiar en el terreno.
3. **Lo que se verificó vs. lo que se infirió.** Con el comando o la cita de archivo:línea.
4. **Decisiones tomadas y por qué.** Incluidas las que se decidió *no* tomar.
5. **Dónde retomar.** El próximo paso concreto.
6. **Lo que quedó abierto.** Preguntas al fundador, riesgos, deuda.
