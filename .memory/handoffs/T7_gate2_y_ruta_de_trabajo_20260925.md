---
tipo: "handoff"
turno: 7
agente: "Kiro"
fecha: 2026-09-25
estado: "cerrado — todo aprobado, la construcción arranca en la etapa 1"
---

# T7 — Gate 2 registrado y ruta de trabajo para cualquier agente

El fundador aprobó el MVP completo, el presupuesto ampliado y confirmó el dato que faltaba. Y pidió una cosa más antes de construir:

> «Apruebo todo lo que menciona, pero antes de seguir, en caso que no este aún, debe haber un mapa/ruta de trabajo para que cualquier agente pueda retomar además de vos»

Tenía razón en que faltaba. Había `RETOMAR.md`, que dice **dónde estás parado**, pero no existía la **ruta completa** con criterios de entrada y salida por etapa, ni la **forma del código** para que dos agentes no construyan piezas incompatibles.

## Frontera declarada

**Creado:**
- `docs/RUTA_DE_TRABAJO.md` — la ruta ejecutable: tabla de estado, siete etapas con precondiciones y criterios de salida verificables, quince reglas de trabajo
- `docs/ARQUITECTURA.md` — estructura del código y los seis contratos entre módulos
- `.memory/handoffs/T7_gate2_y_ruta_de_trabajo_20260925.md` (este archivo)

**Modificado:**
- `docs/PLAN_ETAPA1.md` — **§10 nueva con el Gate 2**, verbatim; §7 marca la decisión 3 como superseded
- `RETOMAR.md` — reescrito: estado verde, y apunta a la ruta como punto de entrada
- `README.md` — sección para agentes reescrita apuntando a la ruta
- `.memory/index.md`, `.memory/log.md`, `.memory/wiki/MOC_Handoffs.md`

**NO se tocó:** ningún código. Este turno tampoco escribió producto, a propósito — el fundador pidió la ruta *antes de seguir*. `sobre_este_plugins.txt`, `C:\Program Files\Drift\`, la carpeta de datos de Drift y `_reference/` sin tocar. No se abrió Drift ni se activó su MCP. `docs/MVP.md` quedó **sin cambios**: fue aprobado tal como estaba.

## El Gate 2

Registrado en `docs/PLAN_ETAPA1.md` §10 con el texto verbatim del fundador de los turnos T5, T6 y T7. Lo resuelto:

| | |
|---|---|
| Motor de dibujo | **Propio** |
| PoC | **Aprobada por ambos**, no se reabre |
| Definición del MVP | `docs/MVP.md` completo |
| Sin programación para el usuario final | Implica **interfaz gráfica** |
| Presupuesto | **10 turnos de MVP** |
| Resolución y fps | **1920×1080 a 30** como default; la herramienta debe admitir otros |
| Estilos | Barras, espejadas, onda. Circular afuera |
| Lo que el MVP no hace | Lista de `MVP.md` §6 confirmada |

**Consecuencia registrada:** el §3 de `PLAN_ETAPA1.md` (alcance del MVP, que decía *"No interfaz gráfica propia"*) queda **superseded por `docs/MVP.md`**. No se borra, para que quede el registro de lo que se pensaba antes.

### Una corrección de aritmética, declarada y no disimulada

El Gate 2 aprobó *"10 turnos de MVP, Etapa 1 a 16"*, contando 6 turnos consumidos. **Este turno es el séptimo**, así que el total honesto es **17**, no 16.

La diferencia es este turno de documentación, que el fundador pidió expresamente. Está anotado en la tabla de estado de la ruta con su explicación, en vez de redondearse para abajo.

## Qué resuelve cada documento nuevo

### `docs/RUTA_DE_TRABAJO.md`

El mapa. Su valor está en tres cosas:

1. **Tabla de estado** que el agente que cierra una etapa actualiza. Es el punto de sincronización: se lee de un vistazo en qué etapa está el proyecto.
2. **Criterios de salida que son comandos, no opiniones.** Cada etapa dice cómo se verifica que terminó. Varios existen específicamente para atrapar los errores que ya cometimos: el criterio 1.3 verifica alineación temporal porque el desfase de 100 ms de T3 nació de no verificarla; el 2.4 verifica que `cuadro(i)` dé lo mismo suelto que en secuencia, porque de eso depende que la vista previa sea posible; el 5.2 compara vista previa contra export, que es lo que protege contra la trampa de los dos motores.
3. **Quince reglas de trabajo**, cada una pagada con un error real. Las de medición son las que más importan.

También tiene un **punto de control del fundador después de la etapa 2**, que no es un turno de trabajo sino una decisión: ver barras reales sobre su video **antes** de gastar los tres turnos de interfaz. Corregir el aspecto ahí es barato; después de construir los controles, no.

### `docs/ARQUITECTURA.md`

La forma del código. Existe para que dos agentes en etapas distintas produzcan piezas que encajan.

Define las tres etapas que no se conocen entre sí (análisis → dibujo → salida), la estructura de archivos, y **seis contratos concretos** con firmas. Los dos que más importan:

- **`analisis` debe producir exactamente `round(duracion * fps)` cuadros**, y el cuadro `i` cubre el audio de `i/fps` a `(i+1)/fps`. Es la lección de T3 convertida en contrato.
- **Los estilos no tienen estado entre cuadros.** Todo lo temporal (suavizado, caída de picos) vive en el análisis. Sin esa regla no se puede dibujar un cuadro suelto, y sin eso no hay vista previa.

Y deja registrado **qué hace difícil a propósito**: un estilo con estado, o una vista previa que dibuje distinto al export. No hay camino para hacer ninguna de las dos sin romper un contrato explícito.

## Dónde retomar

**Etapa 1 de `docs/RUTA_DE_TRABAJO.md`: análisis de audio.** Un turno.

No hay nada pendiente del fundador. El siguiente agente puede empezar a construir, leyendo primero `MVP.md` y `ARQUITECTURA.md`.

## Riesgos anotados para las etapas que vienen

| Riesgo | Cuándo aparece | Mitigación ya prevista |
|---|---|---|
| El análisis no separa bandas y todas las barras suben juntas | Etapa 1 | Criterio 1.4 lo mide contra la estructura conocida de la pista de prueba |
| Un estilo guarda estado y rompe la vista previa | Etapa 2 | Criterio 2.4, y el contrato lo prohíbe explícitamente |
| El dibujo resulta lento y el render de una canción se vuelve incómodo | Etapa 2 | Criterio 2.5 con número; `ARQUITECTURA.md` señala el resplandor como sospechoso principal y dice medir antes de optimizar |
| El aspecto no le gusta al fundador después de invertir en la interfaz | Etapa 3 | El punto de control está **antes** de la interfaz, no después |
| La interfaz se desincroniza del esquema de parámetros | Etapa 5 | Criterio 5.5 compara esquema contra controles; el panel se construye leyendo el esquema |
| La vista previa miente | Etapa 5 | Criterio 5.2. Si falla, **parar**, no seguir |
