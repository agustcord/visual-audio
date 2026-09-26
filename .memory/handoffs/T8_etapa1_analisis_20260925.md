---
tipo: "handoff"
turno: 8
agente: "Kiro"
fecha: 2026-09-25
estado: "cerrado — etapa 1 de la ruta completa, los 5 criterios verificados"
---

# T8 — Etapa 1: análisis de audio

Primera etapa de construcción. Convierte audio en números por cuadro: bandas
logarítmicas, amplitud y forma de onda. Es el cimiento de los tres estilos.

**Los cinco criterios de salida pasan.** 36 comprobaciones automáticas, 0 fallas.

## Frontera declarada

**Creado:**
- `tools/visualizador/__init__.py`, `analisis.py`, `parametros.py`, `consola.py`
- `tests/test_analisis.py` — 36 comprobaciones de los criterios 1.1 a 1.4

**Modificado:**
- `docs/ARQUITECTURA.md` — dos correcciones del contrato de `Analisis`, declaradas
- `docs/RUTA_DE_TRABAJO.md` — tabla de estado, y un aviso nuevo en la etapa 2
- `tools/generar_overlay.py` y `tests/verificar_sincronia.py` — salida UTF-8
- `.memory/log.md`, `.memory/wiki/MOC_Handoffs.md`, `RETOMAR.md`

**NO se tocó:** `tests/fixtures/pista_prueba.wav` ni su generador — su hash está
documentado y `verificar_sincronia.py` depende de su estructura. `docs/MVP.md` sin
cambios. `C:\Program Files\Drift\`, la carpeta de datos de Drift y `_reference/`
sin tocar. No se abrió Drift ni se activó su MCP. Sin dependencias nuevas: sólo
`numpy`, que ya estaba.

## Resultados de los criterios

| # | Criterio | Resultado |
|---|---|---|
| 1.1 | `n_cuadros == round(duracion * fps)` en 24/25/30/60 fps | ✅ exacto en los cuatro |
| 1.2 | Valores en 0..1, sin `NaN` ni infinitos | ✅ en 9 combinaciones extremas de parámetros |
| 1.3 | Alineación con el audio, sin pre-eco | ✅ **desvío 0 cuadros**; los 4 cuadros previos a un golpe quedan en 0.0000 exacto |
| 1.4 | Las bandas reparten el espectro | ✅ ruido rosa **plano, 1.03x**; ruido blanco subiendo 35x como control |
| 1.5 | 3 min en <15 s y <1 GB | ✅ peor caso **1.34 s y 365 MB** |

Reproducir: `python tests\test_analisis.py`

## Las dos decisiones de diseño que definen el módulo

### La ventana de la FFT es causal

Para el cuadro `i` se analizan las muestras que **terminan** en `(i+1)/fps`. Una
ventana centrada produce pre-eco: el dibujo empieza a subir *antes* del golpe,
porque la ventana ve audio de los dos lados.

Verificado con el borde más nítido de la pista (el golpe de 10.0 s después de casi
dos segundos de silencio): **los cuatro cuadros anteriores dan 0.0000 exacto** y el
cuadro 300 —el que contiene los 10.0 s— es el primero con energía. El salto más
grande de toda la pista cae en el cuadro 300, con desvío 0.

Esto es la lección de T3 resuelta en el diseño en vez de parcheada después.

### El suavizado vive en el análisis, no en los estilos

Todo lo temporal se resuelve acá. Es lo que permite que un estilo dibuje el cuadro
300 sin haber dibujado los 299 anteriores, y de eso depende que la vista previa de
la interfaz sea posible.

Con una salvedad que quedó documentada en el código: para la **forma de onda**,
`suavizado` es suavizado *espacial* (lo liso de la línea) y no inercia temporal.
No hay otra opción sensata — cada cuadro de la onda muestra un tramo de audio
distinto, así que promediar la columna 500 de un cuadro con la del anterior no
significa nada.

## El error que encontró la medición del criterio 1.4

**Vale la pena por sí solo.** La primera versión calculaba cada banda como el
**promedio** de potencia de sus bins. Suena razonable y está mal para este uso.

La música reparte su energía aproximadamente por octava, no por hercio. Con bandas
logarítmicas, el promedio mide *densidad* espectral, que cae como 1/f incluso
cuando la energía por banda es constante.

**Medido:** los graves daban entre **117 y 1182 veces** más que los agudos, y el
perfil del espectro quedaba **literalmente vacío arriba de 519 Hz**. Unas barras
así habrían salido con la mitad derecha plana.

La corrección es usar **energía** (no normalizar los pesos por banda), con lo que
una banda ancha de agudos suma muchos bins y una angosta de graves suma pocos, y
eso compensa la caída. Después: graves/agudos bajó a **11–22x** en la pista, y el
ruido rosa sale **plano, 1.03x**.

### Y cómo se verificó bien

Con música **no se puede** verificar: si el perfil sale desparejo, no hay forma de
saber si el análisis está mal o si la canción no tiene nada ahí. Así que la prueba
usa **ruido rosa generado en el momento**, que tiene respuesta conocida: su energía
por octava es constante, así que con bandas logarítmicas tiene que salir plano. Y
**ruido blanco como control opuesto**, que tiene que salir subiendo — si el rosa
saliera plano por casualidad, el blanco no subiría 35x.

## Otros dos arreglos

**Rendimiento: de 14,4 s a 1,3 s.** La primera versión recorría cuadros y columnas
en bucles de Python — 11,8 millones de iteraciones a 60 fps. Vectorizado con un
solo `maximum.reduceat` para la onda y sumas acumuladas para el suavizado
espacial. El peor caso (3 min, 60 fps, 240 barras) pasó de 14,39 s a **1,34 s**.

**La medición de memoria devolvía 0 MB, y lo reportaba como "OK".** Un falso
aprobado propio, del mismo tipo que los de T2: faltaba declarar `argtypes` y
`restype` en la llamada a `GetProcessMemoryInfo`, y la llamada fallaba en silencio.
Corregido: ahora mide 30 MB de base y 222–365 MB de pico.

**La consola de Windows mataba un programa que funcionaba.** `cp1252` no tiene el
símbolo `≈`, y el `print` del resultado lanzaba `UnicodeEncodeError` **después** de
que las 32 comprobaciones habían pasado. Un programa que funciona pero se muere al
contarlo parece uno que falló. Se agregó `visualizador/consola.py`, que pasa la
salida a UTF-8, y de paso se arreglaron los acentos ilegibles de todas las salidas
del proyecto.

## Correcciones al contrato de `ARQUITECTURA.md`, declaradas

Dos cambios sobre lo que yo mismo había escrito en T7, hechos explícitos en el
documento en vez de dejarlos divergir:

1. **`onda` va de 0 a 1, no de −1 a 1.** Guardar la onda con signo la aplasta: hay
   que reducir cientos de muestras a cada columna, y reducir una señal que oscila
   alrededor de cero con su signo intacto da una línea recta. Se guarda el pico de
   magnitud, que es lo que los tres estilos previstos necesitan.
2. **`n_columnas` se acota a `min(1024, TASA/fps)`.** A 60 fps un cuadro son 800
   muestras; pedir 1024 columnas sería inventar resolución.

## Hallazgo para la etapa 2, ya anotado en la ruta

**La pista de prueba es pobre de espectro:** no tiene ningún instrumento entre
500 Hz y 2 kHz. Para el análisis no importó, porque se verifica con ruido rosa.
**Para juzgar barras visualmente sí importa:** con este material las del medio van
a estar planas, y eso se va a leer como un defecto del dibujo cuando es del audio.

Quedó como **primera tarea de la etapa 2**: agregar `pista_espectro.wav` con
melodía en 700–2500 Hz y un redoblante de banda ancha. **Agregar, no modificar** —
`pista_prueba.wav` tiene su hash documentado y la prueba de sincronía depende de su
estructura rítmica.

## Limitación conocida, medida y documentada

Con 64 bandas logarítmicas desde 40 Hz, **las 13 bandas más graves son más angostas
que un bin de la FFT** (3.8 Hz contra 11.7 Hz) y no se resuelven de forma
independiente: se interpolan. Se ve como que los primeros graves se mueven juntos.

Es normal —un analizador de espectro real hace lo mismo— y resolverlo de verdad
pide transformada de Q constante o análisis multirresolución. Está medido en la
prueba (0 pares idénticos entre las 8 primeras bandas, o sea que interpola y no
repite) y queda afuera del MVP.

## Dónde retomar

**Etapa 2 de `docs/RUTA_DE_TRABAJO.md`: motor de dibujo y estilo Barras.** Dos
turnos. Es la etapa más grande, y al cerrarla el fundador puede ver barras reales
sobre su video — hay un punto de control suyo justo después.

Leer antes: el aviso de la pista de prueba en la etapa 2, y `docs/ARQUITECTURA.md`
§3 para el contrato de los estilos.
