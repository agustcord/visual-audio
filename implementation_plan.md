# Plan de Implementación y Triage Factual (T16) — Etapa 5: Interfaz Gráfica Tkinter

## 📌 Pedido Original del Capitán (textual)
> "avanza"

---

## 🧭 PASO 0: Bóveda Resuelta ($VAULT)
- **VAULT Local Resuelto:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\`
- **Estructura base verificada:** `index.md` (presente), `log.md` (presente, 160 líneas, última entrada T15).
- **Entregable durable:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\handoffs\plan_etapa5_interfaz_grafica_tkinter_20260926.md`

---

## 🔍 Declaración Factual del Punto de Partida

### 1. Estado del Repositorio y Entorno en Disco
- **Rama activa:** `master`.
- **Árbol de trabajo:** Cambios de la Etapa 4 completados y verificados en disco.
- **Entorno de ejecución:** Python 3.14.6 (`pythonw.exe` disponible para ejecución directa sin consola negra), FFmpeg 8.0.1, Pillow 11.1.0, NumPy 2.2.3 sobre Windows.
- **Soporte GUI:** Tkinter con versión Tk 8.6 verificada en runtime; soporte de `ImageTk` en Pillow confirmado.
- **Directorio de trabajo:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins`.

### 2. Estado de la Suite de Pruebas (127/127 comprobaciones en verde, 0 fallas)
- `python tests/test_analisis.py`: **36 comprobaciones pasadas, 0 fallas** (análisis espectral y temporal exacto, ventana causal sin pre-eco, energía de bandas logarítmicas).
- `python tests/test_render.py --export`: **36 comprobaciones pasadas, 0 fallas** (renderizado determinista e idempotente, barrido exhaustivo de parámetros, exportación WebM en negro, color y transparente con `alpha_mode='1'`).
- `python tests/verificar_sincronia.py`: **9 comprobaciones pasadas, 0 fallas (+0 cuadros de desvío)** en los 8 ataques rítmicos independientes sobre `pista_prueba.wav`.
- `python tests/test_proyecto.py`: **46 comprobaciones pasadas, 0 fallas** (guardado y apertura de proyectos y presets, validación estricta de versión, advertencia ante audio ausente, inocuidad de `#000000`, fidelidad ΔE < 1.0 sobre fondo oscuro, detección y advertencia de colores inalcanzables, integración CLI).

### 3. Precondiciones de la Etapa 5
- **Etapa 4:** Cerrada en T15 con criterios 4.1 a 4.7 cumplidos. Precondiciones de Etapa 5 formalmente satisfechas según `docs/RUTA_DE_TRABAJO.md`.

---

## 🗺️ Especificación de Tareas para la Etapa 5

### Justificación de Consulta Previa (Regla 28 de SKILL.md)
No se convoca a `ani-pensadora` ni a `ani-investigadora` debido a que las especificaciones de interfaz, contratos de renderizado y esquemas de parámetros están exhaustivamente determinados y verificados en disco en `docs/ARQUITECTURA.md`, `docs/MVP.md` y `tools/visualizador/parametros.py`. Los tradeoffs técnicos de concurrencia y diseño de UI se resuelven de forma directa y autónoma en este plan.

---

### Desglose Detallado de Tareas (Bite-Sized Tasks)

#### Tarea 5.1 — Ventana Principal y Layout Desacoplado (`tools/visualizador/gui.py`)
- **Rol Asignado:** Ani Programadora (Fase 2 - Ejecución).
- **Archivo a generar:** `tools/visualizador/gui.py`.
- **Especificación técnica:**
  * Define la clase principal `VentanaVisualizador` basada en `tkinter.Tk` (o `ttk.Frame` dentro de una ventana raíz).
  * Dimensiones iniciales ergonómicas: 1200×750 píxeles, con soporte completo de redimensionamiento responsivo.
  * Arquitectura desacoplada en dos paneles (`ttk.PanedWindow` horizontal o disposición `grid` fija):
    - **Panel izquierdo (Visualización y Transporte):**
      - Contenedor para el lienzo de vista previa (`tk.Canvas` o `ttk.Label`), manteniendo relación de aspecto del proyecto (ej. 16:9).
      - Barra de transporte inferior: deslizador de tiempo (`ttk.Scale`), indicador de tiempo (`MM:SS.mmm / MM:SS.mmm` y número de cuadro), controles de avance/retroceso y botón de previsualización animada corta.
    - **Panel derecho (Control y Configuración):**
      - Barra superior de acción: botones "Cargar Audio", "Abrir Proyecto", "Guardar Proyecto", selector de "Preset", botón "Aplicar Preset", botón "Guardar Preset".
      - Selector principal de estilo (`ttk.Combobox`) con las opciones registradas en `estilos.disponibles()`.
      - Contenedor scrollable vertical (`tk.Canvas` con `ttk.Scrollbar`) para alojar las secciones de parámetros dinámicos.
      - Botón principal inferior destacado: "Exportar Video".

#### Tarea 5.2 — Formulario de Parámetros Generado Dinámicamente desde `parametros.ESQUEMA`
- **Rol Asignado:** Ani Programadora (Fase 2 - Ejecución).
- **Especificación técnica:**
  * Recorre el esquema agrupado mediante `parametros.por_grupo(estilo)` asegurando que ningún control se encuentre cableado manualmente:
    - Agrupación visual por secciones (`ttk.LabelFrame`):
      1. *Reacción al audio* (`sensibilidad`, `suavizado`, `caida_picos`, `curva_respuesta`, `frec_min`, `frec_max`).
      2. *Forma* (`n_barras`, `grosor_barra`, `redondeo`, `grosor_linea`, `relleno`).
      3. *Posición y tamaño* (`lienzo_ancho`, `lienzo_alto`, `ancho`, `alto`, `x`, `y`).
      4. *Color* (`color`, `color_final`, `degradado`, `opacidad`, `resplandor`, `resplandor_radio`, `tapas_pico`, `reflejo`, `compensar_fondo`, `color_fondo`).
      5. *Salida* (`fps`, `fondo`, `calidad`).
  * Generación polimórfica de widgets según el tipo y metadatos de `Valor`:
    - Numérico continuo/entero (`tipo in (float, int)` con `minimo` y `maximo`): `ttk.Scale` acoplado con `tk.DoubleVar` o `tk.IntVar`, acompañado de un display numérico que muestra el valor actual y su `unidad`.
    - Booleano (`tipo is bool`): `ttk.Checkbutton` acoplado a `tk.BooleanVar`.
    - Enumeración (`opciones`): `ttk.Combobox` en modo solo lectura (`state="readonly"`).
    - Color (`formato == "color"`): Muestra gráfica del color activo (pequeño recuadro coloreado), botón con código hexadecimal y disparador de `tkinter.colorchooser.askcolor()`.
  * Reactividad y Debouncing:
    - Cada modificación de un control notifica al despachador reactivo.
    - Se aplica un temporizador debounce de 50 ms (`root.after(50, ...)`) para prevenir llamadas redundantes al motor durante el arrastre rápido de deslizadores.
  * Habilitación dinámica por dependencias:
    - Evalúa en cada actualización `parametros.tiene_efecto(params, nombre)`. Si un parámetro depende de otro inactivo (ej. `resplandor_radio` cuando `resplandor == 0.0`), su control se deshabilita visualmente (`state="disabled"`).
  * Filtrado dinámico por estilo:
    - Al alternar el estilo en el selector, el panel reconstruye o actualiza la visibilidad de los controles aplicando la condición `v.aplica_a(estilo)`.

#### Tarea 5.3 — Selector de Audio, Proyectos y Presets
- **Rol Asignado:** Ani Programadora (Fase 2 - Ejecución).
- **Especificación técnica:**
  * **Carga de Audio:**
    - Invoca `filedialog.askopenfilename` con filtro de extensiones (`*.mp3;*.wav;*.flac;*.m4a;*.ogg`).
    - Al seleccionar pista: ejecuta `analisis.analizar(ruta, params, estilo)`, calcula la duración total y la cantidad de cuadros, e inmediatamente dibuja el fotograma inicial representativo con los valores por defecto (satisfaciendo el requerimiento del fundador: *"ver una onda predeterminada"* de inmediato).
  * **Gestión de Proyectos:**
    - "Abrir Proyecto": abre diálogo `.json`, invoca `proyecto.abrir(ruta)`, actualiza la pista de audio cargada, el estilo seleccionado y rellena todas las variables de los parámetros.
    - "Guardar Proyecto": abre diálogo de guardado `.json` e invoca `proyecto.guardar(ruta, audio, estilo, params)`.
  * **Gestión de Presets:**
    - Selector desplegable alimentado por `proyecto.listar_presets()` (detectando automáticamente `barras_blancas`, `barras_neon`, `espejadas_frecuencia`, `onda_suave`).
    - "Aplicar Preset": invoca `proyecto.abrir_preset(nombre)`, actualiza el estilo y los parámetros correspondientes, y refresca la vista previa al instante.
    - "Guardar Preset": permite persistir una configuración visual personalizada sin audio mediante `proyecto.guardar_preset()`.

#### Tarea 5.4 — Área de Vista Previa Reactiva, Scrubbing y Fragmento Animado
- **Rol Asignado:** Ani Programadora (Fase 2 - Ejecución).
- **Especificación técnica:**
  * **Contrato de Invarianza Estructural (MVP-5):**
    - La vista previa se genera exclusivamente invocando `Render.cuadro(i)`. Queda terminantemente prohibido contar con un motor o función de dibujo simplificada para previsualización.
  * **Scrubbing Temporal:**
    - El deslizador de transporte permite recorrer desde el cuadro `0` hasta `n_cuadros - 1`.
    - Al mover el cursor, se renderiza el cuadro correspondiente `i`, se reescala proporcionalmente mediante Pillow con filtro bilineal rápido para adaptarse a las dimensiones del canvas de vista previa, y se proyecta mediante `ImageTk.PhotoImage`.
    - Rendimiento garantizado (Criterio 5.3): tiempo de respuesta medido inferior a 500 ms (típicamente 15-25 ms).
  * **Fragmento Animado:**
    - Botón "Previsualizar Fragmento": ejecuta una reproducción de 60 cuadros consecutivos (2 segundos a 30 fps) alrededor del punto actual del cursor.
    - La animación corre mediante el bucle cooperativo `root.after(33, ...)` sin congelar la ventana y permitiendo su detención inmediata.

#### Tarea 5.5 — Diálogo de Exportación en Hilo Secundario y Cancelación Cooperativa
- **Rol Asignado:** Ani Programadora (Fase 2 - Ejecución).
- **Especificación técnica:**
  * Al pulsar "Exportar Video":
    - Solicita destino mediante `filedialog.asksaveasfilename(defaultextension=".webm", filetypes=[("Video WebM", "*.webm")])`.
    - Inicializa la tarea de codificación en un hilo separado `threading.Thread(target=..., daemon=True)`.
  * Diálogo modal o sección de estado con barra de progreso (`ttk.Progressbar`), porcentaje numérico, contador de cuadros `{hecho}/{total}` y botón "Cancelar".
  * Integración con `salida.exportar(render, destino, progreso=callback)`:
    - La función `callback(hecho, total) -> bool` transmite el avance al hilo de UI mediante `root.after(0, ...)`.
    - Si el usuario presiona "Cancelar", se señaliza el evento de cancelación (`threading.Event`), haciendo que el callback devuelva `False`.
    - `salida.py` cancela la codificación de FFmpeg, elimina el archivo incompleto en disco y levanta `ErrorDeSalida`, restableciendo el estado de la interfaz sin congelamientos ni datos corruptos (Criterio 5.4).
  * Al finalizar la exportación con éxito, presenta un mensaje de confirmación que incluye la indicación operativa de Drift según el modo de fondo activo (`salida.SIGUIENTE_PASO[fondo]`).

#### Tarea 5.6 — Suite de Pruebas Automatizadas de la GUI (`tests/test_gui.py`)
- **Rol Asignado:** Ani Programadora (Fase 2 - Ejecución).
- **Archivo a generar:** `tests/test_gui.py`.
- **Especificación técnica:**
  * Pruebas automatizadas en modo desatendido (instanciando la interfaz sin requerir interacción física del operador):
    - **5.1**: Simulación programática del flujo integral: carga de audio, conmutación de estilo, mutación de parámetros, persistencia en proyecto y exportación de video.
    - **5.2**: Verificación pixel a pixel: compara el fotograma generado por el modelo de vista previa de la GUI contra el fotograma extraído del exportador, certificando igualdad estricta de arrays (`np.array_equal`) y hashes SHA-256 (MVP-5).
    - **5.3**: Medición automatizada de latencia: registra el tiempo de renderizado y reescalado de vista previa a media resolución con `time.perf_counter()`, validando que sea estrictamente menor a 500 ms.
    - **5.4**: Simulación de exportación concurrente: verifica que el hilo de UI mantenga su capacidad de respuesta y comprueba la cancelación cooperativa inmediata sin dejar residuos de archivos.
    - **5.5**: Comprobación exhaustiva del esquema: recorre cada una de las claves de `parametros.ESQUEMA` y valida que exista el widget y la variable de control correspondiente en la interfaz.
    - **5.6**: Resiliencia y manejo de errores: somete la interfaz a audios corruptos o inexistentes y valida que el manejador capture `ErrorDeAnalisis` y presente avisos limpios sin tracebacks en consola.

#### Tarea 5.7 — Auditoría de Calidad y Criterios Falsables (Fase 3 - QA)
- **Rol Asignado:** Ani Mal Humor (Fase 3 - QA Lead).
- **Especificación técnica:**
  * Auditoría formal "pedido vs entregado" de la Etapa 5.
  * Ejecución y validación exhaustiva de los criterios 5.1 a 5.6 con la suite en verde.

---

## 🎯 Criterios de Aceptación y Salida Falsables (5.1 a 5.6)

| # | Criterio | Método de Verificación | Condición Falsable de Aprobación |
|---|---|---|---|
| **5.1** | Recorrido completo sin tocar la línea de comandos | Inspección funcional / Test de integración | Operación completa de carga de audio, ajuste de valores, cambio de estilos, guardado de proyecto y exportación realizada sin invocar CLI. |
| **5.2** | Cuadro de la vista previa idéntico al del export | `python tests\test_gui.py` | El array RGBA de `render.cuadro(i)` utilizado por la GUI es idéntico bit a bit (`hashlib.sha256` y `np.array_equal`) al enviado al pipeline de codificación. |
| **5.3** | Vista previa actualizada en menos de 500 ms | `python tests\test_gui.py` | Medición con `time.perf_counter()` del ciclo de renderizado y escalado a media resolución menor a 0.500 s. |
| **5.4** | La interfaz no se congela durante el export, y cancelar funciona | `python tests\test_gui.py` | La exportación corre en hilo secundario; al emitir cancelación, el subproceso finaliza, el archivo parcial se destruye y la UI se restablece. |
| **5.5** | 100% de los valores del esquema presentes en la interfaz | `python tests\test_gui.py` | Verificación refleja: para cada entrada en `parametros.ESQUEMA`, existe un widget interactivo en el formulario dinámico. |
| **5.6** | Audio corrupto o inexistente avisa sin traceback | `python tests\test_gui.py` | Intercepción de `ErrorDeAnalisis` y fallos de archivo con presentación de mensaje de error claro sin excepciones no capturadas. |

---

## 📋 Lista de Cotejo Previa a Emitir el Plan (8 Puntos Canónicos)

1. **¿Alguna tarea contradice una regla escrita de un documento canónico?**
   No. El diseño respeta taxativamente la prohibición de dependencias nuevas (solo `tkinter` y `Pillow`, regla 13), el desacoplamiento estricto del motor (`ARQUITECTURA.md` §8), la preservación de un único motor de renderizado (criterio MVP-5), y la regla de no diseñar para distribución masiva (regla 16).
2. **¿Las herramientas, rutas, skills y comandos que nombro existen y hacen lo que digo?**
   Sí. Verificados empíricamente en disco Python 3.14.6, Tkinter (Tk 8.6), Pillow con `ImageTk`, `pista_espectro.wav`, `pista_prueba.wav`, FFmpeg 8.0.1 y `parametros.por_grupo()`.
3. **¿Cubre todos los requisitos del pedido, incluidos los que una corrida anterior ya cumplía?**
   Sí. Cubre la ventana principal Tkinter desacoplada, formulario dinámico desde `ESQUEMA`, selectores de audio/proyectos/presets, preview reactivo con scrubbing, diálogo/barra de export en hilo secundario con cancelación cooperativa, criterios 5.1 a 5.6, roles explícitos y cero sintaxis en futuro.
4. **¿Cada criterio de aceptación puede fallar (falsable)?**
   Sí. Los 6 criterios poseen métricas estrictamente medibles (hashes SHA-256, benchmarks de tiempo en milisegundos, paridad de conjuntos de parámetros, pruebas de hilos y captura de excepciones).
5. **¿Alguna tarea borra, sobrescribe o mueve algo, y si sí, está autorizado por el Capitán?**
   No. Turno 1 mantiene intacto el código fuente de producto. En ejecución sólo se crean `tools/visualizador/gui.py` y `tests/test_gui.py` como módulos nuevos.
6. **¿Cité el documento canónico que gobierna?**
   Sí. Se citan `docs/RUTA_DE_TRABAJO.md` (§2 y §4 Etapa 5), `docs/ARQUITECTURA.md` (§8) y `docs/MVP.md` (§3, §4 y §7).
7. **¿Si el entregable corre desatendido, prevé detección de fallas, muerte silenciosa y plan de supervisión?**
   Sí. La GUI intercepta las excepciones de dominio del sistema (`ErrorDeAnalisis`, `ErrorDeParametro`, `ErrorDeProyecto`, `ErrorDeSalida`) y las canaliza mediante diálogos informativos, mientras que la exportación en hilo secundario cuenta con supervisión cooperativa por heartbeat y cancelación limpia.
8. **¿El plan de validación emite veredicto definitivo en <= 48h?**
   Sí. La suite de pruebas completa corre y emite su veredicto en menos de 30 segundos.

---

## 🚦 Gate de Decisión del Capitán

Para avanzar a la **Fase 2 (Ejecución)** en el siguiente turno:
1. **Aprobación del Plan:** El Capitán autoriza formalmente la ejecución de la Etapa 5 (Interfaz gráfica Tkinter) conforme al desglose y criterios de aceptación especificados.
2. **Despacho del Escuadrón:** Tras la confirmación del Capitán, Ani Recepcionista derivará la implementación técnica a **Ani Programadora** (Fase 2 Core) y la posterior verificación de calidad a **Ani Mal Humor** (Fase 3 QA).
