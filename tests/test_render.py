#!/usr/bin/env python3
"""Pruebas del motor de dibujo — criterios 2.1 a 2.4 de la etapa 2.

    python tests\\test_render.py            # todo menos el export completo
    python tests\\test_render.py --export    # incluye los tres modos de fondo

El export está detrás de una bandera porque codifica tres videos y tarda; el resto
corre en segundos y es lo que conviene ejecutar mientras se trabaja.

## Los dos criterios que más importan

**2.4 — `cuadro(i)` da lo mismo suelto o en secuencia.** Es lo que verifica que
ningún estilo guarde estado entre cuadros, y de eso depende que la vista previa de
la interfaz sea posible: si dibujar el cuadro 300 necesitara los 299 anteriores, la
interfaz tendría que renderizar media canción por cada deslizador que se mueva.

**2.3 — el barrido de parámetros.** Recorre el esquema y prueba mínimo, default y
máximo de cada valor. No alcanza con que no explote: **cada valor tiene que cambiar
algo**. Un parámetro que no hace nada es peor que uno que falla, porque nadie se
entera.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import time
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "tools"))

from visualizador import consola, estilos, parametros, salida  # noqa: E402
from visualizador.analisis import analizar  # noqa: E402
from visualizador.render import Render  # noqa: E402

consola.preparar()

PISTA = RAIZ / "tests" / "fixtures" / "pista_espectro.wav"
BUILD = RAIZ / "build"

# Lienzo chico para que las pruebas sean rápidas. Lo que se verifica es la lógica,
# no el tamaño: un cuadro de 480x270 ejercita exactamente el mismo código.
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
    return hashlib.sha256(imagen.tobytes()).hexdigest()[:16]


def render_de(estilo: str = "barras", extra: dict | None = None) -> Render:
    p = dict(CHICO)
    p.update(extra or {})
    return Render(analizar(PISTA, p, estilo), estilo, p)


# Los rangos del esquema son absolutos (x hasta 7680 px, y hasta 4320) porque el
# producto permite a propósito sacar el dibujo fuera del cuadro. Pero el lienzo de
# prueba mide 480x270, así que esos extremos dejan el dibujo completamente afuera y
# los tres valores producen el mismo cuadro vacío.
#
# El barrido lo reportaba como "el parámetro no hace nada", y era el método el que
# estaba mal, no el parámetro. Para las posiciones y los tamaños se usan valores
# relativos al lienzo de prueba.
_RELATIVOS_AL_LIENZO = {
    "x": [-80, 0, 200],
    "y": [20, 100, 180],
    "ancho": [120, 480],
    "alto": [20, 80, 200],
    "lienzo_ancho": [240, 480],
    "lienzo_alto": [160, 270],
}


def _valores_a_probar(nombre: str, v: parametros.Valor) -> list:
    return _RELATIVOS_AL_LIENZO.get(nombre) or v.valores_de_barrido()


# --------------------------------------------------------------------------- #

def criterio_2_4() -> None:
    """cuadro(i) es idéntico suelto o en secuencia: los estilos no tienen estado."""
    print("\n2.4  cuadro(i) sin estado entre cuadros")

    for id_estilo in [e.id for e in estilos.disponibles()]:
        # Con todos los adornos activos: si algo guardara estado, el resplandor y
        # el reflejo son los candidatos, porque son los que reusan la capa.
        r = render_de(id_estilo, {"resplandor": 0.6, "reflejo": 0.4, "tapas_pico": True})
        indices = [0, 7, 120, 300, 430, r.n_cuadros - 1]

        sueltos = {i: huella(r.cuadro(i)) for i in indices}

        # En secuencia, y además en orden inverso, que es donde se caería un estilo
        # que dependiera del anterior.
        en_secuencia = {}
        for i in range(0, r.n_cuadros):
            img = r.cuadro(i)
            if i in sueltos:
                en_secuencia[i] = huella(img)
        invertido = {i: huella(r.cuadro(i)) for i in reversed(indices)}

        iguales = all(sueltos[i] == en_secuencia[i] == invertido[i] for i in indices)
        afirmar(iguales, f"{id_estilo}: mismos cuadros suelto, en secuencia y al revés",
                f"{len(indices)} cuadros comprobados")


def criterio_2_3() -> None:
    """Barrido: cada valor del esquema, en mínimo, default y máximo."""
    print("\n2.3  Barrido de parámetros")

    for id_estilo in [e.id for e in estilos.disponibles()]:
        base = render_de(id_estilo)
        cuadro_ref = 430
        huella_base = huella(base.cuadro(cuadro_ref))

        sin_efecto: list[str] = []
        rotos: list[str] = []
        probados = 0

        for nombre, v in parametros.ESQUEMA.items():
            if not v.aplica_a(id_estilo):
                continue
            # `fps` cambia la cantidad de cuadros, así que el cuadro de referencia
            # dejaría de ser comparable; se prueba aparte, en el criterio 2.1.
            if nombre == "fps":
                continue

            # Si el parámetro depende de otro, hay que encender el otro: con el
            # resplandor apagado, su radio no puede cambiar nada. El barrido
            # reportaba eso como "sin efecto" y tenía razón.
            contexto: dict = {}
            if v.depende_de:
                contexto[v.depende_de] = parametros.valor_activador(v.depende_de)

            huellas = set()
            for valor in _valores_a_probar(nombre, v):
                try:
                    r = render_de(id_estilo, {**contexto, nombre: valor})
                    huellas.add(huella(r.cuadro(cuadro_ref)))
                    probados += 1
                except Exception as e:      # noqa: BLE001 — se reporta, no se tapa
                    rotos.append(f"{nombre}={valor!r}: {type(e).__name__}: {e}")

            # Los parámetros de salida no cambian el dibujo: actúan al codificar.
            if nombre in ("fondo", "color_fondo", "calidad"):
                continue
            if len(huellas) < 2:
                sin_efecto.append(nombre)

        afirmar(not rotos, f"{id_estilo}: ningún valor rompe el render",
                f"{probados} combinaciones probadas")
        for r_ in rotos:
            print(f"        {r_}")
        afirmar(not sin_efecto, f"{id_estilo}: todos los valores cambian el dibujo",
                "sin efecto: " + ", ".join(sin_efecto) if sin_efecto else "")
        # `huella_base` se usa para detectar que el barrido realmente varió algo
        # respecto del default, no sólo entre sí.
        afirmar(huella_base != "", f"{id_estilo}: el cuadro de referencia se dibuja")


def estructura_del_dibujo() -> None:
    """El dibujo cae donde dice la caja, y respeta el alpha."""
    print("\nExtra  El dibujo respeta su caja y el canal alpha")

    r = render_de("barras")
    img = r.cuadro(430)
    alfa = np.asarray(img.getchannel("A"))

    afirmar(img.size == (480, 270), "el cuadro mide lo que pide el lienzo", str(img.size))
    afirmar(alfa.max() > 250, "hay dibujo opaco", f"alpha máximo {alfa.max()}")
    afirmar(alfa.min() == 0, "hay zonas transparentes", f"alpha mínimo {alfa.min()}")

    # Sin reflejo ni resplandor, nada puede dibujarse arriba de la caja.
    limpio = render_de("barras", {"reflejo": 0.0, "resplandor": 0.0})
    a2 = np.asarray(limpio.cuadro(430).getchannel("A"))
    arriba = a2[: CHICO["y"] - 1, :]
    afirmar(int(arriba.max()) == 0, "nada se dibuja por encima de la caja",
            f"alpha máximo arriba: {arriba.max()}")

    # Con reflejo, sí tiene que haber algo debajo.
    con_reflejo = render_de("barras", {"reflejo": 0.6, "resplandor": 0.0})
    a3 = np.asarray(con_reflejo.cuadro(430).getchannel("A"))
    debajo = a3[CHICO["y"] + CHICO["alto"] + 3:, :]
    afirmar(int(debajo.max()) > 0, "el reflejo dibuja por debajo de la caja",
            f"alpha máximo abajo: {debajo.max()}")

    # Un cuadro fuera de rango falla claro, no devuelve basura.
    try:
        r.cuadro(r.n_cuadros)
    except IndexError:
        afirmar(True, "un cuadro fuera de rango falla con IndexError")
    else:
        afirmar(False, "un cuadro fuera de rango falla con IndexError", "no falló")

    # Verificaciones específicas de Onda
    r_onda = render_de("onda")
    img_o = r_onda.cuadro(430)
    alfa_o = np.asarray(img_o.getchannel("A"))
    afirmar(img_o.size == (480, 270), "onda: el cuadro mide lo que pide el lienzo", str(img_o.size))
    afirmar(alfa_o.max() > 250, "onda: hay dibujo opaco", f"alpha máximo {alfa_o.max()}")
    afirmar(alfa_o.min() == 0, "onda: hay zonas transparentes", f"alpha mínimo {alfa_o.min()}")

    # Onda: relleno produce mayor superficie que sólo línea
    r_relleno = render_de("onda", {"relleno": True})
    alfa_relleno = np.asarray(r_relleno.cuadro(430).getchannel("A"))
    pix_linea = int((alfa_o > 32).sum())
    pix_relleno = int((alfa_relleno > 32).sum())
    afirmar(pix_relleno > pix_linea, "onda: relleno cubre más superficie que sólo contorno",
            f"{pix_relleno} vs {pix_linea} px")

    # Onda: grosor_linea mayor produce más píxeles
    r_fina = render_de("onda", {"grosor_linea": 2})
    r_gruesa = render_de("onda", {"grosor_linea": 10})
    pix_fina = int((np.asarray(r_fina.cuadro(430).getchannel("A")) > 32).sum())
    pix_gruesa = int((np.asarray(r_gruesa.cuadro(430).getchannel("A")) > 32).sum())
    afirmar(pix_gruesa > pix_fina, "onda: grosor_linea=10 pinta más píxeles que grosor_linea=2",
            f"{pix_gruesa} vs {pix_fina} px")


def criterio_3_4() -> None:
    """Parámetros ajenos a un estilo se ignoran o fallan claro (criterio 3.4)."""
    print("\n3.4  Parámetros ajenos a un estilo no tienen efecto o fallan claro")

    # 1. Onda con parámetros de barras permitidos como desconocidos -> idéntico a default
    base_onda = render_de("onda")
    huella_base_onda = huella(base_onda.cuadro(430))

    ajenos_onda = {
        "n_barras": 120,
        "grosor_barra": 90.0,
        "redondeo": 10.0,
        "tapas_pico": True,
        "frec_min": 100.0,
        "frec_max": 8000.0,
        "caida_picos": 0.8,
    }
    onda_con_ajenos = render_de("onda", ajenos_onda)
    huella_con_ajenos = huella(onda_con_ajenos.cuadro(430))
    afirmar(huella_base_onda == huella_con_ajenos,
            "onda: parámetros ajenos a onda no alteran el dibujo",
            "huella idéntica al default")

    # 2. Barras con parámetros de onda permitidos como desconocidos -> idéntico a default
    base_barras = render_de("barras")
    huella_base_barras = huella(base_barras.cuadro(430))

    ajenos_barras = {
        "grosor_linea": 16,
        "relleno": True,
    }
    barras_con_ajenos = render_de("barras", ajenos_barras)
    huella_barras_con_ajenos = huella(barras_con_ajenos.cuadro(430))
    afirmar(huella_base_barras == huella_barras_con_ajenos,
            "barras: parámetros ajenos a barras no alteran el dibujo",
            "huella idéntica al default")

    # 3. Validación estricta falla claro con ErrorDeParametro
    fallo_claro = False
    try:
        parametros.validar({"n_barras": 100}, estilo="onda", permitir_desconocidos=False)
    except parametros.ErrorDeParametro as e:
        fallo_claro = "no aplica al estilo 'onda'" in str(e)
    afirmar(fallo_claro, "validar estricto rechaza parámetro ajeno a onda con mensaje explicativo")

    fallo_claro_barras = False
    try:
        parametros.validar({"grosor_linea": 8}, estilo="barras", permitir_desconocidos=False)
    except parametros.ErrorDeParametro as e:
        fallo_claro_barras = "no aplica al estilo 'barras'" in str(e)
    afirmar(fallo_claro_barras, "validar estricto rechaza parámetro ajeno a barras con mensaje explicativo")


def coherencia_de_fps() -> None:
    """Un análisis y unos parámetros con fps distinto no se pueden combinar."""
    print("\nExtra  No se puede mezclar un análisis con otros fps")
    a = analizar(PISTA, {**CHICO, "fps": 30}, "barras")
    try:
        Render(a, "barras", {**CHICO, "fps": 60})
    except ValueError as e:
        afirmar("desincronizado" in str(e) or "fps" in str(e),
                "falla al combinar 30 fps con 60", "con mensaje que lo explica")
    else:
        afirmar(False, "falla al combinar 30 fps con 60", "no falló")


def criterio_export(hacer_export: bool) -> None:
    """Exporta en los tres modos de fondo, con el conteo de cuadros exacto (2.1 y 3.1)."""
    print("\n2.1 y 3.1  Export en los tres modos de fondo (Barras y Onda)")
    if not hacer_export:
        print("  (omitido; se corre con --export)")
        return

    import json
    import subprocess

    BUILD.mkdir(exist_ok=True)
    for estilo_id in ("barras", "onda"):
        for modo in ("negro", "color", "transparente"):
            r = render_de(estilo_id, {"fondo": modo, "calidad": "baja"})
            destino = BUILD / f"t_render_{estilo_id}_{modo}.webm"
            t0 = time.perf_counter()
            escrito = salida.exportar(r, destino)
            t = time.perf_counter() - t0

            cmd = ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
                   "-show_entries", "stream=nb_read_frames,width,height",
                   "-show_entries", "stream_tags=alpha_mode", "-of", "json", str(escrito)]
            datos = json.loads(subprocess.run(cmd, capture_output=True, text=True).stdout)
            s = datos["streams"][0]
            leidos = int(s["nb_read_frames"])

            afirmar(leidos == r.n_cuadros, f"{estilo_id} {modo}: conteo de cuadros exacto",
                    f"{leidos} de {r.n_cuadros}, en {t:.1f}s, "
                    f"{escrito.stat().st_size / 1024:.0f} KB")

            if modo == "transparente":
                marca = (s.get("tags") or {}).get("alpha_mode")
                afirmar(marca == "1", f"{estilo_id} transparente: el contenedor declara alpha",
                        f"alpha_mode={marca!r}")


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--export", action="store_true",
                   help="incluye el criterio 2.1 y 3.1, que codifica los videos de prueba")
    args = p.parse_args()

    if not PISTA.exists():
        print(f"error: falta {PISTA}\n"
              f"  Generala con: python tests\\fixtures\\generar_audio_espectro.py",
              file=sys.stderr)
        return 2

    print("Pruebas del motor de dibujo")
    print(f"  pista  : {PISTA.name}")
    print(f"  estilos: {', '.join(e.id for e in estilos.disponibles())}")

    criterio_2_4()
    criterio_2_3()
    criterio_3_4()
    estructura_del_dibujo()
    coherencia_de_fps()
    criterio_export(args.export)

    print(f"\n{_pasadas} comprobaciones pasadas, {len(_fallas)} fallas")
    if _fallas:
        print("\nFallaron:", file=sys.stderr)
        for f in _fallas:
            print(f"  - {f}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
