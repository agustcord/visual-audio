---
tipo: "nota-entidad"
estado: "activo"
relacionado: ["Extensibilidad_de_Drift", "Audio_reactividad_en_Drift"]
verificado: 2026-09-25
---

# Drift (el editor)

Editor de video de escritorio de **CutWire Studios**, libre y de código abierto. No es un proyecto nuestro: el fundador de este proyecto es **un usuario externo**, no parte del equipo de Drift (declarado en `sobre_este_plugins.txt`). Eso condiciona todo: no tenemos autoridad para cambiar el editor, sólo para extenderlo por sus puntos de extensión públicos, o para mantener un fork.

## Ficha

| Dato | Valor | Fuente |
|---|---|---|
| Repositorio | `https://github.com/CutWire-Studios/Drift` | documento fundacional |
| Licencia | **GPLv3** | `LICENSE`, `README.md` |
| Stack | **Qt 6 + FFmpeg**, C++ con UI en QML | `README.md`, `CMakeLists.txt` |
| Instalación local | `C:\Program Files\Drift\drift.exe` | verificado en disco |
| Datos escribibles | `C:\Users\Jonatan Agustín\AppData\Roaming\CutWire Drift\` | `QStandardPaths::AppDataLocation` |
| Plataformas | Linux (Flathub/AppImage), Windows, macOS (Apple Silicon), Android | `README.md` |

La licencia GPLv3 es un dato **operativo**, no decorativo: habilita forkear y redistribuir modificaciones, con la obligación de publicar el fuente derivado bajo la misma licencia. Es lo que hace legalmente posible el camino C de [[Caminos_de_implementacion]].

## Lo que ya trae y nos importa

Drift **ya tiene** varias piezas que un visualizador de audio necesitaría, y conviene no reimplementarlas:

- **Timeline multipista real** con overlays, y clips de texto, forma y sticker sobre el video.
- **Compositor único para preview y export.** El README lo vende como "lo que ves es lo que exportás", y en el código es literal: `FrameCompositor` → `EffectProcessor` → `GpuEffectExecutor` sirven a los dos. Un visualizador que se vea bien en preview se exporta igual.
- **Detección de beats y onsets** sobre la mezcla (ver [[Audio_reactividad_en_Drift]]).
- **Keyframes con easing, tangentes bezier y hold** sobre casi cualquier propiedad, incluidos los parámetros de efecto.
- **Soporte real de canal alpha** en decodificación y compositado, incluido WebM VP9 con alpha:
  - `src/engine/MediaProbe.cpp:37-46` detecta alpha por `AV_PIX_FMT_FLAG_ALPHA`.
  - `src/engine/ClipReader.cpp:1002-1010` fuerza el decodificador `libvpx-vp9` porque *los decodificadores nativos vp9/vp8 ignoran el plano alpha de WebM*.
  - `src/engine/ClipReader.cpp:1209-1214` desactiva la decodificación por hardware en fuentes con alpha (las superficies NV12 tirarían el plano).
  - `src/engine/GpuCompositor.cpp:917-923` compone con blend premultiplicado `GL_ONE / GL_ONE_MINUS_SRC_ALPHA`.
  - **Trampa medida:** `src/engine/PreviewProxyRenderer.cpp:40-45` rechaza proxies en clips con transparencia ("Clips with transparency can't use a proxy"). En material pesado con alpha eso significa decodificación por software sin proxy, o sea preview caro.
- **Servidor MCP local** para que un agente edite el proyecto abierto (ver [[Extensibilidad_de_Drift]]).

## Lo que NO trae

- **Ningún sistema de plugins nativos.** No carga `.dll`/`.so` de terceros. Buscar "plugin" en este proyecto y esperar una API de plugins es el primer error a evitar.
- **Ningún dato de audio en el pipeline de render.** Es el bloqueo central del proyecto; está documentado en [[Audio_reactividad_en_Drift]].
