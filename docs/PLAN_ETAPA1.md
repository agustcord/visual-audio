# Plan y presupuesto — Etapa 1

**Estado: APROBADO por el fundador el 2026-09-25.** El registro del Gate, con sus palabras verbatim, está en §7.
El desarrollo está habilitado por el **camino A**. Los otros caminos siguen cerrados: ver §7 para qué quedó habilitado y qué no.

**Fecha:** 2026-09-25 · **Turno:** T1 (plan) / T2 (Gate registrado) · **Agente:** Kiro
**Depende de:** `VIABILIDAD.md` (veredicto: viable por el camino A)

---

## 1. Las tres decisiones — resueltas

### Decisión 1 — Qué camino se toma → **CAMINO A**

**Camino A** (generar el visualizador con FFmpeg y componerlo como overlay con alpha). Justificación en `VIABILIDAD.md` §7-8.

- **Camino B** (keyframes calculados vía MCP): **fuera del alcance de la Etapa 1.**
  ⚠️ **Corrección de una premisa del Gate.** El fundador lo descartó preguntando si consumía muchos recursos. **No los consume**: su costo está clasificado como *bajo*, igual que el de A. Su límite real es de **capacidad**: produce un escalar por instante, así que no puede dibujar barras de espectro — cada barra necesitaría su propio parámetro en su propio efecto. Queda fuera porque **el camino A ya cubre el objetivo**, no porque sea caro. Anotado como añadido barato para más adelante.
- **Camino C** (fork de Drift): **a futuro, y con compromiso nulo con terceros.** No se forkea, no se ofrece PR a upstream, no se contacta a CutWire Studios. Queda como posible evolución, nada más.

### Decisión 2 — Modelo "overlay pre-renderizado" → **ACEPTADO**

- **Lo que se gana:** tamaño, posición, opacidad y velocidad quedan manejados por los controles nativos de Drift — arrastrás el overlay con el mouse, le ponés keyframes, lo animás como cualquier clip. Y sale gratis.
- **Lo que se acepta perder:** cambiar el **color** o el **estilo** de la onda implica regenerar el overlay (segundos, no minutos). No hay un slider de color en vivo dentro de Drift.

### Decisión 3 — Presupuesto → **APROBADO** (10–14 turnos, §4)

---

## 2. Alcance de la Prueba de Concepto (PoC)

El documento fundacional pide para el PoC *"solo capturar el audio y poder expresar su movimiento de forma rudimentaria"*. Traducido a algo falsable:

### Qué entra

- Un script que toma **un archivo de audio** y genera **un video con canal alpha** (WebM VP9) con la forma de onda dibujada sobre fondo transparente.
- Verificación de que **Drift lo importa y lo compone con transparencia** sobre una pista de video.
- El overlay dura lo mismo que el audio y está **alineado temporalmente** con él.

### Qué NO entra

- Personalizaciones (eso es el MVP).
- Espectro por bandas (el PoC usa forma de onda, que es más simple).
- Automatización vía MCP: en el PoC la importación se hace **a mano**, arrastrando el archivo a Drift. Automatizar antes de validar el formato es poner el carro adelante.
- Interfaz gráfica de ningún tipo.

### Criterios de aceptación (verificables, no opinables)

| # | Criterio | Cómo se verifica |
|---|---|---|
| PoC-1 | El generador produce un `.webm` desde un `.wav`/`.mp3` sin error | Exit code 0 y el archivo existe con tamaño > 0 |
| PoC-2 | El archivo tiene canal alpha real | `ffprobe` reporta un `pix_fmt` con alpha (`yuva420p`) |
| PoC-3 | La duración del overlay coincide con la del audio (±1 frame) | `ffprobe` de las dos duraciones, comparadas |
| PoC-4 | Drift lo importa sin marcarlo como faltante ni corrupto | Aparece en el bin con duración correcta |
| PoC-5 | **Drift lo compone con transparencia**: se ve el video de fondo a través del overlay | Captura de un frame con el overlay sobre un video, inspeccionada visualmente |
| PoC-6 | La onda se mueve en sincronía con la música | Reproducción y verificación a ojo por el fundador |

**PoC-5 es el criterio que mata o salva el camino A.** Si Drift no compone la transparencia como esperamos, hay que replantear antes de gastar un turno más. Por eso va en el PoC y no en el MVP.

---

## 3. Alcance del MVP

El documento fundacional pide *"capturarlo de una forma agradable y que permita realizar algunas pequeñas personalizaciones (velocidad, tamaño, posición, color y opacidad)"*.

### Qué entra

- **Estilos de visualización:** al menos forma de onda y espectro de barras.
- **Las cinco personalizaciones**, repartidas así:

| Personalización | Dónde vive | Quién la implementa |
|---|---|---|
| Color | Parámetro del generador | Nosotros |
| Velocidad | Parámetro del generador + speed curve del clip | Nosotros / Drift |
| Tamaño | Transform del clip | **Drift (gratis)** |
| Posición | Transform del clip | **Drift (gratis)** |
| Opacidad | Propiedad `opacity` del clip | **Drift (gratis)** |

- **Resolución y fps** ajustables, por defecto los del proyecto.
- **Documentación de uso** para el fundador: cómo generar y cómo colocar.
- Opcional, si el presupuesto lo permite: **automatización vía MCP** (importar y colocar el overlay en la pista correcta sin intervención).

### Qué NO entra en el MVP

- Interfaz gráfica propia. La línea de comandos primero; si el fundador la quiere, es etapa siguiente.
- Editor visual de estilos.
- El camino C (fork de Drift).
- Cualquier cosa que requiera modificar el editor.

### Criterios de aceptación

| # | Criterio | Cómo se verifica |
|---|---|---|
| MVP-1 | Al menos 2 estilos funcionando (onda y espectro) | Un render de cada uno, inspeccionado |
| MVP-2 | El color se puede cambiar y el cambio se ve | Dos renders con colores distintos |
| MVP-3 | Tamaño, posición y opacidad se ajustan **dentro de Drift** sin regenerar | El fundador lo hace y lo confirma |
| MVP-4 | Un video musical corto editado de punta a punta con el visualizador | El fundador exporta y lo aprueba |
| MVP-5 | La documentación alcanza para que el fundador lo use solo | El fundador lo usa **sin preguntarle nada al agente** |

**MVP-5 es el criterio real de éxito del MVP.** Lo demás es infraestructura.

---

## 4. Presupuesto propuesto

Turnos = intercambios de agente. La estimación incluye verificación, no sólo escritura de código.

### Etapa 1 completa: **10–14 turnos**

| Tramo | Turnos | Qué entrega |
|---|---|---|
| **T1** ✅ consumido | 1 | Registro, git, viabilidad, este plan |
| **T2 — Gate + andamiaje** | 1 | Decisiones del fundador registradas; estructura del proyecto y primer commit |
| **T3–T4 — PoC** | 2 | Generador mínimo de overlay; PoC-1 a PoC-4 verificados |
| **T5 — Validación del PoC en Drift** | 1 | **PoC-5 y PoC-6.** Requiere al fundador con Drift abierto |
| **T6–T9 — MVP** | 4 | Estilos, color, velocidad, resolución; MVP-1 y MVP-2 |
| **T10 — Documentación de uso** | 1 | Guía para el fundador; MVP-5 |
| **T11 — Validación del MVP** | 1 | MVP-3 y MVP-4. Requiere al fundador editando |
| **Reserva** | 2–3 | Imprevistos. Los overlays con alpha suelen tener sorpresas de color y premultiplicación |

### Puntos de control duros

- **Después de T5:** si PoC-5 falla, **se para y se replantea.** No se sigue al MVP con el camino roto.
- **Después de T9:** el fundador decide si el MVP alcanza o si mueve el alcance.

### Lo que no está presupuestado

- El **camino C** (fork de Drift). Si se decide ir, es un proyecto aparte con su propio presupuesto. Estimación gruesa, sólo para dimensionar: **8–15 turnos** sólo para levantar el build de Qt6+FFmpeg y compilar Drift sin modificar nada, antes de escribir una línea de la tubería de audio. Más mantenimiento indefinido.
- Una **interfaz gráfica**.
- Publicar el trabajo o negociar un PR con upstream.

---

## 5. Riesgos, y qué hacemos con cada uno

| Riesgo | Impacto | Mitigación |
|---|---|---|
| Drift no compone la transparencia como esperamos | **Alto** — invalida el camino A | Se verifica en T5, antes de construir nada encima |
| Preview lento por el overlay con alpha (`PreviewProxyRenderer.cpp:40-45` niega proxies a clips transparentes) | Medio | Generar a la resolución del proyecto y no más; medir en T5 |
| Desalineación temporal entre overlay y audio | Medio | PoC-3 lo mide; es aritmética, no azar |
| Color incorrecto por premultiplicación de alpha | Medio | Está en la reserva; es el bug clásico de este terreno |
| Drift cambia y rompe lo construido | Bajo hoy | Nada de lo que hacemos toca internals de Drift: usamos importación de media y transform de clips, la superficie más estable que tiene |
| Que el fundador no esté disponible para T5 y T11 | Medio | Son los dos turnos que **requieren un humano con Drift abierto**. Conviene coordinarlos |

---

## 6. Qué queda explícitamente fuera de la Etapa 1

El documento fundacional dice que *"para futuro se busca que se pueda elegir distintas personalizaciones o suficiente libertad para que el usuario pueda personalizarlo"*. Eso es **Etapa 2 o posterior**. No se diseña acá, pero se anota para no perderlo:

- Presets de estilo, y estilos definidos por el usuario.
- Reacción por bandas de frecuencia independientes (graves separados de agudos).
- Interfaz gráfica.
- **Camino B — añadido barato, no descartado por costo.** Escribir keyframes calculados por nosotros vía MCP para que el video (o el propio overlay) pulse con la energía real de la música. Cuesta poco; simplemente no hace falta para el MVP. Si alguna vez se quiere, el punto de entrada es `set_keyframe({prop:"fx.<i>.<key>", at, value})`.
- Camino C: uniforms de audio en un fork, con visualizador como efecto GPU nativo y sliders en vivo. **Compromiso nulo con terceros por decisión del fundador:** no se forkea ni se ofrece PR a upstream.

---

## 7. Registro del Gate

Registrado por el agente Kiro en el turno **T2**, el **2026-09-25**. Se registra como **procedencia**, no como veredicto propio.

### Texto del fundador, verbatim

> «Apruebo el plan, la ruta A me parece la mejor, ruta B, según entendí puede consumir muchos recursos? si es asi lo descarto, Ruta C, lo dejamos a futuro como una posible evolución, pero por el momento nulo commpromiso con teceros. Sobre el mommento que necesite Drift abierto avisame en ese turno, Drift cuanta con una opción de conectar vía MCP avisame si también necesita tener acceso, y que cree un archivo con audio para este proyecto, por el resto puedes continuar según tu plan»

### Decisiones resueltas

| Decisión | Resuelta | Contenido |
|---|---|---|
| 1 — Camino técnico | ✅ | **Camino A.** B fuera del alcance (ver la corrección de premisa abajo). C a futuro, **compromiso nulo con terceros**. |
| 2 — Modelo overlay pre-renderizado | ✅ | Aceptado implícitamente al aprobar el plan y elegir A: es el modelo que A implica, y el fundador lo tenía descrito con su costo antes de decidir. |
| 3 — Presupuesto en turnos | ✅ | Aprobado, 10–14 turnos (§4). |

### Corrección de premisa, declarada y no silenciada

El fundador descartó el camino B con una condición: *"según entendí puede consumir muchos recursos? si es asi lo descarto"*. **La condición no se cumple: el camino B no consume muchos recursos.** Este plan y `VIABILIDAD.md` §7 lo clasifican con costo **bajo**, igual que A.

El agente informó la corrección al fundador en el mismo intercambio y **mantuvo el descarte del alcance**, porque la conclusión no cambia por otro motivo: **el camino A ya cubre el objetivo del MVP**, y B no puede dibujar espectro. Queda anotado en §6 como añadido barato, no como opción descartada por costo.

Si el fundador quiere revisar esta lectura, el punto a reabrir es §1 Decisión 1.

### Pedidos adicionales del fundador, y su estado

| Pedido | Estado |
|---|---|
| *"sobre el momento que necesite Drift abierto avisame en ese turno"* | ✅ Anotado. El turno es **T5** (criterio PoC-5). El agente debe avisar **al comenzar ese turno**, no antes ni después. |
| *"Drift cuenta con una opción de conectar vía MCP, avisame si también necesita tener acceso"* | ✅ Respondido: **no hace falta para T5.** La validación de PoC-5 es importación manual. MCP sólo sería necesario si se automatiza la colocación del overlay, que es opcional del MVP (§3). Si se llega a eso, el agente lo pedirá explícitamente. |
| *"que cree un archivo con audio para este proyecto"* | ✅ Ejecutado en T2. Ver §8. |

### Qué quedó habilitado

- ✅ Desarrollo por el **camino A**: generador de overlay, PoC y MVP según §2 y §3.
- ✅ Crear archivos de prueba dentro del repositorio.
- ❌ **No habilitado:** forkear o compilar Drift, contactar a CutWire Studios, escribir en `C:\Program Files\Drift\`, ni activar el servidor MCP de Drift sin pedirlo primero.

---

## 8. Material de prueba del proyecto

A pedido del fundador, el proyecto tiene su propio archivo de audio de prueba. Está en `tests/fixtures/`, es **sintético y reproducible** (lo genera un script del repositorio, no es material con derechos), y está construido a propósito con transientes marcados para que la forma de onda y la detección de onsets tengan algo visible que mostrar.

Detalle y comando de regeneración en `tests/fixtures/README.md`.
