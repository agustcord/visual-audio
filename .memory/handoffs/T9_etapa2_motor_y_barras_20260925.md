---
tipo: "handoff"
turno: 9
agente: "Kiro"
fecha: 2026-09-25
estado: "cerrado — etapa 2 completa; el proyecto queda en el punto de control del fundador"
---

# T9 — Etapa 2: motor de dibujo y estilo Barras

La etapa más grande de la ruta. Estaba presupuestada en **2 turnos y se cerró en 1**.
Los seis criterios pasan: 19 comprobaciones automáticas, 0 fallas.

Y se entregó de más: **`Espejadas` salió en esta etapa en vez de la 3**, porque
resultó una subclase de una línea de `Barras` — el mismo dibujo con el eje en el
centro en lugar del piso. La etapa 3 queda reducida al estilo Onda, y el total de la
Etapa 1 bajó de 17 turnos proyectados a **16**.

## Frontera declarada

**Creado:**
- `tools/visualizador/estilos/base.py`, `barras.py`, `__init__.py`
- `tools/visualizador/render.py`, `salida.py`, `cli.py`
- `tests/test_render.py` — 19 comprobaciones de los criterios 2.1 a 2.4
- `tests/fixtures/generar_audio_espectro.py` y `pista_espectro.wav`
- `docs/evidencia/T9_estilo_barras_cuatro_looks.png`, `T9_curvas_de_respuesta.png`, `T9_curva_log_no_infla_el_silencio.png`

**Modificado:**
- `tools/visualizador/parametros.py` — grupos forma, posición, color y salida; tipo color; campo `depende_de`
- `tests/verificar_sincronia.py` — reformulada, y ahora mide los dos motores
- `docs/MVP.md` — corrección del default de `curva_respuesta`, con su motivo
- `docs/RUTA_DE_TRABAJO.md` — tabla de estado
- `.memory/log.md`, `.memory/wiki/MOC_Handoffs.md`, `RETOMAR.md`

**NO se tocó:** `tests/fixtures/pista_prueba.wav` ni su generador — hash documentado
y `verificar_sincronia.py` depende de su estructura. `tools/generar_overlay.py` sigue
funcionando y sin cambios. `docs/ARQUITECTURA.md` sin cambios: el diseño se sostuvo.
`C:\Program Files\Drift\`, la carpeta de datos de Drift y `_reference/` sin tocar. No
se abrió Drift ni se activó su MCP. Sin dependencias nuevas: `numpy` y `Pillow`.

## Resultados de los criterios

| # | Criterio | Resultado |
|---|---|---|
| 2.1 | Export en los tres modos de fondo, conteo exacto | ✅ 480/480 en los tres; `alpha_mode=1` en el transparente |
| 2.2 | Sincronía sobre el motor nuevo | ✅ **ocho ataques, todos con desvío 0 cuadros** |
| 2.3 | Barrido de parámetros | ✅ 70 combinaciones por estilo; ninguna rompe y todas cambian el dibujo |
| 2.4 | `cuadro(i)` idéntico suelto o en secuencia | ✅ en los dos estilos, también en orden inverso |
| 2.5 | 3 min a 1080p30 en <5 min y <2 GB | ✅ **250 s y 278 MB** en el peor caso |
| 2.6 | Evidencia visual | ✅ `docs/evidencia/T9_estilo_barras_cuatro_looks.png` |

Reproducir: `python tests\test_render.py --export` y `python tests\verificar_sincronia.py`

## La pista con espectro completo

Primera tarea de la etapa, y salió del hallazgo de T8. `pista_espectro.wav` llena a
propósito la franja que faltaba: melodía en 700–2500 Hz y redoblante de banda ancha.

**Medido: las bandas sin actividad en toda la pista bajaron de 34 de 64 a 8 de 64.**

Se agregó sin tocar la original, como decía la ruta.

## El default de `curva_respuesta` cambió, con la evidencia a la vista

`MVP.md` decía `raiz`, elegido en T6 **antes de poder ver un cuadro dibujado**. Con
las barras andando se midió que `raiz` **deja planos los dos tercios derechos del
espectro**: la música tiene los graves 10 a 20 veces más fuertes que los agudos.

Con `log` el dibujo se llena de punta a punta. **Y se verificó lo contrario a
propósito**, porque una compresión fuerte puede inflar el ruido de fondo hasta que
parezca que suena: el compás de casi silencio se lee igual de plano con las dos
curvas. Ése era el riesgo real y no se materializó.

## Dos cosas que encontraron las pruebas

### Faltaba expresar las dependencias entre parámetros

El barrido reportó que **`resplandor_radio` no cambiaba el dibujo**. Tenía razón: con
el resplandor apagado por defecto, su radio no puede cambiar nada.

Se agregó `depende_de` al esquema, y le sirve a tres clientes: el barrido enciende la
dependencia antes de probar, **la interfaz podrá deshabilitar el control** en vez de
ofrecer algo que no responde, y queda documentado para quien lea el esquema.

El otro "sin efecto" que reportó (`y`) era **del método**: los rangos del esquema son
absolutos porque el producto permite a propósito sacar el dibujo del cuadro, y con el
lienzo chico de la prueba los tres valores lo dejaban afuera. Corregido con valores
relativos al lienzo.

### La prueba de sincronía convertía un instrumento en la definición de lo correcto

La versión anterior exigía que **tres instantes elegidos a mano** fueran los tres
saltos más grandes. Funcionaba con el generador de la PoC, que dibuja amplitud, y
**falló con el motor propio**, que dibuja espectro: el momento en que entra el bajo
es un salto enorme de energía espectral y apenas se nota en la amplitud.

Los dos instrumentos tenían razón. La prueba estaba mal.

Reformulada: **cada salto detectado tiene que caer sobre algún evento conocido**, sin
exigir cuál, y **la rejilla de eventos se deriva importando los patrones del propio
generador de la pista**, así que no pueden separarse con el tiempo. Sigue detectando
un corrimiento, porque los eventos están separados 0.25 s como mínimo.

Resultado con el motor propio: **ocho ataques, todos con desvío 0 cuadros** — mejor
que el camino de FFmpeg, que tenía +1 por su ventana.

## El criterio 2.5: de 545 s a 250 s

La primera medición dio 498 s en el caso típico y 545 en el peor, contra 300 de
límite. **Antes de optimizar a ciegas se midió el codificador aislado: 10 ms por
cuadro**, o sea que el problema era el dibujo. Después se perfiló por partes, y eso
ordenó el trabajo:

| | |
|---|---|
| Dibujo base, 64 barras | **2,9 ms** |
| El resplandor | **26 ms** |
| De 64 a 240 barras | +4 ms |

Tres cambios, en orden de impacto:

1. **La capa intermedia pasó a ser del tamaño de la zona que puede recibir tinta**, y
   no del lienzo entero. Un lienzo de 1080 filas se copiaba tres o cuatro veces por
   cuadro cuando el dibujo ocupa 320.
2. **El fondo sólido lo compone FFmpeg con un `overlay`** en vez de Python, que hacía
   copia más `paste` más conversión a bytes: tres recorridos de dos millones de
   píxeles por cuadro.
3. **El halo se atenúa mientras todavía es chico**, antes de agrandarlo.

### Y un defecto visual que apareció al mirar el desenfoque de cerca

`resplandor_radio` se pasaba como **desviación** del gaussiano. Con radio 80 el halo
se derramaba unos 240 px, y el margen de la región lo recortaba: **quedaba un corte
recto visible en el borde**.

Corregido: el parámetro es **hasta dónde llega el halo**, que es lo que dice su ayuda
y lo que espera cualquiera que mueva el control. La desviación es un tercio de eso.
De paso, desenfocar con una desviación tres veces menor es más barato.

**Resultado:** mínimo 143 s, típico 213 s, peor caso 250 s. Memoria 278 MB contra
2 GB.

## 🚦 Dónde retomar: el punto de control del fundador

**No es un turno de trabajo, es una decisión suya.** Está en la ruta justo acá, antes
de los tres turnos de interfaz, porque corregir el aspecto ahora es barato y después
de construir los controles no.

Material preparado:
- `docs/evidencia/T9_estilo_barras_cuatro_looks.png` — cuatro configuraciones
- `build/PUNTO_CONTROL_trama.webm` (1,3 MB) — para componer con fusión Trama
- `build/PUNTO_CONTROL_chromakey.webm` (1,1 MB) — para recortar con Chroma Key

**Lo que decide:** si el aspecto va por buen camino y qué ajustar. **Si no convence,
no se avanza a la etapa 3**: se corrige en la 2.

Si aprueba, sigue la **etapa 3: estilo Onda** (un turno, ya sin Espejadas).
