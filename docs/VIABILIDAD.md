# Informe de viabilidad — Visualizador de audio para Drift

**Fecha:** 2026-09-25 · **Turno:** T1 · **Agente:** Kiro
**Pregunta del documento fundacional:** *¿es posible crear esto para el editor Drift?*

---

## Veredicto

**Sí es viable, pero no por el camino que uno esperaría.**

Un visualizador de audio **no puede implementarse como un efecto de Drift que reaccione a la música en tiempo de render.** Drift no le da a sus shaders ningún dato de audio, y no es un olvido: es una decisión de arquitectura visible en el código.

Lo que **sí** es viable, con las piezas que Drift ya tiene y sin modificar el editor:

- Generar el visualizador **fuera** de Drift y componerlo como un overlay con canal alpha sobre la pista de video.
- Leer los datos de audio reales de Drift (onsets, bpm, y un espectrograma de 64 bandas) a través de su **servidor MCP**.
- Escribir **keyframes calculados por nosotros** en parámetros de efecto, vía MCP, con más resolución de la que consigue el propio Drift con sus templates.

Las tres personalizaciones que más cuestan en un plugin desde cero —tamaño, posición y opacidad— **las resuelve Drift**, porque un overlay es un clip normal con transform y opacidad keyframeables.

---

## 1. Cómo se investigó

No alcanzaba con leer el README. Se auditó el código fuente:

```powershell
git clone --depth 1 --filter=blob:none --no-checkout `
  https://github.com/CutWire-Studios/Drift.git _reference\drift-src
git -C _reference\drift-src sparse-checkout init --cone
git -C _reference\drift-src sparse-checkout set src docs effects effect-templates transitions audio-effects
git -C _reference\drift-src checkout
```

Y se cruzó contra la instalación local (`C:\Program Files\Drift`) y contra la documentación propia de Drift en `docs/`.

Las cuatro preguntas que guiaron la investigación:

1. ¿Existe un sistema de plugins? ¿Qué puede hacer un plugin?
2. ¿Cómo accede una extensión al audio de la timeline?
3. ¿Cómo dibuja una extensión sobre el video?
4. ¿Cómo se distribuye e instala lo que construyamos?

---

## 2. ¿Existe un sistema de plugins?

**No en el sentido habitual.** Drift no carga código nativo de terceros. Tiene **cuatro puntos de extensión**:

| Mecanismo | Qué es | Instalable por un tercero |
|---|---|---|
| **Paquetes de efecto GPU** | Una carpeta con `effect.json` + shader GLSL. Sin compilar, sin firmar. | ✅ a `<AppData>/effects` |
| **Effect templates** | `template.json` que apila efectos y los anima con onsets/beats. | ✅ a `<AppData>/effect-templates` |
| **Addons `.driftpkg`** | Paquete binario firmado (fuentes, stickers, modelos). | ❌ **firma Ed25519 obligatoria** |
| **Servidor MCP** | API local para que un agente edite el proyecto abierto. | ✅ lo activa el usuario |

Detalle completo, con rutas de búsqueda y límites de cada tipo de parámetro, en `.memory/wiki/Extensibilidad_de_Drift.md`.

### Lo bueno: instalar no requiere admin

`src/engine/GpuPackageParse.cpp:394-398` define el orden de búsqueda de paquetes:

1. La variable de entorno `DRIFT_EFFECTS_DIR`
2. `<applicationDir>/effects` → `C:\Program Files\Drift\effects` (requiere admin, **no usar**)
3. `<AppDataLocation>/effects` → `C:\Users\Jonatan Agustín\AppData\Roaming\CutWire Drift\effects`

La tercera ruta es escribible por el usuario y **no tiene verificación de firma**. Un paquete de efecto propio se instala copiando una carpeta.

### Lo malo: la vía de addons está cerrada

`src/engine/AddonPackage.h:82-89` — `install()` sólo promueve el paquete **cuando la firma Ed25519 verifica** contra la clave de CutWire Studios. Sin esa clave privada, **no se puede producir un `.driftpkg` instalable**. La distribución de nuestro trabajo tendrá que ser "copiá esta carpeta", no un paquete de un click.

---

## 3. El hallazgo central: no hay audio en el render

> **Drift no expone ningún uniform, textura ni buffer de audio a sus shaders de efecto.**

Verificado **por ausencia**. Los uniforms que un shader recibe, según `docs/gpu-effects.md` y confirmado en `GlRuntime`:

```
u_currentTexture, u_textureN, u_resolution, u_time, u_timeUs,
u_frameIndex, u_progress, u_fromTexture, u_toTexture, u_depth*, u_face*
```

Un grep de `u_audio|audioLevel|u_level|u_beat|u_rms|u_energy|u_band` sobre todo el repositorio devuelve **cero** resultados en el pipeline de render. Las únicas apariciones de `audioLevel` son los medidores del mixer (`src/engine/AudioRecorder.h:26`, `src/playback/PlaybackEngine.h:141-142`), que alimentan barras en la UI y nunca cruzan al render.

**La evidencia más fuerte es la asimetría.** Drift tiene tuberías completas y deliberadas para dos tipos de datos externos:

- **Profundidad:** `u_depthTexture` en la unidad 8, `u_depthResolution`, `u_hasDepth`, y helpers compilados en un preludio (`driftDepth()`, `driftDepthGuided()`, `driftNormal()`, `packDepth()`).
- **Rostros:** ~40 uniforms, siete contornos como arreglos `vec2[]`, una base ortonormal de pose, y un flag `u_faceValid` que todo shader debe honrar.

Cuando Drift quiere que un shader vea datos externos, **construye esa tubería explícitamente**. Para audio no la construyó. No es un descuido que se pueda rodear con un truco de shader.

---

## 4. Cómo hace Drift la audio-reactividad entonces

Con un **preproceso que hornea keyframes reales** en el proyecto. Nada en tiempo de render.

El template `beat_drop` que viene instalado ilustra el mecanismo completo:

```json
{
  "id": "beat_drop",
  "sync": "onset",
  "layers": [
    { "effectId": "beat_shake",   "params": {"amount": 0.0},
      "pulse": {"param": "amount", "rest": 0.0, "peak": 0.7,  "decayMs": 180} },
    { "effectId": "strobe_flash", "params": {"flash": 0.0},
      "pulse": {"param": "flash",  "rest": 0.0, "peak": 0.5,  "decayMs": 90} },
    { "effectId": "zoom_pulse",   "params": {"punch": 0.0},
      "pulse": {"param": "punch",  "rest": 0.0, "peak": 0.65, "decayMs": 200} }
  ]
}
```

`AppController::applyEffectTemplateInternal` (`src/models/AppController.cpp:18820`) junta los instantes de los onsets, y `applyTemplateLayersToClip` (`:18571`) escribe **dos keyframes por instante** en la propiedad `fx.<i>.<param>`: el valor `peak` en `t`, y el valor `rest` en `t + decayMs`.

### El techo, con nombre y apellido

1. **Un `pulse` por layer, apuntando a un solo parámetro.** `EffectTemplateLayer` tiene un campo `pulse`, no una lista.
2. **El pulso es una constante.** `peak` y `rest` son números fijos, no una envolvente.
3. **Cero bandas de frecuencia.** Todos los layers comparten el mismo conjunto de tiempos.
4. **Se descarta la fuerza del onset.** `AudioOnset` tiene un campo `strength`, y el código que arma los `syncPoints` lo tira: se queda sólo con `seconds`. Un golpe suave y un mazazo producen el mismo keyframe.
5. **Falla en silencio.** Sin análisis de beats previo, el template se aplica **sin animación y sin error**.

`AudioOnsets::analyze()` sí hace un STFT internamente (`AudioOnsets.cpp:89-122`, con `av_tx`), pero **colapsa todos los bins en un escalar por frame** y esa envolvente nunca sale de la función.

### Hay un espectro, pero no va al video

`drift::waveformsheet::spectrogram()` (`src/engine/WaveformSheet.h:55-57`) es el **único análisis multibanda de todo Drift**: bandas log-espaciadas desde 50 Hz hasta Nyquist, log-comprimidas y normalizadas.

Pero devuelve una `QImage`, y la cabecera del archivo declara su propósito: *"audio como imagen para agentes"*. Su **único consumidor** es el handler MCP de `get_waveform`, con 64 bandas y rango 50–8000 Hz.

**No existe ningún puente entre ese espectrograma y el cargador de texturas de los paquetes de efecto.** El dato existe; simplemente no llega al render.

---

## 5. Por qué el atajo obvio no funciona

La idea elegante sería: hornear el espectrograma a un PNG, declararlo en `pipeline.textures[]`, y muestrearlo desde el shader indexando por `u_time`. **No funciona.** Tres razones verificadas:

1. **Validación en tiempo de catálogo.** `GpuPackageParse.cpp:248-265` exige que el archivo exista cuando se parsea el paquete, y el catálogo se escanea al arrancar. Un PNG generado después no entra.
2. **Caché de por vida.** `GlRuntime.cpp:3044-3063` (`staticTexture`) cachea por ruta para todo el proceso, **sin mtime en la clave**, y cachea el fallo como `0`. El comentario es literal: *"Static package assets live for the process lifetime."* Reescribir el PNG en sitio **no actualiza lo que ve la GPU**.
   El contraste está en el mismo archivo (`GlRuntime.h:134-140`): las fotos de Face Swap **sí** se clavean con `path|mtime|size`, *"para que editar una foto en el lugar reconstruya las texturas en vez de servir una vieja"*. Las texturas de paquete no tienen ese cuidado.
3. **Rutas relativas por contrato.** `file` se resuelve contra el directorio del paquete.

Para que esto sirviera habría que generar un paquete de efecto nuevo por cada clip de audio **y reiniciar Drift**. No es un producto.

---

## 6. Lo que Drift sí nos regala

Verificado en código, y es bastante:

**Canal alpha de punta a punta.** Un overlay transparente se compone bien:
- `MediaProbe.cpp:37-46` detecta alpha por `AV_PIX_FMT_FLAG_ALPHA`.
- `ClipReader.cpp:1002-1010` fuerza `libvpx-vp9` porque *los decodificadores nativos vp9/vp8 ignoran el plano alpha de WebM*.
- `ClipReader.cpp:1209-1214` desactiva decodificación por hardware en fuentes con alpha.
- `GpuCompositor.cpp:917-923` compone con blend premultiplicado `GL_ONE / GL_ONE_MINUS_SRC_ALPHA`.
- ⚠️ `PreviewProxyRenderer.cpp:40-45` **rechaza proxies en clips con transparencia** → preview más caro.

**Un compositor único para preview y export.** Lo que se ve es lo que sale.

**Superficie MCP suficiente:** `import_media`, `place_clip`, `add_effect`, `set_effect_param`, `set_keyframe` (con `prop` = `fx.<i>.<key>`), `list_keyframes`, `detect_beats` (bloquea y devuelve bpm + onsets), `get_waveform({image:true})` (64 bandas de espectrograma), y `apply` para batchear.

**FFmpeg 8.0.1 ya instalado** en `C:\ffmpeg\bin\ffmpeg.exe`, con todos los filtros de visualización compilados: `showwaves`, `showwavespic`, `showspectrum`, `showspectrumpic`, `showfreqs`, `showcqt`, `avectorscope`, `showvolume`.

---

## 7. Caminos viables

Comparación completa en `.memory/wiki/Caminos_de_implementacion.md`. Resumen:

| | **A — Overlay generado** | **B — Keyframes vía MCP** | **C — Fork de Drift** |
|---|---|---|---|
| Qué hace | Genera video con alpha y lo importa como clip | Calcula y escribe keyframes en `fx.<i>.<param>` | Agrega uniforms de audio al C++ |
| Da espectro real | ✅ | ❌ sólo un escalar | ✅ |
| Reactivo en vivo | ❌ es un render | ⚠️ keyframes, editables a mano | ✅ sliders vivos |
| Modifica Drift | ❌ | ❌ | ✅ |
| Costo | Bajo | Bajo | **Alto + mantenimiento indefinido** |
| Riesgo | Bajo | Bajo | Toolchain Qt6+FFmpeg, sync con upstream |

### Cómo el camino A cubre lo que pide el documento fundacional

El fundador pide poder personalizar **velocidad, tamaño, posición, color y opacidad**:

| Personalización | Dónde se resuelve |
|---|---|
| **Tamaño** | Transform del clip en Drift — ya existe, keyframable |
| **Posición** | Transform del clip en Drift — arrastrable, keyframable |
| **Opacidad** | Propiedad `opacity` del clip — ya existe, keyframable |
| **Velocidad** | Escala temporal del render y/o speed curve del clip |
| **Color** | Parámetro del filtro en el generador (`colors=`) |

Cuatro de cinco salen **gratis**, con controles que Drift ya tiene y que el usuario ya sabe usar. Ese es el argumento fuerte del camino A: no reimplementamos un inspector.

**El costo honesto:** cambiar el color o el estilo implica **regenerar el overlay**. No es un slider en vivo. Esa es la consecuencia directa del bloqueo de la sección 3, y es la decisión que el fundador tiene que aceptar o rechazar.

---

## 8. Recomendación

**Camino A como base**, con el **camino B como capa opcional** (hacer que el propio overlay o el video pulse con los onsets, usando la energía real en vez del `peak` constante que usa Drift).

**Camino C anotado como evolución futura** y como la contribución que eventualmente valdría ofrecer a upstream: la tubería de `depth` es un molde bastante claro para una de audio, lo que baja el riesgo técnico. Pero arrancar por ahí sería imprudente.

El plan concreto, con presupuesto y criterios de aceptación, está en `PLAN_ETAPA1.md`.

---

## 9. Advertencia de vigencia

Drift está en desarrollo activo. Este informe describe la rama `main` al **2026-09-25**. El hallazgo central (ausencia de audio en el render) es lo que sostiene todas las conclusiones: **un agente futuro debería re-verificarlo** con el grep documentado antes de asumir que sigue vigente. Si upstream agrega uniforms de audio, el camino C se vuelve barato y este informe queda obsoleto.
