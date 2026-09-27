---
tipo: "handoff"
turno: "T18"
fecha: 2026-09-26
agente: "Ani Arquitecta"
tema: "Triage de Fase 1 Core: Plan estructurado para la Etapa 6 (Lanzador visualizador.bat, documentación de usuario y cierre del MVP)"
commit: "pendiente de Gate del Capitán y ejecución técnica"
---

# Plan de Implementación — Etapa 6: Lanzador visualizador.bat, Documentación de Usuario y Cierre del MVP

## 📌 Pedido Original del Capitán (textual)
> "avanza"

---

## 1. Verificación Factual del Punto de Partida (Línea Base)
- **Repositorio y Rama:** `master` en `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins`.
- **Estado del Árbol Git:** Limpio al 100% tras consolidar y commitear las Etapas 4 y 5 en el commit `d692047`.
- **Suite de Pruebas Automatizadas:** 169 comprobaciones pasando al 100% en verde con 0 fallas y 0 regresiones:
  - `tests/test_analisis.py`: 36 comprobaciones pasadas (análisis espectral, curvas logarítmicas, normalización determinista).
  - `tests/test_render.py --export`: 36 comprobaciones pasadas (renderizado determinista, barrido de parámetros, exportación WebM en negro, color y transparente con alpha).
  - `tests/verificar_sincronia.py`: 9 comprobaciones pasadas (alineación temporal exacta, +0 cuadros de desvío en los 3 estilos).
  - `tests/test_proyecto.py`: 46 comprobaciones pasadas (persistencia de proyectos y presets JSON, validación estricta, compensación de color sobre fondos oscuros ΔE < 1.0, advertencias explícitas).
  - `tests/test_gui.py`: 42 comprobaciones pasadas (criterios 5.1 a 5.6 certificados, invarianza MVP-5, latencia < 35 ms, concurrencia y cancelación limpia).
- **Herramientas de Sistema:**
  - Python: `3.14.6` verificado con `pythonw.exe`, `python.exe` y `py.exe` disponibles en PATH.
  - Tkinter: Tk 8.6 operativo.
  - FFmpeg: versión `8.0.1` verificada en PATH.

---

## 2. Alcance y Objetivos de la Etapa 6
Conforme a `docs/RUTA_DE_TRABAJO.md` §2 y §6, `docs/MVP.md` §4 y §5, y las decisiones canónicas del fundador en T10 y T11:
1. Proporcionar el mecanismo de lanzamiento de doble clic para Windows mediante el script batch `visualizador.bat` en la raíz del repositorio, garantizando ejecución sin ventana de consola negra detrás (vía `pythonw.exe`), tolerancia estricta a espacios en rutas (`Jonatan Agustín`), configuración automática de `PYTHONPATH`, y diagnósticos legibles ante ausencia de Python o FFmpeg.
2. Añadir el entrypoint canónico del paquete `tools/visualizador/__main__.py` para estandarizar la invocación modular de Python.
3. Actualizar y estructurar la documentación de usuario final (`docs/COMO_USAR.md`, `docs/GUIA_DE_USO.md`, `README.md`, `RETOMAR.md`), reflejando la aplicación gráfica real, el flujo de trabajo en Drift 0.6.0 (fusión Trama sobre fondo negro, pre-compensación de color con `compensar_fondo`), y relegando el uso por línea de comandos a un apéndice técnico.
4. Construir la suite de pruebas automatizadas `tests/test_lanzador.py` para certificar de forma falsable y desatendida los criterios 6.1 a 6.5.
5. Actualizar la tabla de estado en `docs/RUTA_DE_TRABAJO.md` §1 para dejar el MVP listo para la Etapa 7 (Validación con el fundador).

---

## 3. Justificación de Consulta en Fase 0
- **Decisión sobre Ani Pensadora / Ani Investigadora:** No se convoca a agentes de consulta en este turno.
- **Fundamento Factual:** Las decisiones técnicas, de alcance y de gobernanza fueron ratificadas unívocamente por el fundador en T10 y T11 (fusión Trama como default, lanzador `.bat` con `pythonw.exe` para el MVP, `.exe` post-MVP, distribución fuera de objetivos según regla 16). Los binarios y rutas (`pythonw.exe`, `ffmpeg.exe`, Tkinter) están factual y empíricamente verificados en el entorno de ejecución. No existen bifurcaciones complejas ni incógnitas de diseño.

---

## 4. Desglose Detallado de Tareas

### Tarea 1: Construcción del Lanzador `visualizador.bat`
- **Archivo Destino:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\visualizador.bat`.
- **Contenido y Reglas de Construcción:**
  - Directiva inicial `@echo off` y `setlocal`.
  - Anclaje determinista de directorio base usando `set "SCRIPT_DIR=%~dp0"`.
  - Configuración de entorno: `set "PYTHONPATH=%SCRIPT_DIR%tools;%PYTHONPATH%"`.
  - Detección priorizada de Python:
    1. Preferencia principal: `pythonw.exe` (ejecuta GUI Tkinter en subsistema Windows sin abrir consola negra de fondo).
    2. Fallback 1: `python.exe`.
    3. Fallback 2: `py.exe`.
  - Diagnóstico de ausencia de Python: Si ninguno está disponible, muestra banner legible informando el requerimiento de Python 3.10+ con la opción "Add Python to PATH", pausa la consola para lectura humana (`pause`) y sale con código 1 (`exit /b 1`).
  - Diagnóstico de ausencia de FFmpeg: Ejecuta comprobación silenciosa (`where ffmpeg.exe >nul 2>nul`). Si falla, emite banner explicativo detallando la necesidad de FFmpeg para el visualizador, efectúa `pause` y sale con código 1 (`exit /b 1`).
  - Despacho y ejecución:
    - Cambio al directorio raíz: `cd /d "%SCRIPT_DIR%"`.
    - Si el binario seleccionado es `pythonw.exe`, invoca mediante `start "" "%PYTHON_BIN%" -m visualizador.cli %*`, liberando de inmediato el proceso batch y cerrando la consola instantáneamente.
    - Si el binario es el fallback (`python.exe` o `py.exe`), ejecuta directamente `"%PYTHON_BIN%" -m visualizador.cli %*` preservando la consola para mensajes de diagnóstico.
  - Blindaje con comillas en cada variable para soportar rutas con espacios (`C:\Users\Jonatan Agustín\...`).

### Tarea 2: Entrypoint Canónico del Paquete (`tools/visualizador/__main__.py`)
- **Archivo Destino:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\tools\visualizador\__main__.py`.
- **Implementación:**
  - Código desacoplado estándar:
    ```python
    import sys
    from .cli import main

    if __name__ == "__main__":
        raise SystemExit(main())
    ```
  - Permite invocar tanto `python -m visualizador` como `python -m visualizador.cli`.

### Tarea 3: Documentación de Usuario y Sincronización Canónica
- **Archivos a Crear / Modificar:**
  1. `docs/COMO_USAR.md` (Reescritura completa):
     - Paso 1: Lanzamiento con doble clic en `visualizador.bat`.
     - Paso 2: Flujo interactivo en la interfaz gráfica (carga de audio, previsualización inmediata con preset por defecto, selección de estilos, ajuste de controles reactivos, uso de `compensar_fondo`, guardado de proyectos/presets, scrubbing y exportación WebM).
     - Paso 3: Flujo de composición en Drift 0.6.0: importar `.webm`, posicionar sobre pista de video, asignar Modo de Fusión en **Trama** (Screen). Explicar por qué el fondo negro desaparece con exactitud matemática y cómo `compensar_fondo` preserva el tono original sobre metraje oscuro.
     - Paso 4: Alternativa secundaria de Chroma Key (efecto `key.chroma`) para fondos de color.
     - Apéndice: Referencia de comandos CLI avanzados.
  2. `docs/GUIA_DE_USO.md`:
     - Documento gemelo o puente explícito que apunta a la guía paso a paso, cubriendo la especificación del requerimiento.
  3. `README.md`:
     - Actualizar estado a "MVP Completo — Etapa 6".
     - Documentar `visualizador.bat` como el método principal de arranque.
     - Actualizar mapa de archivos y referencias obsoletas.
  4. `RETOMAR.md`:
     - Sincronizar estado actual: Etapas 1 a 6 cerradas, próximo paso: Etapa 7 (Validación con el fundador).
  5. `docs/RUTA_DE_TRABAJO.md`:
     - Actualizar la tabla de estado de §1 marcando Etapas 4, 5 y 6 como completadas.

### Tarea 4: Suite de Pruebas Automatizadas (`tests/test_lanzador.py`)
- **Archivo Destino:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\tests\test_lanzador.py`.
- **Comprobaciones a Implementar:**
  - **Prueba 6.1 (Documentación fiel y actualizada):** Verifica que `docs/COMO_USAR.md` y `docs/GUIA_DE_USO.md` existan, describan `visualizador.bat`, la interfaz gráfica y el flujo de Trama en Drift, sin referencias obsoletas a `tools/generar_overlay.py` como flujo principal.
  - **Prueba 6.2 (Comandos de documentación ejecutables):** Extrae los comandos presentes en la documentación y verifica sintaxis y ejecución exitosa (ej. `python -m visualizador.cli --listar`).
  - **Prueba 6.3 (Sincronización de estado vivo):** Verifica que `docs/RUTA_DE_TRABAJO.md` y `RETOMAR.md` declaren las etapas cerradas de forma consistente con `log.md`.
  - **Prueba 6.4 (Lanzamiento sin consola y preferencia pythonw):** Analiza `visualizador.bat` confirmando el uso de `pythonw.exe` mediante `start ""`, `@echo off`, `%*`, y simula ejecución no bloqueante.
  - **Prueba 6.5 (Invocación con espacios y desde cualquier directorio de trabajo):** Ejecuta `visualizador.bat` pasando argumentos de consulta (`--listar` o `--help`) desde un directorio externo temporal fuera del repositorio, validando retorno exitoso con código 0.
  - **Prueba Diagnóstica Extra:** Simula ausencia de Python o FFmpeg alterando el PATH en un subproceso y valida que el script emite el mensaje de error explicativo y aborta con código 1.

---

## 5. Criterios de Aceptación Falsables (Criterios 6.1 a 6.5)

| # | Criterio | Método de Verificación Falsable |
|---|---|---|
| **6.1** | `COMO_USAR.md` y `docs/GUIA_DE_USO.md` describen la aplicación real con GUI y flujo de Drift, sin pasos obsoletos | Inspección automatizada en `tests/test_lanzador.py` |
| **6.2** | Todo comando que figure en la documentación corre tal cual está escrito con retorno exitoso | Ejecución automatizada de comandos documentados en `tests/test_lanzador.py` |
| **6.3** | La tabla de estado de `RUTA_DE_TRABAJO.md` §1 y `RETOMAR.md` están sincronizados y al día | Inspección estricta de consistencia en `tests/test_lanzador.py` |
| **6.4** | Doble clic en `visualizador.bat` abre la ventana gráfica y no deja ventana de consola negra visible | Auditoría de sintaxis batch (`pythonw.exe`, `start ""`) y comprobación de proceso en `tests/test_lanzador.py` |
| **6.5** | El `.bat` funciona de forma determinista con espacios en la ruta y desde cualquier directorio de trabajo (`CWD`) | Invocación de `visualizador.bat` desde carpeta externa (`tempfile`) en `tests/test_lanzador.py` |

---

## 6. Asignación Explícita de Roles
- **Fase 1 (Triage y Planificación):** Ani Arquitecta (Tech Lead). Confección del plan, verificación de línea base y registro durable SMF.
- **Fase 2 (Ejecución Técnica Core):** Ani Programadora (Core Logic Multilenguaje). Creación de `visualizador.bat`, `tools/visualizador/__main__.py`, reescritura de documentación (`docs/COMO_USAR.md`, `docs/GUIA_DE_USO.md`, `README.md`, `RETOMAR.md`, `RUTA_DE_TRABAJO.md`) y suite `tests/test_lanzador.py`.
- **Fase 3 (QA & Verificación de Aceptación):** Ani Mal Humor (QA Lead). Auditoría empírica de los criterios 6.1 a 6.5 y certificación de cero regresiones en la suite general (169+ pruebas).

---

## 7. Lista de Cotejo Previa (8 Puntos Obligatorios)
1. **¿Alguna tarea contradice una regla escrita de un documento canónico?** No. Cumple estrictamente con `docs/RUTA_DE_TRABAJO.md` §2 y §6, `docs/MVP.md` §4 y §5, la bitácora T11 y la regla 16 (distribución fuera de alcance).
2. **¿Las herramientas, rutas, skills y comandos que nombro existen y hacen lo que digo?** Sí. `pythonw.exe`, `python.exe`, `py.exe` y `ffmpeg.exe` están verificados en disco y en PATH.
3. **¿Cubre todos los requisitos del pedido, incluidos los que una corrida anterior ya cumplía?** Sí. Cubre lanzador, diagnósticos, documentación de usuario completa, suite de pruebas automatizadas y sincronización de estado.
4. **¿Cada criterio de aceptación puede fallar (falsable)?** Sí. Si falta el `.bat`, si falla ante espacios, o si la documentación tiene comandos rotos, las pruebas fallan de forma determinista.
5. **¿Alguna tarea borra, sobrescribe o mueve algo, y si sí, está autorizado por el Capitán?** No borra nada. Reemplaza `docs/COMO_USAR.md` obsoleto según lo estipulado en la ruta de trabajo.
6. **¿Cité el documento canónico que gobierna?** Sí: `docs/RUTA_DE_TRABAJO.md` (§2 y §6), `docs/MVP.md` (§4 y §5), bitácora T11 y `docs/COLOR_EN_TRAMA.md`.
7. **¿Si el entregable corre desatendido, prevé detección de fallas, muerte silenciosa y plan de supervisión?** Sí. `visualizador.bat` incluye diagnósticos con pausa ante dependencias ausentes, y las pruebas usan timeouts para evitar cuelgues.
8. **¿El plan de validación emite veredicto definitivo en <= 48h?** Sí. La suite completa corre en menos de 2 minutos en disco local.
