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

    def cuadros(self, desde: int = 0, hasta: int | None = None) -> Iterator[Image.Image]:
        """Los cuadros en orden, para el export."""
        fin = self.n_cuadros if hasta is None else min(hasta, self.n_cuadros)
        for i in range(max(0, desde), fin):
            yield self.cuadro(i)
