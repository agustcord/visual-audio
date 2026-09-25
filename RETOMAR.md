# Dónde retomar

**Documento vivo.** Cada agente lo actualiza al cerrar su turno. Si lo que dice acá contradice a otro documento, gana la bitácora `.memory/log.md` — pero entonces alguien tiene que arreglar este archivo.

**Última actualización:** 2026-09-25, turno T2, agente Kiro.

---

## 🟡 Estado: PoC funcionando. El próximo turno necesita al fundador con Drift abierto.

El camino A está aprobado y en marcha. El generador de overlay funciona y cumple los tres criterios que se pueden verificar sin Drift. **Los tres que faltan requieren Drift.**

### ⚠️ Lo primero que tiene que hacer el próximo agente

**Avisarle al fundador que este turno necesita Drift abierto.** Lo pidió explícitamente en el Gate: *"sobre el momento que necesite Drift abierto avisame en ese turno"*.

**No hace falta activar el servidor MCP de Drift.** Ya se le respondió esa pregunta: la importación de T5 es manual. MCP sólo sería necesario para automatizar la colocación del overlay, que es opcional del MVP — y si se llega a eso, hay que pedirlo aparte.

---

## Qué está hecho

| | Qué | Dónde |
|---|---|---|
| ✅ | Proyecto registrado en la bóveda de memoria | `.memory/` |
| ✅ | Repositorio git con commit de línea base | rama `master` |
| ✅ | Investigación de viabilidad con evidencia | `docs/VIABILIDAD.md` |
| ✅ | **Gate del fundador registrado** — camino A habilitado | `docs/PLAN_ETAPA1.md` §7 |
| ✅ | **Audio de prueba del proyecto** (pedido del fundador) | `tests/fixtures/pista_prueba.wav` |
| ✅ | **Generador de overlay funcionando** | `tools/generar_overlay.py` |
| ✅ | PoC-1, PoC-2, PoC-3 verificados con mediciones | `docs/POC_RESULTADOS.md` |
| ⬜ | **PoC-4, PoC-5, PoC-6** — requieren Drift abierto | — |
| ⬜ | MVP: modos de espectro (hoy **no funcionan**) | — |

---

## El próximo paso concreto: T5

Es el **punto de control duro** del plan. Tres criterios, y uno decide si el camino A sigue en pie.

### Cómo se hace

1. Generar el overlay (si no está en `build/`):

   ```powershell
   python tools\generar_overlay.py tests\fixtures\pista_prueba.wav -o build\onda_prueba.webm --color "#00E5FF"
   ```

2. Pedirle al fundador que abra Drift y:
   - Ponga cualquier video en una pista.
   - Importe `build/onda_prueba.webm` (arrastrándolo) y lo coloque en una pista **por encima** del video.
   - Mire si el video de fondo **se ve a través** del overlay.

### Los criterios

| # | Qué verificar | Por qué importa |
|---|---|---|
| **PoC-4** | Drift lo importa sin marcarlo como faltante ni corrupto, con duración correcta | Si falla acá, el problema es el contenedor o el codec |
| **PoC-5** | **Drift compone la transparencia**: se ve el video de fondo a través del overlay | 🔴 **Si esto falla, el camino A queda invalidado y hay que replantear antes de gastar un turno más.** No seguir al MVP con el camino roto |
| **PoC-6** | La onda se mueve en sincronía con la música | Lo juzga el fundador a ojo |

**Medir también, aunque no sea un criterio:** cuánto se pone lento el preview. Drift **niega proxies a clips con transparencia** (`PreviewProxyRenderer.cpp:40-45`), así que el overlay se decodifica por software. Si molesta, las palancas son `--alto` más chico, `--fps 24`, o `--crf` más alto.

### Si PoC-5 pasa

Sigue el MVP (T6–T9). El primer trabajo real ahí: **arreglar los modos de espectro**, que hoy no funcionan (ver abajo). El criterio MVP-1 pide dos estilos andando.

---

## Deuda conocida — no la redescubras

| Tema | Detalle |
|---|---|
| **Espectro roto** | `showfreqs` renderiza todo amontonado en el 12% izquierdo del cuadro e ignora el `colors=` pedido. `showspectrum` directamente falló al renderizar un cuadro y **no se investigó**. Es un problema de mapeo de frecuencias. Evidencia: `docs/evidencia/T2_comparacion_modos.png` |
| **Peso** | 11.6 MB por 16 s → ~130 MB por canción. Estructural: cada cuadro de `showwaves` es una ventana nueva, VP9 no puede predecir. De `--crf 30` a `48` sólo baja de 13.7 a 6.1 MB |
| **Color ~1.5% corrido** | Se pide `#00E5FF` (G=229) y salen píxeles con G=225. Anotado, no investigado |

---

## Lo que un agente nuevo tiene que saber antes de tocar nada

**El hallazgo central:** Drift no le da ningún dato de audio a sus shaders. Por eso el visualizador se genera **fuera** de Drift y se compone como overlay, en vez de ser un efecto que reacciona a la música. Si vas a proponer arquitectura, leé `.memory/wiki/Audio_reactividad_en_Drift.md` primero.

### Trampas del generador, ya pagadas

Están desarrolladas en `docs/POC_RESULTADOS.md`. Resumen para que nadie las repita:

1. **`-shortest` no corta un `filter_complex`.** Una fuente `color` sin `d=` es infinita y no termina nunca.
2. **`alphamerge` no sirve para esto** — devolvía alpha 255 en todo el cuadro. Y no hace falta: **`showwaves` ya emite RGBA con fondo transparente** y acepta `colors=` directo.
3. **`draw=full` no es opcional.** El default `scale` dibuja con alpha máximo 153 y cero píxeles opacos.
4. **No midas con `-ss` antes de `showwaves`**: el primer cuadro después de un salto está incompleto y parece un visualizador roto. Usá `select='gte(n\,<N>)'`. Saltar sobre el `.webm` ya codificado sí es válido.
5. **`ffprobe` reporta `pix_fmt=yuv420p` en un WebM que sí tiene alpha.** En WebM el alpha de VP9 va como datos adicionales de cada bloque. Verificá con el tag `alpha_mode` y decodificando con `-c:v libvpx-vp9` **antes** de `-i`. Drift hace exactamente eso mismo.

### Datos operativos verificados

- **Drift instalado:** `C:\Program Files\Drift\drift.exe` — **sólo lectura**, no escribir ahí.
- **Paquetes propios irían a:** `%APPDATA%\CutWire Drift\effects\` — escribible, sin firma. (Hoy no usamos esta vía.)
- **FFmpeg:** `C:\ffmpeg\bin\ffmpeg.exe` 8.0.1, con `showwaves`, `showspectrum`, `showfreqs`, `showcqt`, `avectorscope`.
- **Python:** 3.14.6.
- **Código de referencia de Drift:** `_reference/drift-src/` (no versionado; comando de reconstrucción en el handoff T1).

### Límites que el fundador fijó

- **Compromiso nulo con terceros.** No forkear Drift, no ofrecer PR a upstream, no contactar a CutWire Studios.
- **No activar el servidor MCP de Drift** sin pedírselo antes.
- Camino B fuera del alcance (pero **no** por costo: es barato, simplemente no hace falta — ver `docs/PLAN_ETAPA1.md` §7).

---

## Vigencia

El informe de viabilidad describe la rama `main` de Drift al **2026-09-25**. Si pasó tiempo, re-verificá el hallazgo central antes de confiar en el plan:

```powershell
Select-String -Path "_reference\drift-src\src\**\*.cpp","_reference\drift-src\src\**\*.h" `
  -Pattern "u_audio|u_beat|u_rms|u_energy|u_band"
```

Si eso devuelve algo en el pipeline de render (no en medidores de UI), upstream agregó audio a los shaders y `docs/VIABILIDAD.md` quedó obsoleto.
