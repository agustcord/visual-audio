---
tipo: "nota-decision"
estado: "propuesta — pendiente del Gate del fundador"
relacionado: ["Audio_reactividad_en_Drift", "Extensibilidad_de_Drift"]
verificado: 2026-09-25
---

# Caminos de implementación

Dado el bloqueo documentado en [[Audio_reactividad_en_Drift]], hay **tres rutas técnicamente viables** y una que parece viable pero no lo es. Esta nota las compara para que la decisión sea informada, no por descarte.

## Camino A — Generar el visualizador fuera y componerlo como overlay ⭐ recomendado

**Idea:** un programa nuestro toma el audio, genera un video con canal alpha que contiene sólo la onda o el espectro sobre fondo transparente, y lo importa a Drift como un clip de overlay en una pista superior.

**Por qué funciona.** Los dos extremos están verificados:
- La generación: FFmpeg **8.0.1** está instalado en `C:\ffmpeg\bin\ffmpeg.exe` y tiene todos los filtros de visualización compilados: `showwaves`, `showwavespic`, `showspectrum`, `showspectrumpic`, `showfreqs`, `showcqt`, `avectorscope`, `showvolume`. Verificado con `ffmpeg -filters`.
- El compositado: Drift soporta alpha de punta a punta, incluido WebM VP9, con código dedicado a ello (citas en [[Drift_editor]]).

**Cómo se cubren las personalizaciones que pide el documento fundacional:**

| Personalización | Dónde se resuelve |
|---|---|
| Tamaño | Transform del clip en Drift (`width`/`height`), o la escala de render en el generador |
| Posición | Transform del clip en Drift (`x`/`y`) — arrastrable a mano, keyframable |
| Opacidad | Propiedad `opacity` del clip en Drift |
| Color | Parámetros del filtro en el generador (`colors=` en `showwaves`/`showspectrum`) |
| Velocidad | La escala temporal del render, y/o el speed curve del clip |

Cuatro de las cinco salen **gratis** usando controles que Drift ya tiene y que el usuario ya sabe usar. Eso es lo que hace fuerte a este camino: no reimplementamos un inspector.

**Costos y trampas:**
- Es un **paso de render**: cambiar el color implica regenerar el overlay. No es un slider en vivo.
- `PreviewProxyRenderer.cpp:40-45` rechaza proxies en clips con transparencia → preview más caro. Mitigable generando el overlay a la resolución del proyecto y no más.
- Hay que resolver el alineamiento temporal del overlay con el audio de la timeline. Es aritmética, no magia, pero es donde van a aparecer los bugs.

## Camino B — Calcular keyframes propios y escribirlos vía MCP

**Idea:** hacer lo que hace un effect template, pero mejor: leer los datos de audio con `get_waveform`/`detect_beats`, calcular nosotros los valores, y escribirlos con `set_keyframe` en `fx.<i>.<param>`.

**Qué gana sobre un template:** un template escribe un `peak` constante y descarta la fuerza del onset. Nosotros podemos escribir **un valor distinto por keyframe**, proporcional a la energía real. Eso ya es una mejora audible sobre `beat_drop`.

**Su techo, que es duro:** produce **un escalar por instante**, no un espectro. Sirve para "que el video pulse con la música" (escalar, zoom, brillo, shake). **No sirve para dibujar barras de espectro**, porque no hay forma de animar 32 barras independientes: cada barra necesitaría su propio parámetro en su propio efecto, y el costo de keyframes se multiplica por 32.

Útil como **complemento** del camino A, no como sustituto.

## Camino C — Fork de Drift agregando uniforms de audio

**Idea:** modificar el C++ para exponer al shader una textura de audio (por ejemplo `u_audioTexture` con la envolvente y las bandas indexadas por tiempo, en la línea de cómo Drift ya expone `u_depthTexture`). Con eso, un visualizador **sí** se puede escribir como paquete de efecto GPU, reactivo en tiempo de render, con sliders vivos.

**Es legal:** GPLv3 habilita el fork, con la obligación de publicar el derivado bajo la misma licencia.

**Es el camino "correcto" a nivel arquitectura y el más caro por lejos:**
- Requiere levantar el toolchain de build de Qt6 + FFmpeg (ver `docs/BUILDING.md` de Drift, 21 KB de instrucciones).
- Requiere mantener el fork sincronizado con upstream, indefinidamente.
- El fundador **no es del equipo de Drift**, así que o mantiene un binario propio, o negocia un PR upstream cuyo tiempo no controla.
- La infraestructura ya existente para `depth` es un molde bastante claro a seguir, lo que baja el riesgo técnico pero no el costo de mantenimiento.

Razonable como **objetivo de largo plazo** o como PR a upstream. Irresponsable como punto de partida.

## Camino descartado — Hornear un espectrograma a PNG y leerlo desde un shader

Parece el atajo elegante y **no funciona**. Tres razones, todas verificadas en código:

1. `pipeline.textures[]` **valida la existencia del archivo en tiempo de parseo del catálogo** (`GpuPackageParse.cpp:248-265`), y el catálogo se escanea al arrancar. Un PNG generado después no entra sin recargar el catálogo.
2. `staticTexture()` (`GlRuntime.cpp:3044-3063`) cachea **por ruta y para toda la vida del proceso**, sin mtime en la clave. Reescribir el PNG en sitio **no** actualiza lo que ve la GPU: queda congelado hasta cerrar Drift.
3. El campo `file` está pensado como relativo al directorio del paquete. Una ruta absoluta probablemente funcionaría por cómo se comporta `QDir::filePath()`, pero es un efecto colateral, no un contrato — y no hay recarga en caliente igual.

Para que este camino sirviera habría que generar **un paquete de efecto nuevo por cada clip de audio** y reiniciar Drift. Eso no es un producto.

## Recomendación

**Camino A como base del PoC y del MVP, con el camino B como capa opcional encima** (pulsos sincronizados sobre el propio overlay o sobre el video). **Camino C anotado como evolución futura**, y como la contribución que eventualmente valdría la pena ofrecerle a upstream.

La decisión es del fundador, y no es sólo técnica: el camino C implica mantener un fork de un editor de video, que es un compromiso de tiempo muy distinto a generar overlays.
