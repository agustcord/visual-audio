# Visualizador de audio para Drift

Plugin para el editor de video **[Drift](https://github.com/CutWire-Studios/Drift)** (CutWire Studios) que dibuja la onda o el espectro del audio sobre el video, para poder seguir visualmente la pista musical. Pensado para edición de videos musicales.

Proyecto de **Jonatan Córdoba**, usuario externo de Drift — **no forma parte del equipo de CutWire Studios**.

---

## Estado

**Etapa 1, turno 4. El generador funciona y hay dos rutas verificadas para componerlo en Drift.**

El estado vivo y el próximo paso están en **[`RETOMAR.md`](RETOMAR.md)**. Si sos un agente que retoma este proyecto, **empezá por ahí.**

### Probarlo

```powershell
python tools\generar_overlay.py tests\fixtures\pista_prueba.wav -o build\onda.webm --lienzo 1920x1080
```

Después, en Drift: importar, poner en una pista por encima del video, y modo de fusión **Trama**. Los detalles y la alternativa con Chroma Key están en [`docs/COMO_USAR.md`](docs/COMO_USAR.md).

> **Ojo con la versión de Drift.** La 0.6.0 (la publicada) **no soporta video con canal alpha**: descarta el alpha y compone el clip como un rectángulo negro. Por eso la transparencia la resuelve Drift con un modo de fusión o con el efecto Chroma Key, en vez de venir en el archivo. Cuando salga 0.7.0 alcanzará con `--fondo transparente`, que ya está implementado.

---

## Por dónde entrar

| Si querés… | Leé |
|---|---|
| **Trabajar en el proyecto (cualquier agente)** | **[`docs/RUTA_DE_TRABAJO.md`](docs/RUTA_DE_TRABAJO.md)** — la ruta, los criterios y las reglas |
| **Usarlo** | [`docs/COMO_USAR.md`](docs/COMO_USAR.md) — guía paso a paso |
| Entender el propósito y la autoridad del proyecto | [`sobre_este_plugins.txt`](sobre_este_plugins.txt) — documento fundacional, firmado |
| Saber dónde retomar el trabajo | [`RETOMAR.md`](RETOMAR.md) |
| Saber qué hace el MVP y con qué criterios se aprueba | [`docs/MVP.md`](docs/MVP.md) |
| **Escribir código**: contratos y estructura | [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) |
| Saber si esto es técnicamente posible y por qué | [`docs/VIABILIDAD.md`](docs/VIABILIDAD.md) |
| Ver el alcance, el presupuesto y las decisiones del fundador | [`docs/PLAN_ETAPA1.md`](docs/PLAN_ETAPA1.md) — los dos Gates, verbatim |
| Ver qué mide el PoC y qué salió mal en el camino | [`docs/POC_RESULTADOS.md`](docs/POC_RESULTADOS.md) |
| Entender el audio de prueba | [`tests/fixtures/README.md`](tests/fixtures/README.md) |
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
├── tools/
│   └── generar_overlay.py   El generador de overlay
├── tests/fixtures/
│   ├── pista_prueba.wav     Audio de prueba del proyecto
│   ├── generar_audio_prueba.py   Lo regenera de forma determinista
│   └── README.md            Por qué está construido así
├── docs/
│   ├── VIABILIDAD.md        ¿Es posible? Con evidencia citada
│   ├── PLAN_ETAPA1.md       Alcance, presupuesto, decisiones del fundador
│   ├── POC_RESULTADOS.md    Mediciones del PoC y trampas encontradas
│   └── evidencia/           Capturas que respaldan las mediciones
├── .memory/                 Memoria técnica (bóveda Obsidian)
│   ├── index.md             Índice de doble lectura (humano / agente)
│   ├── log.md               Bitácora append-only
│   ├── wiki/                Notas de dominio con evidencia
│   └── handoffs/            Un handoff por turno de agente
├── build/                   NO versionado — salidas de render
└── _reference/              NO versionado — clon de sólo lectura de Drift
```

---

## Si sos un agente que retoma este proyecto

**Tu punto de entrada es [`docs/RUTA_DE_TRABAJO.md`](docs/RUTA_DE_TRABAJO.md).** Tiene la tabla de estado, las siete etapas con criterios de entrada y salida, y las quince reglas de trabajo. Está escrita para que puedas ubicarte y ejecutar sin haber estado en las conversaciones anteriores.

El orden corto:

1. **[`docs/RUTA_DE_TRABAJO.md`](docs/RUTA_DE_TRABAJO.md)** — dónde estamos y qué sigue.
2. **[`RETOMAR.md`](RETOMAR.md)** — estado vivo y, sobre todo, **las trampas ya pagadas**. Cada una costó un error real.
3. **[`docs/MVP.md`](docs/MVP.md)** — qué hace el MVP y con qué criterios se aprueba.
4. **[`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md)** — antes de escribir una línea de código.

Las reglas completas están en la ruta (§3). Las cinco que más importan:

- **Ningún criterio se declara cumplido sin el comando que lo prueba.** Si no lo pudiste medir, decilo.
- **Medí sobre todo el material, no sobre muestras**, y contra algo conocido del audio — no contra lo que el archivo dice de sí mismo.
- **Si un resultado no tiene sentido físico, sospechá del instrumento antes que de lo medido.** Pasó dos veces y las dos el instrumento era el roto.
- **Declará tu frontera:** qué tocaste y, explícitamente, qué no.
- **`C:\Program Files\Drift\` es de sólo lectura**, y `_reference/drift-src/` no se edita ni se versiona.

---

## Licencia y relación con Drift

Drift es **GPLv3**. Este proyecto no incluye ni redistribuye código de Drift: lo consume por sus puntos de extensión públicos (paquetes de efecto por archivos, y el servidor MCP local). El clon en `_reference/` es material de consulta y está excluido del control de versiones.

Si en el futuro se toma el camino de forkear Drift (documentado como "camino C"), **el derivado queda obligado a GPLv3**.
