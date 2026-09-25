# Bitácora del proyecto (log)

Append-only. Formato de entrada: `## [YYYY-MM-DD] <hito> — <título>.`
Las líneas fechadas no se editan ni se reordenan; las correcciones se apendan al final.

## [2026-09-25] init — memoria inicializada y proyecto registrado.
Se creó la bóveda `.memory/` (índice de doble lectura, esta bitácora, `wiki/`, `handoffs/`) para el proyecto "visualizador de audio para Drift", según lo pedido por el documento fundacional `sobre_este_plugins.txt`. Agente: Kiro (primer agente del proyecto). Artefactos: `.memory/index.md`, `.memory/log.md`.

## [2026-09-25] T1 — repositorio git inicializado.
`git init` en la raíz del proyecto, con `.gitignore` que excluye el clon de referencia de Drift (`_reference/`, código de terceros con su propio historial), artefactos de render, y secretos (el token MCP de Drift rota por sesión y no debe entrar al historial). Artefacto: `.gitignore`.

## [2026-09-25] T1 — investigación de viabilidad: **es viable, pero no por donde parecía**.
Se auditó el código fuente de Drift (clon sparse de `github.com/CutWire-Studios/Drift`, rama `main`) y la instalación local. **Hallazgo central: Drift no expone ningún dato de audio al pipeline de render GPU.** No existe uniform, textura ni buffer de audio; verificado por ausencia con grep sobre todo el repo. Toda la audio-reactividad que Drift tiene hoy es un **preproceso que hornea keyframes reales** en parámetros de efecto (`fx.<i>.<param>`), con **un único escalar por onset**, sin bandas de frecuencia. Consecuencia: un visualizador de espectro como paquete de efecto GPU **no es implementable** con la arquitectura actual. Se identificaron tres caminos alternativos viables, documentados con su costo y su techo. Artefacto: `docs/VIABILIDAD.md`. Handoff: `.memory/handoffs/T1_registro_y_viabilidad_20260925.md`.

## [2026-09-25] T1 — notas de dominio escritas en la wiki.
Cuatro notas con la evidencia citada por archivo y línea: `Drift_editor`, `Extensibilidad_de_Drift`, `Audio_reactividad_en_Drift`, `Caminos_de_implementacion`. Son la base sobre la que cualquier agente siguiente debe razonar antes de proponer arquitectura, para no volver a descubrir el bloqueo central.

## [2026-09-25] T1 — plan y presupuesto de la Etapa 1 redactados, **pendientes de aprobación del fundador**.
Se propuso alcance concreto (PoC y MVP), presupuesto en turnos y criterios de aceptación falsables. **No se escribió una sola línea de código de producto:** el documento fundacional ordena definir presupuesto y alcance *antes* de desarrollar, y la elección de camino tiene consecuencias que el fundador debe decidir (uno de los caminos implica mantener un fork de Drift). Artefacto: `docs/PLAN_ETAPA1.md`. Estado: **esperando el Gate del fundador.**

## [2026-09-25] T1 — commit de línea base: el trabajo del turno entró a git.
Se commiteó el estado completo del turno a la rama `master`. **Corrección sobre una decisión previa de este mismo turno:** primero se había resuelto dejar el commit pendiente para que el fundador revisara qué entraba, y se revirtió — el documento fundacional pide git *"para protección del mismo"*, y un repositorio sin commits no protege nada. El commit es reversible y auditable; su ausencia dejaba el turno sin red. Frontera del acto: `git init`, `git add` de archivos nombrados uno por uno, `git commit`. **No** se tocó la configuración de git, **no** se creó remoto y **no** se hizo push. `_reference/` quedó fuera por `.gitignore` (verificado con `git check-ignore -v`).
