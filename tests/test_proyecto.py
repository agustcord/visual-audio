#!/usr/bin/env python3
"""Pruebas de proyectos, presets y compensación de color — criterios 4.1 a 4.7 de la etapa 4.

    python tests\\test_proyecto.py

Verifica:
- 4.1: Guardar -> reabrir -> exportar da cuadros idénticos bit a bit.
- 4.2: Proyecto con versión desconocida o parámetro inválido falla claro (ErrorDeProyecto / ErrorDeParametro).
- 4.3: Los presets de fábrica cargan y producen cuadros sin excepción.
- 4.4: Proyecto con audio ausente o movido avisa con la ruta exacta faltante.
- 4.5: compensar_fondo="#000000" preserva el render idéntico bit a bit (cero píxeles de diferencia).
- 4.6: Compensación de color sobre fondo oscuro produce delta_e < 1.0 respecto al color deseado.
- 4.7: Color inalcanzable (D < B) emite advertencia explícita con el canal que satura.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
import tempfile
import warnings
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from visualizador import cli, consola, parametros, proyecto  # noqa: E402
from visualizador.analisis import analizar  # noqa: E402
from visualizador.parametros import (  # noqa: E402
    ErrorDeParametro,
    a_rgb01,
    compensar_color,
    delta_e,
    es_color_alcanzable,
    trama,
)
from visualizador.proyecto import (  # noqa: E402
    ErrorDeProyecto,
    abrir,
    abrir_preset,
    guardar,
    guardar_preset,
    listar_presets,
)
from visualizador.render import Render  # noqa: E402

consola.preparar()

PISTA = RAIZ / "tests" / "fixtures" / "pista_espectro.wav"
CHICO = {"lienzo_ancho": 480, "lienzo_alto": 270, "ancho": 480, "alto": 80, "x": 0, "y": 170}

_fallas: list[str] = []
_pasadas = 0


def afirmar(condicion: bool, titulo: str, detalle: str = "") -> None:
    global _pasadas
    if condicion:
        _pasadas += 1
        print(f"  OK    {titulo}" + (f"  ({detalle})" if detalle else ""))
    else:
        _fallas.append(titulo)
        print(f"  FALLA {titulo}" + (f"  ({detalle})" if detalle else ""))


def huella(imagen) -> str:
    return hashlib.sha256(imagen.tobytes()).hexdigest()


# --------------------------------------------------------------------------- #
# Criterios 4.1 a 4.7
# --------------------------------------------------------------------------- #

def criterio_4_1(tmp_dir: Path) -> None:
    """4.1 Guardar -> reabrir -> exportar da cuadros idénticos bit a bit."""
    print("\n4.1  Guardar -> reabrir -> exportar da cuadros idénticos")

    params_originales = {
        **CHICO,
        "color": "#FF8800",
        "color_final": "#00FFCC",
        "degradado": "altura",
        "sensibilidad": 4.5,
        "n_barras": 48,
    }

    # Render directo como referencia
    analisis_dir = analizar(PISTA, params_originales, "barras")
    render_dir = Render(analisis_dir, "barras", params_originales)
    cuadro_dir = render_dir.cuadro(120)
    hash_dir = huella(cuadro_dir)

    # Persistir en archivo de proyecto
    ruta_proy = tmp_dir / "proyecto_4_1.json"
    guardar(ruta_proy, PISTA, "barras", params_originales)
    afirmar(ruta_proy.is_file(), "archivo de proyecto creado en disco", str(ruta_proy.name))

    # Reabrir proyecto
    audio_re, estilo_re, params_re = abrir(ruta_proy)
    afirmar(audio_re.resolve() == PISTA.resolve(), "la ruta de audio coincide", str(audio_re.name))
    afirmar(estilo_re == "barras", "el estilo coincide", estilo_re)

    # Render desde proyecto reabierto
    analisis_re = analizar(audio_re, params_re, estilo_re)
    render_re = Render(analisis_re, estilo_re, params_re)
    cuadro_re = render_re.cuadro(120)
    hash_re = huella(cuadro_re)

    afirmar(hash_dir == hash_re, "cuadro reabierto idéntico bit a bit al directo",
            f"SHA {hash_dir[:12]}")
    afirmar(np.array_equal(np.asarray(cuadro_dir), np.asarray(cuadro_re)),
            "comparación de arreglos RGBA: cero diferencias")


def criterio_4_2(tmp_dir: Path) -> None:
    """4.2 Proyecto con versión desconocida o valor inválido falla con mensaje claro."""
    print("\n4.2  Validación estricta de versión y parámetros en proyecto")

    # 1. Versión no soportada
    ruta_v2 = tmp_dir / "proy_v2.json"
    with open(ruta_v2, "w", encoding="utf-8") as f:
        json.dump({"version": 2, "audio": str(PISTA), "estilo": "barras", "params": {}}, f)

    try:
        abrir(ruta_v2)
        afirmar(False, "abrir versión 2 debe fallar con ErrorDeProyecto")
    except ErrorDeProyecto as e:
        afirmar("versión" in str(e).lower(), "versión no soportada levanta ErrorDeProyecto", str(e))
    except Exception as e:  # noqa: BLE001
        afirmar(False, "abrir versión 2 falló con tipo inesperado", f"{type(e).__name__}: {e}")

    # 2. JSON mal formado
    ruta_corrupta = tmp_dir / "proy_corrupto.json"
    with open(ruta_corrupta, "w", encoding="utf-8") as f:
        f.write("{ version: 1, audio: corrupto")

    try:
        abrir(ruta_corrupta)
        afirmar(False, "JSON corrupto debe fallar con ErrorDeProyecto")
    except ErrorDeProyecto as e:
        afirmar("mal formado" in str(e).lower() or "json" in str(e).lower(),
                "JSON corrupto levanta ErrorDeProyecto explicativo", str(e))
    except Exception as e:  # noqa: BLE001
        afirmar(False, "JSON corrupto falló con tipo inesperado", f"{type(e).__name__}: {e}")

    # 3. Parámetro fuera de rango o inválido
    ruta_invalido = tmp_dir / "proy_invalido.json"
    with open(ruta_invalido, "w", encoding="utf-8") as f:
        json.dump({
            "version": 1,
            "audio": str(PISTA),
            "estilo": "barras",
            "params": {"sensibilidad": 999.0},
        }, f)

    try:
        abrir(ruta_invalido)
        afirmar(False, "parámetro inválido debe fallar con ErrorDeParametro")
    except ErrorDeParametro as e:
        afirmar("máximo" in str(e).lower() or "sensibilidad" in str(e).lower(),
                "parámetro inválido levanta ErrorDeParametro explicativo", str(e))
    except Exception as e:  # noqa: BLE001
        afirmar(False, "parámetro inválido falló con tipo inesperado", f"{type(e).__name__}: {e}")

    # 4. Campo obligatorio faltante
    ruta_sin_audio = tmp_dir / "proy_sin_audio.json"
    with open(ruta_sin_audio, "w", encoding="utf-8") as f:
        json.dump({"version": 1, "estilo": "barras", "params": {}}, f)

    try:
        abrir(ruta_sin_audio)
        afirmar(False, "falta de campo audio debe fallar con ErrorDeProyecto")
    except ErrorDeProyecto as e:
        afirmar("audio" in str(e).lower(), "campo obligatorio faltante levanta ErrorDeProyecto", str(e))


def criterio_4_3() -> None:
    """4.3 Los presets de fábrica cargan y exportan."""
    print("\n4.3  Presets de fábrica cargan y exportan")

    presets = listar_presets()
    esperados = ["barras_blancas", "barras_neon", "espejadas_frecuencia", "onda_suave"]

    afirmar(len(presets) >= 4, "al menos 4 presets disponibles", f"{len(presets)} presets encontrados")
    for nombre in esperados:
        afirmar(nombre in presets, f"preset de fábrica '{nombre}' existe en presets/")

        # Abrir y validar
        estilo, p = abrir_preset(nombre)
        afirmar(bool(estilo and p), f"'{nombre}' carga con estilo '{estilo}' y parámetros válidos")

        # Renderizar un cuadro de prueba
        p_chico = {**p, **CHICO}
        analisis = analizar(PISTA, p_chico, estilo)
        render = Render(analisis, estilo, p_chico)
        cuadro = render.cuadro(100)
        afirmar(cuadro.size == (480, 270), f"'{nombre}' renderiza cuadro (480x270) sin fallar")


def criterio_4_4(tmp_dir: Path) -> None:
    """4.4 Proyecto con audio movido o ausente avisa qué falta."""
    print("\n4.4  Proyecto con audio ausente reporta ruta faltante")

    nombre_fantasma = "audio_inexistente_de_prueba_404.wav"
    ruta_fantasma = tmp_dir / nombre_fantasma
    ruta_proy = tmp_dir / "proy_fantasma.json"

    with open(ruta_proy, "w", encoding="utf-8") as f:
        json.dump({
            "version": 1,
            "audio": str(ruta_fantasma),
            "estilo": "barras",
            "params": {},
        }, f)

    try:
        abrir(ruta_proy)
        afirmar(False, "audio inexistente debe fallar con ErrorDeProyecto")
    except ErrorDeProyecto as e:
        msg = str(e)
        afirmar(nombre_fantasma in msg,
                "el mensaje de error reporta la ruta del audio faltante", msg)
    except Exception as e:  # noqa: BLE001
        afirmar(False, "audio inexistente falló con tipo inesperado", f"{type(e).__name__}: {e}")


def criterio_4_5() -> None:
    """4.5 compensar_fondo='#000000' no altera ni un píxel."""
    print("\n4.5  Inocuidad del compensar_fondo default (#000000)")

    # Cuadro sin especificar compensar_fondo
    p_def = dict(CHICO)
    r_def = Render(analizar(PISTA, p_def, "barras"), "barras", p_def)
    cuadro_def = r_def.cuadro(200)

    # Cuadro con compensar_fondo="#000000" explícito
    p_comp0 = dict(CHICO, compensar_fondo="#000000")
    r_comp0 = Render(analizar(PISTA, p_comp0, "barras"), "barras", p_comp0)
    cuadro_comp0 = r_comp0.cuadro(200)

    arr_def = np.asarray(cuadro_def, dtype=np.int32)
    arr_comp0 = np.asarray(cuadro_comp0, dtype=np.int32)
    diff = np.abs(arr_def - arr_comp0)

    afirmar(int(diff.max()) == 0,
            "compensar_fondo='#000000' coincide al 100% (cero píxeles con diferencia)",
            f"diferencia máxima = {diff.max()}")
    afirmar(huella(cuadro_def) == huella(cuadro_comp0),
            "hash SHA-256 idéntico entre default implícito y explícito")


def criterio_4_6() -> None:
    """4.6 Compensado sobre fondo oscuro da ΔE < 1 contra el pedido."""
    print("\n4.6  Fidelidad colorimétrica sobre fondos oscuros (ΔE < 1.0)")

    casos = [
        ("#141414", "#22D3EE", "casi negro + celeste"),
        ("#141414", "#FFC83C", "casi negro + amarillo"),
        ("#101C38", "#22D3EE", "azul nocturno + celeste"),
        ("#101C38", "#FFFFFF", "azul nocturno + blanco"),
    ]

    for fondo_hex, deseado_hex, etiqueta in casos:
        comp_hex, alcanzable = compensar_color(deseado_hex, fondo_hex)
        afirmar(alcanzable, f"{etiqueta}: alcanzable sin recorte")

        # Fusión Trama Drift de fondo con color compensado
        resultado = trama(a_rgb01(fondo_hex), a_rgb01(comp_hex))
        de = delta_e(a_rgb01(deseado_hex), resultado)

        afirmar(de < 1.0, f"{etiqueta}: ΔE < 1.0 (imperceptible)",
                f"deseado={deseado_hex} comp={comp_hex} ΔE={de:.4f}")


def criterio_4_7() -> None:
    """4.7 Color inalcanzable (D < B en algún canal) avisa, no recorta en silencio."""
    print("\n4.7  Detección y aviso explícito ante color inalcanzable")

    # Gris medio (#808080 = 128,128,128) con celeste (#22D3EE: R=34, G=211, B=238)
    # R: deseado 34 < fondo 128 -> D < B (imposible oscurecer con Trama)
    fondo_claro = "#808080"
    color_oscuro = "#22D3EE"

    afirmar(not es_color_alcanzable(color_oscuro, fondo_claro),
            "es_color_alcanzable identifica correctamente D < B como False")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        comp_hex, alcanzable = compensar_color(color_oscuro, fondo_claro)

        afirmar(not alcanzable, "compensar_color retorna alcanzable=False")
        afirmar(len(w) >= 1, "emite advertencia explícita en warnings", f"{len(w)} warnings")

        if w:
            aviso = str(w[0].message)
            afirmar("R" in aviso and "no es alcanzable" in aviso.lower(),
                    "la advertencia menciona el canal saturado (R)", aviso)

    # Verificar que Render también avisa ante color inalcanzable
    with warnings.catch_warnings(record=True) as w_render:
        warnings.simplefilter("always")
        p_inval = dict(CHICO, color=color_oscuro, compensar_fondo=fondo_claro)
        r_inval = Render(analizar(PISTA, p_inval, "barras"), "barras", p_inval)
        _ = r_inval.cuadro(10)
        afirmar(len(w_render) >= 1, "Render emite advertencia ante compensar_fondo inalcanzable")


def pruebas_cli(tmp_dir: Path) -> None:
    """Verifica integración CLI: --proyecto, --guardar-proyecto, --preset, --guardar-preset."""
    print("\nExtra  Integración con interfaz CLI")

    # 1. Guardar preset desde CLI
    ruta_preset = tmp_dir / "cli_preset.json"
    codigo = cli.main(["--guardar-preset", str(ruta_preset), "--color", "#112233", "--estilo", "onda"])
    afirmar(codigo == 0, "--guardar-preset termina con éxito (código 0)")
    afirmar(ruta_preset.is_file(), "archivo de preset generado por CLI")
    est_pre, p_pre = abrir_preset(ruta_preset)
    afirmar(est_pre == "onda" and p_pre["color"] == "#112233",
            "preset generado contiene los valores especificados")

    # 2. Guardar proyecto desde CLI
    ruta_proy = tmp_dir / "cli_proy.json"
    codigo_proy = cli.main([
        str(PISTA),
        "--guardar-proyecto", str(ruta_proy),
        "--estilo", "espejadas",
        "--sensibilidad", "4.0",
    ])
    afirmar(codigo_proy == 0, "--guardar-proyecto termina con éxito (código 0)")
    afirmar(ruta_proy.is_file(), "archivo de proyecto generado por CLI")
    aud_p, est_p, p_p = abrir(ruta_proy)
    afirmar(est_p == "espejadas" and p_p["sensibilidad"] == 4.0,
            "proyecto generado contiene estilo y parámetros correctos")

    # 3. Previsualizar cuadro usando --proyecto
    salida_png = tmp_dir / "cli_preview.png"
    codigo_prev = cli.main([
        "--proyecto", str(ruta_proy),
        "--cuadro", "50",
        "-o", str(salida_png),
    ])
    afirmar(codigo_prev == 0, "--proyecto con --cuadro produce vista previa exitosa")
    afirmar(salida_png.is_file(), "cuadro PNG generado desde --proyecto")


def main() -> int:
    print("Pruebas de Proyectos, Presets y Compensación de Color (Etapa 4)")
    print(f"  pista   : {PISTA.name}")
    print(f"  presets : {listar_presets()}\n")

    tmp_dir = Path(tempfile.mkdtemp(prefix="drift_test_etapa4_"))
    try:
        criterio_4_1(tmp_dir)
        criterio_4_2(tmp_dir)
        criterio_4_3()
        criterio_4_4(tmp_dir)
        criterio_4_5()
        criterio_4_6()
        criterio_4_7()
        pruebas_cli(tmp_dir)
    finally:
        shutil.rmtree(tmp_dir, ignore_errors=True)

    print(f"\n{_pasadas} comprobaciones pasadas, {len(_fallas)} fallas\n")
    if _fallas:
        print("Fallas:")
        for f in _fallas:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
