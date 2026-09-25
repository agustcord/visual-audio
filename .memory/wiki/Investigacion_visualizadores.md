---
tipo: "nota-investigacion"
estado: "activo"
relacionado: ["Caminos_de_implementacion"]
fecha: 2026-09-25
turno: 6
---

# Investigación: qué ofrecen los visualizadores de audio que ya existen

Relevada para definir el MVP con criterios del mercado en vez de una lista de deseos. El fundador pidió explícitamente mirar servicios similares.

**Advertencia de uso:** esta nota documenta **convenciones de la industria y nombres de parámetros**, que es información de hecho. **No se copió código de ninguna de estas fuentes.** Si en algún momento se toma prestada una idea de implementación concreta, se cita en el código con su licencia.

---

## Los estilos que todos consideran básicos

Cruzando siete herramientas, el núcleo se repite con mucha consistencia:

| Estilo | Qué es | ¿Está en todas? |
|---|---|---|
| **Barras de espectro** | Barras verticales, una por banda de frecuencia | ✅ en todas |
| **Forma de onda** | Línea de amplitud, a veces rellena | ✅ en todas |
| **Circular / radial** | Barras alrededor de un anillo | ✅ en casi todas |
| **Barras espejadas** | Barras simétricas que crecen desde el centro | frecuente |
| **Pulso** | Anillos concéntricos que reaccionan a los graves | ocasional |
| **Partículas** | Puntos que se generan con el audio | ocasional |

Fuentes: [Music Visualizer Lab](https://musicvisualizerlab.com/) ("waveform, spectrum, bars, circular"), [EchoWave](https://echowave.io/tools/audio-visualizer/) ("classic waveform line, FFT frequency bars, spectrum analyzer display, siri-style radial pulse"), [SoundGrail](https://soundgrail.com/tools/audio-visualizer) ("Waveform, Bars, Circular"), [LyricsToSong](https://lyricstosongai.com/audio-tools/audio-visualizer) ("waveforms, frequency bars, circular spectrum, particles, 3D"), [audiospectr](https://github.com/bradsec/audiospectr) (8 capas), [Wav2Bar](https://picorims.github.io/wav2bar-website/), [Banger.show](https://banger.show/guides/clips/spectre).

**Conclusión para el MVP:** tres estilos cubren lo que el mercado considera imprescindible. Circular es el cuarto en orden de importancia.

---

## Los parámetros que el mercado considera estándar

### De Banger.show, visualizador "Spectre" — con rangos concretos

La fuente más útil porque publica los rangos exactos ([guía](https://banger.show/guides/clips/spectre)):

| Parámetro | Rango | Qué hace |
|---|---|---|
| Color | — | color de la base de la barra |
| End Color | — | color de la punta: hace el degradado |
| Opacity | 0–1 | transparencia |
| **Intensity** | **0.5–10** | cuánto reaccionan las barras al audio |
| **Bars Width** | **0.5–10** | grosor de cada barra |
| **Bars Count** | **5–240** | cantidad de barras |
| Bottom Aligned | on/off | crecen desde abajo, o centradas creciendo en ambas direcciones |

### De audiospectr — taxonomía completa por estilo

Proyecto Python con licencia MIT, casi el mismo producto que vamos a construir. Su lista de campos por estilo (del README):

- **bars**: `bar_count`, `bar_width`, `spacing`, `corner_radius`, `mirror`, `color`, `secondary_color`, `peak_indicators`, `smoothing_type`, `smoothing_factor`, `analyzer_range`, `amplitude_scale`, `response_curve`
- **waveform**: `line_width`, `color`, `fill_color`, `smoothing_factor` (0–1, default 0.65 — más alto da una línea más fluida y lenta)
- **circular**: `bar_count`, `radius`, `inner_radius`, `bar_width`, `rotation_speed`, `color`, `amplitude_scale`, `response_curve`, `min_bar_length`
- **comunes a toda capa**: `x`, `y`, `width`, `height`, `opacity`, `blend_mode` (`normal`/`add`/`screen`), y efectos: `glow`, `glow_intensity`, `glow_radius`, `grain`, `blur`

### Síntesis: los parámetros que aparecen en todas partes

1. **Color**, y **segundo color** para degradado.
2. **Opacidad.**
3. **Sensibilidad / intensidad** — cuánto reacciona al audio. Es el parámetro que más cambia la sensación.
4. **Cantidad de elementos** (barras).
5. **Grosor** y **separación**.
6. **Suavizado temporal** — si el movimiento es nervioso o fluido.
7. **Posición y tamaño.**
8. **Espejado / alineación.**
9. **Resplandor.**
10. **Tapas de pico** — el indicador que se queda arriba y cae despacio.

---

## Arquitectura: el mercado valida la que propusimos

Dos confirmaciones independientes del diseño de *analizar una vez, dibujar muchas veces*:

- **audiospectr**: *"pre-analiza el audio en datos de FFT, forma de onda, RMS y bandas de frecuencia por cuadro, compone una o más capas RGBA sobre un fondo, y después pasa los cuadros crudos directo a FFmpeg para codificar"*. Es exactamente la arquitectura de tres etapas que propusimos.
- **EchoWave** lo dice desde el lado del usuario: *"cada estilo lee del mismo análisis FFT, así que cambiar de estilo mantiene la sincronía del audio"*. Es la consecuencia visible de separar análisis de dibujo: **cambiar el estilo no puede desincronizar nada.**

*(Contenido reformulado para cumplir con las restricciones de licencia de las fuentes.)*

### La previsualización: un solo motor, no dos

audiospectr resuelve la previsualización con `--dump-frame N`, que **renderiza un cuadro real con el motor real** y lo guarda como PNG sin codificar el video entero.

Esto importa porque evita la trampa clásica: si la interfaz dibujara su propia versión rápida para previsualizar, tendríamos **dos motores que se desincronizan**, y la vista previa mentiría. Drift mismo hace bandera de lo contrario — *"un compositor, un resultado, sin sorpresas"*.

**Decisión de diseño que se toma de acá:** la vista previa del MVP se genera con el motor de producción. Va a ser más lenta que dibujar en un lienzo, y en cambio no puede mentir.

---

## Antecedentes directos, y por qué igual construimos

El fundador preguntó si conviene usar otra herramienta. Hay dos candidatas reales y hay que ser honesto sobre ellas.

### audiospectr — MIT, Python, línea de comandos

Lo más parecido que existe a lo que queremos.

**Lo que ya hace:** analiza MP3/WAV/FLAC/M4A/OGG, ocho estilos de capa, presets con nombre, proyectos en JSON multicapa, efectos de resplandor y grano, previsualización de un cuadro, y exporta MP4.

**Por qué no nos sirve tal cual:**

1. **Exporta MP4 H.264 con audio AAC**, compuesto sobre un fondo de color o imagen. Nuestro caso es el opuesto: necesitamos un overlay **sin fondo** (o con fondo recortable) y **sin audio**, porque el audio ya está en la timeline de Drift.
2. Está pensado para **videos musicales autónomos** (pantalla completa con fondo), no para overlays de un editor.
3. Requiere `uv` y `librosa`: instalación nueva.
4. **No tiene interfaz gráfica**, y el fundador pidió explícitamente que el MVP no requiera programación del usuario final. Una línea de comandos con veinte banderas no cumple eso.

**Atajo que sí existe y conviene declarar:** aceptando su MP4 y poniéndole `--background-color "#00FF00"`, se podría recortar con el Chroma Key de Drift. Sería una solución rápida, sin interfaz y con un fondo quemado. Queda registrada como alternativa real por si el fundador prefiere probar antes de que construyamos.

### Wav2Bar — app de escritorio libre

Objetos: visualizadores, temporizadores, texto, imágenes, flujos de partículas y fondos. Es el antecedente más cercano a la **forma de producto** que el fundador describió: cargar audio, ver, elegir, personalizar, guardar, exportar.

**No se encontró evidencia de que exporte con canal alpha ni con fondo transparente**, que es el requisito que define nuestro caso de uso. Está en reescritura (`wav2bar-reborn`), así que su estado es móvil.

### Por qué construir, en una línea

Ninguna de las dos resuelve **overlay sin fondo para un editor de video**, que es el requisito central. Y la parte que habría que agregarles —el aspecto y el formato de salida— es justamente donde vive todo el valor para el fundador. Lo que sí tomamos de ellas es la **taxonomía de parámetros y la arquitectura**, que están validadas y no hay razón para reinventar.

---

## Lo que esta investigación cambió de nuestro plan

1. **El espectro de barras es lo más importante, no la forma de onda.** Nosotros arrancamos por la onda porque `showwaves` de FFmpeg existía. El mercado trata las barras como el estilo principal.
2. **Faltaban parámetros que son estándar y no estaban en el plan**: sensibilidad, suavizado temporal, cantidad de barras, separación, degradado de dos colores, tapas de pico, resplandor. El plan sólo mencionaba color, velocidad, tamaño, posición y opacidad.
3. **Hay rangos de referencia** para no inventar: barras 5–240, intensidad 0.5–10, suavizado 0–1 con 0.65 de default razonable.
4. **La previsualización tiene que usar el motor de producción**, no un dibujante aparte.
5. **Un solo análisis alimenta todos los estilos**, así que cambiar de estilo nunca puede romper la sincronía.
