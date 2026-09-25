---
tipo: "nota-concepto"
estado: "activo"
relacionado: ["Drift_editor", "Audio_reactividad_en_Drift", "Caminos_de_implementacion"]
verificado: 2026-09-25
---

# Extensibilidad de Drift

**Drift no tiene un sistema de plugins.** No carga código nativo de terceros. Lo que tiene son **cuatro puntos de extensión**, y conviene saber exactamente qué permite y qué prohíbe cada uno antes de diseñar nada.

## 1. Paquetes de efecto GPU (por archivos, sin compilar)

El mecanismo más accesible. Un efecto es **una carpeta con archivos de texto**:

```
effects/mi_efecto/
├── effect.json      # metadata, parámetros de usuario, pipeline de passes
├── main.frag        # GLSL #version 330 core
└── thumbnail.png    # opcional, preview en el navegador de efectos
```

Documentado por Drift en `docs/gpu-effects.md`. Nada se compila ni se firma: Drift parsea el JSON y materializa el `.frag` tal cual.

**Dónde se instalan** — `src/engine/GpuPackageParse.cpp:394-398`, función `defaultSearchPaths()`:

1. La variable de entorno `DRIFT_EFFECTS_DIR`
2. `<applicationDir>/effects` → `C:\Program Files\Drift\effects` (requiere admin, **no usar**)
3. `<AppDataLocation>/effects` → `C:\Users\Jonatan Agustín\AppData\Roaming\CutWire Drift\effects` ← **este es el nuestro**

El tercero es el que convierte esto en algo instalable por un usuario sin privilegios y sin tocar la instalación. **No hay verificación de firma en esta ruta.**

**Modo gracia:** si el shader no compila, el efecto pasa el frame sin tocarlo. Un paquete roto no rompe el editor.

### Los límites que importan

- **Uniforms disponibles** (reservados por el motor): `u_currentTexture`, `u_textureN`, `u_resolution`, `u_time`, `u_timeUs`, `u_frameIndex`, `u_progress`, `u_fromTexture`, `u_toTexture`, `u_depth*`, `u_face*`. **Ninguno de audio.**
- **Tipos de parámetro:** `float` (keyframable), `bool` (no keyframable), `color` (se bindea como `vec3`, alpha descartado, **no keyframable**), `file` (**no se bindea como uniform**; sólo lo usa el backend `model3d`).
- **`pipeline.textures[]` sirve sólo para assets estáticos.** `src/engine/GpuPackageParse.cpp:248-265` resuelve `tex.path = QDir(packageDir).filePath(tex.file)` y **valida que el archivo exista en tiempo de parseo del catálogo**. Peor: `src/engine/GlRuntime.cpp:3044-3063` (`staticTexture`) cachea la textura **por ruta, para toda la vida del proceso**, sin mtime en la clave, y cachea incluso el fallo como `0`. El comentario en el código es explícito: *"Static package assets live for the process lifetime."* → **un PNG reescrito en sitio queda congelado en la versión que se subió a la GPU primero.** El contraste está en el mismo archivo (`GlRuntime.h:134-140`): las fotos de Face Swap sí se clavean con `path|mtime|size` justamente para evitar servir una textura vieja. Las texturas de paquete no.
- **Sin `#include`.** Cada `.frag` se materializa verbatim; los helpers se duplican a propósito para que el paquete sea autocontenido y redistribuible.

## 2. Effect templates (`effect-templates/`)

Un template apila varios efectos sobre un clip y los anima. Es el único mecanismo declarativo que toca audio. Formato: `effect-templates/<id>/template.json`.

Search path simétrico al de efectos, vía `defaultEffectTemplateSearchPaths()` en `src/engine/EffectTemplateCatalog.cpp` (variable de entorno `DRIFT_TEMPLATES_DIR`, luego `<appDir>`, luego `<AppData>/effect-templates`). Los IDs se resuelven por primera aparición, con un comentario en `scanDirectories()`: *"Installed addons supersede the bundled `<appDir>` copy"*.

Su capacidad y su techo están en [[Audio_reactividad_en_Drift]]. Resumen: **un parámetro animado por layer, un escalar compartido, sin bandas de frecuencia.**

## 3. Addons `.driftpkg` — cerrados para nosotros

Formato binario propio (`src/engine/AddonPackage.h:11-24`): magic `DRIFTPKG`, manifest JSON, payload en un frame zstd, digest SHA-256 y **firma Ed25519 de 64 bytes**.

`install()` (`AddonPackage.h:82-89`) descomprime a un `.partial` y **sólo promueve el directorio cuando la firma Ed25519 verifica** contra `AddonSigningKey.h`. `readManifest()` no valida firma y su propio comentario advierte no usarla para decidir confianza.

**Consecuencia práctica: sin la clave privada de CutWire Studios no se puede empaquetar un addon instalable.** Esta vía está cerrada para un tercero. La distribución de nuestro trabajo tiene que ser "copiá esta carpeta a `<AppData>/effects`", que sí funciona y no está vedado.

Los `kind` que un addon puede declarar hoy son `fonts`, `stickers`, `whisper-model`; el comentario en `AddonPackage.h:35-37` dice que `effects`, `transitions`, `audio-effects` y `onnx-model` son enrutables sin cambiar el formato, y `src/engine/AddonManager.cpp:625-640` ya enruta `effect-templates` a `reloadEffectTemplateCatalog()`.

## 4. Servidor MCP — el punto de extensión más potente

Drift expone un servidor MCP en localhost para que un agente edite el proyecto abierto. Documentado en `docs/MCP.md`.

- Se activa en **Settings → Agent access**, apagado en cada arranque por defecto. Bind **sólo a `127.0.0.1`**, token bearer que **rota por sesión**.
- También corre headless: `drift --headless`.

### Ops relevantes para un visualizador

| Op | Qué hace | Definición |
|---|---|---|
| `import_media({paths})` | Trae archivos al bin. Rutas absolutas o `file://`. Bloquea hasta probar cada uno (tope 15 s). No es undoable. | `src/mcp/McpCatalog.cpp:470` |
| `place_clip({asset, at, track, new_track})` | Pone un clip en la timeline, devuelve su id. | `:511` |
| `add_effect({effect, …})` | Apila un efecto, devuelve su `index`. | `:693` |
| `set_effect_param({index, key, value})` | Valor **estático**, no keyframe. | `:709` |
| **`set_keyframe({prop, at, value})`** | **Escribe un keyframe.** Para parámetros de efecto, `prop` se escribe `fx.<i>.<key>`. | `:838` |
| `list_keyframes({prop})` | Lee las keys existentes. | `:830` |
| `detect_beats({start, duration})` | **Bloquea** y devuelve bpm + tiempos de beats y onsets. | `docs/MCP.md:164` |
| `get_waveform({image:true})` | Devuelve una imagen con la onda y **un espectrograma de 64 bandas**. Prohibido dentro de `apply`. | `AppController.cpp` ~26935-27120 |
| `apply({ops:[…]})` | Batch. | `:1353` |

### Trampas de MCP, medidas

- **`apply` no es atómico.** Para en el primer error y deja aplicado todo lo anterior: `{ok:false, error:"apply_failed", stopped:<i>, done:[…]}`.
- **Un batch no puede referenciar un id creado en el mismo batch.** Hay que cortar después de `place_clip` o `add_effect` para leer el id/index.
- **Sin `maxItems` declarado** en el array de `ops`: no hay tope numérico de keyframes por batch, sólo el costo.
- **`set_keyframe_interpolation` mueve el playhead** a `at`, lo que cambia el destino de ops posteriores en el mismo batch.
- **El stack de efectos vive en un *adjustment clip* enlazado**, creado en su propio lane y reportado como `host:{track,index,clip}`. Hay que seguir direccionando el clip original, y esperar ese lane extra en `inspect`.
- **El análisis de beats es transitorio:** cualquier edición que cambie la mezcla lo invalida. Chequear `stale` en `inspect({detail:true}).beats` antes de confiar en una grilla vieja (`docs/MCP.md:184`).

## Tabla de decisión

| Mecanismo | Instalable por un tercero | Puede leer audio | Sirve para un visualizador de espectro |
|---|---|---|---|
| Paquete de efecto GPU | ✅ sin firma, a `<AppData>/effects` | ❌ ningún uniform de audio | ❌ no por sí solo |
| Effect template | ✅ sin firma | ⚠️ sólo onsets/beats, escalar | ❌ no da espectro |
| Addon `.driftpkg` | ❌ requiere firma Ed25519 | — | ❌ vía cerrada |
| Servidor MCP | ✅ activable por el usuario | ✅ onsets, beats, espectrograma de 64 bandas | ✅ **es el camino** |
