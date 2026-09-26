# Arquitectura del visualizador

**Estado: vigente desde T7 (2026-09-25).**
Este documento define **cómo se organiza el código**. `docs/MVP.md` define *qué* hace; la ruta de ejecución está en `docs/RUTA_DE_TRABAJO.md`.

**Para cualquier agente: leé esto antes de escribir código.** Existe para que dos agentes trabajando en etapas distintas produzcan piezas que encajan. Si te parece que hay que cambiar algo de acá, **cambialo explícitamente y registralo** — no lo contradigas en silencio.

---

## El principio que ordena todo

```
       ANÁLISIS                    DIBUJO                   SALIDA
   audio → números          números → píxeles         píxeles → archivo
   (una vez por audio)      (una vez por cuadro)      (una vez por export)
```

Tres etapas que no se conocen entre sí:

- **El análisis** no sabe que existen los estilos. Produce números.
- **Los estilos** no saben de archivos de audio ni de FFmpeg. Reciben números y dibujan.
- **La salida** no sabe qué se dibujó. Recibe cuadros y los codifica.

Dos consecuencias que valen la pena, y que el mercado confirma:

1. **Cambiar de estilo no puede desincronizar nada**, porque todos leen el mismo análisis.
2. **La vista previa y el export usan el mismo camino.** No hay un dibujante rápido para previsualizar y otro para exportar. Es la garantía estructural del criterio MVP-5.

---

## Estructura de archivos

```
tools/
├── generar_overlay.py          LEGADO. El generador de la PoC, basado en filtros de
│                               FFmpeg. NO se borra: sirve como modo rápido y como
│                               referencia de los tres modos de fondo, que ya funcionan.
│
└── visualizador/               EL PRODUCTO
    ├── __init__.py
    ├── analisis.py             audio → datos por cuadro
    ├── parametros.py           esquema, defaults, rangos, validación
    ├── estilos/
    │   ├── __init__.py         registro: nombre → clase
    │   ├── base.py             el contrato que todo estilo cumple
    │   ├── barras.py
    │   ├── espejadas.py
    │   └── onda.py
    ├── render.py               une análisis + estilo → cuadros RGBA
    ├── salida.py               cuadros → archivo, con los tres modos de fondo
    ├── proyecto.py             guardar/abrir proyectos y presets
    ├── cli.py                  cliente de línea de comandos
    └── gui.py                  cliente de interfaz gráfica

presets/                        presets de fábrica, en JSON
tests/
├── fixtures/                   pista_prueba.wav y su generador
├── verificar_sincronia.py      prueba de regresión que ya existe
└── ...                         las que agregue cada etapa
```

**`cli.py` y `gui.py` son dos clientes del mismo motor.** Ninguno de los dos contiene lógica de dibujo ni de análisis. Si la interfaz resulta incómoda, se reemplaza sin tocar nada más.

---

## Los contratos

### 1. Análisis — `analisis.py`

```python
def analizar(ruta_audio: Path, fps: int, params: dict) -> Analisis
```

Devuelve:

```python
@dataclass
class Analisis:
    n_cuadros: int            # EXACTAMENTE round(duracion * fps)
    fps: int
    duracion: float           # segundos, del audio
    bandas: np.ndarray        # forma (n_cuadros, n_bandas), valores 0..1
    amplitud: np.ndarray      # forma (n_cuadros,), valores 0..1 — para el estilo onda
    onda: np.ndarray          # forma (n_cuadros, n_columnas), -1..1 — forma de onda cruda
    frecuencias: np.ndarray   # forma (n_bandas + 1,), los bordes en Hz
```

**Reglas que no se negocian:**

- **`n_cuadros == round(duracion * fps)`, exacto.** Es la lección de T3: el overlay quedaba 100 ms desfasado y faltaban 3 cuadros, y la comprobación de duración lo aprobaba porque leía metadatos en vez de contar. **El cuadro `i` cubre el audio de `i/fps` a `(i+1)/fps`.** Sin corrimientos.
- **Los valores salen normalizados 0..1**, ya con el suavizado temporal y la caída de picos aplicados. El suavizado vive **acá** y no en los estilos, para que los tres se comporten igual.
- **Sin dependencia de `librosa`.** Se lee con FFmpeg a PCM crudo y se analiza con `numpy`. El fundador eligió esta ruta por liviana; agregar dependencias pesadas la contradice.

### 2. Parámetros — `parametros.py`

**Un solo diccionario plano gobierna todo.** La interfaz lo arma, la línea de comandos lo arma, el proyecto lo serializa, el motor lo consume.

```python
ESQUEMA = {
    "sensibilidad": Valor(tipo=float, min=0.5,  max=10.0, default=3.0,  grupo="audio"),
    "suavizado":    Valor(tipo=float, min=0.0,  max=1.0,  default=0.65, grupo="audio"),
    "n_barras":     Valor(tipo=int,   min=5,    max=240,  default=64,   grupo="forma",
                          estilos=["barras", "espejadas"]),
    ...
}

def defaults(estilo: str) -> dict
def validar(params: dict, estilo: str) -> dict   # completa faltantes, falla si hay inválidos
```

Por qué un esquema declarativo y no parámetros sueltos: **la interfaz se construye leyéndolo.** Agregar un valor nuevo es agregar una fila, y aparece solo en la interfaz, en la línea de comandos, en la validación y en el barrido de la prueba MVP-4. Si no, hay que tocar cinco lugares y uno se olvida.

La lista completa de valores con sus rangos está en `docs/MVP.md` §3, que es la fuente.

### 3. Estilos — `estilos/base.py`

```python
class Estilo(ABC):
    id: str                 # "barras"
    nombre: str             # "Barras"
    usa: tuple[str, ...]    # qué del análisis necesita: ("bandas",) o ("onda",)

    @abstractmethod
    def dibujar(self, lienzo: Image.Image, datos: DatosCuadro, p: dict) -> None:
        """Dibuja UN cuadro sobre `lienzo`, que es RGBA y ya tiene el tamaño final."""
```

**Reglas:**

- **El estilo dibuja y nada más.** No abre archivos, no llama a FFmpeg, no decide el fondo.
- **Dibuja con alpha**, siempre. El modo de fondo lo aplica `salida.py` después. Así un estilo sirve para los tres modos sin saberlo.
- **Sin estado entre cuadros.** Todo lo que dependa del tiempo (suavizado, caída de picos) ya viene resuelto en el análisis. Un estilo con estado interno rompe la posibilidad de renderizar un cuadro suelto, y eso es justo lo que necesita la vista previa.

Ese último punto es el que hace posible la vista previa: **cualquier cuadro se puede dibujar sin haber dibujado los anteriores.**

### 4. Render — `render.py`

```python
class Render:
    def __init__(self, analisis: Analisis, estilo: Estilo, params: dict): ...

    def cuadro(self, i: int) -> Image.Image:
        """El cuadro i como RGBA. Lo usan la vista previa Y el export."""

    def cuadros(self) -> Iterator[Image.Image]:
        """Todos, en orden, para el export."""
```

**`cuadro(i)` es el corazón del criterio MVP-5.** La vista previa llama a `cuadro(i)` y el export llama a `cuadros()`, que internamente es el mismo `cuadro(i)`. No hay forma de que divergan sin que alguien rompa esto a propósito.

### 5. Salida — `salida.py`

```python
def exportar(render: Render, destino: Path, modo_fondo: str,
             progreso: Callable[[int, int], bool] | None = None) -> None
```

- Aplica el modo de fondo: `transparente`, `negro` (para Trama) o `color` (para Chroma Key).
- Canaliza los cuadros crudos a FFmpeg por entrada estándar. **No escribe PNGs intermedios en disco.**
- `progreso` devuelve `False` para cancelar. Un render de tres minutos no puede dejar la interfaz congelada sin decir nada.

Los parámetros de codificación de los tres modos **ya están resueltos y verificados** en `tools/generar_overlay.py`. Reusar esos valores, no reinventarlos: incluyen el `-auto-alt-ref 0` que Drift documenta como obligatorio para VP9 con alpha.

### 6. Proyectos — `proyecto.py`

```python
def guardar(ruta: Path, audio: Path, estilo: str, params: dict) -> None
def abrir(ruta: Path) -> tuple[Path, str, dict]
def guardar_preset(ruta: Path, estilo: str, params: dict) -> None   # sin el audio
```

JSON legible, con un campo `version` desde el primer día. Los presets llevan el aspecto sin el audio, para reusarlos en otra canción.

---

## Decisiones tomadas, con su motivo

| Decisión | Por qué |
|---|---|
| `numpy` + `Pillow` + `tkinter`, nada más | Ya están en la máquina. El fundador eligió esta ruta porque After Effects le resultaba pesado y caro; sumar dependencias la contradice |
| Leer el audio con FFmpeg a PCM crudo | FFmpeg ya es una dependencia y ya está. Evita `librosa`, que arrastra media ciencia de datos |
| El suavizado vive en el análisis | Para que los tres estilos se comporten igual, y para que un estilo pueda dibujar un cuadro suelto |
| Los estilos dibujan con alpha siempre | Un estilo sirve para los tres modos de fondo sin saber que existen |
| Esquema de parámetros declarativo | La interfaz se construye leyéndolo. Agregar un valor es una fila, no cinco archivos |
| `generar_overlay.py` no se borra | Funciona, está verificado, y sus parámetros de codificación son la referencia de los tres modos de fondo |
| Cuadros por entrada estándar a FFmpeg | Sin archivos intermedios: más rápido y no llena el disco |

---

## Rendimiento: el presupuesto de tiempo

Una canción de 3 minutos a 1920×1080 y 30 fps son **5400 cuadros**.

| Etapa | Objetivo |
|---|---|
| Análisis | una sola vez, unos pocos segundos |
| Dibujo por cuadro | del orden de 10 ms → **menos de un minuto** en total |
| Codificación | en paralelo, canalizada |

**Si el dibujo se va por encima de ~30 ms por cuadro, hay que medir antes de optimizar.** El resplandor por desenfoque gaussiano es el sospechoso más probable: en el prototipo de T5 era lo más caro. Se puede desenfocar a media resolución y escalar, que es lo que hace `audiospectr` con su `glow_scale`.

**No optimizar antes de medir.** Una canción de prueba y un cronómetro.

---

## Lo que este diseño hace fácil, y lo que hace difícil

**Fácil:**
- Agregar un estilo: una clase nueva y una fila en el registro.
- Agregar un valor: una fila en el esquema.
- Reemplazar la interfaz: no toca el motor.
- Probar sin interfaz: la línea de comandos usa el mismo motor.

**Difícil, a propósito:**
- Un estilo que dependa del cuadro anterior. Está prohibido por el contrato, y la vista previa es la razón.
- Una vista previa que dibuje distinto al export. No hay camino para hacerlo sin romper `render.cuadro`.

**Difícil, y es una limitación real:**
- Capas múltiples en un solo archivo. El diseño es de un visualizador por render. Para dos, se generan dos y se apilan en Drift. Está declarado en `MVP.md` §6 como fuera de alcance, pero si algún día entra, **es acá donde habría que cambiar el diseño**: `render.py` pasaría a componer una lista de capas.
