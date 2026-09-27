# Handoff Durable T15 — Etapa 4: Proyectos, presets y compensación de color

- **Fecha:** 2026-09-26
- **Turno:** T15 (Fase 2 — Ejecución Core)
- **Rol:** Ani Programadora (Core Logic Multilenguaje)
- **Pedido Original del Capitán:** "procede"
- **Commit Base:** `7c77176` (Etapa 3 cerrada)
- **Rama:** `master`

---

## 1. Resumen Ejecutivo

Se implementó de forma completa y determinista la **Etapa 4 (Proyectos, presets y compensación de color)** del visualizador de audio Drift conforme a `docs/ARQUITECTURA.md` §6, `docs/COLOR_EN_TRAMA.md` y `implementation_plan.md`.

Se añadieron:
1. El módulo de persistencia y serialización `tools/visualizador/proyecto.py`.
2. Las funciones de álgebra de Trama y el parámetro `compensar_fondo` en `tools/visualizador/parametros.py`.
3. Los 4 presets canónicos de fábrica en `presets/`.
4. La pre-compensación de color en el pipeline de `tools/visualizador/render.py`.
5. La integración de proyectos y presets en la línea de comandos `tools/visualizador/cli.py`.
6. La suite completa de pruebas `tests/test_proyecto.py` validando los criterios 4.1 a 4.7 más pruebas de integración CLI.

La suite total del proyecto alcanza **127 comprobaciones automatizadas pasando al 100% en verde, con 0 fallas**.

---

## 2. Detalle de Archivos y Mutaciones de Estado

### A. Módulo de Proyectos y Presets (`tools/visualizador/proyecto.py`)
- Define la excepción de dominio `ErrorDeProyecto(ValueError)`.
- `guardar(ruta, audio, estilo, params)`: serializa en JSON legible (`indent=2`, UTF-8, `"version": 1`), validando previamente estilo y parámetros contra el esquema.
- `abrir(ruta) -> tuple[Path, str, dict]`: deserializa el archivo de proyecto, valida estructura JSON, versión requerida (`version == 1`), estilo conocido y parámetros contra `parametros.validar`. Comprueba la existencia física de la pista de audio (resolviendo rutas absolutas o relativas al directorio del proyecto) y levanta `ErrorDeProyecto` informando con precisión el archivo faltante ante audio desplazado o ausente.
- `guardar_preset(ruta, estilo, params)`: persiste la configuración visual y estilística libre de audio.
- `abrir_preset(ruta_o_nombre, directorio=None) -> tuple[str, dict]`: carga presets desde rutas absolutas/relativas o buscando por nombre en el directorio canónico `presets/`.
- `listar_presets(directorio=None) -> list[str]`: enumera los nombres disponibles en el catálogo de presets.

### B. Parámetro `compensar_fondo` y Álgebra de Color (`tools/visualizador/parametros.py`)
- Incorpora al `ESQUEMA` en el grupo `"color"`:
  - `compensar_fondo`: tipo `str`, default `"#000000"`, formato `"color"`.
- Implementa funciones puras de álgebra de Trama (`docs/COLOR_EN_TRAMA.md`):
  - `a_rgb01(hexa)` y `a_hex(rgb01)`: conversiones deterministas entre hexadecimal y float64 en `[0.0, 1.0]`.
  - `trama(base, src)`: `1.0 - (1.0 - base) * (1.0 - src)` correspondiente al shader `kLayerFragShader` de Drift.
  - `es_color_alcanzable(deseado_hex, fondo_hex) -> bool`: comprueba si en cada canal RGB se cumple `D >= B - 1e-9`.
  - `compensar_color(deseado_hex, fondo_hex) -> tuple[str, bool]`: calcula `src = 1.0 - (1.0 - deseado) / (1.0 - fondo)`. Si el color no es alcanzable, emite una advertencia explícita (`UserWarning`) detallando el canal saturado en lugar de recortar silenciosamente.
  - `a_lab(rgb01)` y `delta_e(a, b)`: cálculo de distancia perceptual CIE Lab ΔE76 con blanco D65 para verificación colorimétrica rigurosa.

### C. Presets de Fábrica (`presets/`)
Se generaron en la raíz del proyecto los 4 presets canónicos con `"version": 1`:
- `presets/barras_blancas.json`: estilo `barras`, color `#FFFFFF`, degradado `ninguno`, fondo `negro` (look inmune al corrimiento de Trama).
- `presets/barras_neon.json`: estilo `barras`, degradado `altura`, color `#00E5FF` a `#0050DC`, resplandor `0.3`, reflejo `0.2`.
- `presets/espejadas_frecuencia.json`: estilo `espejadas`, degradado `ancho`, color `#FF007F` a `#7F00FF`, redondeo `50.0`.
- `presets/onda_suave.json`: estilo `onda`, color `#00FFCC`, grosor_linea `4`, relleno `true`, degradado `altura`.

### D. Pipeline de Render (`tools/visualizador/render.py`)
- En `Render.__init__`:
  - Si `compensar_fondo != "#000000"`, pre-compensa `color` y `color_final` (si está activo para degradado) mediante `parametros.compensar_color`.
  - Si `compensar_fondo == "#000000"`, se preserva de manera estricta la invariante: los colores no se modifican y el render es idéntico bit a bit a la línea base original.

### E. Interfaz CLI (`tools/visualizador/cli.py`)
- Se integraron los flags:
  - `--proyecto ARCHIVO`: abre proyecto y aplica su audio, estilo y parámetros.
  - `--guardar-proyecto ARCHIVO`: persiste la configuración y audio activo en un JSON de proyecto.
  - `--preset NOMBRE_O_RUTA`: carga preset de fábrica o archivo externo.
  - `--guardar-preset ARCHIVO`: persiste estilo y parámetros en formato preset.
- Se agregó el listado de presets disponibles en `--listar`.
- Se atrapa `proyecto.ErrorDeProyecto` reportando mensajes claros a stderr con código de salida 2, sin tracebacks crudos.

### F. Suite de Pruebas (`tests/test_proyecto.py`)
Implementa 46 comprobaciones automatizadas cubriendo los criterios 4.1 a 4.7 y CLI:
- **4.1**: Guardar -> reabrir -> exportar produce cuadros idénticos bit a bit (`hashlib.sha256` y `np.array_equal`).
- **4.2**: Proyecto con versión no soportada, JSON mal formado, parámetro inválido o campo faltante levanta excepciones explicativas (`ErrorDeProyecto`, `ErrorDeParametro`).
- **4.3**: Los 4 presets de fábrica cargan y renderizan cuadros válidos de prueba sin fallar.
- **4.4**: Proyecto con audio faltante o movido reporta la ruta del archivo ausente en el mensaje.
- **4.5**: `compensar_fondo="#000000"` no altera ni un píxel comparado con el default implícito (diferencia máxima = 0).
- **4.6**: Compensación sobre fondos oscuros (`#141414`, `#101C38`) logra fidelidad colorimétrica ΔE < 1.0 (imperceptible para el ojo humano).
- **4.7**: Color inalcanzable (`D < B`) emite advertencia explícita en consola indicando el canal saturado (`R`), prohibiendo recortes silenciosos.
- **CLI**: Comprobaciones de guardado y previsualización con flags `--guardar-preset`, `--guardar-proyecto` y `--proyecto`.

---

## 3. Evidencia Empírica de Verificación

Todas las pruebas se ejecutaron en el entorno real sobre Windows:

1. `python tests\test_analisis.py`:
   - **36 comprobaciones pasadas, 0 fallas**.
2. `python tests\test_render.py --export`:
   - **36 comprobaciones pasadas, 0 fallas** (incluye barrido de parámetros con `compensar_fondo` y codificación WebM en negro, color y transparente para barras y onda).
3. `python tests\verificar_sincronia.py`:
   - **9 comprobaciones pasadas, 0 desvíos (+0 cuadros)** en los 8 ataques rítmicos.
4. `python tests\test_proyecto.py`:
   - **46 comprobaciones pasadas, 0 fallas**.

**Total de la suite general:** 127 comprobaciones pasadas, 0 fallas, 0 regresiones.

---

## 4. Estado y Próximos Pasos

- **Etapa 4:** Completada en su totalidad por Ani Programadora (Fase 2 - Ejecución).
- **Siguiente paso:** Pase a **Fase 3 — Auditoría de Calidad y Criterios Falsables** a cargo de Ani Mal Humor (QA Lead).
