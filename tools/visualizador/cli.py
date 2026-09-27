"""Cliente de línea de comandos.

**Sus opciones no están escritas a mano: se generan recorriendo
`parametros.ESQUEMA`.** Agregar un valor nuevo al esquema lo hace aparecer acá solo,
con su rango y su ayuda. Si estuviera cableado, agregar un valor serían dos
ediciones y una se olvidaría.

Es uno de los dos clientes del motor; el otro será la interfaz gráfica. Ninguno de
los dos contiene lógica de dibujo ni de análisis.

    python -m visualizador.cli cancion.mp3 -o onda.webm
    python -m visualizador.cli cancion.mp3 --estilo espejadas --n-barras 96
    python -m visualizador.cli cancion.mp3 --cuadro 300 -o vista.png
    python -m visualizador.cli --listar
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path
from typing import Any

from . import consola, estilos, parametros, proyecto
from .analisis import ErrorDeAnalisis, analizar
from .render import Render
from .salida import ErrorDeSalida, SIGUIENTE_PASO, exportar


def _nombre_de_opcion(nombre: str) -> str:
    return "--" + nombre.replace("_", "-")


def _agregar_opciones_del_esquema(p: argparse.ArgumentParser) -> None:
    """Una opción por fila del esquema, agrupadas como en la interfaz."""
    for grupo, valores in parametros.por_grupo().items():
        g = p.add_argument_group(parametros.GRUPOS[grupo])
        for nombre, v in valores:
            kwargs: dict[str, Any] = {"dest": nombre, "default": None, "help": _ayuda(v)}
            if v.tipo is bool:
                # Con un par --x / --sin-x se puede forzar los dos valores, que es
                # lo que necesita el barrido de parámetros.
                g.add_argument(_nombre_de_opcion(nombre), dest=nombre,
                               action="store_true", default=None, help=_ayuda(v))
                g.add_argument(_nombre_de_opcion("sin_" + nombre), dest=nombre,
                               action="store_false", default=None,
                               help=argparse.SUPPRESS)
                continue
            if v.opciones:
                kwargs["choices"] = list(v.opciones)
                kwargs["type"] = str
            else:
                kwargs["type"] = v.tipo
                kwargs["metavar"] = v.unidad.upper() or v.tipo.__name__.upper()
            g.add_argument(_nombre_de_opcion(nombre), **kwargs)


def _ayuda(v: parametros.Valor) -> str:
    partes = [v.ayuda]
    if v.minimo is not None and v.maximo is not None:
        partes.append(f"[{v.minimo:g} a {v.maximo:g}{' ' + v.unidad if v.unidad else ''}]")
    partes.append(f"(default: {v.default})")
    texto = " ".join(partes)
    return texto.replace("%", "%%")


def _listar() -> int:
    print("Estilos disponibles:")
    for e in estilos.disponibles():
        print(f"  {e.id:12} {e.nombre:20} usa: {', '.join(e.usa)}")
    presets = proyecto.listar_presets()
    if presets:
        print("\nPresets de fábrica disponibles:")
        for pre in presets:
            print(f"  {pre}")
    print("\nValores ajustables, por grupo:")
    for grupo, valores in parametros.por_grupo().items():
        print(f"\n  {parametros.GRUPOS[grupo]}")
        for nombre, v in valores:
            rango = ""
            if v.opciones:
                rango = " / ".join(v.opciones)
            elif v.minimo is not None:
                rango = f"{v.minimo:g} a {v.maximo:g}"
            solo = f"  (sólo {', '.join(v.estilos)})" if v.estilos else ""
            print(f"    {nombre:20} {str(v.default):12} {rango}{solo}")
    return 0


def construir_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="visualizador",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("audio", type=Path, nargs="?",
                   help="archivo de audio (mp3, wav, flac, m4a, ogg)")
    p.add_argument("-o", "--salida", type=Path, default=None,
                   help="archivo de salida (default: <audio>_visual.webm)")
    p.add_argument("--estilo", default=None,
                   choices=[e.id for e in estilos.disponibles()],
                   help="estilo de dibujo (default: barras)")
    p.add_argument("--cuadro", type=int, default=None, metavar="N",
                   help="en vez de exportar el video, guarda SÓLO el cuadro N como "
                        "PNG. Es la vista previa, y usa el mismo motor que el "
                        "export, así que lo que muestra es lo que va a salir")
    p.add_argument("--proyecto", type=Path, default=None, metavar="ARCHIVO",
                   help="carga audio, estilo y parámetros desde un archivo JSON de proyecto")
    p.add_argument("--guardar-proyecto", type=Path, default=None, metavar="ARCHIVO",
                   help="guarda la configuración activa y la ruta del audio en un JSON de proyecto")
    p.add_argument("--preset", default=None, metavar="NOMBRE_O_RUTA",
                   help="aplica un preset de fábrica (por nombre) o desde archivo JSON")
    p.add_argument("--guardar-preset", type=Path, default=None, metavar="ARCHIVO",
                   help="guarda el estilo y parámetros actuales en un archivo JSON de preset")
    p.add_argument("--gui", action="store_true",
                   help="abre la interfaz gráfica interactiva")
    p.add_argument("--listar", action="store_true",
                   help="lista los estilos, presets y los valores ajustables, y sale")
    _agregar_opciones_del_esquema(p)
    return p


def main(argv: list[str] | None = None) -> int:
    consola.preparar()

    # Si se invoca directamente sin argumentos en la terminal, abrir la interfaz gráfica
    es_invocacion_sin_argumentos = argv is None and len(sys.argv) == 1

    args = construir_parser().parse_args(argv)

    if args.gui or es_invocacion_sin_argumentos:
        from . import gui
        return gui.main(
            audio=args.audio,
            proyecto_path=args.proyecto,
            preset=args.preset,
            estilo=args.estilo,
        )

    if args.listar:
        return _listar()

    try:
        params_base: dict[str, Any] = {}
        estilo_elegido = args.estilo

        if args.proyecto:
            audio_proy, estilo_proy, params_proy = proyecto.abrir(args.proyecto)
            if args.audio is None:
                args.audio = audio_proy
            if estilo_elegido is None:
                estilo_elegido = estilo_proy
            params_base.update(params_proy)

        if args.preset:
            estilo_pre, params_pre = proyecto.abrir_preset(args.preset)
            if estilo_elegido is None:
                estilo_elegido = estilo_pre
            params_base.update(params_pre)

        if estilo_elegido is None:
            estilo_elegido = "barras"

        pedidos = {n: getattr(args, n) for n in parametros.ESQUEMA
                   if getattr(args, n, None) is not None}
        params_combinados = {**params_base, **pedidos}
        params = parametros.validar(params_combinados, estilo_elegido)

        if args.guardar_preset:
            proyecto.guardar_preset(args.guardar_preset, estilo_elegido, params)
            print(f"preset guardado: {args.guardar_preset}")
            if args.audio is None and args.salida is None and args.cuadro is None:
                return 0

        if args.guardar_proyecto:
            if args.audio is None:
                print("error: falta el archivo de audio para guardar el proyecto.", file=sys.stderr)
                return 2
            proyecto.guardar(args.guardar_proyecto, args.audio, estilo_elegido, params)
            print(f"proyecto guardado: {args.guardar_proyecto}")
            if args.salida is None and args.cuadro is None:
                return 0

        if args.audio is None:
            print("error: falta el archivo de audio. Usá --help para ver las opciones.",
                  file=sys.stderr)
            return 2

        t0 = time.perf_counter()
        analisis = analizar(args.audio, params, estilo_elegido)
        t_analisis = time.perf_counter() - t0

        render = Render(analisis, estilo_elegido, params)

        print(f"audio   : {args.audio.name}  ({analisis.duracion:.2f}s, "
              f"{analisis.n_cuadros} cuadros a {analisis.fps} fps)")
        print(f"estilo  : {render.estilo.nombre}")
        print(f"lienzo  : {render.tamano[0]}x{render.tamano[1]}, dibujo "
              f"{render.caja.ancho}x{render.caja.alto} en ({render.caja.x},{render.caja.y})")
        print(f"analisis: {t_analisis:.2f}s")

        if args.cuadro is not None:
            destino = args.salida or args.audio.with_name(
                f"{args.audio.stem}_cuadro{args.cuadro}.png")
            destino.parent.mkdir(parents=True, exist_ok=True)
            render.cuadro(args.cuadro).save(destino)
            print(f"\nvista previa del cuadro {args.cuadro} "
                  f"({args.cuadro / analisis.fps:.3f}s): {destino}")
            return 0

        destino = args.salida or args.audio.with_name(f"{args.audio.stem}_visual.webm")
        print(f"fondo   : {params['fondo']}   calidad: {params['calidad']}")
        print("\nrenderizando...")

        t0 = time.perf_counter()
        ultimo = [-1]

        def progreso(hecho: int, total: int) -> bool:
            pct = hecho * 100 // total
            if pct != ultimo[0]:
                ultimo[0] = pct
                print(f"\r  {pct:3d}%  ({hecho}/{total} cuadros)", end="", flush=True)
            return True

        escrito = exportar(render, destino, progreso)
        t_render = time.perf_counter() - t0
        print(f"\r  100%  ({analisis.n_cuadros}/{analisis.n_cuadros} cuadros)")

        tamano = escrito.stat().st_size
        print(f"\nlisto en {t_render:.1f}s: {escrito}  ({tamano / 1024**2:.1f} MB)")
        print(f"\n{SIGUIENTE_PASO[str(params['fondo'])]}")
        return 0

    except (ErrorDeAnalisis, ErrorDeSalida, parametros.ErrorDeParametro, proyecto.ErrorDeProyecto) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\ninterrumpido.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
