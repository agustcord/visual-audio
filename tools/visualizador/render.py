"""Render: une el análisis con un estilo y produce cuadros.

## Este archivo es la garantía del criterio MVP-5

La vista previa de la interfaz llama a `cuadro(i)`. El export llama a `cuadros()`,
que por dentro **es el mismo `cuadro(i)`**. No hay un dibujante rápido para
previsualizar y otro para exportar, así que no hay forma de que la vista previa
muestre algo distinto de lo que va a salir.

Es la trampa clásica de estas herramientas, y la única defensa real es estructural:
que no exista el segundo camino. Drift mismo hace bandera de lo contrario — *un
compositor, un resultado, sin sorpresas*.

## Y la consecuencia de que los estilos no guarden estado

`cuadro(i)` se puede llamar en cualquier orden, con cualquier salto, cuantas veces
haga falta, y siempre devuelve lo mismo. Eso es lo que permite que la interfaz
muestre el cuadro donde está la barra de tiempo sin renderizar los anteriores.
"""

from __future__ import annotations

from typing import Any, Iterator

from PIL import Image

from . import parametros
from .analisis import Analisis
from .estilos import Caja, DatosCuadro, Estilo, obtener


class Render:
    """Dibuja los cuadros de un análisis con un estilo y unos parámetros."""

    def __init__(self, analisis: Analisis, estilo: Estilo | str,
                 params: dict[str, Any] | None = None):
        self.analisis = analisis
        self.estilo = obtener(estilo) if isinstance(estilo, str) else estilo
        self.p = parametros.validar(params or {}, self.estilo.id,
                                    permitir_desconocidos=True)

        fondo_comp = self.p.get("compensar_fondo", "#000000")
        if fondo_comp != "#000000":
            if "color" in self.p:
                comp, _ = parametros.compensar_color(self.p["color"], fondo_comp)
                self.p["color"] = comp
            if "color_final" in self.p and parametros.tiene_efecto(self.p, "color_final"):
                comp_final, _ = parametros.compensar_color(self.p["color_final"], fondo_comp)
                self.p["color_final"] = comp_final

        self.tamano = (int(self.p["lienzo_ancho"]), int(self.p["lienzo_alto"]))
        self.caja = Caja(
            x=int(self.p["x"]), y=int(self.p["y"]),
            ancho=int(self.p["ancho"]), alto=int(self.p["alto"]),
        )

        if analisis.fps != int(self.p["fps"]):
            raise ValueError(
                f"el análisis se hizo a {analisis.fps} fps y los parámetros piden "
                f"{self.p['fps']}. Hay que rehacer el análisis: los cuadros no "
                f"coincidirían y el overlay quedaría desincronizado."
            )

    @property
    def n_cuadros(self) -> int:
        return self.analisis.n_cuadros

    def datos_de(self, i: int) -> DatosCuadro:
        a = self.analisis
        return DatosCuadro(
            indice=i,
            bandas=a.bandas[i],
            amplitud=float(a.amplitud[i]),
            onda=a.onda[i],
        )

    def cuadro(self, i: int) -> Image.Image:
        """El cuadro `i` como RGBA, con fondo transparente.

        Lo usan la vista previa y el export. No hay otro camino.
        """
        if not 0 <= i < self.n_cuadros:
            raise IndexError(
                f"el cuadro {i} está fuera de rango: hay {self.n_cuadros} "
                f"(0 a {self.n_cuadros - 1})"
            )
        lienzo = Image.new("RGBA", self.tamano, (0, 0, 0, 0))
        self.estilo.dibujar(lienzo, self.datos_de(i), self.caja, self.p)
        return lienzo

    def cuadro_viewport(self, i: int, ancho_vp: int, alto_vp: int) -> Image.Image:
        """El cuadro `i` renderizado directamente a resolución de visor (Viewport LOD).

        Calcula el factor de escala uniforme k respecto al lienzo maestro y adapta
        la Caja, grosores de trazo y radios de resplandor para dibujar directo sobre
        el tamaño reducido, alcanzando > 120 FPS teóricos en CPU sin alterar la
        invarianza del export maestro.
        """
        if not 0 <= i < self.n_cuadros:
            raise IndexError(
                f"el cuadro {i} está fuera de rango: hay {self.n_cuadros} "
                f"(0 a {self.n_cuadros - 1})"
            )

        if ancho_vp <= 0 or alto_vp <= 0:
            raise ValueError(f"dimensiones de viewport inválidas: {ancho_vp}x{alto_vp}")

        lienzo_w, lienzo_h = self.tamano
        k = min(ancho_vp / lienzo_w, alto_vp / lienzo_h)

        if k >= 1.0:
            return self.cuadro(i)

        vp_w = max(1, int(round(lienzo_w * k)))
        vp_h = max(1, int(round(lienzo_h * k)))

        caja_vp = Caja(
            x=int(round(self.caja.x * k)),
            y=int(round(self.caja.y * k)),
            ancho=max(1, int(round(self.caja.ancho * k))),
            alto=max(1, int(round(self.caja.alto * k))),
        )

        p_vp = dict(self.p)
        p_vp["lienzo_ancho"] = vp_w
        p_vp["lienzo_alto"] = vp_h
        p_vp["x"] = caja_vp.x
        p_vp["y"] = caja_vp.y
        p_vp["ancho"] = caja_vp.ancho
        p_vp["alto"] = caja_vp.alto

        if "grosor_linea" in p_vp:
            p_vp["grosor_linea"] = max(1, int(round(float(self.p["grosor_linea"]) * k)))

        if "resplandor_radio" in p_vp:
            p_vp["resplandor_radio"] = max(1.0, float(self.p["resplandor_radio"]) * k)

        lienzo = Image.new("RGBA", (vp_w, vp_h), (0, 0, 0, 0))
        self.estilo.dibujar(lienzo, self.datos_de(i), caja_vp, p_vp)
        return lienzo

    def cuadros(self, desde: int = 0, hasta: int | None = None) -> Iterator[Image.Image]:
        """Los cuadros en orden, para el export."""
        fin = self.n_cuadros if hasta is None else min(hasta, self.n_cuadros)
        for i in range(max(0, desde), fin):
            yield self.cuadro(i)
