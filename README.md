# Visualizador de audio para Drift

Plugin para el editor de video **[Drift](https://github.com/CutWire-Studios/Drift)** (CutWire Studios) que dibuja la onda o el espectro del audio sobre el video, para poder seguir visualmente la pista musical. Pensado para edición de videos musicales.

Proyecto de **Jonatan Córdoba**, usuario externo de Drift — **no forma parte del equipo de CutWire Studios**.

---

## Estado

**Etapa 1, turno 1 cerrado. Investigación de viabilidad terminada. Desarrollo detenido esperando decisiones del fundador.**

El estado vivo y el próximo paso concreto están en **[`RETOMAR.md`](RETOMAR.md)**. Si sos un agente que retoma este proyecto, **empezá por ahí.**

---

## Por dónde entrar

| Si querés… | Leé |
|---|---|
| Entender el propósito y la autoridad del proyecto | [`sobre_este_plugins.txt`](sobre_este_plugins.txt) — documento fundacional, firmado |
| Saber dónde retomar el trabajo | [`RETOMAR.md`](RETOMAR.md) |
| Saber si esto es técnicamente posible y por qué | [`docs/VIABILIDAD.md`](docs/VIABILIDAD.md) |
| Ver el alcance, el presupuesto y los criterios de aceptación | [`docs/PLAN_ETAPA1.md`](docs/PLAN_ETAPA1.md) |
| Navegar la memoria técnica completa | [`.memory/index.md`](.memory/index.md) |
| Ver el historial de turnos | [`.memory/log.md`](.memory/log.md) |

---

## El hallazgo que define el proyecto

En una línea: **Drift no le da ningún dato de audio a sus shaders.**

Eso significa que un visualizador **no** puede ser un efecto de Drift que reaccione a la música mientras renderiza. Verificado leyendo el código fuente, no suponiendo: Drift tiene tuberías completas y explícitas para llevar **profundidad** (`u_depth*`) y **rostros** (`u_face*`) hasta un shader, y ninguna para audio. La asimetría es la prueba.

Toda la audio-reactividad que Drift tiene hoy (los templates tipo `beat_drop`) es un preproceso que hornea keyframes, con un único escalar por golpe, sin bandas de frecuencia, y descartando incluso la fuerza del onset.

**El camino viable** es generar el visualizador fuera de Drift y componerlo como un overlay con canal alpha. Suena a menos, pero tiene una ventaja concreta: tamaño, posición y opacidad los maneja Drift con sus propios controles, que ya son buenos y el usuario ya sabe usar.

Razonamiento completo con citas por archivo y línea en [`docs/VIABILIDAD.md`](docs/VIABILIDAD.md).

---

## Organización del repositorio

```
.
├── sobre_este_plugins.txt   Documento fundacional (autoridad sobre el propósito)
├── README.md                Esta puerta
├── RETOMAR.md               Estado vivo y próximo paso
├── docs/
│   ├── VIABILIDAD.md        ¿Es posible? Con evidencia citada
│   └── PLAN_ETAPA1.md       Alcance, presupuesto, criterios de aceptación
├── .memory/                 Memoria técnica (bóveda Obsidian)
│   ├── index.md             Índice de doble lectura (humano / agente)
│   ├── log.md               Bitácora append-only
│   ├── wiki/                Notas de dominio con evidencia
│   └── handoffs/            Un handoff por turno de agente
└── _reference/              NO versionado — clon de sólo lectura de Drift
```

---

## Reglas para agentes

Este proyecto lo trabajan varios agentes distintos. Estas reglas existen para que nadie repita pasos ni destruya trabajo hecho:

1. **Leé [`RETOMAR.md`](RETOMAR.md) antes de actuar.** Dice qué está hecho, qué no, y qué sigue.
2. **Leé `.memory/wiki/Audio_reactividad_en_Drift.md` antes de proponer arquitectura.** Sin eso vas a diseñar algo que no se puede construir.
3. **Dejá un handoff** en `.memory/handoffs/` y una entrada en `.memory/log.md` al terminar tu turno. El formato está en `.memory/wiki/MOC_Handoffs.md`.
4. **`log.md` es append-only.** Las entradas fechadas no se editan ni se reordenan.
5. **`C:\Program Files\Drift\` es de sólo lectura.** Los paquetes propios van a `%APPDATA%\CutWire Drift\`, nunca a la instalación.
6. **`_reference/drift-src/` no se edita ni se versiona.** Es código GPLv3 de terceros; se reconstruye con el comando documentado en el handoff T1.
7. **Declará tu frontera:** qué tocaste y, explícitamente, qué no. Es lo que le permite al siguiente confiar en el terreno.
8. **No revivas una decisión cerrada sin declararlo.** Si la revertís, la nota vieja se marca `superseded` con el motivo; no se borra.

---

## Licencia y relación con Drift

Drift es **GPLv3**. Este proyecto no incluye ni redistribuye código de Drift: lo consume por sus puntos de extensión públicos (paquetes de efecto por archivos, y el servidor MCP local). El clon en `_reference/` es material de consulta y está excluido del control de versiones.

Si en el futuro se toma el camino de forkear Drift (documentado como "camino C"), **el derivado queda obligado a GPLv3**.
