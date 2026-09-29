# Handoff — Tarea 2.2: Empaquetado y Dependencias

**Ejecutora:** Ani Programadora  
**Turno:** T47  
**Fecha:** 2026-09-29  
**Estado:** ✅ COMPLETA

---

## Archivos Creados

| Archivo | Ruta | Tamaño |
|---------|------|--------|
| `requirements.txt` | `requirements.txt` (raíz) | ~120 B |
| `pyproject.toml` | `pyproject.toml` (raíz) | ~1.1 KB |

---

## Criterios de Aceptación Verificados

### CA-PUB-2: requirements.txt
- [x] Archivo existe en la raíz del repositorio.
- [x] Contiene `numpy>=1.24.0`, `pillow>=10.0.0`, `scipy>=1.10.0`.
- [x] `python -m pip install -r requirements.txt` resuelve con exit code 0 (las 3 satisfechas).

### CA-PUB-2: pyproject.toml
- [x] Nombre: `visual-audio`
- [x] Versión: `0.1.0`
- [x] Autor: `Jonatan Córdoba`
- [x] Licencia: `PolyForm-Noncommercial-1.0.0`
- [x] Entrypoint CLI: `visual-audio = "visualizador.cli:main"`
- [x] Paquetes discovery: `where = ["tools"]`
- [x] Build system: setuptools >= 68.0 (PEP 517/518)
- [x] `requires-python = ">=3.10"`
- [x] TOML parsea correctamente con `tomllib` (Python 3.11+ stdlib).

### CA-PUB-5: Ausencia de rutas locales
- [x] `grep -i "C:\\Users" requirements.txt` → 0 coincidencias.
- [x] `grep -i "C:\\Users" pyproject.toml` → 0 coincidencias.

---

## Verificación por Ejecución

```
> python -m pip install -r requirements.txt
Requirement already satisfied: numpy>=1.24.0 (2.5.1)
Requirement already satisfied: pillow>=10.0.0 (12.3.0)
Requirement already satisfied: scipy>=1.10.0 (1.18.0)
[exit code 0]

> python -c "import tomllib; ..."
name=visual-audio
version=0.1.0
license=PolyForm-Noncommercial-1.0.0
author=Jonatan Córdoba
entrypoint=visualizador.cli:main
[exit code 0]
```

---

## Notas para Tareas Downstream

1. **URLs de GitHub** en `pyproject.toml` usan placeholder `JonatanCordoba/visual-audio`. El Capitán debe confirmar el nombre real del repositorio en GitHub antes de publicar.
2. La GUI se lanza con `visualizador.bat` o `python -m visualizador` (no con el entrypoint `visual-audio` de setuptools, que requiere `pip install -e .`). El entrypoint de setuptools es para una instalación formal futura.
3. No se tocó ningún archivo de código de producto (fuera de alcance).
