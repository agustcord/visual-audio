# Dónde retomar

**Documento vivo.** Cada agente lo actualiza al cerrar su turno. Si lo que dice acá contradice a otro documento, gana la bitácora `.memory/log.md` — pero entonces alguien tiene que arreglar este archivo.

**Última actualización:** 2026-09-25, turno T1, agente Kiro.

---

## 🔴 Estado: DETENIDO esperando al fundador

El desarrollo **no arrancó a propósito**. El documento fundacional ordena definir presupuesto y alcance *antes* de desarrollar, y hay tres decisiones que no corresponde que tome un agente.

### Las tres preguntas abiertas

Están desarrolladas en [`docs/PLAN_ETAPA1.md`](docs/PLAN_ETAPA1.md) §1. Resumidas:

1. **¿Qué camino técnico?** Recomendado: **A** (generar el visualizador con FFmpeg y componerlo como overlay con alpha), con **B** (keyframes calculados vía MCP) como capa opcional. **C** (forkear Drift) queda como evolución futura.

2. **¿Se acepta el modelo "overlay pre-renderizado"?** Tamaño, posición, opacidad y velocidad quedan manejados por los controles nativos de Drift, gratis. El costo: cambiar **color** o **estilo** requiere regenerar el overlay — no hay slider de color en vivo. Es la consecuencia directa del bloqueo técnico.

3. **¿Se aprueba el presupuesto?** Propuesto: **10–14 turnos** para la Etapa 1 completa (PoC + MVP), con un punto de control duro después del turno de validación del PoC.

---

## Qué está hecho

| | Qué | Dónde |
|---|---|---|
| ✅ | Proyecto registrado en la bóveda de memoria Obsidian | `.memory/` |
| ✅ | Repositorio git inicializado, con `.gitignore` | `.gitignore` |
| ✅ | Investigación de viabilidad, con evidencia por archivo y línea | `docs/VIABILIDAD.md` |
| ✅ | Notas de dominio sobre Drift, su extensibilidad y su audio | `.memory/wiki/` |
| ✅ | Plan, presupuesto y criterios de aceptación falsables | `docs/PLAN_ETAPA1.md` |
| ✅ | Handoff del turno 1 | `.memory/handoffs/T1_registro_y_viabilidad_20260925.md` |
| ✅ | Commit de línea base (la "protección" que pide el documento fundacional) | rama `master` |
| ⬜ | Gate del fundador sobre las tres decisiones | `docs/PLAN_ETAPA1.md` §7 |
| ⬜ | Código de producto — **nada escrito todavía** | — |

---

## El próximo paso concreto

**Si el fundador aprueba el camino A**, el turno T2 hace, en este orden:

1. **Registrar el Gate.** Completar la tabla de `docs/PLAN_ETAPA1.md` §7 con las palabras del fundador, verbatim y con fecha. Sin esto el plan sigue en borrador.
2. **Andamiaje mínimo** del generador, sin lógica todavía: estructura de carpetas y decisión de lenguaje.

Y después, T3–T4, el PoC: generar un overlay de onda con alpha desde un archivo de audio, cumpliendo los criterios **PoC-1 a PoC-4** de `docs/PLAN_ETAPA1.md` §2.

### ⚠️ El turno que decide todo es T5

**PoC-5** — verificar que Drift compone la transparencia del overlay sobre una pista de video — **requiere al fundador con Drift abierto**. Si ese criterio falla, el camino A queda invalidado y hay que replantear antes de gastar un turno más. Conviene coordinarlo con anticipación.

**Si el fundador elige el camino C** (fork de Drift), este plan no sirve: hay que presupuestar de nuevo. Estimación gruesa sólo para dimensionar: 8–15 turnos *nada más para compilar Drift sin modificarlo*, más mantenimiento indefinido del fork.

---

## Lo que un agente nuevo tiene que saber antes de tocar nada

**El hallazgo central, en una línea:** Drift no le da ningún dato de audio a sus shaders. No hay uniform, textura ni buffer de audio en el pipeline de render.

Eso significa que **un visualizador no puede ser un efecto GPU que reaccione a la música**, que es lo primero que cualquiera intenta. Si vas a proponer arquitectura, **leé `.memory/wiki/Audio_reactividad_en_Drift.md` primero.** Tiene las citas por archivo y línea, y explica por qué el atajo obvio (hornear un espectrograma a PNG y leerlo desde el shader) tampoco funciona.

### Datos operativos que ya están verificados

- **Drift instalado:** `C:\Program Files\Drift\drift.exe` — **sólo lectura**, no escribir ahí.
- **Paquetes propios van a:** `C:\Users\Jonatan Agustín\AppData\Roaming\CutWire Drift\effects\` — escribible, sin verificación de firma.
- **FFmpeg:** `C:\ffmpeg\bin\ffmpeg.exe`, versión 8.0.1, con `showwaves`, `showspectrum`, `showfreqs`, `showcqt`, `avectorscope` compilados.
- **Código de referencia de Drift:** `_reference/drift-src/` (no versionado; el comando para reconstruirlo está en el handoff T1).
- **MCP de Drift:** se activa en Settings → Agent access. Apagado en cada arranque, bind sólo a `127.0.0.1`, token rotativo por sesión.

### Trampas ya documentadas, no las redescubras

- `apply` de MCP **no es atómico**: para en el primer error y deja aplicado lo anterior.
- Un batch de MCP **no puede referenciar un id creado en el mismo batch**.
- El análisis de beats de Drift es **transitorio**: cualquier edición que cambie la mezcla lo invalida. Chequear `stale`.
- Drift **niega proxies de preview a clips con transparencia** → preview caro con overlays.
- Los addons `.driftpkg` exigen **firma Ed25519**: esa vía de distribución está cerrada para un tercero.
- Las texturas de paquete se cachean **de por vida del proceso**, sin mtime en la clave.

---

## Vigencia

El informe de viabilidad describe la rama `main` de Drift al **2026-09-25**. Drift está en desarrollo activo.

Si pasó tiempo, **re-verificá el hallazgo central** antes de confiar en el plan:

```powershell
Select-String -Path "_reference\drift-src\src\**\*.cpp","_reference\drift-src\src\**\*.h" `
  -Pattern "u_audio|u_beat|u_rms|u_energy|u_band"
```

Si eso devuelve algo en el pipeline de render (no en medidores de UI), upstream agregó audio a los shaders: el camino C se volvió barato y `docs/VIABILIDAD.md` quedó obsoleto.
