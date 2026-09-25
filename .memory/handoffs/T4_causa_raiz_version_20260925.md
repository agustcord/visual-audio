---
tipo: "handoff"
turno: 4
agente: "Kiro"
fecha: 2026-09-25
estado: "cerrado — causa raíz identificada, dos rutas listas para que el fundador pruebe"
---

# T4 — Drift 0.6.0 no soporta canal alpha

La causa raíz de PoC-5 no era ninguna de las que investigué en T3. Era la versión.

## El dato del fundador que cerró el diagnóstico

> «el negro cubría todo, no tenía transparencia […] el audio solo tapaba de negro con su franja, no todo el proyecto. tanto b y c, cubren la pantalla de negro en modo normal»

Tres consecuencias inmediatas:

- **No es un problema de formato.** ProRes 4444 falla igual que WebM/VP9.
- **No es relleno por diferencia de tamaño.** El negro cubre exactamente el rectángulo del clip: franja cuando el clip es franja, pantalla completa cuando es pantalla completa.
- **No es premultiplicación**, que era la pista que quedaba anotada en `RETOMAR.md`. Con alpha recto mal interpretado se verían bordes sucios, no opacidad total.

El negro es **nuestro fondo transparente con el alpha descartado**: transparente es RGB(0,0,0) con alpha 0, y sin alpha queda negro sólido.

## Lo que faltaba verificar, y debí verificar primero

El clon de referencia es `main`, que es **0.7.0 en desarrollo**. `CHANGELOG.md` declara *"Last released version: `0.6.0`"*. El `drift.exe` instalado es del **2026-09-13**, anterior al clon.

**Estuve tres turnos razonando sobre código que no está en el build del fundador.**

Verificación directa contra el binario:

| Cadena en `drift.exe` | Resultado |
|---|---|
| `vp9_alpha` | **ausente** |
| `prores_4444` | **ausente** |
| `Clips with transparency can't use a proxy` | **ausente** |

Con **control de método**, para que la ausencia signifique algo:

| Control | Resultado |
|---|---|
| `dnxhr_10`, `h265_10` — vecinos en la **misma** tabla de presets | presentes |
| `libx264`, `libvpx-vp9`, `dnxhr`, `theora`, `vp9`, `prores` | presentes |

La búsqueda ASCII detecta lo que existe, así que la ausencia de los dos presets con alpha es real y no un artefacto de cómo Qt guarda las cadenas.

**Conclusión: el soporte de canal alpha se agregó a Drift después de 0.6.0.**

### La lección, sin adornos

Un `findstr` de un minuto contra el binario instalado habría ahorrado el turno T3 completo. La regla queda anotada en `RETOMAR.md`: **verificar que la versión instalada contenga la parte del código sobre la que se va a razonar, antes de razonar.**

## Frontera declarada

**Creado:** `docs/COMO_USAR.md`, `docs/evidencia/T4_trama_vs_chromakey.png`, este handoff.
**Modificado:** `tools/generar_overlay.py`, `docs/POC_RESULTADOS.md` (adenda T4), `RETOMAR.md`, `.memory/log.md`, `.memory/wiki/MOC_Handoffs.md`.
**Generado en `build/`** (no versionado): `D_negro_trama.webm`, `E_magenta_chromakey.webm`, y simulaciones.
**Borrado:** `docs/evidencia/T4_comparacion_trama_vs_chromakey.png`, reemplazado por la versión corregida (la primera simulación era errónea, ver abajo).

**NO se tocó:** `sobre_este_plugins.txt`; `C:\Program Files\Drift\` (sólo lectura: se leyeron cadenas del binario y el `effect.json` del Chroma Key); la carpeta de datos de Drift; `_reference/drift-src/`; `docs/VIABILIDAD.md`; `docs/PLAN_ETAPA1.md` (el Gate no cambió — el cambio de diseño queda para registrar cuando el fundador confirme). **No se abrió Drift ni se activó su MCP.**

## Qué ofrece 0.6.0 y las dos rutas

Inventario verificado de la versión instalada:

- **Modos de fusión**: Screen (Trama), Multiply, Overlay, Lighten, Darken, Add — presentes en el binario.
- **Efecto `key.chroma`**, instalado en `effects/chroma_key`. Recorta **por tono** (0–360°), con Tolerance, Edge Softness y Spill Removal.

**Detalle que condiciona el diseño: el negro no tiene tono**, así que el Chroma Key no puede recortar un fondo negro. Para esa ruta el fondo tiene que ser un color.

| | Fondo negro + Trama | Fondo de color + Chroma Key |
|---|---|---|
| Pasos en Drift | un menú | agregar efecto, ajustar 2–4 parámetros |
| Sobre fondo claro | ❌ se lava | ✅ |
| Altera colores | ✅ aclara | ❌ |
| Bordes sucios | ninguno | posibles, se ajustan |
| Tamaño (16 s, 1080p) | 5,5 MB | 3,2 MB |

Se agregó al generador `--fondo {transparente,negro,color}` y `--color-fondo`, con default **`negro`** porque es lo que funciona hoy. `--fondo transparente` queda implementado y verificado para cuando salga 0.7.0.

Para el Chroma Key hay que elegir el color de fondo **lejos en tono** del color de la onda: con onda cian (~186°), magenta (300°) queda a 114° mientras el verde quedaría a 66°, donde el recorte se comería parte del dibujo.

### El premio inesperado

| Fondo | 16 s a 1080p | Por canción de 3 min |
|---|---|---|
| Canal alpha | 11,7 MB | ~130 MB |
| Negro | **5,5 MB** | ~62 MB |
| Color | **3,2 MB** | ~36 MB |

Sin canal alpha VP9 comprime mucho mejor. **La ruta que funciona en la versión del fundador es además la más liviana**, así que la deuda de peso baja a menos de la mitad.

## Un error propio, declarado

La primera simulación del modo Trama devolvió un cuadro magenta absurdo, y **sospeché del archivo antes que de mi medición**. Inspeccionando píxeles, los archivos estaban perfectos: D con fondo RGB(0,0,0) y onda RGB(0,227,253); E con fondo RGB(254,0,253).

La falla era mía: `blend=all_mode=screen` recibía un input en RGB y otro en YUV, ffmpeg convertía todo a YUV, y aplicar "screen" a los **planos de croma** produce colores sin sentido. Corregido forzando `format=gbrp` en ambos inputs. La evidencia errónea se borró y se reemplazó.

Es la **segunda vez** en el proyecto que el instrumento de medición falla antes que lo medido — la primera fue el `-ss` antes de `showwaves` en T3. Las dos veces se detectó igual: **porque el resultado no tenía sentido físico**, no porque algo fallara ruidosamente. Está anotado como regla en `RETOMAR.md`.

## Dónde retomar

`RETOMAR.md`. El próximo agente ve si el fundador ya probó D y E y con cuál se queda. La guía escrita para él es `docs/COMO_USAR.md`.

Si alguna funciona, PoC-5 queda cumplido **con la salvedad declarada** de que la transparencia la resuelve Drift y no el archivo — hay que registrarlo en `PLAN_ETAPA1.md` como cambio de diseño dentro del camino A, no como camino nuevo. Después sigue el MVP, y el primer trabajo real ahí es **arreglar los modos de espectro**, que siguen sin funcionar.
