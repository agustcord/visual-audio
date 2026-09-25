# Prueba T3 — ¿por qué Drift mostró fondo negro?

**Para:** Jonatan (fundador) · **Turno:** T3 · **Fecha:** 2026-09-25

En T2 probaste el overlay y tuviste que ponerle modo de fusión **Trama** (Screen) para no ver un fondo negro. Eso significa que **Drift no usó el canal alpha**. Trama funciona de casualidad —negro en modo Screen no aporta nada— pero aclara los colores y dejaría de funcionar sobre un fondo claro, así que no sirve como solución.

Este documento tiene **dos preguntas para vos** y **tres archivos para probar**. Con eso cierro el diagnóstico.

---

## Lo que ya descarté, leyendo el código de Drift

Para que no parezca que estoy tirando archivos a ver si alguno pega: eliminé tres explicaciones con evidencia.

| Hipótesis | Cómo la descarté | Resultado |
|---|---|---|
| El archivo no declara el alpha donde Drift lo busca | `MediaProbe.cpp:37-50` lee el tag `alpha_mode` del contenedor, además del formato de píxel. Nuestro archivo tiene `alpha_mode=1` | ❌ Drift **sí** debería detectarlo |
| El FFmpeg de Drift no trae el decodificador libvpx, y el decodificador nativo de VP9 ignora el plano alpha | Busqué las cadenas del decodificador en `avcodec-61.dll` de Drift: `WebM Project VP9 Decoder`, `libvpx VP9` y `libvpx-vp9` están **presentes** | ❌ el decodificador está |
| Al archivo le faltaba `-auto-alt-ref 0`, que el exportador de Drift desactiva para VP9 con alpha (`Exporter.cpp:895-898`) | Audité el alpha **cuadro por cuadro**, los 477 del archivo que probaste: **cero cuadros opacos** | ❌ el alpha del archivo estaba sano de punta a punta |

La tercera valía la pena mirarla porque el propio Drift lo documenta como obligatorio, y **ahora el generador lo aplica igual** — es gratis y evita un modo de falla real.

Con eso agotado, me quedan dos explicaciones y no puedo elegir entre ellas leyendo código. Necesito un dato tuyo.

---

## Las dos preguntas

### 1. El negro que viste, ¿qué forma tenía?

- **(a)** Una **franja** del alto de la onda, como del tercio inferior de la pantalla, y el resto del video se veía normal.
- **(b)** Todo el cuadro negro, tapando el video entero.

Si es **(a)**, la causa más probable es que el clip medía 1920×320 y tu proyecto es 1080p: Drift lo encajó y rellenó con negro **opaco**. El archivo estaba bien y el problema es de tamaño.

Si es **(b)**, Drift está descartando el canal alpha en su cadena de render, y la solución es cambiar de formato.

### 2. ¿De qué tamaño es el lienzo de tu proyecto?

Supongo 1920×1080. Si es otro, decime y regenero con ese.

---

## Los tres archivos

Están en `build/`. Probá **B** primero: si funciona, terminamos.

| Archivo | Qué es | Qué demuestra si funciona |
|---|---|---|
| **A** `A_banda_webm.webm` | Igual que el que probaste (1920×320), pero con los arreglos de T3 | Que el problema era uno de los defectos que corregí |
| **B** `B_lienzo_webm.webm` | **Cuadro completo 1920×1080**, con la onda como banda abajo y el resto transparente | Que el negro era relleno por diferencia de tamaño — hipótesis (a) |
| **C** `C_lienzo_prores.mov` | ProRes 4444 en MOV, 1920×1080. Es el **otro** formato con alpha que Drift exporta por su cuenta, y lo detecta por dos vías independientes | Que WebM es el problema y hay que usar MOV |

Los tres pasan la verificación automática: 480 de 480 cuadros con transparencia intacta, duración exacta, y sincronía dentro de un cuadro.

### Cómo probarlos

Para cada uno, **sin ponerle Trama ni ningún modo de fusión** — eso es justamente lo que estamos tratando de no necesitar:

1. Un video cualquiera en una pista.
2. El archivo importado en una pista **por encima**.
3. ¿Se ve el video de fondo a través de la onda?

Decime cuáles funcionan. Con eso queda cerrado.

> ⚠️ **C pesa 121 MB** para 16 segundos, porque ProRes 4444 no tiene pérdida. Si resulta que C es el único que funciona, el peso pasa a ser un problema de diseño a resolver y lo trato como tal — no te voy a proponer archivos de 1,3 GB por canción.

---

## Los tres defectos que encontré y corregí en el camino

Independientemente de cuál sea la causa del negro, buscarla destapó tres problemas reales. Los dos primeros afectaban lo que ya habías probado.

### 1. El overlay iba 100 ms atrasado respecto de la música 🔴

El más importante, y el más fácil de no notar nunca.

`showwaves` entrega los cuadros con intervalos perfectos, pero **etiqueta el primero en el instante 0.100 s en vez de 0**. Un corrimiento constante de tres cuadros: la onda reaccionaba después del golpe.

Se corrige rebasando los tiempos (`setpts=PTS-STARTPTS`). Medido contra tres puntos de referencia independientes de la pista de prueba:

| Punto conocido | Antes | Después |
|---|---|---|
| Primer bombo (0.0 s) | 0.133 s | 0.033 s |
| Entra el bajo (1.0 s) | 1.133 s | 1.033 s |
| Ataque del tramo intenso (10.0 s) | 10.133 s | 10.033 s |

Los 33 ms que quedan son **un cuadro exacto**: un golpe que suena en el instante *t* cae en el cuadro que contiene *t*. Eso es correcto, no es error.

Hay ahora una prueba de regresión que lo vigila: `python tests\verificar_sincronia.py`.

### 2. Faltaban 3 cuadros al final, y mi verificación decía que no

El mismo corrimiento hacía que el recorte final se comiera los últimos tres cuadros: **477 donde van 480**.

Lo que me hace ruido de esto no es el bug, es que **mi verificación lo aprobaba con "desvío 0.0 ms"**. Estaba leyendo la duración que declara el contenedor, y el WebM declaraba 16.000 s aunque tuviera 477 cuadros. Lo pesqué porque el mismo contenido en MOV declaró los 15.900 s reales y reprobó — dos formatos discrepando sobre el mismo contenido.

Ahora la verificación **cuenta los cuadros decodificados** y desconfía del contenedor: si los dos no coinciden, manda el conteo y lo dice.

### 3. Mi verificación reprobaba archivos correctos

Contaba como falla los cuadros donde no se dibuja nada. Pero en un pasaje silencioso **corresponde** que no se dibuje nada: estaba confundiendo silencio con rotura. Ahora los informa como nota y sólo reprueba por cuadros **opacos**, que es el único modo de falla real.

---

## Y algo que me sirvió de este turno

La razón por la que estos tres defectos existían es que mi verificación de T2 medía **dos cuadros sueltos** y la duración declarada. Con eso, un archivo 100 ms desfasado, con tres cuadros faltantes, pasaba en verde.

La verificación de ahora recorre **todos** los cuadros y mide contra puntos de referencia conocidos del audio. Es la que debí escribir desde el principio, y es lo que hace que la próxima vez que algo se rompa, se note acá y no en tu timeline.
