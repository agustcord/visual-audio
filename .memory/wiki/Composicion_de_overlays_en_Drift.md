---
tipo: "nota-dominio"
estado: "activo"
creado: 2026-09-25
turno: "T10"
fuente: "_reference/drift-src/src/engine/GpuCompositor.cpp + medición propia"
---

# Composición de overlays en Drift

Cómo se compone un clip sobre otro en Drift, y qué implica eso para un overlay que se genera afuera. Es la nota que explica **por qué la fusión Trama es una solución y no un parche**.

Ver también: [[Audio_reactividad_en_Drift]] (el bloqueo que obliga a generar afuera), [[Extensibilidad_de_Drift]].

Documento derivado, con las tablas de medición: `docs/COLOR_EN_TRAMA.md`.

## Los siete modos de fusión, con su matemática

De `src/core/BlendMode.h:7`:

```cpp
enum class BlendMode { Normal, Multiply, Screen, Overlay, Add, Darken, Lighten };
```

Y su implementación en el shader `kLayerFragShader`, `src/engine/GpuCompositor.cpp:134-145`:

| Modo | En la interfaz | Fórmula |
|---|---|---|
| Normal | Normal | `src` |
| Multiply | Multiplicar | `base * src` |
| **Screen** | **Trama** | `1 - (1-base)(1-src)` |
| Overlay | Superponer | `mix(2·base·src, 1-2(1-base)(1-src), step(0.5, base))` |
| Add | Sumar | fixed-function `glBlendFunc(GL_ONE, GL_ONE)` |
| Darken | Oscurecer | `min(base, src)` |
| Lighten | Aclarar | `max(base, src)` |

**Normal y Add son fixed-function; los otros cinco hacen ping-pong del canvas** (`isFixedFunctionBlend`, línea 266). Detalle de rendimiento, no de resultado: Trama cuesta una pasada extra, y aun así el fundador reportó que el reproductor no se puso lento con el overlay de 1080p.

## Las tres cosas que hay que saber del shader

Están en `GpuCompositor.cpp`, en el `main()` del mismo shader, y ninguna es obvia desde la interfaz:

**1. No lineariza.** No hay conversión a luz lineal antes de mezclar: las cuentas van sobre los valores sRGB tal como salen de la textura. Consecuencia práctica: la fusión se puede reproducir exactamente con aritmética sobre los bytes del color, sin curvas de gamma. Es lo que hace `tools/medir_trama.py`.

**2. Usa alpha recta.** Des-premultiplica (`src.rgb / src.a`) antes de mezclar, y vuelve a premultiplicar al componer.

**3. La opacidad del clip mezcla, no atenúa.**

```glsl
float sa = src.a * u_opacity;
vec3 outRgb = blended * sa + dstRgb * dst.a * (1.0 - sa);
```

Bajar la opacidad de un clip con fusión Trama **no hace las barras más tenues: las mezcla de vuelta con el video**. Para atenuar el dibujo hay que hacerlo antes de exportar. Trampa real para el usuario final, y la razón de que la herramienta tenga su propio parámetro `opacidad`.

## Por qué Trama resuelve la falta de canal alpha

Drift 0.6.0 descarta el canal alpha de un video (ver [[Drift_editor]]). Trama lo reemplaza porque el negro es su elemento neutro:

```
src = 0  →  out = 1 - (1-base)(1-0) = base
```

**El video de abajo pasa intacto, bit por bit.** No es un truco que aproxima: es una identidad algebraica. Verificado sobre seis fondos, del negro puro al blanco quemado.

El precio está del otro lado: donde sí hay dibujo, el video suma luz y el color se corre hacia el blanco. Trama **sólo puede aclarar**. Las mediciones están en `docs/COLOR_EN_TRAMA.md` §2; el resumen es que sobre metraje oscuro el desvío es de ΔE 0 a 9, y que el blanco es exacto sobre cualquier metraje porque `src = 1` siempre da blanco.

## Por qué Trama es mejor que Chroma Key, y no sólo lo disponible

El efecto `key.chroma` (`effects/chroma_key/main.frag`) saca el alpha de un `smoothstep` sobre una puntuación de croma normalizada por luma, y además resta la componente del tono clave a lo que sobrevive para compensar el rebote de la pantalla. Es un keyer decente para lo que está hecho —filmar contra una tela verde— pero:

- El recorte es **aproximado en todo el cuadro**, no sólo donde hay dibujo.
- Recorta **por tono**, así que el negro no se puede recortar: no tiene tono. Por eso la ruta de Chroma Key necesita fondo de color.
- Le come el borde al dibujo, que es exactamente lo que el fundador reportó a mano: *"es muy dificil ocultar"*.

Trama no tiene ninguno de los tres problemas. **La conclusión vale también para cuando llegue la 0.7**: el orden de preferencia es alpha > Trama > Chroma Key, y Chroma Key queda como último recurso.

## Add como alternativa descartada

`Add` (`out = base + src`) también deja pasar el negro intacto y es más barato (fixed-function, sin ping-pong). Pero satura al blanco mucho antes que Trama sobre cualquier fondo no negro, porque no tiene el término `(1-base)` que lo frena. Trama es la versión suave del mismo efecto. No vale la pena ofrecer las dos.
