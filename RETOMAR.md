# Dónde retomar

**Documento vivo.** Cada agente lo actualiza al cerrar su turno. Si lo que dice acá contradice a otro documento, gana la bitácora `.memory/log.md` — pero entonces alguien tiene que arreglar este archivo.

**Última actualización:** 2026-09-25, turno T4, agente Kiro.

---

## 🔴 Estado (T6): MVP definido. **No construir hasta que el fundador apruebe.**

El fundador pidió **un freno** para definir el MVP antes de gastar turnos, y tenía razón: al definirlo, el presupuesto pasó de 6 turnos a **10**.

**Lo primero que tiene que hacer el próximo agente:** ver si el fundador respondió las **cinco preguntas de [`docs/MVP.md`](docs/MVP.md) §9**. Construir antes de eso sería exactamente lo que él quiso evitar.

Las preguntas, resumidas:

1. ¿Los tres estilos son los correctos? (barras, barras espejadas, onda — circular afuera)
2. ¿Falta o sobra algún valor de los ~25?
3. **¿Aprueba los 10 turnos**, llevando la Etapa 1 a 16 contra los 10–14 del Gate?
4. ¿Confirma la lista de lo que el MVP **no** hace?
5. **Dato faltante:** ¿a qué resolución y fps trabaja en Drift? Se asumió 1920×1080 a 30

### Dos cosas ya decididas por él, para no reabrirlas

- **La PoC está aprobada** por ambos.
- **Motor de dibujo propio**, no los filtros de FFmpeg.
- **Criterio que ordena todo el MVP:** *"el MVP no debe contener programación para el usuario final"*. Eso implica interfaz gráfica, y **contradice el §3 de `PLAN_ETAPA1.md`**, que decía "sin interfaz gráfica". Se resuelve a favor de lo que dijo ahora: `docs/MVP.md` reemplaza ese §3.

### Cuando apruebe, el orden es

Las siete etapas de `docs/MVP.md` §8. La primera es el análisis de audio a bandas por cuadro, y la segunda el motor de dibujo con el estilo Barras. **Punto de control tras la etapa 2** (4 turnos): el fundador ve barras reales sobre su video antes de gastar los 3 turnos de interfaz.

---

## Estado anterior (T4): las dos rutas de composición en Drift

**Drift 0.6.0 no soporta video con canal alpha.** Es la versión publicada y la que tiene instalada el fundador. El soporte existe en la rama de desarrollo de Drift (0.7.0, sin publicar).

Eso explica PoC-5 entero: el negro que veía era nuestro fondo transparente con el alpha descartado (transparente es RGB 0,0,0 con alpha 0; sin alpha queda negro sólido). No era el formato, no era el tamaño, no era la premultiplicación.

**El camino A sigue en pie**, con un cambio de diseño: la transparencia la resuelve Drift con herramientas que ya tiene, en vez de venir en el archivo.

### Lo primero que tiene que hacer el próximo agente

Ver si el fundador ya probó los dos archivos de `build/` y con cuál se queda. Están descritos en **[`docs/COMO_USAR.md`](docs/COMO_USAR.md)**, que es la guía escrita para él.

```powershell
# D — fondo negro, se compone con fusión Trama. Lo más simple
python tools\generar_overlay.py tests\fixtures\pista_prueba.wav -o build\D_negro_trama.webm --color "#00E5FF" --lienzo 1920x1080 --margen 60

# E — fondo magenta, se recorta con el efecto Chroma Key. Funciona sobre fondo claro
python tools\generar_overlay.py tests\fixtures\pista_prueba.wav -o build\E_magenta_chromakey.webm --color "#00E5FF" --fondo color --color-fondo "#FF00FF" --lienzo 1920x1080 --margen 60
```

En Drift, para E hay que poner **Key Colour en 300** (magenta) y subir Tolerance.

---

## Lo que se sabe de la versión instalada

Verificado contra `C:\Program Files\Drift\drift.exe`:

| | |
|---|---|
| Versión | **0.6.0** (binario del 2026-09-13) |
| Canal alpha en video | ❌ **no soportado**. Los presets `vp9_alpha` y `prores_4444` no existen en el binario |
| Modos de fusión | ✅ Screen (Trama), Multiply, Overlay, Lighten, Darken, Add |
| Efecto Chroma Key | ✅ `key.chroma`, en `effects/chroma_key`. Recorta **por tono** (0–360°) |

**El clon de referencia `_reference/drift-src/` es `main` = 0.7.0 en desarrollo, y NO coincide con el binario instalado.** Si vas a razonar sobre el código de Drift, verificá primero que la parte que te importa exista en el build del fundador. Método:

```powershell
findstr /C:"la_cadena_que_buscas" "C:\Program Files\Drift\drift.exe"
```

Y siempre con un **control**: buscá también algo que sí deba estar, para saber que el método detecta. Los ids de preset (`libx264`, `dnxhr_10`, `h265_10`) sirven bien porque son `const char*` y quedan en ASCII.

---

## Qué está hecho

| | Qué | Dónde |
|---|---|---|
| ✅ | Memoria, git, viabilidad, Gate del fundador | `.memory/`, `docs/` |
| ✅ | Audio de prueba determinista | `tests/fixtures/pista_prueba.wav` |
| ✅ | Generador con tres tipos de fondo y dos formatos | `tools/generar_overlay.py` |
| ✅ | Desincronización de 100 ms corregida, con prueba de regresión | `tests/verificar_sincronia.py` |
| ✅ | **Causa raíz de PoC-5 identificada** | `docs/POC_RESULTADOS.md` adenda T4 |
| ✅ | **Dos rutas que funcionan en 0.6.0**, con evidencia visual | `docs/evidencia/T4_trama_vs_chromakey.png` |
| ✅ | **Guía de uso para el fundador** | `docs/COMO_USAR.md` |
| ⏸️ | PoC-5 — esperando que el fundador pruebe D y E | — |
| ⬜ | MVP: modos de espectro (hoy **no funcionan**) | — |

### Si D o E funcionan

PoC-5 queda cumplido **con la salvedad declarada** de que la transparencia la resuelve Drift y no el archivo. Corresponde:

1. Registrarlo en `docs/PLAN_ETAPA1.md` como cambio de diseño dentro del camino A, no como camino nuevo.
2. Seguir al MVP (T6–T9). El primer trabajo real ahí: **arreglar los modos de espectro**, que hoy no funcionan.

### Si ninguno funciona

Volver al Gate. Pero sería raro: las dos rutas usan funciones propias de Drift que están verificadas en su binario.

---

## Deuda conocida — no la redescubras

| Tema | Detalle |
|---|---|
| **Espectro roto** | `showfreqs` renderiza amontonado en el 12% izquierdo e ignora el `colors=` pedido. `showspectrum` falló al renderizar y **no se investigó**. Evidencia: `docs/evidencia/T2_comparacion_modos.png`. Es el criterio MVP-1 |
| **Peso** | Bajó bastante al dejar el alpha: fondo negro 5,5 MB y fondo de color 3,2 MB por 16 s, contra 11,7 MB con alpha. Por canción de 3 min: ~62 MB y ~36 MB. Sigue siendo estructural (cada cuadro es una ventana nueva) |
| **Color ~1.5% corrido** | Se pide `#00E5FF` (G=229) y salen píxeles con G=225. No investigado |
| **Cuantización de 1 cuadro** | La onda va 33 ms tarde a 30 fps. Correcto por construcción, no es bug |
| **`--fondo transparente`** | Implementado y verificado, pero **inútil hasta Drift 0.7.0**. No lo borres: cuando salga, es el camino bueno |

---

## Trampas ya pagadas — no las repitas

### Del generador

1. **`-shortest` no corta un `filter_complex`.** Una fuente `color` sin `d=` es infinita y no termina nunca (generó 21 MB de un audio de 16 s).
2. **`alphamerge` no sirve acá** — daba alpha 255 en todo el cuadro. Y no hace falta: `showwaves` ya emite RGBA con fondo transparente y acepta `colors=` directo.
3. **`draw=full` no es opcional.** El default `scale` dibuja con alpha máximo 153 y cero píxeles opacos.
4. **`showwaves` etiqueta el primer cuadro en PTS 0.1 s.** Sin `setpts=PTS-STARTPTS` todo va 100 ms tarde **y** se pierden 3 cuadros al recortar.
5. **El negro no tiene tono**, así que el Chroma Key no puede recortarlo. Fondo de color para esa ruta.

### De medir

6. **No midas con `-ss` antes de `showwaves`**: el primer cuadro después de un salto está incompleto y parece un visualizador roto. Usá `select='gte(n\,<N>)'`. Saltar sobre el archivo **ya codificado** sí es válido.
7. **`ffprobe` reporta `pix_fmt=yuv420p` en un WebM que sí tiene alpha.** Verificá con el tag `alpha_mode` y decodificando con `-c:v libvpx-vp9` **antes** de `-i`.
8. **La duración que declara el contenedor miente.** Un WebM con 477 cuadros declaraba 16.000 s. **Contá cuadros.**
9. **No uses `-vf` sobre una salida de `filter_complex`** — no se aplica. Poné el filtro dentro de la cadena.
10. **`blend` mezcla en el espacio de color que le toque.** Si un input viene en RGB y otro en YUV, ffmpeg convierte a YUV y aplicar "screen" a los planos de croma da colores absurdos. Forzá `format=gbrp` en los dos inputs.
11. **Verificá la versión instalada antes de razonar sobre el código.** El clon es `main`; el fundador corre 0.6.0.

### La regla general

El instrumento de medición ya falló **dos veces** antes que lo medido (el `-ss` en T3, el `blend` en T4). Las dos veces se detectó **porque el resultado no tenía sentido físico**, no porque algo fallara ruidosamente. Y la verificación de T2 aprobaba en verde un archivo 100 ms desfasado al que le faltaban 3 cuadros.

**Si agregás un criterio: que recorra todo el material, y que mida contra algo conocido del audio — no contra lo que el archivo dice de sí mismo.**

---

## Datos operativos verificados

- **Drift instalado:** `C:\Program Files\Drift\drift.exe`, **0.6.0** — **sólo lectura**.
- **FFmpeg:** `C:\ffmpeg\bin\ffmpeg.exe` 8.0.1. **Python:** 3.14.6.
- **Código de referencia:** `_reference/drift-src/` = `main` (0.7.0-dev), no versionado. Comando de reconstrucción en el handoff T1.

## Límites que el fundador fijó

- **Compromiso nulo con terceros.** No forkear Drift, no ofrecer PR a upstream, no contactar a CutWire Studios.
- **No activar el servidor MCP de Drift** sin pedírselo antes.
- Camino B fuera del alcance, pero **no por costo**: es barato, simplemente no hace falta (`docs/PLAN_ETAPA1.md` §7).
