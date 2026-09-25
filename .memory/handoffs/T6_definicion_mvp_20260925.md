---
tipo: "handoff"
turno: 6
agente: "Kiro"
fecha: 2026-09-25
estado: "cerrado — MVP definido, pendiente de aprobación del fundador"
---

# T6 — Investigación de mercado y definición del MVP

El fundador aprobó el motor propio y aceptó más turnos, pero **frenó antes de gastarlos** para definir con precisión qué hace el MVP. Fue la decisión correcta: al definirlo, el número de turnos pasó de 6 a 10, y mejor saberlo ahora.

## Lo que el fundador fijó, y una contradicción que hay que registrar

Criterio nuevo y decisivo:

> «el MVP no debe contener programación para el usuario final»

Con el recorrido: cargar audio, ver una onda predeterminada, elegir estilo, modificar valores, personalizar, guardar, exportar.

**Eso implica interfaz gráfica, y contradice el §3 de `PLAN_ETAPA1.md`**, que decía *"No interfaz gráfica propia. La línea de comandos primero; si el fundador la quiere, es etapa siguiente."* La contradicción se resuelve a favor de lo que dijo el fundador ahora: `docs/MVP.md` reemplaza ese §3.

También quedó **la PoC aprobada por ambos**, así que no se vuelve sobre eso.

## Frontera declarada

**Creado:** `.memory/wiki/Investigacion_visualizadores.md`, `docs/MVP.md`, este handoff.
**Modificado:** `.memory/index.md`, `.memory/log.md`, `.memory/wiki/MOC_Handoffs.md`.

**NO se tocó:** ningún código. Este turno no escribió producto a propósito — el fundador pidió definir antes de construir. `docs/PLAN_ETAPA1.md` queda **sin modificar**: su §3 está superseded por `docs/MVP.md`, y el registro del Gate de T2 sigue válido. `sobre_este_plugins.txt`, `C:\Program Files\Drift\`, la carpeta de datos de Drift y `_reference/` sin tocar. No se abrió Drift ni se activó su MCP.

## La investigación

Siete herramientas relevadas: Music Visualizer Lab, EchoWave, SoundGrail, LyricsToSong, Banger.show, audiospectr y Wav2Bar. Todo en `.memory/wiki/Investigacion_visualizadores.md` con fuentes citadas, y con la aclaración explícita de que **no se copió código de ninguna**.

### Cinco cosas que cambiaron el plan

1. **El espectro de barras es el estilo principal, no la forma de onda.** Nosotros arrancamos por la onda únicamente porque `showwaves` de FFmpeg ya existía — o sea, la herramienta disponible nos había elegido la prioridad. Las siete la tratan como el estilo central.
2. **Faltaban parámetros estándar.** El plan mencionaba color, velocidad, tamaño, posición y opacidad. El mercado considera igual de básicos: sensibilidad, suavizado temporal, cantidad de barras, separación, degradado de dos colores, tapas de pico y resplandor.
3. **Hay rangos publicados**, así que no hace falta inventar: barras 5–240 e intensidad 0.5–10 (Banger.show), suavizado 0.65 por defecto (audiospectr).
4. **La previsualización tiene que usar el motor de producción.** audiospectr lo resuelve con `--dump-frame`, que renderiza un cuadro real. Si la interfaz dibujara su propia versión rápida, tendríamos dos motores desincronizándose y la vista previa mentiría.
5. **Un solo análisis alimenta todos los estilos**, así que cambiar de estilo no puede romper la sincronía. EchoWave lo vende como característica; es la consecuencia de separar análisis de dibujo.

### La arquitectura quedó validada por fuentes independientes

`audiospectr` describe el mismo diseño de tres etapas que propusimos en T5: pre-analizar a datos por cuadro, componer capas, pasar cuadros crudos a FFmpeg. No es que hayamos acertado por suerte, pero conviene saber que es el camino que otros ya recorrieron.

### Antecedentes: se evaluó usarlos, y se declara por qué no

- **audiospectr** (MIT, Python, CLI) hace mucho de lo que queremos. No sirve tal cual porque exporta MP4 con audio compuesto **sobre un fondo** —lo opuesto a un overlay sin fondo y sin audio—, requiere `uv` y `librosa`, y **no tiene interfaz**. Se declaró igual un **atajo real**: con `--background-color "#00FF00"` su MP4 se podría recortar con el Chroma Key de Drift, por si el fundador prefiere probar antes de que construyamos.
- **Wav2Bar** es el antecedente más cercano en *forma de producto*. **No se encontró evidencia de export con canal alpha ni fondo transparente**, que es el requisito central, y está en reescritura.

Ninguna resuelve *overlay sin fondo para un editor de video*.

## El MVP, resumido

Detalle completo en `docs/MVP.md`.

- **Tres estilos**: barras, barras espejadas, onda. Elegidos porque comparten el mismo modelo de disposición (banda horizontal), así que el segundo y el tercero son funciones de dibujo y no arquitectura nueva.
- **Circular afuera, y no se promete**: introduce coordenadas polares, centro, radio interior y rotación — otra familia de parámetros y otra forma de posicionar. Primer candidato a agregarse después.
- **~25 valores** en cinco grupos: reacción al audio, forma, posición y tamaño, color, salida.
- **Interfaz de escritorio con tkinter**, que viene con Python y ya está en la máquina (Tk 8.6 verificado). Cero instalación: es la respuesta directa a que After Effects le resultara pesado y caro.
- **Regla de arquitectura que no se negocia:** la vista previa se dibuja con el mismo motor que exporta. Consecuencia honesta declarada: **no habrá previsualización en vivo a 30 fps**, sino un cuadro real que se actualiza, más fragmentos cortos animados a pedido.
- **El motor no sabe que existe la interfaz.** Es una biblioteca; la interfaz y la línea de comandos son dos clientes. Si la interfaz resulta incómoda se reemplaza sin tocar el motor, y mientras se construye hay algo usable en cada turno.
- **Nueve criterios de aceptación falsables.** MVP-9 (el fundador edita un video solo, sin preguntar nada) es el real; MVP-5 (vista previa idéntica al export) es el que protege contra la trampa de los dos motores.

## El presupuesto, con el número incómodo

**10 turnos**, no 6. Lleva la Etapa 1 a **16 en total**, contra los **10–14 aprobados** en el Gate de T2.

No es un sobrecosto por imprevistos: el alcance creció cuando se decidió motor propio (T5) e interfaz gráfica (T6), y las dos decisiones fueron deliberadas y del fundador. Pero el exceso **necesita su aprobación explícita**, y se le ofrecieron dos cortes:

1. Sin interfaz: −3 turnos, entra en presupuesto, **pero no cumple lo que él mismo pidió**. Se recomienda no recortar ahí.
2. Dos estilos en vez de tres: −1 turno. Ahorra poco, porque las espejadas son casi gratis.

Se propuso además un **punto de control tras la etapa 2** (4 turnos), donde el fundador va a poder ver barras reales sobre su video **antes** de gastar los 3 turnos de interfaz. Si el aspecto no convence, corregir ahí es barato.

## Dónde retomar

`RETOMAR.md`. **No empezar a construir hasta que el fundador responda las cinco preguntas de `docs/MVP.md` §9**, en particular la aprobación de los 10 turnos. Construir antes sería exactamente lo que él quiso evitar al pedir el freno.

Falta un dato suyo: **a qué resolución y cuadros por segundo trabaja en Drift**. Se asumió 1920×1080 a 30; si hace vertical para Shorts o Reels, cambian los defaults.
