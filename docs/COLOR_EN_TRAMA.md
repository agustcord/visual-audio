# Color y fusión Trama: qué se conserva exacto y qué se corre

**Vigente desde T10 (2026-09-25). Responde una pregunta del fundador en el punto de control.**

> *"Por el momento vamos con trama, el tema es poder ajustar la combinación de
> colores del fondo, cuando nuestro fondo sea de cierto color (estoy pensando que
> tal vez si deberiamos apuntar a la 0.7 o aceptar en esta version que el color que
> podamos obtener puede defirir del color deseado, solo una aproximación)."*

Reproducible: `python tools\medir_trama.py`
Evidencia: `docs/evidencia/T10_trama_corrimiento_de_color.png`

---

## 1. La fórmula, leída del compositor de Drift

No se dedujo ni se sacó de un tutorial. Está en `_reference/drift-src/src/engine/GpuCompositor.cpp:135`, en el shader `kLayerFragShader`:

```glsl
vec3 blendRgb(vec3 base, vec3 src) {
    if (u_blendMode == 1) return base * src;                          // Multiply
    if (u_blendMode == 2) return 1.0 - (1.0 - base) * (1.0 - src);    // Screen / Trama
    ...
```

Y unas líneas más abajo, la composición:

```glsl
vec3 blended = clamp(blendRgb(dstRgb, srcRgb), 0.0, 1.0);
float outA   = sa + dst.a * (1.0 - sa);
vec3 outRgb  = blended * sa + dstRgb * dst.a * (1.0 - sa);
```

Tres cosas que hay que leer del shader para saberlas, y que cambian las cuentas:

| | |
|---|---|
| **No lineariza** | No hay conversión a luz lineal antes de mezclar. Las cuentas van sobre los valores sRGB tal como salen de la textura. Por eso `tools/medir_trama.py`, que trabaja sobre los bytes del color, reproduce **exactamente** lo que se ve en Drift. |
| **Usa alpha recta** | Des-premultiplica (`src.rgb / src.a`) antes de mezclar. |
| **La opacidad del clip mezcla de vuelta** | `sa = src.a * u_opacity`. Nuestro overlay llega opaco en todo el cuadro, así que con opacidad 1 queda `out = blended`, la fusión pura. Bajar la opacidad en Drift **no atenúa las barras**: las mezcla con el video, que es distinto. |

---

## 2. Hay que separar dos cosas que se estaban tratando como una

La preocupación era "el color puede diferir del deseado, solo una aproximación". Medido, eso es cierto de una mitad y falso de la otra.

### El fondo negro no se aproxima: desaparece exacto

Donde el overlay es negro, `src = 0`, y entonces:

```
out = 1 - (1 - base) * (1 - 0) = base
```

El video pasa **intacto, bit por bit**. Verificado sobre los seis fondos de prueba, del negro puro al blanco quemado: los seis salen `intacto`.

Esto importa porque es lo que se temía perder. Trama no ensucia, no aclara y no vela el video donde no hay dibujo. No es una aproximación ni un truco que "más o menos funciona": es una identidad algebraica.

**Contraste con Chroma Key**, que es lo que el fundador ya notó a mano: ahí el recorte *sí* es aproximado en todo el cuadro, porque el alpha sale de un `smoothstep` sobre una puntuación de croma. Trama no tiene nada de eso. Por eso, incluso cuando la 0.7 traiga alpha, **Trama sigue siendo mejor que Chroma Key en 0.6** y no era sólo la opción disponible.

### El color de la barra sí se corre, y siempre hacia el blanco

Ahí donde hay dibujo, el video de abajo suma luz. Nunca resta: Trama no puede oscurecer. Medido en ΔE76 (CIE Lab; abajo de 1 no se distingue, arriba de 10 es otro color):

| Fondo del video | blanco | celeste `#22D3EE` | rosa `#F0509B` | amarillo `#FFC83C` | rojo oscuro `#8B1A1A` |
|---|---|---|---|---|---|
| negro puro `#000000` | 0 | **0** | **0** | **0** | **0** |
| casi negro `#141414` | 0 | **2** | **5** | **5** | 8 |
| azul nocturno `#101C38` | 0 | **2** | 9 | 16 | 25 |
| gris medio `#808080` | 0 | 17 | 38 | 37 | 47 |
| piel iluminada `#C89878` | 0 | 33 | 47 | 33 | 49 |
| blanco quemado `#F0F0F0` | 0 | 42 | 74 | 70 | 84 |

### Las dos conclusiones prácticas de esa tabla

**El blanco es exacto sobre cualquier fondo.** Columna entera en 0. No es casualidad: con `src = 1`, `out = 1 - (1-base)*0 = 1`. Siempre blanco. Una barra blanca o casi blanca es inmune al problema, en cualquier metraje.

**Lo que manda es el brillo del video *detrás de las barras*, no del video en general.** Sobre metraje oscuro —que es la mayoría de un video musical, y más si la banda va en el tercio inferior— los colores saturados se corren entre 0 y 9 ΔE. Eso se nota comparando lado a lado, no mirando el video.

---

## 3. Se puede compensar, y sobre metraje oscuro da exacto

Si se conoce el fondo `B` y se quiere obtener `D`, hay que **dibujar más oscuro**:

```
src = 1 - (1 - D) / (1 - B)
```

Medido: sobre los tres fondos oscuros, la compensación lleva el error a **ΔE 0.0 en las cinco barras**. No aproximado, exacto.

**Tiene un límite duro y no es un defecto de Drift.** Sólo hay solución cuando `D >= B` en cada canal: no existe ningún color que, dibujado con Trama sobre un fondo claro, dé un resultado más oscuro que ese fondo. Sobre gris medio y más claro la compensación no llega, y la tabla lo marca como `imposible, se recortó`. En esos casos hasta empeora un poco, porque recortar a 0 en un canal desbalancea el tono.

Y una limitación de método que no hay que disimular: la fórmula pide **un** color de fondo. El video real cambia por píxel y por cuadro. Lo que se puede hacer es compensar contra el color promedio de la zona donde van las barras, y eso acerca mucho sin ser perfecto.

---

## 4. La decisión: no hay que elegir entre 0.6 y 0.7

**El modo `transparente` ya está escrito, verificado y esperando** en `tools/visualizador/salida.py`, con los `-auto-alt-ref 0` y `-lag-in-frames 0` que el propio exportador de Drift documenta como obligatorios para VP9 con alpha. El día que 0.7.0 traiga el preset de alpha, el fundador cambia una opción y el problema de color desaparece entero: con alpha no hay fusión, y el color sale exacto sobre cualquier metraje.

Así que apuntar a la 0.7 **no es un trabajo pendiente, es una opción ya construida**. Lo que no se puede hacer es *probarla*: el binario instalado es 0.6.0 y no existe todavía una 0.7 contra la que verificar. Escribir más código para una versión que no se puede ejecutar iría contra la disciplina del proyecto, que es no declarar nada verificado sin un comando que lo demuestre.

**Se trabaja para 0.6 porque es la única que se puede verificar hoy, con la 0.7 ya cubierta por construcción.**

---

## 5. Qué hacer mientras tanto, sin escribir una línea

| | Cuándo |
|---|---|
| **Barras blancas o casi blancas** | Siempre exacto. Es la salida segura si el metraje es claro o cambia mucho |
| **Poner la banda donde el video es oscuro** | El tercio inferior de un plano nocturno da ΔE 0–9 |
| **Un degradado oscuro debajo de la banda** | Lleva el fondo cerca de negro justo ahí y vuelve el color casi exacto. Cuesta que el video se oscurezca en esa franja: es una decisión estética, no un arreglo técnico |
| **Bajar la opacidad del clip** | ⚠️ **No hace lo que parece.** Mezcla las barras con el video en vez de atenuarlas. Para barras más suaves conviene el parámetro `opacidad` de la herramienta, que sí actúa sobre el dibujo |

---

## 6. Pendiente derivado

**Parámetro `compensar_fondo` para la etapa 4.** El usuario dice de qué color es el video donde van las barras y la herramienta pre-oscurece el dibujo con la fórmula de §3. Chico de implementar (ya está medido y probado), y sobre metraje oscuro es la diferencia entre ΔE 9 y ΔE 0.

Requisitos para que no prometa de más:
1. Apagado por defecto. Con `#000000` no cambia nada, así que el default no puede empeorar lo que ya funciona.
2. Cuando el color pedido no sea alcanzable, **decirlo en la interfaz** en vez de recortar en silencio. La condición es `D >= B` por canal.
3. Que la vista previa muestre el resultado compuesto sobre ese fondo, no el dibujo suelto. Si no, el usuario ve barras oscurísimas y cree que se rompió algo.

El punto 3 toca el contrato de `render.cuadro(i)` (hoy devuelve el dibujo con alpha y nada más), así que se diseña en la etapa 4 y se implementa junto con la interfaz.
