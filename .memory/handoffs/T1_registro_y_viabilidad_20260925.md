---
tipo: "handoff"
turno: 1
agente: "Kiro"
fecha: 2026-09-25
estado: "cerrado — con un Gate abierto hacia el fundador"
---

# T1 — Registro del proyecto, git, e investigación de viabilidad

Primer turno del proyecto. El documento fundacional (`sobre_este_plugins.txt`, firmado por Jonatan Córdoba) ordena para esta primera etapa, en este orden: (1) registrar el proyecto en `.memory` vía Obsidian, (2) definir y ejecutar la investigación de viabilidad, (3) de confirmarse, definir presupuesto y alcances, (4) *después* desarrollar. Y en paralelo, iniciar git.

Este turno cerró (1), (2), (3) y git. **No cerró (4), a propósito** — ver "Gate abierto".

## Frontera declarada

**Creado:**
- `.gitignore`
- `.memory/index.md`, `.memory/log.md`
- `.memory/wiki/MOC_Handoffs.md`, `Drift_editor.md`, `Extensibilidad_de_Drift.md`, `Audio_reactividad_en_Drift.md`, `Caminos_de_implementacion.md`
- `.memory/handoffs/T1_registro_y_viabilidad_20260925.md` (este archivo)
- `README.md`, `RETOMAR.md`
- `docs/VIABILIDAD.md`, `docs/PLAN_ETAPA1.md`
- Repositorio git (`git init`)

**Descargado, no versionado:** `_reference/drift-src/` — clon sparse de sólo lectura de `github.com/CutWire-Studios/Drift`, rama `main`, con `src docs effects effect-templates transitions audio-effects`. Excluido por `.gitignore` porque es código de terceros (GPLv3) con su propio historial.

**NO se tocó:**
- `sobre_este_plugins.txt` — el documento fundacional es del fundador; se lee, no se edita.
- `C:\Program Files\Drift\` — **sólo lectura**. No se instaló, modificó ni borró nada ahí.
- `C:\Users\Jonatan Agustín\AppData\Roaming\CutWire Drift\` — inspeccionada, **no escrita**.
- No se creó ningún efecto, template ni código de producto.
- No se abrió Drift ni se activó su servidor MCP.
- No se escribió nada en la instalación ni en la carpeta de datos de Drift.

## Lo que se verificó, y cómo

Todo lo sustantivo salió de **leer el código fuente de Drift**, no de su README ni de suposiciones. Las citas por archivo y línea viven en las notas de la wiki; el resumen y el razonamiento en `docs/VIABILIDAD.md`.

Comandos de verificación reproducibles:

```powershell
# Filtros de visualización de audio disponibles en FFmpeg
ffmpeg -hide_banner -filters | Select-String "showwaves|showspectrum|showfreqs|showcqt|avectorscope"

# Carpeta de datos escribible de Drift
Get-ChildItem "$env:APPDATA" -Directory | Where-Object { $_.Name -match 'drift|cutwire' }

# Ausencia de cualquier uniform de audio en el pipeline GPU (el hallazgo central)
# Devuelve sólo medidores de UI, nada en GlRuntime ni en shaders:
Select-String -Path "_reference\drift-src\src\**\*.cpp","_reference\drift-src\src\**\*.h" `
  -Pattern "u_audio|u_beat|u_rms|u_energy|u_band"
```

Reconstruir el clon de referencia:

```powershell
git clone --depth 1 --filter=blob:none --no-checkout `
  https://github.com/CutWire-Studios/Drift.git _reference\drift-src
git -C _reference\drift-src sparse-checkout init --cone
git -C _reference\drift-src sparse-checkout set src docs effects effect-templates transitions audio-effects
git -C _reference\drift-src checkout
```

## El hallazgo que cambia el plan

La pregunta del documento fundacional era "¿es posible crear esto para Drift?". La respuesta corta: **sí, pero no como un efecto de audio reactivo, que es lo que uno esperaría.**

**Drift no expone ningún dato de audio a su pipeline de render GPU.** Verificado por ausencia. Hay tuberías completas y explícitas para profundidad (`u_depth*`) y para rostros (`u_face*`), cada una con su preludio, sus helpers y su flag de validez — y **ninguna** para audio. La asimetría es la evidencia: cuando Drift quiere que un shader vea datos externos, construye esa tubería a mano.

La audio-reactividad que Drift tiene hoy (los templates tipo `beat_drop`) es un **preproceso que hornea keyframes**, con un único escalar por onset, sin bandas de frecuencia, y que **descarta incluso la fuerza del onset**. Detalle completo con citas en [[Audio_reactividad_en_Drift]].

**Consecuencia de diseño:** el dibujo del visualizador no puede ser un shader que "escuche". Tiene que ser pre-calculado. Las tres rutas viables y la que parece viable pero no lo es están en [[Caminos_de_implementacion]].

## Decisiones tomadas en este turno

1. **Documentar antes de codear.** El documento fundacional lo pide explícitamente y el hallazgo lo justifica: empezar a codear un efecto GPU habría sido tirar el trabajo a la basura al tercer turno.
2. **`_reference/` fuera del repositorio.** Es código GPLv3 de terceros con su propio historial. Versionarlo mezclaría autorías y licencias en nuestro árbol. Se reconstruye con el comando de arriba.
3. **Recomendar el camino A** (generar overlay con alpha por FFmpeg + importar vía MCP) como base. Razón principal: cuatro de las cinco personalizaciones que pide el fundador (tamaño, posición, opacidad, velocidad) las resuelven controles que Drift **ya tiene**, y el usuario ya sabe usar. No reimplementamos un inspector.
4. **Hacer el commit de línea base.** Primero lo había dejado pendiente para que el fundador revisara qué entra, y me corregí: el documento fundacional pide git *"para protección del mismo"*, y un repositorio sin commits no protege nada. Un commit es reversible y revisable; no hacerlo dejaba el trabajo del turno sin red. Sólo `git init` + `git add` de archivos nombrados + `git commit`; **no** se configuró git, ni se creó remoto, ni se hizo push.

## Gate abierto — decisión del fundador

`docs/PLAN_ETAPA1.md` propone alcance y presupuesto, y **queda pendiente de aprobación**. Hay tres preguntas que no corresponde que decida un agente:

1. **Qué camino se toma** (A recomendado, B complemento, C fork de largo plazo).
2. **El presupuesto en turnos** para el PoC y para el MVP.
3. **Si se acepta el modelo "overlay pre-renderizado"** en lugar de un efecto con sliders en vivo. Es la consecuencia directa del bloqueo y cambia cómo se siente el producto.

## Dónde retomar

`RETOMAR.md`, que es el documento vivo de estado. El próximo paso concreto, **si el fundador aprueba el camino A**, es el PoC: generar un overlay de onda con alpha desde un archivo de audio y verificar que Drift lo compone con transparencia sobre una pista de video. Eso valida el camino de punta a punta antes de construir nada encima.

## Riesgos anotados

- **El análisis de beats de Drift es transitorio.** Cualquier edición que cambie la mezcla lo invalida (`docs/MCP.md:184`). Si el producto llega a depender de él, hay que chequear `stale` antes de confiar en una grilla.
- **Preview caro con alpha.** `PreviewProxyRenderer.cpp:40-45` rechaza proxies en clips transparentes. Generar el overlay a la resolución del proyecto y no más.
- **Drift está en desarrollo activo.** El clon es de la rama `main` al 2026-09-25. Un agente futuro debería re-verificar el hallazgo central antes de asumir que sigue vigente: si upstream agrega uniforms de audio, el camino C se vuelve gratis y el A queda obsoleto.
- **`apply` de MCP no es atómico.** Para en el primer error y deja aplicado lo anterior. Cualquier automatización tiene que ser idempotente o saber limpiar.
