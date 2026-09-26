---
tipo: "handoff"
turno: "T10"
fecha: 2026-09-25
agente: "Kiro"
tema: "Punto de control aprobado, decisión de composición, y el color de Trama medido"
commit: "pendiente al escribir; ver git log"
---

# T10 — Punto de control aprobado y el color de Trama medido

Turno **no presupuestado**: era el punto de control del fundador, que es una decisión suya y no trabajo de agente. Se consumió en medir y documentar la pregunta que trajo, no en código de producto.

## Lo que decidió el fundador, verbatim

> *"Por lo que veo la funcion de chroma key no esta muy avanzada dentro de drift en esta version, es muy dificil ocultar. Por el momento vamos con trama, el tema es poder ajustar la combinación de colores del fondo, cuando nuestro fondo sea de cierto color (estoy pensando que tal vez si deberiamos apuntar a la 0.7 o aceptar en esta version que el color que podamos obtener puede defirir del color deseado, solo una aproximación). Sobre los estilos y variables, para esta primer version me parece bien."*

Se traduce en tres cosas:

| | |
|---|---|
| **Aspecto del estilo Barras** | ✅ **Aprobado.** Desbloquea la etapa 3 |
| **Estilos y ~25 parámetros** | ✅ Aprobados para la primera versión. No se reabre el alcance |
| **Composición** | **Trama.** Chroma Key descartado para esta versión, con evidencia de uso a mano |

**El modo `color` (Chroma Key) no se borra.** Sigue implementado y verificado. Deja de ser ruta recomendada, no deja de existir. Regla 15 de la ruta: una decisión revertida se marca, no se elimina.

## La pregunta del color: qué se midió y qué salió

El fundador la planteó como una disyuntiva (apuntar a 0.7 **o** aceptar una aproximación). Medida, la disyuntiva se disuelve por dos lados distintos.

### Primero: había dos cosas mezcladas en "aproximación"

- **El fondo no se aproxima: desaparece exacto.** Con `src = 0`, Trama da `out = base`. Identidad algebraica, no truco. Verificado sobre seis fondos: los seis `intacto`.
- **El color de la barra sí se corre**, siempre hacia el blanco, y cuánto depende del brillo del video **detrás de las barras**.

Esa separación importa porque lo que se temía perder (que el video se ensucie donde no hay dibujo) no se pierde nunca.

### Segundo: no hay que elegir entre 0.6 y 0.7

**El modo `transparente` ya está escrito y verificado** en `salida.py` desde T9, con los `-auto-alt-ref 0` y `-lag-in-frames 0` obligatorios. El día que 0.7 traiga el preset de alpha, el fundador cambia una opción. Apuntar a 0.7 no es trabajo pendiente: es una opción ya construida.

Lo que **no** se puede hacer es probarla, porque no existe una 0.7 contra la que verificar. Escribir más código para eso violaría la regla 6 (nada se declara cumplido sin el comando que lo prueba).

### Los números

`python tools\medir_trama.py` — ΔE76, 6 fondos × 5 colores de barra:

| Fondo | blanco | celeste | rosa | amarillo | rojo oscuro |
|---|---|---|---|---|---|
| negro puro | 0 | 0 | 0 | 0 | 0 |
| casi negro `#141414` | 0 | 2 | 5 | 5 | 8 |
| azul nocturno `#101C38` | 0 | 2 | 9 | 16 | 25 |
| gris medio | 0 | 17 | 38 | 37 | 47 |
| piel iluminada | 0 | 33 | 47 | 33 | 49 |
| blanco quemado | 0 | 42 | 74 | 70 | 84 |

**Dos hallazgos que no se esperaban y que cambian recomendaciones:**

1. **El blanco es exacto sobre cualquier fondo.** Columna entera en 0, porque `src = 1` da `out = 1` siempre. Una barra blanca es inmune al problema. Es la salida segura para metraje claro o cambiante, y por eso la etapa 4 debe traer un preset blanco.
2. **La compensación `src = 1 - (1-D)/(1-B)` da ΔE 0.0 exacto** sobre los tres fondos oscuros. No "mejor": exacto. Y es **imposible** cuando `D < B` en algún canal, porque Trama sólo suma luz. No es un defecto de Drift.

## Frontera: qué se tocó y qué no

**Nuevo**
- `tools/medir_trama.py` — reproduce la fusión de Drift y mide el corrimiento en ΔE76 (Lab, D65)
- `docs/COLOR_EN_TRAMA.md` — la respuesta completa, con la fórmula citada del shader
- `docs/evidencia/T10_trama_corrimiento_de_color.png`
- `.memory/wiki/Composicion_de_overlays_en_Drift.md` — los 7 modos de fusión con su matemática

**Modificado**
- `docs/RUTA_DE_TRABAJO.md` — Gate cerrado; etapa 3 pasa a ser sólo Onda (el encabezado todavía decía "Onda y Barras espejadas", desactualizado desde T9); etapa 4 recibe `compensar_fondo` y tres criterios nuevos (4.5–4.7); §2 lista el documento nuevo
- `RETOMAR.md` — estado, decisiones del punto de control, dos entradas de deuda nuevas; se sacó un párrafo de T7 que seguía anunciando la etapa 2 como siguiente
- `.memory/index.md` — nota nueva en el MOC y en el índice máquina

**NO se tocó**
- **Nada de `tools/visualizador/`.** Ni una línea de código de producto. La compensación es etapa 4, no se adelantó
- Los estilos, el análisis, la salida, las pruebas. Las 55 comprobaciones siguen como estaban
- El modo `color` y el modo `transparente`: los dos quedan
- `docs/COMO_USAR.md` — sigue describiendo la PoC. Es deuda de la etapa 6 y no se tocó acá para no hacer un arreglo a medias

## Verificado en este turno

```powershell
python tests\test_analisis.py      # 36 comprobaciones, 0 fallas
python tests\test_render.py        # 15 (las 4 de export piden --export)
python tools\medir_trama.py        # tabla + PNG
```

La fórmula de Trama está leída de `_reference/drift-src/src/engine/GpuCompositor.cpp:135`. ⚠️ **Ese clon es 0.7.0-dev.** No se verificó contra el binario 0.6.0 instalado, y no hacía falta: el fundador ya comprobó a mano que Trama funciona en su versión, que es la evidencia más fuerte que el `findstr`. Si algún día un resultado de color no cuadra, ése es el primer supuesto a revisar.

## Para el próximo agente

**Etapa 3, estilo Onda.** Un turno. Las dos precondiciones están cumplidas: etapa 2 cerrada (T9) y punto de control aprobado (T10). Se puede empezar directo.

Y el pendiente derivado, que **no se adelantó a propósito**: `compensar_fondo` en la etapa 4. Los tres requisitos están en `docs/COLOR_EN_TRAMA.md` §6. El que importa es el tercero: la vista previa tiene que mostrar el resultado **compuesto** sobre el fondo declarado, porque si no el usuario ve barras oscurísimas y cree que se rompió algo. Eso toca el contrato de `render.cuadro(i)`, que hoy devuelve el dibujo con alpha y nada más — así que se diseña en la 4 y se implementa con la interfaz en la 5.
