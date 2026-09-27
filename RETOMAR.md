# Dónde retomar

**Documento vivo.** Cada agente lo actualiza al cerrar su turno. Si contradice a otro documento, gana la bitácora `.memory/log.md` — pero entonces alguien tiene que arreglar este archivo.

**Última actualización:** 2026-09-26, turno T19, agente Ani Programadora.

---

## 🚦 Estado: etapas 1, 2, 3, 4, 5 y 6 cerradas. MVP COMPLETO. Toca la etapa 7 (Validación con el fundador).

El MVP está terminado de punta a punta:
- **Lanzador de escritorio:** `visualizador.bat` en la raíz ejecuta la aplicación mediante `pythonw.exe` sin dejar consola negra de fondo en Windows.
- **Interfaz gráfica:** `tools/visualizador/gui.py` desacoplada del motor de render, con visor y transporte interactivo, scrubbing, fragmento de prueba animado, controles polimórficos autogenerados desde el esquema declarativo, apertura/guardado de proyectos y presets, y exportación asíncrona no bloqueante con cancelación cooperativa.
- **Proyectos y presets:** `tools/visualizador/proyecto.py` con 4 presets de fábrica en `presets/` (`barras_blancas`, `barras_neon`, `espejadas_frecuencia`, `onda_suave`) y parámetro `compensar_fondo` para fidelidad de color en modo Trama sobre video oscuro (ΔE < 1.0).
- **Motor de render y análisis:** 3 estilos de dibujo (`barras`, `espejadas`, `onda`), análisis FFT por bandas logarítmicas causales, y exportación WebM en fondos negro, color y transparente (con alpha para Drift 0.7+).
- **Suite de pruebas:** Más de 170 comprobaciones automáticas pasando al 100% en verde con 0 fallas y 0 regresiones.

### Lo que el fundador decidió en el punto de control y turnos previos

| Tema | Decisión del fundador |
|---|---|
| **Aspecto de barras** | ✅ Aprobado en T10: *"Sobre los estilos y variables, para esta primer version me parece bien"* |
| **Composición** | **Trama (Screen)** sobre fondo negro. Chroma Key descartado como default por limitaciones en Drift 0.6.0 |
| **Color** | Compensación matemática con `compensar_fondo` (`docs/COLOR_EN_TRAMA.md`), y preset de barras blancas inmune |
| **Puerta de entrada** | **`visualizador.bat` para el MVP** (T11). Ejecutable `.exe` con PyInstaller post-MVP |
| **Distribución** | ❌ **No es objetivo de este proyecto** (Regla 16 de la ruta) |

---

## Lo primero que tiene que hacer el próximo agente

**Etapa 7: Validación con el fundador.**
- Acompañar al fundador con Drift abierto para editar un video musical de punta a punta.
- Criterio clave del MVP: **El fundador lo usa solo, sin preguntarle nada al agente** (MVP-9).

---

## Probarlo ahora mismo

```powershell
# 1. Abrir la interfaz gráfica interactiva (doble clic o desde terminal):
.\visualizador.bat

# 2. Consultar estilos, presets y parámetros por CLI:
.\visualizador.bat --listar

# 3. Exportar un video directamente por CLI:
.\visualizador.bat tests\fixtures\pista_espectro.wav -o build\prueba.webm --preset barras_neon

# 4. Correr la suite completa de pruebas:
python tests\test_analisis.py
python tests\test_render.py --export
python tests\verificar_sincronia.py
python tests\test_proyecto.py
python tests\test_gui.py
python tests\test_lanzador.py
```

---

## Organización del código y documentación

| Documento | Contenido |
|---|---|
| [`docs/GUIA_DE_USO.md`](docs/GUIA_DE_USO.md) | Guía de uso completa para el usuario final (lanzador, GUI, Drift) |
| [`docs/COMO_USAR.md`](docs/COMO_USAR.md) | Referencia paso a paso de uso y composición |
| [`docs/RUTA_DE_TRABAJO.md`](docs/RUTA_DE_TRABAJO.md) | Tabla de etapas, criterios de salida y reglas de trabajo |
| [`docs/MVP.md`](docs/MVP.md) | Especificación y criterios de aceptación del MVP |
| [`docs/ARQUITECTURA.md`](docs/ARQUITECTURA.md) | Contratos de código y desacoplamiento de componentes |
| [`docs/COLOR_EN_TRAMA.md`](docs/COLOR_EN_TRAMA.md) | Fundamentos matemáticos y mediciones de la fusión Trama |

---

## Datos operativos verificados

- **Drift:** `C:\Program Files\Drift\drift.exe`, versión 0.6.0 — **sólo lectura**.
- **FFmpeg:** `C:\ffmpeg\bin\ffmpeg.exe` 8.0.1 en PATH.
- **Python:** 3.14.6 con `pythonw.exe`, `python.exe` y `py.exe` en PATH.
- **Lanzador:** `visualizador.bat` probado con espacios y rutas absolutas.
