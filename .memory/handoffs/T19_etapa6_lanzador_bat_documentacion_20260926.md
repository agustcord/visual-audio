# Handoff T19 — Etapa 6: Lanzador visualizador.bat, documentación de usuario y cierre del MVP

- **Fecha:** 2026-09-26
- **Turno:** T19
- **Agente:** Ani Programadora (Core Logic multilenguaje)
- **Fase del Ciclo Core:** 2 (Ejecución Técnica)
- **Rama:** `master`
- **Estado de Pruebas:** 213 comprobaciones pasando al 100% en verde con 0 fallas y 0 regresiones.

---

## 1. Resumen Ejecutivo de la Etapa 6

En este turno se implementó y completó la **Etapa 6 (Lanzador visualizador.bat, documentación de usuario y cierre del MVP)** conforme a `docs/RUTA_DE_TRABAJO.md` §4, `docs/MVP.md` §4-§5 y el plan de triage de Fase 1 `implementation_plan.md`:

1. **Lanzador de escritorio para Windows (`visualizador.bat`):**
   - Invocación de doble clic sin ventana de consola negra visible de fondo mediante `start "" "%PYTHONW_BIN%"` cuando no se pasan argumentos (modo interactivo GUI).
   - Invocación sincrónica limpia con `python.exe` / `py.exe` preservando la salida en consola cuando se pasan argumentos CLI (`%*`).
   - Anclaje determinista al directorio del script (`%~dp0`) y entrecomillado robusto para soportar rutas con espacios (`C:\Users\Jonatan Agustín\...`).
   - Configuración determinista de `PYTHONPATH` hacia la carpeta `tools/`.
   - Diagnósticos explícitos con pausa interactiva (`pause`) y retorno de código de error 1 ante ausencia de Python 3.10+ o FFmpeg en PATH.

2. **Entrypoint canónico de paquete (`tools/visualizador/__main__.py`):**
   - Permite la ejecución directa del paquete tanto con `python -m visualizador` como con `python -m visualizador.cli`.

3. **Corrección de robustez en CLI (`tools/visualizador/cli.py`):**
   - Se detectó y resolvió un fallo en el formateador de ayuda de `argparse` provocado por el carácter `%` en las unidades de parámetros (`[10 a 100 %]`), escapándolo como `%%` para prevenir `ValueError: unsupported format character ']'`.

4. **Documentación de Usuario Completa:**
   - `docs/GUIA_DE_USO.md`: Guía de usuario completa explicando el lanzamiento con `visualizador.bat`, el uso de la interfaz gráfica, presets, y la composición en Drift 0.6.0 (fusión Trama, fórmula matemática, pre-compensación de color con `compensar_fondo` y alternativa Chroma Key).
   - `docs/COMO_USAR.md`: Reescritura integral alineando el documento al producto terminado, relegando comandos CLI al apéndice y eliminando referencias obsoletas a scripts de la PoC como flujo principal.
   - `README.md`: Actualizado con el estado "MVP Completo — Etapas 1 a 6 cerradas", lanzador de escritorio y árbol del repositorio al día.
   - `RETOMAR.md`: Sincronizado marcando las etapas 1 a 6 cerradas y la preparación para la Etapa 7 (Validación con el fundador).
   - `docs/RUTA_DE_TRABAJO.md`: Tabla de estado de §1 actualizada con las Etapas 4, 5 y 6 cerradas, situando el puntero en la Etapa 7.

5. **Suite de pruebas automatizadas (`tests/test_lanzador.py`):**
   - 44 comprobaciones automatizadas cubriendo los criterios 6.1 a 6.5, diagnósticos de dependencias ausentes y entrypoint canónico.

---

## 2. Matriz de Trazabilidad de Criterios (Etapa 6)

| # | Criterio | Evidencia Observable y Método de Verificación | Estado |
|---|---|---|---|
| **6.1** | `docs/COMO_USAR.md` y `docs/GUIA_DE_USO.md` describen la aplicación real con GUI y flujo de Drift, sin pasos obsoletos | Verificado en `tests/test_lanzador.py::probar_criterio_6_1`. Ambos archivos existen, detallan `visualizador.bat`, la GUI, Trama y `compensar_fondo`, sin aconsejar `generar_overlay.py` como método principal. | ✅ CUMPLIDO |
| **6.2** | Todo comando que figure en la documentación corre tal cual está escrito con retorno exitoso | Verificado en `tests/test_lanzador.py::probar_criterio_6_2`. Se ejecutan `python -m visualizador.cli --listar`, `python -m visualizador --listar` y `python -m visualizador.cli --help`, todos retornando código 0. | ✅ CUMPLIDO |
| **6.3** | La tabla de estado de `RUTA_DE_TRABAJO.md` §1 y `RETOMAR.md` están sincronizados y al día | Verificado en `tests/test_lanzador.py::probar_criterio_6_3`. RUTA_DE_TRABAJO §1 tiene Etapas 4 (T15), 5 (T17) y 6 (T19) cerradas, y RETOMAR.md declara Etapa 7 como siguiente. | ✅ CUMPLIDO |
| **6.4** | Doble clic en `visualizador.bat` abre la ventana gráfica y no deja ventana de consola negra visible | Verificado en `tests/test_lanzador.py::probar_criterio_6_4`. Auditoría sintáctica de batch (`@echo off`, `setlocal`, `start "" "%PYTHONW_BIN%"` y `%~dp0`). | ✅ CUMPLIDO |
| **6.5** | El `.bat` funciona de forma determinista con espacios en la ruta y desde cualquier directorio de trabajo (CWD) | Verificado en `tests/test_lanzador.py::probar_criterio_6_5`. Invocación de `visualizador.bat --listar` y `--help` desde directorio temporal externo (`tempfile`), retornando código 0 con listados completos. | ✅ CUMPLIDO |
| **Extra** | Diagnósticos ante ausencia de Python o FFmpeg y entrypoint canónico | Verificado en `tests/test_lanzador.py::probar_diagnosticos_y_entrypoint`. Despojo de PATH simulado retorna código 1 y mensajes explícitos de error. | ✅ CUMPLIDO |

---

## 3. Estado de la Suite de Pruebas

Ejecución consolidada completa de los 6 módulos:
- `tests/test_analisis.py`: **36 comprobaciones** en verde.
- `tests/test_render.py --export`: **36 comprobaciones** en verde.
- `tests/verificar_sincronia.py`: **9 comprobaciones** en verde.
- `tests/test_proyecto.py`: **46 comprobaciones** en verde.
- `tests/test_gui.py`: **42 comprobaciones** en verde.
- `tests/test_lanzador.py`: **44 comprobaciones** en verde.
**TOTAL: 213 comprobaciones automáticas pasando al 100% en verde con 0 fallas y 0 regresiones.**

---

## 4. Frontera de Modificaciones

### Archivos Creados:
- `visualizador.bat` (Lanzador de escritorio para Windows)
- `tools/visualizador/__main__.py` (Entrypoint canónico del paquete)
- `docs/GUIA_DE_USO.md` (Guía de usuario paso a paso)
- `tests/test_lanzador.py` (Suite de pruebas de la Etapa 6)

### Archivos Modificados:
- `tools/visualizador/cli.py` (Escape de `%` a `%%` en texto de ayuda para `argparse`)
- `tests/test_gui.py` (Sincronización de atributo `_hilo_export` en prueba 5.4 para eliminar condición de carrera en máquinas veloces)
- `docs/COMO_USAR.md` (Reescritura completa para alinear al producto terminado con GUI y Trama)
- `README.md` (Sincronización de estado MVP, lanzador y estructura de carpetas)
- `RETOMAR.md` (Sincronización de estado: etapas 1 a 6 cerradas, puntero en Etapa 7)
- `docs/RUTA_DE_TRABAJO.md` (Actualización de tabla de estado §1 y contabilidad de turnos)

### Archivos Explícitamente NO Tocados:
- `tools/visualizador/analisis.py`
- `tools/visualizador/render.py`
- `tools/visualizador/salida.py`
- `tools/visualizador/parametros.py`
- `tools/visualizador/estilos/*`
- `tools/generar_overlay.py`
- `tests/fixtures/*`
- `C:\Program Files\Drift\*` (Solo lectura)
