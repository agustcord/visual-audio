# Dónde retomar

**Documento vivo.** Cada agente lo actualiza al cerrar su turno. Si contradice a otro documento, gana la bitácora `.memory/log.md` — pero entonces alguien tiene que arreglar este archivo.

**Última actualización:** 2026-09-25, turno T7, agente Kiro.

---

## 🟢 Estado: todo aprobado. **Empezar la etapa 1 de la ruta.**

El fundador aprobó el MVP, el presupuesto ampliado y la ruta de trabajo. **No hay nada pendiente de su parte.** A construir.

### Tu punto de entrada es la ruta, no este archivo

👉 **[`docs/RUTA_DE_TRABAJO.md`](docs/RUTA_DE_TRABAJO.md)**

Ahí está la tabla de estado, las siete etapas con sus criterios de entrada y salida, y las reglas de trabajo. Está escrita para que **cualquier agente** pueda ubicarse y ejecutar, no sólo el que estuvo en esta conversación.

**Siguiente:** etapa 1, análisis de audio. Un turno.

### Antes de escribir código, leé estos dos

| | Por qué |
|---|---|
| [`docs/MVP.md`](docs/MVP.md) | **Qué** hace el MVP: tres estilos, los ~25 valores con rangos y defaults, los nueve criterios |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | **Cómo** se organiza el código y cuáles son los contratos. Existe para que dos agentes produzcan piezas que encajan |

---

## Lo que el fundador decidió, para no reabrirlo

| | |
|---|---|
| **PoC** | Aprobada por ambos |
| **Motor de dibujo** | **Propio**, no los filtros de FFmpeg |
| **Forma del producto** | Herramienta externa; el archivo se importa a Drift |
| **Sin programación para el usuario final** | Implica **interfaz gráfica**. Contradice el §3 de `PLAN_ETAPA1.md`, que queda superseded por `docs/MVP.md` |
| **Estilos** | Barras, barras espejadas, onda. Circular afuera y **no prometido** |
| **Presupuesto** | 10 turnos de MVP. Etapa 1 a **17** en total |
| **Estándar de proyecto** | **1920×1080 a 30 fps** como default. La herramienta debe admitir otros |
| **Compromiso nulo con terceros** | No forkear Drift, no PR a upstream, no contactar a CutWire Studios |

Los dos Gates con el texto verbatim del fundador están en [`docs/PLAN_ETAPA1.md`](docs/PLAN_ETAPA1.md) §7 y §10.

---

## Estado de Drift, que condiciona la salida

Verificado contra `C:\Program Files\Drift\drift.exe`:

| | |
|---|---|
| Versión instalada | **0.6.0** (binario del 2026-09-13) |
| Canal alpha en video | ❌ **no soportado.** Los presets `vp9_alpha` y `prores_4444` no existen en el binario |
| Modos de fusión | ✅ Screen (Trama), Multiply, Overlay, Lighten, Darken, Add |
| Efecto Chroma Key | ✅ `key.chroma`. Recorta **por tono** (0–360°) |

Por eso hay tres modos de fondo: `negro` para componer con Trama, `color` para recortar con Chroma Key, y `transparente` que está implementado pero **espera Drift 0.7.0**.

**Ritmo de publicación de Drift:** promedio ~9 días entre versiones menores, máximo observado 14. La 0.6.0 tiene 12 días al 2026-09-25, así que 0.7.0 está en ventana.

⚠️ **`_reference/drift-src/` es la rama `main` (0.7.0 en desarrollo) y NO coincide con el binario instalado.** Antes de razonar sobre código de Drift, verificá que esa parte exista en su build:

```powershell
findstr /C:"la_cadena_que_buscas" "C:\Program Files\Drift\drift.exe"
```

Y siempre con un **control**: buscá también algo que sí deba estar. Los ids de preset (`libx264`, `dnxhr_10`) sirven, porque son `const char*` y quedan en ASCII.

---

## Qué existe hoy y funciona

| | Qué | Dónde |
|---|---|---|
| ✅ | Audio de prueba determinista, con estructura conocida para medir | `tests/fixtures/pista_prueba.wav` |
| ✅ | Generador de la PoC, tres modos de fondo, se autoverifica | `tools/generar_overlay.py` |
| ✅ | Prueba de regresión de sincronía | `tests/verificar_sincronia.py` |
| ✅ | Guía de uso para el fundador | `docs/COMO_USAR.md` |
| ⬜ | El producto del MVP | `tools/visualizador/` — **por crear, etapa 1** |

`tools/generar_overlay.py` **no se borra.** Funciona, está verificado, y sus parámetros de codificación son la referencia de los tres modos de fondo — incluido el `-auto-alt-ref 0` que Drift documenta como obligatorio para VP9 con alpha.

---

## Deuda conocida — no la redescubras

| Tema | Detalle |
|---|---|
| **Espectro de FFmpeg roto** | `showfreqs` amontona todo en el 15% izquierdo e ignora el color pedido; `showspectrum` falló al renderizar. **Es la razón del motor propio.** No intentes arreglarlo: se reemplaza. Evidencia: `docs/evidencia/T5_ffmpeg_vs_propio.png` |
| **Peso del archivo** | Con fondo sólido: 5,5 MB (negro) y 3,2 MB (color) por 16 s a 1080p. Con alpha: 11,7 MB. Es estructural con `showwaves`; **el motor propio podría mejorarlo** dibujando menos detalle irrelevante |
| **Color ~1.5% corrido** | `showwaves` devuelve G=225 cuando se pide G=229. **Desaparece con el motor propio**, que escribe los píxeles exactos |
| **Cuantización de 1 cuadro** | La onda va 33 ms tarde a 30 fps. Correcto por construcción, no es bug |
| **`--fondo transparente`** | Implementado y verificado, **inútil hasta Drift 0.7.0**. No lo borres |

---

## Trampas ya pagadas — no las repitas

### Del generador con FFmpeg

1. **`-shortest` no corta un `filter_complex`.** Una fuente `color` sin `d=` es infinita y no termina nunca (generó 21 MB de un audio de 16 s).
2. **`alphamerge` no sirve acá** — daba alpha 255 en todo el cuadro. Y no hacía falta: `showwaves` ya emite RGBA transparente.
3. **`draw=full` no es opcional** en `showwaves`. El default `scale` da alpha máximo 153 y cero píxeles opacos.
4. **`showwaves` etiqueta el primer cuadro en PTS 0.1 s.** Sin `setpts=PTS-STARTPTS` todo va 100 ms tarde **y** se pierden 3 cuadros al recortar.
5. **El negro no tiene tono**, así que el Chroma Key no puede recortarlo. Para esa ruta, fondo de color.

### De medir

6. **No midas con `-ss` antes de `showwaves`**: el primer cuadro después de un salto está incompleto y parece un visualizador roto. Usá `select='gte(n\,<N>)'`.
7. **`ffprobe` reporta `pix_fmt=yuv420p` en un WebM que sí tiene alpha.** Verificá con el tag `alpha_mode` y decodificando con `-c:v libvpx-vp9` **antes** de `-i`.
8. **La duración que declara el contenedor miente.** Un WebM con 477 cuadros declaraba 16.000 s. **Contá cuadros.**
9. **No uses `-vf` sobre una salida de `filter_complex`** — no se aplica.
10. **`blend` mezcla en el espacio de color que le toque.** Un input RGB y otro YUV terminan en YUV, y "screen" sobre los planos de croma da colores absurdos. Forzá `format=gbrp` en los dos.
11. **Verificá la versión instalada antes de razonar sobre el código** de Drift.

### La regla que resume las tres últimas

El instrumento de medición falló **dos veces** antes que lo medido (el `-ss` en T3, el `blend` en T4). Las dos se detectaron **porque el resultado no tenía sentido físico**, no porque algo fallara ruidosamente. Y la verificación de T2 aprobaba en verde un archivo 100 ms desfasado al que le faltaban tres cuadros.

**Si agregás un criterio: que recorra todo el material, y que mida contra algo conocido del audio — no contra lo que el archivo dice de sí mismo.**

---

## Datos operativos verificados

- **Drift:** `C:\Program Files\Drift\drift.exe`, 0.6.0 — **sólo lectura**.
- **FFmpeg:** `C:\ffmpeg\bin\ffmpeg.exe` 8.0.1, con todos los filtros de visualización.
- **Python:** 3.14.6. **`numpy`, `scipy`, `Pillow` y `tkinter` (Tk 8.6) disponibles.** Nada más se instala sin consultar.
- **Código de referencia:** `_reference/drift-src/` = `main` (0.7.0-dev), no versionado. Comando de reconstrucción en el handoff T1.
