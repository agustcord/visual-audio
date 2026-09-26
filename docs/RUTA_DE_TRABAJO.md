# Ruta de trabajo

**Vigente desde T7 (2026-09-25). Aprobada por el fundador.**

Este documento existe por pedido explícito del fundador: *"debe haber un mapa/ruta de trabajo para que cualquier agente pueda retomar además de vos"*.

Es la **ruta ejecutable** del MVP. Cada etapa dice qué necesita para empezar, qué hace, y cómo se sabe que terminó. Un agente que nunca vio este proyecto debería poder ubicarse acá y empezar a trabajar.

---

## Cómo usar este documento

```
1. Leé la tabla de estado (§1) y encontrá la primera etapa sin cerrar.
2. Verificá sus PRECONDICIONES. Si alguna falla, esa es tu tarea, no la etapa.
3. Hacé las tareas de la etapa.
4. Verificá los CRITERIOS DE SALIDA. Son comandos, no opiniones.
5. Registrá: handoff + bitácora + actualizar la tabla de estado + commit.
```

**No saltees etapas.** Cada una asume que la anterior está cerrada y verificada.

**Si una etapa no cierra**, dejá el handoff diciendo exactamente en qué criterio quedó y por qué. Es más útil que un avance a medias sin explicar.

---

## 1. Tabla de estado

**El agente que cierra una etapa actualiza esta tabla.** Es el punto de sincronización del proyecto.

| # | Etapa | Turnos | Estado | Cerrada en |
|---|---|---|---|---|
| — | Registro, viabilidad, git | 1 | ✅ cerrada | T1 |
| — | Gate 1, audio de prueba, PoC | 1 | ✅ cerrada | T2 |
| — | Diagnóstico de composición en Drift | 2 | ✅ cerrada | T3, T4 |
| — | Decisión del motor de dibujo | 1 | ✅ cerrada | T5 |
| — | Investigación y definición del MVP | 1 | ✅ cerrada | T6 |
| — | Gate 2 y ruta de trabajo | 1 | ✅ cerrada | T7 |
| **1** | **Análisis de audio** | 1 | ⬜ **SIGUIENTE** | — |
| **2** | **Motor de dibujo y estilo Barras** | 2 | ⬜ | — |
| **G** | **🚦 Punto de control del fundador** | — | ⬜ | — |
| **3** | **Estilos Onda y Barras espejadas** | 1 | ⬜ | — |
| **4** | **Proyectos y presets** | 1 | ⬜ | — |
| **5** | **Interfaz gráfica** | 3 | ⬜ | — |
| **6** | **Integración y documentación** | 1 | ⬜ | — |
| **7** | **Validación con el fundador** | 1 | ⬜ | — |

**Consumido: 7 turnos. Restante del MVP: 10. Total Etapa 1: 17.**

> Nota sobre el número: el Gate 2 aprobó "10 turnos de MVP, Etapa 1 a 16" contando 6 turnos consumidos. Este turno (T7) es el séptimo, así que el total honesto es **17**. La diferencia es un turno de documentación que el fundador pidió expresamente; se registra en vez de disimularse.

---

## 2. Documentos que gobiernan

Leelos en este orden si estás llegando ahora:

| Documento | Qué dice | Cuándo leerlo |
|---|---|---|
| [`sobre_este_plugins.txt`](../sobre_este_plugins.txt) | El propósito, firmado por el fundador | Siempre, primero |
| [`RETOMAR.md`](../RETOMAR.md) | Estado vivo y trampas acumuladas | Siempre |
| **Este documento** | La ruta y los criterios | Siempre |
| [`MVP.md`](MVP.md) | **Qué** hace el MVP: estilos, los ~25 valores, criterios | Antes de cualquier etapa |
| [`ARQUITECTURA.md`](ARQUITECTURA.md) | **Cómo** se organiza el código, los contratos | **Antes de escribir código** |
| [`PLAN_ETAPA1.md`](PLAN_ETAPA1.md) §7 y §10 | Los dos Gates, verbatim: qué autorizó el fundador | Ante cualquier duda de alcance |
| [`VIABILIDAD.md`](VIABILIDAD.md) | Por qué el visualizador no puede ser un efecto de Drift | Si vas a proponer arquitectura |
| [`POC_RESULTADOS.md`](POC_RESULTADOS.md) | Mediciones y los errores ya cometidos | Antes de medir algo |
| [`COMO_USAR.md`](COMO_USAR.md) | Guía del fundador. **Hay que mantenerla al día** | Al cambiar algo que se use |
| [`.memory/wiki/`](../.memory/wiki/) | Notas de dominio con evidencia citada | Según el tema |

---

## 3. Reglas de trabajo

No negociables. Están acá porque cada una se pagó con un error real.

### Registro

1. **Un handoff por turno** en `.memory/handoffs/`, con el formato `T<N>_<tema>_<YYYYMMDD>.md`. El molde está en `.memory/wiki/MOC_Handoffs.md`.
2. **Una entrada en `.memory/log.md`** que cite el handoff. **Append-only**: las entradas fechadas no se editan ni se reordenan.
3. **Declarar la frontera**: qué tocaste y, explícitamente, **qué no**. Es lo que le permite al siguiente confiar en el terreno.
4. **Actualizar la tabla de estado** de §1 y el estado de `RETOMAR.md`.
5. **Commit al cerrar**, con el mensaje explicando el *por qué* y no sólo el *qué*.

### Verificación

6. **Ningún criterio se declara cumplido sin el comando que lo prueba.** Si no lo podés medir, decí que no lo pudiste medir.
7. **Medir sobre todo el material, no sobre muestras.** La verificación de T2 aprobaba en verde un archivo 100 ms desfasado al que le faltaban tres cuadros, porque miraba dos cuadros sueltos y metadatos declarados.
8. **Medir contra algo conocido del audio**, no contra lo que el archivo dice de sí mismo. La duración que declara un contenedor miente; contá cuadros.
9. **Si un resultado no tiene sentido físico, sospechá del instrumento antes que de lo medido.** Pasó dos veces (el `-ss` de T3, el `blend` de T4) y las dos veces el instrumento era el roto.

### Límites

10. **`C:\Program Files\Drift\` es de sólo lectura.** Nunca escribir ahí.
11. **No activar el servidor MCP de Drift** sin pedírselo al fundador.
12. **No forkear ni compilar Drift, ni contactar a CutWire Studios.** Compromiso nulo con terceros, decisión del Gate 1.
13. **No agregar dependencias de Python** más allá de `numpy`, `Pillow` y `tkinter` sin consultarlo. El fundador eligió esta ruta por liviana.
14. **`_reference/drift-src/` es de sólo lectura y no se versiona.** Y es la rama `main` (0.7.0 en desarrollo), **que no coincide con la versión instalada del fundador (0.6.0)**. Antes de razonar sobre código de Drift, verificá que esa parte exista en su binario.
15. **No revivas una decisión cerrada sin declararlo.** Si la revertís, la nota vieja se marca `superseded` con el motivo; no se borra.

---

## 4. Las etapas

### Etapa 1 — Análisis de audio

**1 turno.** Convierte audio en números por cuadro. Es el cimiento de los tres estilos.

**Precondiciones:** FFmpeg en el PATH; `numpy` disponible; `tests/fixtures/pista_prueba.wav` existe.

**Tareas**
- Crear el paquete `tools/visualizador/` con `analisis.py` y `parametros.py`.
- Leer el audio con FFmpeg a PCM crudo mono (sin `librosa`).
- FFT por cuadro → bandas logarítmicas entre `frec_min` y `frec_max`.
- Suavizado temporal y caída de picos, ambos configurables.
- Normalizar 0..1. Producir también `amplitud` y `onda` para el estilo Onda.
- `parametros.py` con el esquema declarativo de los valores del grupo *audio* de `MVP.md` §3.

**Criterios de salida**

| # | Criterio | Cómo |
|---|---|---|
| 1.1 | `n_cuadros == round(duracion * fps)` exacto, en 24, 25, 30 y 60 fps | prueba automática |
| 1.2 | Los valores caen en 0..1, sin `NaN` ni infinitos | prueba automática |
| 1.3 | **El análisis está alineado con el audio**: los ataques conocidos de la pista de prueba (0.0 s, 1.0 s, 10.0 s) caen dentro de un cuadro | prueba automática, al estilo de `tests/verificar_sincronia.py` |
| 1.4 | Las bandas **separan** el espectro: el compás 4 de la pista (casi silencio) da energía baja en todas, y el tramo intenso la reparte entre graves y agudos | medición documentada |
| 1.5 | Un audio de 3 minutos se analiza en menos de 15 s y sin pasar de 1 GB | medición |

> 1.3 y 1.4 son los que importan. 1.3 porque el desfase de 100 ms de T3 nació de no verificar alineación. 1.4 porque un análisis que no separa bandas produce barras que suben y bajan todas juntas, y eso se ve como un error de diseño aunque el código esté bien.

---

### Etapa 2 — Motor de dibujo y estilo Barras

**2 turnos.** La etapa más grande. Al cerrar, el fundador puede ver barras reales sobre su video.

**Precondiciones:** etapa 1 cerrada.

**Tareas**
- `estilos/base.py` con el contrato de `ARQUITECTURA.md` §3.
- `estilos/barras.py`: cantidad, grosor, separación, redondeo, degradado de dos colores, opacidad, resplandor, tapas de pico, reflejo, alineación abajo o centrada.
- `render.py` con `cuadro(i)` y `cuadros()`.
- `salida.py` con los tres modos de fondo, **reusando los parámetros de codificación ya verificados** de `tools/generar_overlay.py`.
- `cli.py` para manejar todo desde la línea de comandos.
- Completar `parametros.py` con los grupos *forma*, *posición*, *color* y *salida*.

**Criterios de salida**

| # | Criterio | Cómo |
|---|---|---|
| 2.1 | Exporta un WebM en los tres modos de fondo, con el conteo de cuadros exacto | comando |
| 2.2 | `tests/verificar_sincronia.py` pasa sobre la salida del motor nuevo | comando |
| 2.3 | **Barrido de parámetros**: mínimo, default y máximo de cada valor no rompen el render y producen cuadros distintos | prueba automática (es el MVP-4) |
| 2.4 | **`cuadro(i)` es idéntico llamado suelto o en secuencia** | prueba automática — protege el contrato "sin estado entre cuadros" |
| 2.5 | Canción de 3 min a 1080p30: menos de 5 min y sin pasar de 2 GB | medición |
| 2.6 | Evidencia visual guardada en `docs/evidencia/` | inspección |

> 2.4 es el que garantiza que la vista previa sea posible. Si falla, algún estilo guardó estado y hay que arreglarlo antes de seguir.

---

### 🚦 Punto de control del fundador

**Después de la etapa 2. No es un turno de trabajo, es una decisión.**

El agente le presenta al fundador:
- Un export de barras con los valores por defecto, para poner en su timeline.
- Dos o tres variantes de aspecto.
- El tiempo de render medido.

**Lo que el fundador decide:** si el aspecto va por buen camino, y qué ajustar.

**Por qué acá:** corregir el aspecto ahora es barato. Después de invertir tres turnos en la interfaz, cambiar el aspecto significa además rehacer controles.

**Si el aspecto no convence, no se avanza a la etapa 3.** Se corrige en la 2.

---

### Etapa 3 — Estilos Onda y Barras espejadas

**1 turno.** Dos estilos que son funciones de dibujo, no arquitectura nueva.

**Precondiciones:** etapa 2 cerrada y **punto de control aprobado**.

**Tareas**
- `estilos/espejadas.py`: barras simétricas desde el centro.
- `estilos/onda.py`: línea de amplitud con grosor y relleno opcional.
- Registrar los dos en `estilos/__init__.py`.
- Declarar en el esquema qué valor aplica a qué estilo.

**Criterios de salida**

| # | Criterio | Cómo |
|---|---|---|
| 3.1 | Los tres estilos exportan sin error | comando |
| 3.2 | **Cambiar de estilo con los mismos valores no desincroniza** | `verificar_sincronia.py` con los tres (es el MVP-3) |
| 3.3 | El barrido de parámetros pasa en los tres | prueba automática |
| 3.4 | Un valor que no aplica a un estilo se ignora o falla claro, nunca a medias | prueba automática |

---

### Etapa 4 — Proyectos y presets

**1 turno.** Guardar y reabrir, más presets de fábrica.

**Precondiciones:** etapa 3 cerrada.

**Tareas**
- `proyecto.py`: guardar y abrir, con campo `version`.
- Guardar preset (aspecto sin audio) y aplicarlo.
- Tres o cuatro presets de fábrica en `presets/`, uno por estilo como mínimo.
- Comandos de la línea de comandos para todo eso.

**Criterios de salida**

| # | Criterio | Cómo |
|---|---|---|
| 4.1 | **Guardar → reabrir → exportar da cuadros idénticos** | comparación automática (es el MVP-6) |
| 4.2 | Un proyecto con un valor inválido o de versión desconocida **falla con un mensaje claro**, no a medias | prueba automática |
| 4.3 | Los presets de fábrica cargan y exportan | comando |
| 4.4 | Un proyecto cuyo audio se movió de lugar avisa qué falta | prueba automática |

---

### Etapa 5 — Interfaz gráfica

**3 turnos.** La etapa que cumple *"sin programación para el usuario final"*.

**Precondiciones:** etapa 4 cerrada. `tkinter` disponible (verificado: Tk 8.6).

**Tareas**
- `gui.py`: ventana con vista previa y panel de valores.
- Cargar audio con el diálogo del sistema; **mostrar vista previa con los valores por defecto de inmediato** (lo pidió así el fundador: *"ver una onda predeterminada"*).
- Selector de estilo.
- **Panel construido leyendo el esquema de `parametros.py`**, agrupado como en `MVP.md` §3. No cablear controles a mano: si se agrega un valor al esquema, tiene que aparecer solo.
- Barra de tiempo para moverse por la canción.
- Vista previa que se actualiza al cambiar un valor, **usando `render.cuadro(i)`** y nada más.
- Botón de fragmento animado corto.
- Guardar y abrir proyecto, aplicar preset.
- Exportar con barra de progreso y cancelación.

**Criterios de salida**

| # | Criterio | Cómo |
|---|---|---|
| 5.1 | Recorrido completo sin tocar la línea de comandos: cargar, elegir, ajustar, guardar, exportar | el fundador lo hace |
| 5.2 | **El cuadro de la vista previa es idéntico al del export** salvo compresión | comparación automática (es el MVP-5) |
| 5.3 | La vista previa se actualiza en menos de 500 ms a media resolución | medición |
| 5.4 | La interfaz **no se congela** durante el export, y cancelar funciona | prueba manual documentada |
| 5.5 | Todos los valores del esquema aparecen en la interfaz | prueba automática que compara esquema contra controles |
| 5.6 | Un audio corrupto o inexistente da un mensaje claro, sin traceback | prueba manual documentada |

> 5.2 es el criterio que protege contra la trampa de los dos motores. Si falla, la vista previa miente: **parar y arreglar**, no seguir.
> 5.5 existe para que el esquema no se desincronice de la interfaz con el tiempo.

---

### Etapa 6 — Integración y documentación

**1 turno.**

**Precondiciones:** etapa 5 cerrada.

**Tareas**
- Los tres modos de fondo elegibles desde la interfaz, con el recordatorio de qué hacer en Drift al terminar.
- **Reescribir `COMO_USAR.md`** para la aplicación nueva, dejando lo de la línea de comandos como apéndice.
- Actualizar `README.md` y `RETOMAR.md`.
- Revisar que nada de la documentación contradiga a la herramienta.

**Criterios de salida**

| # | Criterio | Cómo |
|---|---|---|
| 6.1 | `COMO_USAR.md` describe la aplicación real, sin pasos obsoletos | lectura contra la herramienta |
| 6.2 | Todo comando que aparezca en la documentación corre tal cual está escrito | ejecutar cada uno |
| 6.3 | La tabla de estado de §1 y `RETOMAR.md` están al día | inspección |

---

### Etapa 7 — Validación con el fundador

**1 turno.** Requiere al fundador con Drift abierto.

**Precondiciones:** etapa 6 cerrada. **Avisarle al empezar**, como pidió.

**Tareas**
- Acompañarlo en un video musical completo.
- Anotar cada fricción, aunque sea chica.

**Criterios de salida**

| # | Criterio |
|---|---|
| 7.1 | El export se compone bien en Drift en modo Trama y con Chroma Key (MVP-7) |
| 7.2 | Un video musical editado de punta a punta y exportado |
| 7.3 | **El fundador lo usa solo, sin preguntarle nada al agente** (MVP-9) |

> **7.3 es el criterio real del MVP.** Todo lo demás es infraestructura para que sea posible.

---

## 5. Después del MVP

No comprometido. En orden de valor esperado:

1. **Estilo circular / radial.** El más pedido de los que quedaron afuera. Requiere el segundo modelo de disposición (polar).
2. **`--fondo transparente` como default**, cuando salga Drift 0.7.0. Ya está implementado; es cambiar un default y actualizar la documentación.
3. **Más presets.**
4. **Camino B**: keyframes calculados vía MCP para que el video pulse con la música. Barato, y quedó fuera del MVP por alcance, no por costo.
5. **Capas múltiples.** Requiere cambiar `render.py` (ver `ARQUITECTURA.md`, última sección).
6. **Camino C**: uniforms de audio en un fork de Drift. **Bloqueado por decisión del fundador** (compromiso nulo con terceros).
