# Dónde retomar

**Documento vivo.** Cada agente lo actualiza al cerrar su turno. Si lo que dice acá contradice a otro documento, gana la bitácora `.memory/log.md` — pero entonces alguien tiene que arreglar este archivo.

**Última actualización:** 2026-09-25, turno T3, agente Kiro.

---

## 🔴 Estado: PoC-5 FALLÓ. Punto de control duro. No avanzar al MVP.

El fundador probó el overlay en Drift y **tuvo que aplicarle el modo de fusión "Trama" (Screen) para no ver un fondo negro**. Drift **no honró el canal alpha**.

Trama funciona por casualidad (negro en modo Screen no aporta nada) pero aclara los colores y no funcionaría sobre un fondo claro. **No cuenta como criterio cumplido.**

El plan (`docs/PLAN_ETAPA1.md` §4) dice que si PoC-5 falla se para y se replantea. **Se paró.**

### ⚠️ Lo primero que tiene que hacer el próximo agente

Leer **[`docs/PRUEBA_T3_ALPHA.md`](docs/PRUEBA_T3_ALPHA.md)** y ver si el fundador ya respondió. Ahí quedaron **dos preguntas** y **tres archivos** para que pruebe. Sin su respuesta no se puede elegir entre las dos hipótesis vivas, y ponerse a cambiar cosas sería adivinar.

---

## Lo que sí funcionó de la prueba

| Criterio | Estado |
|---|---|
| PoC-4 — Drift importa el archivo | ✅ lo importó y lo reprodujo |
| PoC-5 — Drift compone la transparencia | ❌ **falla**, requirió modo Trama |
| PoC-6 — la onda se mueve con la música | ⚠️ se movía, pero iba **100 ms atrasada** (ya corregido) |
| Rendimiento del preview | ✅ **no se puso lento** — el riesgo de la falta de proxy en clips con alpha no se materializó |

---

## Las dos hipótesis vivas

Tres ya se descartaron con evidencia; están en `docs/POC_RESULTADOS.md` (adenda T3). **No las vuelvas a investigar:** el tag `alpha_mode` está donde Drift lo busca, el decodificador libvpx está en el FFmpeg de Drift, y el alpha del archivo estaba sano en los 477 cuadros.

Quedan dos, y sólo un dato del fundador las separa:

1. **Relleno por diferencia de tamaño.** El clip medía 1920×320 en un proyecto 1080p y Drift lo rellenó con negro opaco. **Predice que el negro se vio como una franja**, no como el cuadro entero. Si es esto, el archivo **B** lo resuelve.
2. **Drift descarta el alpha de WebM/VP9 en su cadena de render**, pese a tener las piezas. **Predice negro en todo el cuadro**, y que **C** (ProRes 4444) funcione.

### Los tres archivos del experimento

Se regeneran así:

```powershell
# A — la banda sola, como la que falló, pero con los arreglos de T3
python tools\generar_overlay.py tests\fixtures\pista_prueba.wav -o build\A_banda_webm.webm --color "#00E5FF"

# B — cuadro completo 1080p, onda abajo, resto transparente
python tools\generar_overlay.py tests\fixtures\pista_prueba.wav -o build\B_lienzo_webm.webm --color "#00E5FF" --lienzo 1920x1080 --margen 60

# C — ProRes 4444 en MOV, el otro formato con alpha que Drift exporta por su cuenta
python tools\generar_overlay.py tests\fixtures\pista_prueba.wav -o build\C_lienzo_prores.mov --color "#00E5FF" --formato mov --lienzo 1920x1080 --margen 60
```

El fundador los prueba **sin aplicar ningún modo de fusión** — eso es lo que estamos tratando de no necesitar.

### Si ninguno funciona

Entonces el camino A está en duda de verdad y hay que volver al Gate con el fundador. Antes de eso, quedan dos cosas por mirar que **no** se investigaron todavía:

- Si Drift tiene una propiedad de clip o de pista que habilite la transparencia y esté apagada por defecto.
- Si el problema está en el compositor y no en el decodificador: `GpuCompositor.cpp:917-923` compone con alpha premultiplicado (`GL_ONE / GL_ONE_MINUS_SRC_ALPHA`), y `showwaves` entrega alpha **recto**, no premultiplicado. Si Drift no premultiplica al subir la textura, el resultado sobre negro se vería... negro. **Esta es la pista más prometedora si B y C fallan.**

---

## Qué está hecho

| | Qué | Dónde |
|---|---|---|
| ✅ | Memoria, git, viabilidad, Gate del fundador | `.memory/`, `docs/` |
| ✅ | Audio de prueba determinista | `tests/fixtures/pista_prueba.wav` |
| ✅ | Generador con dos formatos y posicionamiento | `tools/generar_overlay.py` |
| ✅ | **Desincronización de 100 ms corregida** | `setpts=PTS-STARTPTS` |
| ✅ | **Prueba de regresión de sincronía** | `tests/verificar_sincronia.py` |
| ✅ | Verificación que audita todos los cuadros | dentro del generador |
| ❌ | **PoC-5** — bloqueado, esperando al fundador | `docs/PRUEBA_T3_ALPHA.md` |
| ⬜ | MVP: modos de espectro (hoy **no funcionan**) | — |

---

## Deuda conocida — no la redescubras

| Tema | Detalle |
|---|---|
| **Espectro roto** | `showfreqs` renderiza amontonado en el 12% izquierdo e ignora el `colors=` pedido. `showspectrum` falló al renderizar y **no se investigó**. Evidencia: `docs/evidencia/T2_comparacion_modos.png` |
| **Peso** | WebM: 11,7 MB por 16 s → ~130 MB por canción. ProRes: 121 MB por 16 s → **~1,3 GB por canción**, inviable tal cual. Es estructural: cada cuadro de `showwaves` es una ventana nueva y VP9 no puede predecir |
| **Color ~1.5% corrido** | Se pide `#00E5FF` (G=229) y salen píxeles con G=225. No investigado |
| **Cuantización de 1 cuadro** | La onda va 33 ms tarde a 30 fps. Es correcto por construcción, no es bug |

---

## Trampas ya pagadas — no las repitas

En el generador (`docs/POC_RESULTADOS.md` tiene el detalle):

1. **`-shortest` no corta un `filter_complex`.** Una fuente `color` sin `d=` es infinita y no termina nunca.
2. **`alphamerge` no sirve acá** — daba alpha 255 en todo el cuadro. Y no hace falta: **`showwaves` ya emite RGBA con fondo transparente** y acepta `colors=` directo.
3. **`draw=full` no es opcional.** El default `scale` dibuja con alpha máximo 153 y cero píxeles opacos.
4. **`showwaves` etiqueta el primer cuadro en PTS 0.1 s.** Sin `setpts=PTS-STARTPTS` todo el overlay va 100 ms tarde **y** se pierden 3 cuadros al recortar.
5. **No midas con `-ss` antes de `showwaves`**: el primer cuadro después de un salto está incompleto y parece un visualizador roto. Usá `select='gte(n\,<N>)'`. Saltar sobre el archivo **ya codificado** sí es válido.
6. **`ffprobe` reporta `pix_fmt=yuv420p` en un WebM que sí tiene alpha.** El alpha de VP9 en WebM va como datos adicionales de bloque. Verificá con el tag `alpha_mode` y decodificando con `-c:v libvpx-vp9` **antes** de `-i`.
7. **La duración que declara el contenedor miente.** Un WebM con 477 cuadros declaraba 16.000 s. **Contá cuadros.**
8. **No uses `-vf` sobre una salida de `filter_complex`** — no se aplica. Poné el filtro dentro de la cadena.

### Sobre cómo verificar

La verificación de T2 medía dos cuadros sueltos y la duración declarada, y con eso aprobaba en verde un archivo 100 ms desfasado al que le faltaban 3 cuadros. **Si vas a agregar un criterio, que recorra todo el material y que mida contra algo conocido del audio, no contra lo que el archivo dice de sí mismo.**

---

## Datos operativos verificados

- **Drift instalado:** `C:\Program Files\Drift\drift.exe` — **sólo lectura**.
- **FFmpeg:** `C:\ffmpeg\bin\ffmpeg.exe` 8.0.1. **Python:** 3.14.6.
- **Código de referencia de Drift:** `_reference/drift-src/` (no versionado; comando en el handoff T1).
- El FFmpeg de Drift **sí** trae el decodificador libvpx-vp9 y maneja `alpha_mode`.

## Límites que el fundador fijó

- **Compromiso nulo con terceros.** No forkear Drift, no ofrecer PR a upstream, no contactar a CutWire Studios.
- **No activar el servidor MCP de Drift** sin pedírselo antes. Para las pruebas de importación manual no hace falta.
- Camino B fuera del alcance, pero **no por costo**: es barato, simplemente no hace falta (`docs/PLAN_ETAPA1.md` §7).
