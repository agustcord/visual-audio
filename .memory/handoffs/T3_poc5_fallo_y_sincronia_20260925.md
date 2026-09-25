---
tipo: "handoff"
turno: 3
agente: "Kiro"
fecha: 2026-09-25
estado: "cerrado — PoC-5 FALLÓ, bloqueado esperando al fundador"
---

# T3 — PoC-5 falló, tres hipótesis descartadas, y una desincronización de 100 ms

El fundador probó el overlay en Drift. **PoC-5 falló.** Este turno documentó la falla, descartó tres causas con evidencia, preparó un experimento para separar las dos que quedan, y encontró tres defectos reales del generador que la verificación de T2 aprobaba en verde.

## El reporte del fundador

> «Hice la prueba para ver la onda de audio debi ponerlo encima de las otras pista, y ponerle "trama", para que se vea visible lo anda y no el fondo negro, y se vea la parte inferior, el reproductor no se puso lento.»

Interpretación: **Drift no honró el canal alpha**, y lo resolvió aplicando el modo de fusión Trama (Screen). Trama funciona por casualidad —negro en Screen no aporta nada al resultado— pero aclara los colores y dejaría de funcionar sobre un fondo claro. **No cuenta como PoC-5 cumplido.**

Dos datos positivos del mismo reporte:
- **PoC-4 pasó:** Drift importó y reprodujo el archivo sin marcarlo corrupto.
- **El reproductor no se puso lento.** El riesgo de rendimiento que anotamos en T1 y T2 (Drift niega proxies a clips transparentes, `PreviewProxyRenderer.cpp:40-45`) **no se materializó**. Se puede bajar de la lista de riesgos.

Según `docs/PLAN_ETAPA1.md` §4, PoC-5 es el punto de control duro: si falla se para y se replantea. **Se paró. No se avanzó al MVP.**

## Frontera declarada

**Creado:** `docs/PRUEBA_T3_ALPHA.md`, `tests/verificar_sincronia.py`, este handoff.
**Modificado:** `tools/generar_overlay.py`, `docs/POC_RESULTADOS.md` (adenda T3), `RETOMAR.md`, `.memory/log.md`, `.memory/wiki/MOC_Handoffs.md`.
**Generado en `build/`** (no versionado): `A_banda_webm.webm`, `B_lienzo_webm.webm`, `C_lienzo_prores.mov`.

**NO se tocó:** `sobre_este_plugins.txt`; `C:\Program Files\Drift\` (sólo lectura, sólo se leyeron cadenas de `avcodec-61.dll`); la carpeta de datos de Drift; `_reference/drift-src/` (citado, no editado); `docs/VIABILIDAD.md` (sigue vigente); `docs/PLAN_ETAPA1.md` (el Gate no cambió). **No se abrió Drift ni se activó su MCP.** No se forkeó ni compiló Drift.

## Tres hipótesis descartadas con evidencia

Importante para el próximo agente: **no las vuelvas a investigar.**

| Hipótesis | Verificación | Resultado |
|---|---|---|
| El archivo no declara el alpha donde Drift lo busca | `MediaProbe.cpp:37-50` lee el tag `alpha_mode` del contenedor además del formato de píxel; nuestro archivo tiene `alpha_mode=1` | ❌ Drift sí debería detectarlo |
| El FFmpeg de Drift no trae el decodificador libvpx, y el nativo de VP9 ignora el plano alpha | Cadenas presentes en `avcodec-61.dll` de Drift: `WebM Project VP9 Decoder`, `libvpx VP9`, `libvpx-vp9` | ❌ el decodificador está |
| Faltaba `-auto-alt-ref 0`, que el exportador de Drift desactiva para VP9 con alpha (`Exporter.cpp:895-898`) | Auditoría cuadro por cuadro de los 477 cuadros del archivo probado: **cero opacos** | ❌ el alpha estaba sano de punta a punta |

La tercera se aplicó igual al generador: Drift la documenta como obligatoria y no cuesta nada.

## Las dos hipótesis vivas, y el experimento

No se separan leyendo código. Hacía falta un dato del fundador, así que se le preguntó en vez de adivinar (`docs/PRUEBA_T3_ALPHA.md`):

1. **Relleno por diferencia de tamaño** — clip 1920×320 en proyecto 1080p, Drift rellena con negro opaco. **Predice que el negro se vio como una franja.** Lo resolvería el archivo B.
2. **Drift descarta el alpha de WebM/VP9 en su render.** **Predice negro en todo el cuadro**, y que C (ProRes 4444) funcione.

Las dos preguntas al fundador: qué forma tenía el negro (franja o cuadro entero), y de qué tamaño es el lienzo de su proyecto. Los tres archivos discriminan.

**Si B y C fallan, la pista más prometedora que queda sin investigar** es la premultiplicación: `GpuCompositor.cpp:917-923` compone con alpha premultiplicado (`GL_ONE / GL_ONE_MINUS_SRC_ALPHA`) y `showwaves` entrega alpha **recto**. Si Drift no premultiplica al subir la textura, sobre negro el resultado se vería negro. Está anotado en `RETOMAR.md`.

## Lo que salió mal del lado nuestro

Buscar la causa destapó tres defectos reales. Los dos primeros afectaban al archivo que el fundador ya había probado.

### 1. 🔴 El overlay iba 100 ms atrasado

`showwaves` entrega los cuadros con intervalos exactos de 1/fps pero **etiqueta el primero en PTS 0.100 s en vez de 0**. Corrimiento constante de 3 cuadros: la onda reaccionaba después del golpe. Es el defecto más importante del turno y el más fácil de no notar nunca.

Corregido con `setpts=PTS-STARTPTS`. Medido contra tres puntos de referencia independientes de la pista de prueba, que se movieron de **0.133 / 1.133 / 10.133 s** a **0.033 / 1.033 / 10.033 s**. El residuo de 33 ms es **un cuadro exacto** de cuantización: un ataque en *t* cae en el cuadro que contiene *t*. Correcto por construcción.

Prueba de regresión nueva: `tests/verificar_sincronia.py`. Mide contra los **ataques** conocidos de la pista y no contra los silencios, a propósito: el borde del silencio es difuso porque la cola de decaimiento del bombo ocupa ~600 ms, y medir contra un borde difuso daba un desvío aparente que no era un bug. Se probó y confundía; está documentado en el propio archivo para que nadie lo "arregle" de vuelta.

### 2. Faltaban 3 cuadros, y PoC-3 lo aprobaba con "desvío 0.0 ms"

El mismo corrimiento hacía que `-t` recortara la cola: **477 cuadros donde van 480**.

**Lo serio no es el bug, es que mi propia verificación lo declaraba perfecto.** Leía `format=duration`, y el WebM declaraba 16.000 s teniendo 477 cuadros. Se detectó porque el mismo contenido en MOV declaró los 15.900 s reales y reprobó: **dos formatos discrepando sobre el mismo contenido.** Si no hubiera agregado el formato MOV para otra cosa, esto seguiría oculto.

Corregido: PoC-3 **cuenta los cuadros decodificados** (dato que la auditoría de alpha ya produce de paso) y, si el contenedor discrepa, lo dice explícitamente.

### 3. La verificación reprobaba archivos correctos

PoC-2b contaba como falla los cuadros sin nada dibujado. En un pasaje silencioso **corresponde** que no se dibuje nada: confundía silencio con rotura. Un verificador que cría lobos deja de servir. Corregido: los vacíos se informan como nota y sólo reprueban los **opacos**.

## La lección del turno

La verificación de T2 medía **dos cuadros sueltos** y la **duración declarada**. Con ese instrumento, un archivo 100 ms desfasado y con tres cuadros faltantes pasaba entero en verde.

La de ahora recorre **todos** los cuadros y mide contra puntos de referencia conocidos del audio. Es la que debí escribir en T2. Anotado en `RETOMAR.md` como regla: si agregás un criterio, que recorra todo el material y mida contra algo conocido del audio, no contra lo que el archivo dice de sí mismo.

## Novedades del generador

- `--formato {webm,mov}` — los dos formatos con alpha que Drift exporta por su cuenta. ProRes 4444 pesa **10 veces más** (121 MB contra 11,7 MB por 16 s) porque no tiene pérdida.
- `--lienzo ANCHOxALTO`, `--posicion {arriba,centro,abajo}`, `--margen PX` — genera el cuadro completo del tamaño del proyecto con la banda situada dentro y el resto **transparente de verdad** (verificado: la zona rellenada mide alpha 0 exacto, mínimo y máximo, mientras la banda va de 0 a 255). Salió del experimento y queda como función: resuelve la personalización de **posición** sin tocar Drift.
- `-auto-alt-ref 0` y `-lag-in-frames 0` en VP9, como hace Drift.

## Dónde retomar

`RETOMAR.md`. El próximo agente **no debe cambiar nada del generador hasta tener la respuesta del fundador** a las dos preguntas de `docs/PRUEBA_T3_ALPHA.md`. Ponerse a modificar sería adivinar entre dos hipótesis que un solo dato separa.
