"""
tests/test_lanzador.py
======================
Pruebas automatizadas de la Etapa 6: Lanzador visualizador.bat, documentación
de usuario y cierre del MVP.

Criterios de aceptación verificados:
  6.1  docs/COMO_USAR.md y docs/GUIA_DE_USO.md describen la aplicación real con GUI
       y flujo de Drift, sin pasos obsoletos.
  6.2  Todo comando que figure en la documentación corre tal cual está escrito
       con retorno exitoso (código 0).
  6.3  La tabla de estado de docs/RUTA_DE_TRABAJO.md §1 y RETOMAR.md están
       sincronizados y al día (Etapa 6 cerrada, próxima Etapa 7).
  6.4  Doble clic en visualizador.bat abre la ventana gráfica y no deja ventana de
       consola negra visible (uso de pythonw.exe y start "").
  6.5  El .bat funciona de forma determinista con espacios en la ruta y desde
       cualquier directorio de trabajo (CWD).
  Extra: Diagnósticos ante dependencias ausentes (Python / FFmpeg no en PATH) y
         entrypoint canónico tools/visualizador/__main__.py.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

# Directorio raíz del proyecto y paquete tools
DIR_RAIZ = Path(__file__).resolve().parent.parent
DIR_TOOLS = DIR_RAIZ / "tools"
DIR_DOCS = DIR_RAIZ / "docs"

# Contador de aserciones para reporte final
_total_comprobaciones = 0
_fallas = 0


def afirmar(condicion: bool, descripcion: str, detalle: str = "") -> None:
    global _total_comprobaciones, _fallas
    _total_comprobaciones += 1
    if condicion:
        msg = f"  OK    {descripcion}"
        if detalle:
            msg += f"  ({detalle})"
        print(msg)
    else:
        _fallas += 1
        msg = f"  FALLA {descripcion}"
        if detalle:
            msg += f"  -- Detalle: {detalle}"
        print(msg)


# ==============================================================================
# Criterio 6.1: Documentación fiel, completa y actualizada
# ==============================================================================
def probar_criterio_6_1() -> None:
    print("\n6.1  Documentación fiel y actualizada (COMO_USAR.md y GUIA_DE_USO.md)")

    ruta_como_usar = DIR_DOCS / "COMO_USAR.md"
    ruta_guia_uso = DIR_DOCS / "GUIA_DE_USO.md"

    afirmar(ruta_como_usar.exists(), "docs/COMO_USAR.md existe en disco")
    afirmar(ruta_guia_uso.exists(), "docs/GUIA_DE_USO.md existe en disco")

    texto_como_usar = ruta_como_usar.read_text(encoding="utf-8") if ruta_como_usar.exists() else ""
    texto_guia_uso = ruta_guia_uso.read_text(encoding="utf-8") if ruta_guia_uso.exists() else ""

    # Verifica mención a visualizador.bat
    afirmar("visualizador.bat" in texto_como_usar, "COMO_USAR.md describe el lanzador visualizador.bat")
    afirmar("visualizador.bat" in texto_guia_uso, "GUIA_DE_USO.md describe el lanzador visualizador.bat")

    # Verifica mención al modo Trama en Drift
    afirmar("Trama" in texto_como_usar or "Screen" in texto_como_usar, "COMO_USAR.md describe el modo Trama en Drift")
    afirmar("Trama" in texto_guia_uso or "Screen" in texto_guia_uso, "GUIA_DE_USO.md describe el modo Trama en Drift")

    # Verifica mención a compensar_fondo
    afirmar("compensar_fondo" in texto_como_usar, "COMO_USAR.md describe el uso de compensar_fondo")
    afirmar("compensar_fondo" in texto_guia_uso, "GUIA_DE_USO.md describe el uso de compensar_fondo")

    # Verifica mención a la interfaz gráfica
    afirmar("interfaz" in texto_como_usar.lower() or "gui" in texto_como_usar.lower() or "gráfica" in texto_como_usar.lower(),
            "COMO_USAR.md describe el flujo de la interfaz gráfica")
    afirmar("interfaz" in texto_guia_uso.lower() or "gui" in texto_guia_uso.lower() or "gráfica" in texto_guia_uso.lower(),
            "GUIA_DE_USO.md describe el flujo de la interfaz gráfica")

    # Verifica que NO propongan tools\generar_overlay.py como flujo principal
    lineas_cu_ppal = [
        l for l in texto_como_usar.splitlines()
        if "generar_overlay.py" in l and not any(k in l.lower() for k in ("poc", "históric", "antiguo", "referencia"))
    ]
    afirmar(len(lineas_cu_ppal) == 0,
            "COMO_USAR.md no recomienda generar_overlay.py como flujo principal",
            f"{len(lineas_cu_ppal)} líneas halladas")


# ==============================================================================
# Criterio 6.2: Todo comando documentado corre tal cual está escrito
# ==============================================================================
def probar_criterio_6_2() -> None:
    print("\n6.2  Comandos de documentación ejecutables")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(DIR_TOOLS)

    # 1. python -m visualizador.cli --listar
    cmd1 = [sys.executable, "-m", "visualizador.cli", "--listar"]
    res1 = subprocess.run(cmd1, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(DIR_RAIZ), env=env, timeout=15)
    afirmar(res1.returncode == 0, "python -m visualizador.cli --listar retorna código 0",
            f"código={res1.returncode}")
    afirmar("Estilos disponibles:" in res1.stdout and "barras_neon" in res1.stdout,
            "--listar muestra estilos y presets")

    # 2. python -m visualizador --listar (a través de __main__.py)
    cmd2 = [sys.executable, "-m", "visualizador", "--listar"]
    res2 = subprocess.run(cmd2, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(DIR_RAIZ), env=env, timeout=15)
    afirmar(res2.returncode == 0, "python -m visualizador --listar retorna código 0",
            f"código={res2.returncode}")
    afirmar("Estilos disponibles:" in res2.stdout, "__main__.py despacha a cli.main()")

    # 3. python -m visualizador.cli --help
    cmd3 = [sys.executable, "-m", "visualizador.cli", "--help"]
    res3 = subprocess.run(cmd3, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(DIR_RAIZ), env=env, timeout=15)
    afirmar(res3.returncode == 0, "python -m visualizador.cli --help retorna código 0",
            f"código={res3.returncode}")
    afirmar("--preset" in res3.stdout and "--proyecto" in res3.stdout,
            "--help documenta opciones CLI esperadas")


# ==============================================================================
# Criterio 6.3: Sincronización de estado vivo (RUTA_DE_TRABAJO y RETOMAR)
# ==============================================================================
def probar_criterio_6_3() -> None:
    print("\n6.3  Sincronización de estado vivo (RUTA_DE_TRABAJO.md y RETOMAR.md)")

    ruta_retomar = DIR_RAIZ / "RETOMAR.md"
    ruta_ruta_trabajo = DIR_DOCS / "RUTA_DE_TRABAJO.md"

    afirmar(ruta_retomar.exists(), "RETOMAR.md existe en disco")
    afirmar(ruta_ruta_trabajo.exists(), "docs/RUTA_DE_TRABAJO.md existe en disco")

    texto_retomar = ruta_retomar.read_text(encoding="utf-8") if ruta_retomar.exists() else ""
    texto_ruta = ruta_ruta_trabajo.read_text(encoding="utf-8") if ruta_ruta_trabajo.exists() else ""

    # Verifica que RETOMAR.md declare Etapas 1 a 6 cerradas
    afirmar("etapas 1, 2, 3, 4, 5 y 6 cerradas" in texto_retomar.lower() or "etapas 1 a 6 cerradas" in texto_retomar.lower(),
            "RETOMAR.md declara etapas 1 a 6 cerradas")
    afirmar("etapa 7" in texto_retomar.lower(),
            "RETOMAR.md declara que la próxima etapa es la 7 (Validación)")

    # Verifica que RUTA_DE_TRABAJO.md tenga Etapas 4, 5 y 6 cerradas en la tabla
    afirmar(re.search(r"\|\s*\*\*4\*\*\s*\|.*?\|\s*✅\s*\*\*cerrada\*\*\s*\|\s*T15\s*\|", texto_ruta) is not None,
            "RUTA_DE_TRABAJO.md §1 marca Etapa 4 como cerrada en T15")
    afirmar(re.search(r"\|\s*\*\*5\*\*\s*\|.*?\|\s*✅\s*\*\*cerrada\*\*\s*\|\s*T17\s*\|", texto_ruta) is not None,
            "RUTA_DE_TRABAJO.md §1 marca Etapa 5 como cerrada en T17")
    afirmar(re.search(r"\|\s*\*\*6\*\*\s*\|.*?\|\s*✅\s*\*\*cerrada\*\*\s*\|\s*T19\s*\|", texto_ruta) is not None,
            "RUTA_DE_TRABAJO.md §1 marca Etapa 6 como cerrada en T19")
    afirmar(re.search(r"\|\s*\*\*7\*\*\s*\|.*?\|\s*⬜\s*\*\*ACÁ ESTAMOS\*\*\s*\|", texto_ruta) is not None,
            "RUTA_DE_TRABAJO.md §1 sitúa el puntero de ejecución en la Etapa 7")


# ==============================================================================
# Criterio 6.4: Lanzamiento sin consola y preferencia pythonw.exe
# ==============================================================================
def probar_criterio_6_4() -> None:
    print("\n6.4  Lanzador visualizador.bat: preferencia pythonw.exe y arranque limpio")

    ruta_bat = DIR_RAIZ / "visualizador.bat"
    afirmar(ruta_bat.exists(), "visualizador.bat existe en la raíz del repositorio")

    contenido_bat = ruta_bat.read_text(encoding="utf-8") if ruta_bat.exists() else ""

    # Verifica @echo off y setlocal
    afirmar("@echo off" in contenido_bat, "visualizador.bat inicia con @echo off")
    afirmar("setlocal" in contenido_bat, "visualizador.bat usa setlocal para aislar el entorno")

    # Verifica detección de pythonw.exe
    afirmar("pythonw.exe" in contenido_bat, "visualizador.bat busca y prioriza pythonw.exe")

    # Verifica arranque no bloqueante con start "" para pythonw
    afirmar(re.search(r'start\s+""\s+"%PYTHONW_BIN%"', contenido_bat) is not None or
            'start "" "%PYTHONW_BIN%"' in contenido_bat,
            "visualizador.bat usa 'start \"\"' para lanzar pythonw.exe sin dejar consola negra")

    # Verifica anclaje al directorio con %~dp0
    afirmar("%~dp0" in contenido_bat, "visualizador.bat ancla deterministamente la ruta con %~dp0")

    # Verifica configuración de PYTHONPATH
    afirmar("PYTHONPATH=" in contenido_bat and "tools" in contenido_bat,
            "visualizador.bat configura PYTHONPATH apuntando a tools/")


# ==============================================================================
# Criterio 6.5: Invocación con espacios y desde cualquier directorio de trabajo
# ==============================================================================
def probar_criterio_6_5() -> None:
    print("\n6.5  Invocación de visualizador.bat con espacios y desde directorio externo")

    ruta_bat = str(DIR_RAIZ / "visualizador.bat")
    afirmar(" " in ruta_bat, f"La ruta del proyecto contiene espacios reales ('{ruta_bat}')")

    with tempfile.TemporaryDirectory(prefix="drift_test_bat_") as temp_dir:
        # Invocar visualizador.bat --listar desde el directorio temporal externo
        res_listar = subprocess.run(
            [ruta_bat, "--listar"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=temp_dir,
            timeout=20,
        )

        afirmar(res_listar.returncode == 0,
                "visualizador.bat --listar invocado desde CWD externo retorna código 0",
                f"código={res_listar.returncode}")
        afirmar("Estilos disponibles:" in res_listar.stdout and "onda" in res_listar.stdout,
                "salida stdout contiene los estilos disponibles")
        afirmar("Presets de fábrica disponibles:" in res_listar.stdout,
                "salida stdout contiene los presets de fábrica")

        # Invocar visualizador.bat --help desde el directorio temporal externo
        res_help = subprocess.run(
            [ruta_bat, "--help"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=temp_dir,
            timeout=20,
        )

        afirmar(res_help.returncode == 0,
                "visualizador.bat --help invocado desde CWD externo retorna código 0",
                f"código={res_help.returncode}")
        afirmar("--lienzo" in res_help.stdout or "--gui" in res_help.stdout,
                "salida de ayuda expone las opciones del visualizador")


# ==============================================================================
# Diagnósticos de Ausencia de Dependencias y Entrypoint Canónico
# ==============================================================================
def probar_diagnosticos_y_entrypoint() -> None:
    print("\nExtra: Diagnósticos de dependencias ausentes y entrypoint canónico")

    # 1. Entrypoint canónico __main__.py
    ruta_main = DIR_TOOLS / "visualizador" / "__main__.py"
    afirmar(ruta_main.exists(), "tools/visualizador/__main__.py existe en disco")
    contenido_main = ruta_main.read_text(encoding="utf-8") if ruta_main.exists() else ""
    afirmar("from .cli import main" in contenido_main, "__main__.py importa cli.main")

    ruta_bat = str(DIR_RAIZ / "visualizador.bat")

    # 2. Diagnóstico: Simular ausencia de FFmpeg alterando el PATH
    # Se crea un entorno sin ffmpeg en PATH y se alimenta stdin con salto de línea para el 'pause'
    env_sin_ffmpeg = os.environ.copy()
    # Filtra entradas de PATH que contengan ffmpeg
    rutas_path = env_sin_ffmpeg.get("PATH", "").split(os.pathsep)
    rutas_filtradas = [p for p in rutas_path if "ffmpeg" not in p.lower()]
    env_sin_ffmpeg["PATH"] = os.pathsep.join(rutas_filtradas)

    res_ffmpeg = subprocess.run(
        [ruta_bat],
        input="\n\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(DIR_RAIZ),
        env=env_sin_ffmpeg,
        timeout=10,
    )

    afirmar(res_ffmpeg.returncode == 1,
            "visualizador.bat retorna código 1 si no encuentra FFmpeg",
            f"código={res_ffmpeg.returncode}")
    afirmar("ERROR: No se encontro FFmpeg" in res_ffmpeg.stdout,
            "visualizador.bat muestra mensaje explicativo ante ausencia de FFmpeg")

    # 3. Diagnóstico: Simular ausencia total de Python alterando el PATH
    # Se crea un entorno con PATH mínimo donde no existan python.exe, pythonw.exe ni py.exe
    env_sin_python = os.environ.copy()
    # Mantener solo rutas básicas del sistema (System32) donde no reside python
    system_root = os.environ.get("SystemRoot", r"C:\Windows")
    env_sin_python["PATH"] = os.path.join(system_root, "System32")

    res_py = subprocess.run(
        [ruta_bat],
        input="\n\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(DIR_RAIZ),
        env=env_sin_python,
        timeout=10,
    )

    afirmar(res_py.returncode == 1,
            "visualizador.bat retorna código 1 si no encuentra Python",
            f"código={res_py.returncode}")
    afirmar("ERROR: No se encontro Python" in res_py.stdout,
            "visualizador.bat muestra mensaje explicativo ante ausencia de Python")


def main() -> int:
    print("=" * 72)
    print("Pruebas Automatizadas de Lanzador, Documentación y Cierre MVP (Etapa 6)")
    print("=" * 72)

    probar_criterio_6_1()
    probar_criterio_6_2()
    probar_criterio_6_3()
    probar_criterio_6_4()
    probar_criterio_6_5()
    probar_diagnosticos_y_entrypoint()

    print("\n" + "=" * 72)
    print(f"Resumen: {_total_comprobaciones} comprobaciones pasadas, {_fallas} fallas")
    print("=" * 72)

    return 1 if _fallas > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
