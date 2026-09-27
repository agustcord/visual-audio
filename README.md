# Visualizador de audio para Drift

Plugin y aplicación complementaria para el editor de video **[Drift](https://github.com/CutWire-Studios/Drift)** (CutWire Studios) que genera e incrusta el espectro o la forma de onda del audio sobre el video musical.

Proyecto de **Jonatan Córdoba**, usuario externo de Drift — **no forma parte del equipo de CutWire Studios**.

---

## Estado

**MVP Completo — Etapas 1 a 6 cerradas. Próximo paso: Etapa 7 (Validación con el fundador).**

El estado vivo y los detalles de continuidad están en **[`RETOMAR.md`](RETOMAR.md)**.

### Cómo abrirlo y probarlo

1. **Interfaz Gráfica (Recomendado):**  
   Hacé doble clic en **`visualizador.bat`** en la raíz del repositorio. Se abre inmediatamente la aplicación de escritorio sin consolas de fondo. Cargás tu canción, ves la onda predeterminada al instante, personalizás a gusto y exportás el video WebM.
2. **Línea de Comandos:**  
   ```powershell
   .\visualizador.bat tests\fixtures\pista_espectro.wav -o build\onda.webm
   # O directamente con Python:
   python -m visualizador tests\fixtures\pista_espectro.wav -o build\onda.webm
   ```
3. **Composición en Drift 0.6.0:**  
   Importás el archivo `.webm` generado, lo ubicás en una pista por encima del video y ponés el modo de fusión en **Trama (Screen)**. El fondo negro desaparece de forma exacta. Para detalles y compensación de color (`compensar_fondo`), consultá [`docs/GUIA_DE_USO.md`](docs/GUIA_DE_USO.md) y [`docs/COMO_USAR.md`](docs/COMO_USAR.md).

> **Compatibilidad con Drift:** Drift 0.6.0 no procesa video con canal alpha nativo en el timeline. El método estándar verificado es fondo negro + fusión Trama (o Chroma Key secundario). Cuando esté disponible Drift 0.7.0, el modo `--fondo transparente` ya está construido en el motor y listo para usarse.

---

## Por dónde entrar

| Si querés… | Leé |
|---|---|
| **Usar la aplicación** | **[`docs/GUIA_DE_USO.md`](docs/GUIA_DE_USO.md)** o [`docs/COMO_USAR.md`](docs/COMO_USAR.md) |
| **Trabajar en el proyecto (agentes)** | **[`docs/RUTA_DE_TRABAJO.md`](docs/RUTA_DE_TRABAJO.md)** — mapa de etapas y reglas de trabajo |
| Saber dónde retomar el trabajo | [`RETOMAR.md`](RETOMAR.md) |
| Saber qué hace el MVP y sus criterios | [`docs/MVP.md`](docs/MVP.md) |
| **Arquitectura técnica y contratos** | [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) |
| Entender el color en modo Trama | [`docs/COLOR_EN_TRAMA.md`](docs/COLOR_EN_TRAMA.md) |
| Viabilidad técnica inicial | [`docs/VIABILIDAD.md`](docs/VIABILIDAD.md) |
| Entender el propósito y la autoridad | [`sobre_este_plugins.txt`](sobre_este_plugins.txt) — documento fundacional |
| Navegar la memoria técnica completa | [`.memory/index.md`](.memory/index.md) |
| Ver la bitácora de turnos | [`.memory/log.md`](.memory/log.md) |

---

## El hallazgo que define el proyecto

En una línea: **Drift no le da ningún dato de audio a sus shaders.**

Eso significa que un visualizador **no** puede ser un efecto interno de Drift que reaccione a la música mientras renderiza. Verificado leyendo el código fuente: Drift tiene tuberías completas para llevar profundidad (`u_depth*`) y rostros (`u_face*`) a un shader, pero ninguna para audio.

**El camino viable y óptimo** es generar el visualizador externamente y componerlo como un overlay en Drift con modo de fusión Trama. Tamaño, posición, velocidad y opacidad los maneja Drift con sus propios controles nativos.

---

## Organización del repositorio

```
.
├── visualizador.bat         Lanzador de doble clic para Windows (sin consola negra)
├── sobre_este_plugins.txt   Documento fundacional (autoridad sobre el propósito)
├── README.md                Esta puerta de entrada
├── RETOMAR.md               Estado vivo y próximo paso
├── presets/                 Presets de fábrica JSON (barras_blancas, barras_neon, etc.)
├── tools/
│   ├── visualizador/        Paquete principal de la aplicación
│   │   ├── __main__.py      Entrypoint canónico (python -m visualizador)
│   │   ├── gui.py           Interfaz gráfica de escritorio (Tkinter)
│   │   ├── cli.py           Línea de comandos
│   │   ├── analisis.py      Motor de análisis espectral FFT y forma de onda
│   │   ├── render.py        Motor de renderizado determinista
│   │   ├── salida.py        Exportación WebM vía FFmpeg
│   │   ├── proyecto.py      Persistencia de proyectos y presets JSON
│   │   ├── parametros.py    Esquema unificado declarativo y álgebra de color
│   │   └── estilos/         Implementaciones de estilos (barras, espejadas, onda)
│   ├── generar_overlay.py   Generador original de la PoC (referencia histórica)
│   └── medir_trama.py       Instrumento de medición de álgebra de Trama
├── tests/
│   ├── fixtures/            Audios de prueba deterministas (pista_prueba, pista_espectro)
│   ├── test_analisis.py     Pruebas del análisis de audio
│   ├── test_render.py       Pruebas del motor de dibujo y export
│   ├── verificar_sincronia.py Validación estricta de alineación temporal
│   ├── test_proyecto.py     Pruebas de proyectos, presets y compensar_fondo
│   ├── test_gui.py          Pruebas automatizadas de la GUI Tkinter
│   └── test_lanzador.py     Pruebas del lanzador .bat y consistencia de docs
├── docs/                    Documentación técnica y guías de usuario
├── .memory/                 Memoria técnica y bitácora del proyecto
└── build/                   NO versionado — salidas de render
```

---

## Licencia y relación con Drift

Drift es **GPLv3**. Este proyecto no incluye ni redistribuye código de Drift: es una herramienta complementaria externa que produce metraje compatible para ser compuesto en la línea de tiempo.
