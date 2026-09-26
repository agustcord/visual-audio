# Definición del MVP

**Estado: PROPUESTA — pendiente de aprobación del fundador.**
**Fecha:** 2026-09-25 · **Turno:** T6 · **Agente:** Kiro
**Base:** `.memory/wiki/Investigacion_visualizadores.md` (relevamiento de siete herramientas del mercado)

Este documento reemplaza el §3 de `PLAN_ETAPA1.md`, que definía el MVP antes de saber lo que ahora sabemos.

---

## Antes de todo: qué queda cerrado

- **La PoC está aprobada** por ambos. No se vuelve sobre eso.
- **El motor de dibujo es propio**, no los filtros de FFmpeg. Decidido en T5 con evidencia.
- **La herramienta es externa a Drift.** Genera un archivo que se importa.
- **La transparencia la resuelve Drift** con modo Trama o Chroma Key en 0.6.0, o con canal alpha cuando salga 0.7.0. Es un parámetro, no una apuesta.

---

## 1. Qué hace el MVP, de punta a punta

El recorrido que describió el fundador, hecho explícito:

```
1. Abrir la aplicación
2. Cargar un audio  (MP3 de base; también WAV, FLAC, M4A, OGG)
3. Ver de inmediato una vista previa con el estilo y los valores por defecto
4. Elegir un estilo de una lista
5. Modificar sus valores, viendo el cambio en la vista previa
6. Moverse por la canción para ver cómo queda en otros momentos
7. Guardar el proyecto  (para reabrirlo y seguir después)
8. Exportar el video para Drift
```

**Sin escribir una línea de código ni de línea de comandos.** Ése es el criterio que ordena todo el diseño.

### Una regla de arquitectura que no se negocia

**La vista previa se dibuja con el mismo motor que exporta.**

Si la interfaz dibujara su propia versión rápida para previsualizar, tendríamos dos motores desincronizándose y la vista previa mentiría. Es la trampa clásica de estas herramientas, y Drift mismo hace bandera de lo contrario: *un compositor, un resultado, sin sorpresas*.

Consecuencia honesta: la vista previa **no va a ser un video a 30 cuadros por segundo en vivo**. Va a ser un cuadro real, que se actualiza cuando movés un valor (del orden de décimas de segundo) y que podés mover a lo largo de la canción. Además va a haber un botón para renderizar **un fragmento corto animado** cuando quieras ver el movimiento de verdad.

Menos espectacular que un lienzo en vivo. Pero lo que ves es lo que exportás.

---

## 2. Cuántos estilos: tres, y por qué esos

El fundador preguntó cuántos. La investigación dice que el mercado considera imprescindibles las barras, la onda y el circular.

### Los tres del MVP

| Estilo | Qué es | Por qué está |
|---|---|---|
| **Barras** | Barras verticales, una por banda de frecuencia, creciendo desde la base | Es **el** estilo de video musical. Aparece en las siete herramientas relevadas |
| **Barras espejadas** | Barras simétricas que crecen desde el centro hacia arriba y abajo | Muy usado, y **casi gratis** una vez que existen las barras: es el mismo dibujo con otro origen |
| **Onda** | Línea de amplitud, con relleno opcional | Es lo que pediste originalmente, y ya está probado en la PoC |

**El motivo de que sean estos tres y no otros:** los tres comparten el mismo modelo de disposición — una **banda horizontal** que se ubica con x, y, ancho y alto. Una vez construido ese modelo, el segundo y el tercer estilo son funciones de dibujo nuevas, no arquitectura nueva.

### El cuarto, y su costo real

**Circular / radial** — barras alrededor de un anillo. Es el siguiente en importancia según la investigación, y visualmente el más llamativo.

**No está en el MVP porque introduce un segundo modelo de disposición**: coordenadas polares, centro en vez de esquina, radio interior y exterior, rotación. No es una función de dibujo más: es otra familia de parámetros y otra forma de posicionar.

**Propuesta:** queda como el primer agregado después del MVP. Si el presupuesto alcanza, entra; si no, se hace en la etapa siguiente. **No se promete.**

### Lo que queda afuera y no se discute en esta etapa

Partículas, pulso de anillos, texto (título/artista), barra de progreso, 3D. Existen en otras herramientas, no son lo que pediste, y cada uno es una familia de parámetros entera.

---

## 3. Qué valores se pueden modificar

El fundador preguntó cuáles. Mencionó longitud, espesor y posición horizontal y vertical. La investigación agregó varios que son estándar y que faltaban en el plan original.

Están agrupados por lo que hacen, que es también como irían en la interfaz.

### A. Reacción al audio — los que más cambian la sensación

| Valor | Rango | Default | Qué hace |
|---|---|---|---|
| **Sensibilidad** | 0.5 – 10 | 3.0 | Cuánto salta el dibujo con el sonido. El que más cambia el carácter |
| **Suavizado** | 0 – 1 | 0.65 | 0 = nervioso y exacto; 1 = fluido y perezoso |
| **Rango de frecuencias** | 20 Hz – 20 kHz | 40 – 14000 | Qué parte del espectro se dibuja. Recortar los extremos suele mejorar mucho |
| **Curva de respuesta** | lineal / raíz / log | **log** | Cuánto se levantan los pasajes suaves |

> **Corrección del default, hecha en la etapa 2 con la evidencia a la vista.** Este
> documento decía `raiz`, elegido antes de poder ver un cuadro dibujado. Con las
> barras andando se midió que **`raiz` deja planos los dos tercios derechos del
> espectro**: la música tiene los graves 10 a 20 veces más fuertes que los agudos, y
> la raíz no comprime lo suficiente. Con `log` el dibujo se llena de punta a punta
> **y el pasaje silencioso sigue leyéndose como silencio** — se verificó lo segundo
> a propósito, porque una compresión fuerte puede inflar el ruido de fondo hasta que
> parezca que suena. Evidencia: `docs/evidencia/T9_curvas_de_respuesta.png`.
| **Caída de picos** | 0 – 1 | 0.4 | Qué tan rápido baja el dibujo después de un golpe |

Rangos de sensibilidad y suavizado tomados de las convenciones relevadas (Banger.show publica 0.5–10 para intensidad; audiospectr usa 0.65 de suavizado por defecto).

### B. Forma y geometría

| Valor | Rango | Default | Aplica a |
|---|---|---|---|
| **Cantidad de barras** | 5 – 240 | 64 | barras, espejadas |
| **Grosor de barra** | 10% – 100% del espacio | 62% | barras, espejadas |
| **Separación** | derivada del grosor | — | barras, espejadas |
| **Redondeo de puntas** | 0 – 50% del grosor | 50% | barras, espejadas |
| **Grosor de línea** | 1 – 20 px | 4 | onda |
| **Relleno bajo la línea** | sí / no | no | onda |

### C. Posición y tamaño — lo que el fundador llamó longitud y posición

| Valor | Rango | Default | Qué hace |
|---|---|---|---|
| **Ancho** | hasta el lienzo | todo el ancho | el "largo" de la banda |
| **Alto** | hasta el lienzo | 320 px | la altura máxima del dibujo |
| **Posición horizontal** | 0 – ancho del lienzo | centrado | |
| **Posición vertical** | 0 – alto del lienzo | abajo con margen | |
| **Tamaño del lienzo** | — | 1920×1080 | el del proyecto de Drift |

> Estos cuatro **también** se pueden ajustar en Drift sobre el clip ya colocado, y ahí es más cómodo porque se arrastra con el mouse. Están en la herramienta para que el archivo salga ya bien encuadrado, no para reemplazar a Drift.

### D. Color y aspecto

| Valor | Default | Qué hace |
|---|---|---|
| **Color** | cian | color principal |
| **Color final** | azul | el otro extremo del degradado |
| **Dirección del degradado** | por altura | por altura de barra, o a lo ancho del cuadro |
| **Opacidad** | 1.0 | |
| **Resplandor** | apagado | halo alrededor del dibujo; intensidad y radio ajustables |
| **Tapas de pico** | apagado | la marquita que se queda arriba y cae despacio |
| **Reflejo** | apagado | copia atenuada debajo, como sobre un piso brillante |

### E. Salida

| Valor | Opciones | Default |
|---|---|---|
| **Modo de fondo** | Trama (negro) · Chroma Key (color) · Transparente (Drift 0.7+) | Trama |
| **Cuadros por segundo** | 24 / 25 / 30 / 60 | 30 |
| **Calidad** | tres niveles con nombre, no un número crudo | media |

**Total: unos 25 valores.** Es comparable a lo que ofrecen las herramientas relevadas para estos estilos, y bastante menos abrumador que After Effects.

---

## 4. La interfaz

**Escritorio, con Python y tkinter.**

Por qué tkinter y no algo más lindo: **viene incluido con Python**, ya está en la máquina (verificado, Tk 8.6). Cero instalación, cero suscripción, arranca en un segundo. Es la respuesta directa a que After Effects te resultara pesado y caro para el uso que le dabas.

No va a ser hermoso. Va a ser un panel de valores a un lado y la vista previa al otro.

### Disposición propuesta

```
┌───────────────────────────────┬──────────────────────────┐
│                               │  Audio:  [cancion.mp3 ]  │
│      VISTA PREVIA             │  Estilo: [ Barras   ▾ ]  │
│      (cuadro real)            │                          │
│                               │  ▸ Reacción al audio     │
│                               │  ▸ Forma                 │
│                               │  ▸ Posición y tamaño     │
│                               │  ▸ Color                 │
├───────────────────────────────┤  ▸ Salida                │
│ ◀ ────────●──────────── ▶     │                          │
│      0:42 / 3:15              │  [Guardar]  [Exportar]   │
└───────────────────────────────┴──────────────────────────┘
```

### Cómo se abre: `.bat` ahora, `.exe` más adelante

**Decisión del fundador en T11.** Quedó explícita porque era un punto ciego: el MVP prometía *"sin programación para el usuario final"* pero nada decía cómo se lanza la herramienta, y abrir una terminal para arrancarla también es programación para quien no programa.

| | Qué es | Cuándo |
|---|---|---|
| **`visualizador.bat`** | Acceso directo de doble clic. Llama a `pythonw.exe`, que abre la ventana **sin consola negra detrás** | **En el MVP**, etapa 6. Minutos, sin turno extra |
| **`.exe` autónomo** | Empaquetado con PyInstaller: corre en una máquina sin Python | **Etapa más avanzada**, después del MVP. No comprometido |

Por qué el `.bat` alcanza para el MVP: Python ya está instalado en la máquina del fundador (3.14.6, con `pythonw.exe` verificado en disco). El `.exe` resuelve un problema de **distribución**, no de uso, y el único usuario del MVP es el fundador. Empaquetar antes de que la herramienta esté terminada significa rehacer el empaquetado cada vez que algo cambie.

Costos del `.exe` que hay que aceptar cuando llegue el momento, y que no son especulación: PyInstaller es una **dependencia nueva** (necesita aprobación, regla 13 de la ruta), el archivo pesa entre 80 y 150 MB porque empaqueta Python, `numpy` y `Pillow`, arranca más lento en frío, y los antivirus dan falsos positivos con cierta frecuencia.

### Distribuir a terceros no es un objetivo de este proyecto

Textual del fundador: *"El día de mañana puede que quiera distribuir esto, pero eso depende del resultado final, y no es una ruta que este proyecto actualmente este trabajando como un objetivo"*.

Consecuencia para cualquier agente: **no diseñar para distribución.** Nada de instaladores, actualizaciones automáticas, telemetría, licencias, ni abstracciones "por si algún día otro lo usa". Se construye para un usuario, que es el fundador. Si esa puerta se abre, se abre con una decisión suya y se planifica entonces.

> Nota que ahorra un susto a futuro: la herramienta **no incluye ni enlaza código de Drift**, así que no es obra derivada y la GPLv3 de Drift no le impone condiciones. Distribuirla sería una decisión libre, no un problema legal. Distinto es el empaquetado como *addon* de Drift, que sí está cerrado para un tercero por la firma Ed25519 — ver `.memory/wiki/Extensibilidad_de_Drift.md`.

### Principio de diseño: el motor no sabe que existe la interfaz

El motor de render es una biblioteca que recibe un diccionario de parámetros y devuelve cuadros. La interfaz es un cliente más, igual que la línea de comandos.

Esto tiene una consecuencia práctica que vale declarar: **si la interfaz resulta incómoda, se reemplaza sin tocar el motor.** Y mientras se construye, la línea de comandos sigue funcionando, así que hay algo usable en cada turno y no al final.

Y una que aplica al empaquetado: el `.bat` y, más adelante, el `.exe` **sólo lanzan `gui.py`**. No son una capa con lógica propia. Eso es lo que hace que empaquetar no cueste rediseñar nada.

---

## 5. Guardar y exportar

### Guardar — proyecto

Un archivo `.json` legible que contiene la ruta del audio, el estilo y todos los valores. Se reabre y se sigue trabajando.

Es JSON y no un formato binario a propósito: se puede leer, versionar, comparar y arreglar a mano si algo se rompe.

### Guardar — preset

Sólo el aspecto, sin el audio. Para reusar un estilo en otra canción. El MVP incluye **tres o cuatro presets de fábrica**, para que haya de dónde partir en vez de una pantalla en blanco.

### Exportar

El video para Drift, en el modo de fondo elegido. Con barra de progreso y posibilidad de cancelar — un render de tres minutos no puede dejar la aplicación congelada sin decir nada.

Al terminar, un recordatorio de qué hacer en Drift según el modo elegido (poner Trama, o agregar Chroma Key con el tono correcto).

---

## 6. Lo que el MVP NO hace

Declarado para que no haya sorpresas:

- ❌ **No reproduce el audio.** Es un generador, no un reproductor. Te movés por la canción con una barra y ves cuadros.
- ❌ **No previsualiza en vivo a 30 fps.** Cuadro real que se actualiza, más fragmentos cortos animados a pedido.
- ❌ **No hace capas múltiples.** Un visualizador por archivo. Si querés dos, generás dos y los apilás en Drift, que para eso es un editor.
- ❌ **No pone texto, ni título, ni carátula, ni fondo de imagen.** Eso lo hace Drift mucho mejor.
- ❌ **No estilo circular** en el MVP (ver §2).
- ❌ **No partículas, ni pulso, ni 3D.**
- ❌ **No se instala como plugin de Drift.** Es una aplicación aparte; ya está establecido.
- ❌ **No detecta el tempo ni corta a tiempo.** Drift ya tiene detección de beats.

---

## 7. Criterios de aceptación

Falsables, no opinables.

| # | Criterio | Cómo se verifica |
|---|---|---|
| MVP-1 | Carga MP3, WAV, FLAC, M4A y OGG sin error | Un archivo de cada uno, cargado |
| MVP-2 | Los **tres** estilos renderizan | Un export de cada uno, inspeccionado |
| MVP-3 | Cambiar de estilo **no** desincroniza | `verificar_sincronia.py` pasa con los tres |
| MVP-4 | Los ~25 valores tienen efecto visible y ninguno rompe el render | Barrido automático: mínimo, default y máximo de cada valor, sin excepciones y con cuadros distintos |
| MVP-5 | La vista previa coincide con el export | Cuadro *N* de la vista previa contra cuadro *N* del video: idénticos salvo compresión |
| MVP-6 | Guardar y reabrir un proyecto da el mismo resultado | Comparación de cuadros antes y después de reabrir |
| MVP-7 | El export se compone bien en Drift | **Lo verifica el fundador**, en los modos Trama y Chroma Key |
| MVP-8 | Una canción real de 3 min exporta sin agotar la memoria | Medición de tiempo y memoria máxima |
| MVP-9 | **El fundador edita un video musical de punta a punta, solo** | Lo hace sin preguntarle nada al agente |

**MVP-9 es el criterio real.** Los otros ocho son infraestructura para que ése sea posible.

**MVP-5 es el que protege contra la trampa de los dos motores.** Si falla, la vista previa está mintiendo y hay que parar.

---

## 8. Presupuesto, con el número honesto

El plan aprobado asignaba **4 turnos** al MVP, y después se habló de 6. Con el alcance definido acá, **ninguno de los dos alcanza.** El número realista es **10**, y el fundador pidió explícitamente que se lo dijera antes y no en el camino.

| Etapa | Turnos | Entrega | ¿Sirve por sí sola? |
|---|---|---|---|
| **1. Análisis de audio** | 1 | MP3 y compañía a bandas por cuadro, con suavizado y caída de picos. Reutilizable por todos los estilos | Sí — los datos se pueden inspeccionar |
| **2. Motor y estilo Barras** | 2 | Motor de dibujo, barras completas con toda la §3, export por línea de comandos | **Sí — ya reemplaza lo que hay hoy** |
| **3. Onda y Barras espejadas** | 1 | Los otros dos estilos | Sí — tres estilos usables |
| **4. Proyectos y presets** | 1 | Guardar y reabrir, presets de fábrica | Sí |
| **5. Interfaz** | 3 | Carga, lista de estilos, panel de valores, vista previa con barra de tiempo, export con progreso | **Es la etapa que cumple "sin programación"** |
| **6. Integración y documentación** | 1 | Los tres modos de fondo desde la interfaz, guía de uso reescrita | Sí |
| **7. Validación con el fundador** | 1 | MVP-7 y MVP-9 | — |
| **Total** | **10** | | |

### Lo que esto significa para el presupuesto total

| | Turnos |
|---|---|
| Consumidos hasta acá (T1–T6) | 6 |
| MVP según este plan | 10 |
| **Total Etapa 1** | **16** |
| Presupuesto aprobado en el Gate | 10–14 |

**Nos pasamos de 2 a 6 turnos**, y necesito que el fundador lo apruebe explícitamente. No es un sobrecosto por imprevistos: es que el alcance del MVP creció cuando decidimos motor propio e interfaz gráfica, y las dos decisiones fueron deliberadas.

### Dónde recortar, si prefiere

Dos cortes posibles, en orden de lo que menos duele:

1. **Sin interfaz gráfica: −3 turnos (total 13, dentro del presupuesto).** Queda la línea de comandos más proyectos en JSON y presets. **Pero no cumple "sin programación para el usuario final"**, que es lo que el fundador pidió. Mi recomendación es no recortar acá.
2. **Dos estilos en vez de tres: −1 turno.** Barras y onda, sin espejadas. Ahorra poco porque las espejadas son casi gratis.

### Punto de control intermedio

**Después de la etapa 2** (4 turnos, con las barras andando por línea de comandos) conviene un alto: el fundador va a poder ver barras de verdad sobre su video y decidir si el aspecto va por buen camino **antes** de gastar los 3 turnos de la interfaz.

Si en ese punto el aspecto no convence, se corrige ahí, que es barato.

---

## 9. Lo que necesito que decida el fundador

1. **¿Los tres estilos son los correctos?** Barras, barras espejadas, onda. Circular queda afuera del MVP y es el primer candidato a agregarse después.
2. **¿Falta o sobra algún valor** de los ~25 de la §3?
3. **¿Aprueba los 10 turnos**, llevando la Etapa 1 a 16 en total? Y si no, ¿qué corte prefiere de los dos de la §8?
4. **¿Confirma la lista de lo que el MVP no hace** (§6)? Ahí es donde suelen aparecer los malentendidos.
5. **Dato que necesito:** ¿a qué resolución y cuadros por segundo trabaja tus proyectos en Drift? Asumí 1920×1080 a 30. Si hacés vertical para Shorts o Reels, cambia el default.
