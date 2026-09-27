---
tipo: "handoff"
turno: 14
agente: "Ani Arquitecta"
fecha: 2026-09-26
estado: "planificado — triage de Etapa 4 (Proyectos, presets y compensación de color) completado; esperando Gate del Capitán"
---

# Plan de Implementación y Triage Factual (T14) — Etapa 4: Proyectos, presets y compensación de color

## 📌 Pedido Original del Capitán (textual)
> "avanza"

---

## 🧭 Bóveda Resuelta ($VAULT)
- **VAULT Local Resuelto:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\`
- **Estructura base verificada:** `index.md` (presente), `log.md` (presente, 154 líneas, última entrada T13).

---

## 🔍 Declaración Factual del Punto de Partida

### 1. Estado del Repositorio y Entorno en Disco
- **Rama activa:** `master`.
- **Árbol de trabajo:** Limpio (`working tree clean`).
- **Commit de base verificado:** `7c77176` ("T13: implementacion y cierre de Etapa 3 (Estilo Onda)").
- **Entorno de ejecución:** Python 3.14.6, FFmpeg 8.0.1, Pillow 11.1.0, NumPy 2.2.3 sobre Windows.
- **Directorio de trabajo:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins`.

### 2. Estado de la Suite de Pruebas (75/75 comprobaciones en verde, 0 fallas)
- `python tests/test_analisis.py`: **36 comprobaciones pasadas, 0 fallas** (cuadros exactos en 24/25/30/60 fps, rango 0..1 sin NaNs, ventana causal sin pre-eco, respuesta plana con ruido rosa en 1.03x).
- `python tests/test_render.py --export`: **36 comprobaciones pasadas, 0 fallas** (cuadro idempotente sin estado mutable, barrido de 196 combinaciones en los 3 estilos, exportación exacta a 480 cuadros en WebM en negro, color y transparente con `alpha_mode='1'`).
- `python tests/verificar_sincronia.py` (ejecutado en `barras`, `espejadas` y `onda`): **Alineación temporal exacta con desvío +0 cuadros** en 8 ataques rítmicos independientes sobre `pista_prueba.wav`.

### 3. Precondiciones de la Etapa 4
- **Etapa 3:** Cerrada en T13 con criterios 3.1 a 3.4 cumplidos. Precondiciones de Etapa 4 formalmente satisfechas según `docs/RUTA_DE_TRABAJO.md`.

---

## 🗺️ Especificación de Tareas para la Etapa 4

### Justificación de Consulta Previa (Regla 28 de SKILL.md)
Consulta externa no requerida: los fundamentos matemáticos de la compensación de color en Trama están medidos y demostrados en `docs/COLOR_EN_TRAMA.md` y `tools/medir_trama.py`. Los contratos de serialización y gestión de proyectos están definidos en `docs/ARQUITECTURA.md` §6 y `docs/RUTA_DE_TRABAJO.md` §4. No existen divergencias técnicas que requieran deliberación externa en esta fase.

---

### Desglose Detallado de Tareas (Bite-Sized Tasks)

#### Tarea 4.1 — Módulo de Persistencia y Serialización (`proyecto.py`)
- **Rol Asignado:** Ani Programadora (Fase 2 - Ejecución).
- **Archivo a generar:** `tools/visualizador/proyecto.py`.
- **Especificación técnica:**
  * Estructura JSON canónica con metadato `"version": 1`.
  * Esquema de proyecto: almacena ruta de audio (`audio`), estilo (`estilo`) y diccionario de parámetros (`params`).
  * Esquema de preset: almacena estilo (`estilo`) y diccionario de parámetros (`params`), excluyendo deliberadamente la pista de audio.
  * Funciones de contrato:
    - `guardar(ruta: Path, audio: Path, estilo: str, params: dict) -> None`: serializa con formato indentado legible (indent=2) y codificación UTF-8.
    - `abrir(ruta: Path) -> tuple[Path, str, dict]`: deserializa, valida existencia del archivo, valida versión del esquema, valida parámetros con `parametros.validar` y comprueba la existencia de la pista de audio. Ante audio ausente o desplazado, levanta excepción explicativa con la ruta faltante.
    - `guardar_preset(ruta: Path, estilo: str, params: dict) -> None`: persiste la configuración visual libre de audio.
    - `abrir_preset(ruta: Path) -> tuple[str, dict]`: carga y valida el preset contra el esquema del estilo correspondiente.
    - `listar_presets(directorio: Path | None = None) -> list[str]`: inspecciona la carpeta `presets/` y enumera los nombres disponibles.
  * Excepciones de dominio: `ErrorDeProyecto(ValueError)` con mensaje claro del fallo.

#### Tarea 4.2 — Integración del Parámetro `compensar_fondo` y Álgebra de Trama
- **Rol Asignado:** Ani Programadora (Fase 2 - Ejecución).
- **Archivos a modificar:**
  * `tools/visualizador/parametros.py`:
    - Incorpora al `ESQUEMA` en grupo `"color"`:
      ```python
      "compensar_fondo": Valor(
          etiqueta="Compensar fondo",
          tipo=str, default="#000000", grupo="color", formato="color",
          ayuda="Color del video detrás de las barras para compensar el aclarado "
                "de la fusión Trama de Drift. En #000000 está apagado y no modifica nada.",
      )
      ```
    - Incorpora funciones matemáticas de compensación (portadas desde `tools/medir_trama.py`):
      `compensar_color(deseado_hex: str, fondo_hex: str) -> tuple[str, bool]`
      `es_color_alcanzable(deseado_hex: str, fondo_hex: str) -> bool`
      Fórmula: `src = 1.0 - (1.0 - deseado) / (1.0 - fondo)` evaluada en canal RGB 0..1.
      Condición de alcanzabilidad: `D >= B` en cada canal. Cuando `D < B`, genera advertencia explícita (`warnings.warn` o registro claro en consola) en lugar de recortar silenciosamente.

#### Tarea 4.3 — Generación de Presets de Fábrica
- **Rol Asignado:** Ani Programadora (Fase 2 - Ejecución).
- **Directorio a crear:** `presets/`.
- **Archivos a generar (JSON válidos con `"version": 1`):**
  * `presets/barras_blancas.json`: Estilo `barras`, color `#FFFFFF`, degradado `"ninguno"`, fondo `"negro"`. Look de referencia inmune a cualquier alteración de color por Trama (demostrado en `docs/COLOR_EN_TRAMA.md` §2).
  * `presets/barras_neon.json`: Estilo `barras`, color `#00E5FF`, color_final `#0050DC`, degradado `"altura"`, resplandor `0.3`, reflejo `0.2`.
  * `presets/espejadas_frecuencia.json`: Estilo `espejadas`, color `#FF007F`, color_final `#7F00FF`, degradado `"ancho"`, redondeo `50.0`.
  * `presets/onda_suave.json`: Estilo `onda`, color `#00FFCC`, grosor_linea `4`, relleno `True`, degradado `"altura"`.

#### Tarea 4.4 — Adaptación del Pipeline de Render (`render.py`)
- **Rol Asignado:** Ani Programadora (Fase 2 - Ejecución).
- **Archivo a modificar:** `tools/visualizador/render.py`.
- **Especificación técnica:**
  * En `Render.__init__`: cuando `p["compensar_fondo"]` tiene un valor distinto a `"#000000"`, pre-compensa los colores efectivos de dibujo (`color` y `color_final` si aplica) utilizando `compensar_color`.
  * Ante color inalcanzable (`alcanzable == False`), emite aviso explícito al usuario documentando la desviación.
  * Preservación estricta de invariante: con `compensar_fondo == "#000000"`, los colores permanecen idénticos bit a bit a la línea base actual.

#### Tarea 4.5 — Incorporación de Opciones en Interfaz CLI (`cli.py`)
- **Rol Asignado:** Ani Programadora (Fase 2 - Ejecución).
- **Archivo a modificar:** `tools/visualizador/cli.py`.
- **Especificación técnica:**
  * Agrega opciones al parser de argumentos:
    - `--proyecto ARCHIVO`: carga audio, estilo y parámetros desde archivo JSON y ejecuta el render o preview.
    - `--guardar-proyecto ARCHIVO`: persiste la configuración activa junto con la ruta del audio.
    - `--preset NOMBRE_O_RUTA`: aplica un preset desde archivo o desde `presets/`.
    - `--guardar-preset ARCHIVO`: persiste estilo y parámetros en formato preset.

#### Tarea 4.6 — Suite de Pruebas de Etapa 4 (`tests/test_proyecto.py`)
- **Rol Asignado:** Ani Programadora (Fase 2 - Ejecución).
- **Archivo a generar:** `tests/test_proyecto.py`.
- **Especificación técnica:**
  * Comprobación automatizada de los 7 criterios de salida (4.1 a 4.7).
  * Validación de persistencia, integridad de deserialización, detección de audios movidos, inocuidad de compensación nula, y fidelidad colorimétrica ΔE76 < 1.0.

#### Tarea 4.7 — Auditoría de Calidad y Criterios Falsables (Fase 3 - QA)
- **Rol Asignado:** Ani Mal Humor (Fase 3 - QA Lead).
- **Especificación técnica:**
  * Verificación empírica contra matriz "pedido vs entregado".
  * Comprobación de que la suite pase al 100% sin advertencias no controladas.

---

## 🎯 Criterios de Aceptación y Salida Falsables (4.1 a 4.7)

| # | Criterio | Comando de verificación | Condición de aprobación (Falsable) |
|---|---|---|---|
| **4.1** | Guardar → reabrir → exportar da cuadros idénticos | `python tests\test_proyecto.py` | Hash SHA-256 de fotogramas renderizados desde proyecto idéntico bit a bit a los generados directamente por CLI/Render. |
| **4.2** | Proyecto con versión desconocida o valor inválido falla con mensaje claro | `python tests\test_proyecto.py` | `abrir()` levanta `ErrorDeProyecto` o `ErrorDeParametro` con mensaje explicativo; no produce tracebacks crudos ni datos a medias. |
| **4.3** | Los presets de fábrica cargan y exportan | `python tests\test_proyecto.py` | Todos los archivos en `presets/` cargan válidamente y producen cuadros sin excepción. |
| **4.4** | Proyecto con audio movido o ausente avisa qué falta | `python tests\test_proyecto.py` | `abrir()` detecta la ausencia física del audio y reporta la ruta esperada con precisión. |
| **4.5** | `compensar_fondo` con default `#000000` no altera ni un píxel | `python tests\test_proyecto.py` | Cuadro con `#000000` coincide al 100% (cero píxeles con diferencia) contra cuadro generado sin el parámetro. |
| **4.6** | Compensado sobre fondo oscuro da ΔE < 1 contra el pedido | `python tests\test_proyecto.py` | Medición colorimétrica en CIE Lab tras aplicar fórmula Trama da distancia perceptual ΔE76 < 1.0. |
| **4.7** | Color inalcanzable (`D < B` en algún canal) avisa, no recorta en silencio | `python tests\test_proyecto.py` | Genera advertencia explícita en consola o log indicando el canal saturado; prohíbe recorte opaco silencioso. |

---

## 📋 Lista de Cotejo Previa a Emitir el Plan (8 Puntos Canónicos)

1. **¿Alguna tarea contradice una regla escrita de un documento canónico?**
   No. Se preservan estrictamente los contratos de `docs/RUTA_DE_TRABAJO.md`, `docs/MVP.md`, `docs/COLOR_EN_TRAMA.md` y `docs/ARQUITECTURA.md`.
2. **¿Las herramientas, rutas, skills y comandos que nombro existen y hacen lo que digo?**
   Sí. Rutas validadas en disco, Python 3.14.6 y suites de pruebas automáticas verificadas en ejecución activa.
3. **¿Cubre todos los requisitos del pedido, incluidos los que una corrida anterior ya cumplía?**
   Sí. Verificado el punto de partida (75 pruebas en verde, commit `7c77176`), gestión de proyectos `.json`, presets de fábrica, `compensar_fondo`, criterios 4.1 a 4.7 y asignación de roles.
4. **¿Cada criterio de aceptación puede fallar (falsable)?**
   Sí. Todas las pruebas evalúan condiciones numéricas, aserciones de igualdad de bytes e intercepciones de excepciones.
5. **¿Alguna tarea borra, sobrescribe o mueve algo, y si sí, está autorizado por el Capitán?**
   No. Turno 1 mantiene el código de producto intacto. En Turno 2 sólo se añaden módulos nuevos y extensiones no destructivas.
6. **¿Cité el documento canónico que gobierna?**
   Sí. Se citan `docs/RUTA_DE_TRABAJO.md`, `docs/COLOR_EN_TRAMA.md` y `docs/ARQUITECTURA.md`.
7. **¿Si el entregable corre desatendido, prevé detección de fallas, muerte silenciosa y plan de supervisión?**
   Sí. Manejo explícito con excepciones de dominio `ErrorDeProyecto` y avisos visibles ante colores inalcanzables.
8. **¿El plan de validación emite veredicto definitivo en <= 48h?**
   Sí. La suite de pruebas entrega su veredicto en menos de 25 segundos.

---

## 🚦 Gate de Decisión del Capitán

Para avanzar a la **Fase 2 (Ejecución)** en el siguiente turno:
1. **Aprobación del Plan:** El Capitán autoriza formalmente la ejecución de la Etapa 4 (Proyectos, presets y compensación de color) conforme al desglose y criterios detallados.
2. **Despacho del Escuadrón:** Tras la confirmación del Capitán, Ani Recepcionista derivará la implementación a **Ani Programadora** y la posterior auditoría a **Ani Mal Humor**.
