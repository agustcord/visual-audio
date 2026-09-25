---
tipo: "nota-concepto"
estado: "activo"
relacionado: ["Extensibilidad_de_Drift", "Caminos_de_implementacion"]
verificado: 2026-09-25
---

# Audio-reactividad en Drift

Esta nota documenta **el hallazgo que condiciona todo el proyecto**. Cualquier agente que vaya a proponer arquitectura debe leerla primero, o va a diseñar algo imposible.

## El bloqueo central

> **Drift no expone ningún dato de audio al pipeline de render GPU.**

No hay uniform, ni textura, ni buffer de audio disponible para un shader de efecto. Verificado **por ausencia**: un grep de `u_audio|audioLevel|u_level|u_beat|u_rms|u_energy|u_band` sobre todo el repositorio devuelve cero resultados en `GlRuntime` y en los shaders. Las únicas apariciones de `audioLevel` son los **medidores de la UI** (`src/engine/AudioRecorder.h:26`, `src/playback/PlaybackEngine.h:141-142`, `AppController::trackAudioLevels`), que alimentan las barras del mixer y nunca cruzan hacia el render.

Los uniforms que un shader de efecto sí recibe están listados en `docs/gpu-effects.md`: `u_currentTexture`, `u_textureN`, `u_resolution`, `u_time`, `u_timeUs`, `u_frameIndex`, `u_progress`, `u_fromTexture`, `u_toTexture`, `u_depth*`, `u_face*`. Hay una ruta completa para **profundidad** y otra para **rostros** —ambas con su preludio compilado, sus helpers y su flag de validez— y **ninguna para audio**. La asimetría es la prueba: cuando Drift quiere que un shader vea datos externos, construye esa tubería explícitamente. Para audio no la construyó.

## Cómo Drift hace audio-reactividad entonces

Con un **preproceso que hornea keyframes reales en el proyecto**. No hay nada en tiempo de render.

### El análisis

`AudioOnsets::analyze()` devuelve `AudioBeatAnalysis` (`src/engine/AudioOnsets.h:8-35`):

```cpp
QList<AudioOnset> onsets;  // { double seconds; float strength; }
QList<double> beats;       // grilla regular; vacía si bpm == 0
int beatsPerBar = 4;
int firstDownbeat;
double bpm;
double confidence;
```

Internamente **sí hace STFT** (`AudioOnsets.cpp:89-122`, función `onsetEnvelope`, usando `av_tx`): calcula flujo espectral log-magnitud rectificado a media onda. Pero **colapsa todos los bins en un escalar por frame** (`flux += max(0, mag[k] - prevMag[k])`), y esa envolvente **nunca sale de la función**: sólo alimenta el detector de picos y la autocorrelación de tempo.

Detalles operativos: se mezcla a mono a **22050 Hz** (`kBeatAnalysisRate`) porque, según el comentario del código, *los hats y platillos —las señales de onset más nítidas en música— viven arriba de 4 kHz*. Con menos de **4 segundos** de material (`kMinAnalysisSec`) devuelve bpm 0 y sin grilla.

### El horneado

`AppController::applyEffectTemplateInternal` (`src/models/AppController.cpp:18820`) arma la lista de `syncPoints` según el campo `sync` del template:

- `"clip"` → dos puntos: el 0 y la duración del clip.
- `"onset"` → cada onset que cae dentro del clip, guardado como `at - clipStart`. **Descarta `onset.strength`**: se queda sólo con el instante.
- `"beat"` / `"bar"` → la grilla de beats, filtrando por compás en el caso de `bar`.

Después, `applyTemplateLayersToClip` (`AppController.cpp:18571`) escribe, por cada punto de sincronía, **dos keyframes** en la propiedad `fx.<effectIndex>.<param>`:

```cpp
writeClipPropValue(clip, prop, t,           layer.pulse.peak, false, true);
writeClipPropValue(clip, prop, t + decayUs, layer.pulse.rest, false, true);
```

Son keyframes de proyecto de verdad: quedan serializados, son editables a mano en la UI y legibles por MCP con `list_keyframes`.

### El formato del template

`src/engine/EffectTemplateCatalog.cpp`, función `parsePulse()` (líneas 48-63): un `pulse` tiene exactamente cuatro campos.

```json
"pulse": { "param": "amount", "rest": 0.0, "peak": 0.7, "decayMs": 180 }
```

Ejemplo real, `effect-templates/beat_drop/template.json` (instalado): `"sync": "onset"` con tres layers, cada uno pulsando un parámetro distinto de un efecto distinto (`beat_shake.amount`, `strobe_flash.flash`, `zoom_pulse.punch`) con decaimientos de 180, 90 y 200 ms.

## El techo, explícito

1. **Un `pulse` por layer, y apunta a un solo parámetro.** `EffectTemplateLayer` tiene un único campo `pulse`, no una lista.
2. **El pulso es una constante disparada en una lista de instantes.** `peak` y `rest` son números fijos. No hay envolvente continua.
3. **No hay bandas de frecuencia en ninguna parte del camino.** Todos los layers de un template comparten el mismo conjunto de tiempos. Lo único que puede variar entre layers es `peak`, `rest` y `decayMs`.
4. **Ni siquiera se usa la fuerza del onset.** Un golpe suave y un golpe fuerte producen el mismo keyframe.
5. **Falla en silencio.** Si `m_beatAnalysisRaw` está vacío, `syncPoints` queda vacío y el template se aplica **sin animación y sin error**.

## La única excepción: hay un espectro, pero no va al video

`drift::waveformsheet::spectrogram()` (`src/engine/WaveformSheet.h:55-57`) es **el único análisis multibanda de todo Drift**: espectrograma de frecuencia logarítmica, N bandas log-espaciadas desde `minHz` (default 50 Hz) hasta Nyquist, comprimido logarítmicamente y normalizado al máximo global.

Pero `WaveformSheet::render()` devuelve una **`QImage`**, y la cabecera del archivo declara su propósito sin ambigüedad: es *"audio como imagen para agentes"*. Su **único consumidor** es el handler MCP de `get_waveform` (`AppController.cpp` ~26935-27120), con `kMcpSpectrogramBins = 64`, rango reportado `min_hz 50 / max_hz 8000`, ancho máximo 2000 px y tope de 600 s.

**No existe ningún puente entre `WaveformSheet`/`MediaWaveform` y el cargador de texturas de paquetes de efecto.** El único camino imagen→shader es `pipeline.textures[]`, que lee archivos de disco, valida su existencia en tiempo de catálogo y los cachea de por vida (ver [[Extensibilidad_de_Drift]]).

Complementariamente, `MediaWaveform` (`src/engine/MediaWaveform.h`) da picos de amplitud a 100 por segundo por defecto, y un band-pass de voz de 300 Hz–3 kHz de 4º orden (`speechPeaks`/`voicePeaks`) — que es **una** banda, no un análisis multibanda.

## Lo que esto implica

Para un visualizador de onda o espectro, el dato existe (`get_waveform` da 64 bandas, `detect_beats` da onsets y bpm) pero **sólo es alcanzable desde fuera del render, vía MCP**. El dibujo, entonces, no puede ser un shader que "escuche": tiene que ser algo pre-calculado. Las opciones están en [[Caminos_de_implementacion]].
