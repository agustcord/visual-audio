"""Estilo Onda: forma de onda continua centrada en el eje.

Dibuja la amplitud temporal como una línea continua simétrica alrededor
del eje central de la caja asignada. Soporta grosor de línea configurable,
relleno opcional del cuerpo de la onda, degradados por ancho o altura,
resplandor (halo) y reflejo inferior.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .. import parametros
from .base import Caja, DatosCuadro, Estilo
from .barras import (
    ALTO_REFLEJO,
    ESCALA_RESPLANDOR,
    _mezclar,
    _sigma,
)


class Onda(Estilo):
    """Línea de amplitud continua con relleno y adornos opcionales."""

    id = "onda"
    nombre = "Onda"
    usa = ("onda",)

    def dibujar(self, lienzo: Image.Image, datos: DatosCuadro,
                caja: Caja, p: dict[str, Any]) -> None:
        valores = self._valores(datos, caja.ancho)
        if valores.size == 0 or caja.ancho <= 0 or caja.alto <= 0:
            return

        # Camino corto: sin reflejo, sin resplandor y sin transparencia parcial,
        # la onda se pinta directo sobre el lienzo, ahorrando la composición de capas.
        if (float(p.get("reflejo", 0.0)) <= 0.0 and float(p.get("resplandor", 0.0)) <= 0.0
                and float(p.get("opacidad", 1.0)) >= 1.0):
            self._dibujar_onda(lienzo, valores, caja, p)
            return

        region = self._region(lienzo.size, caja, p)
        if region is None:
            return

        capa = Image.new("RGBA", (region.ancho, region.alto), (0, 0, 0, 0))
        caja_rel = Caja(caja.x - region.x, caja.y - region.y, caja.ancho, caja.alto)
        self._dibujar_onda(capa, valores, caja_rel, p)

        if float(p.get("reflejo", 0.0)) > 0.0:
            self._agregar_reflejo(capa, caja_rel, float(p["reflejo"]))

        opacidad = float(p.get("opacidad", 1.0))
        destino = (region.x, region.y)

        # El halo va debajo del dibujo, así que se compone primero.
        if float(p.get("resplandor", 0.0)) > 0.0:
            halo = self._halo(capa, float(p["resplandor"]) * opacidad,
                              float(p.get("resplandor_radio", 18.0)))
            lienzo.alpha_composite(halo, dest=destino)

        if opacidad < 1.0:
            capa = self._atenuar(capa, opacidad)

        lienzo.alpha_composite(capa, dest=destino)

    # -- piezas ------------------------------------------------------------- #

    def _valores(self, datos: DatosCuadro, ancho: int) -> np.ndarray:
        """Remuestrea la onda al ancho de la caja en píxeles."""
        onda = datos.onda
        if onda.size == 0 or ancho <= 0:
            return np.array([], dtype=np.float32)
        n_puntos = max(2, ancho)
        if onda.size == n_puntos:
            return onda
        origen = np.linspace(0.0, 1.0, onda.size)
        destino = np.linspace(0.0, 1.0, n_puntos)
        return np.interp(destino, origen, onda).astype(np.float32)

    def _region(self, tamano: tuple[int, int], caja: Caja,
                p: dict[str, Any]) -> Caja | None:
        """La zona del lienzo que puede recibir tinta, acotada a sus bordes."""
        margen = int(float(p.get("grosor_linea", 4))) + 2
        if float(p.get("resplandor", 0.0)) > 0.0:
            margen += int(float(p.get("resplandor_radio", 18.0))) + 2
        cola = 0
        if float(p.get("reflejo", 0.0)) > 0.0:
            cola = int(caja.alto * ALTO_REFLEJO) + 4

        x0 = max(0, caja.x - margen)
        y0 = max(0, caja.y - margen)
        x1 = min(tamano[0], caja.derecha + margen)
        y1 = min(tamano[1], caja.abajo + cola + margen)
        if x1 <= x0 or y1 <= y0:
            return None
        return Caja(x0, y0, x1 - x0, y1 - y0)

    def _dibujar_onda(self, capa: Image.Image, valores: np.ndarray,
                      caja: Caja, p: dict[str, Any]) -> None:
        n = valores.size
        if n < 2:
            return

        xs = np.linspace(caja.x, caja.derecha, n, dtype=np.float32)
        eje = caja.y + caja.alto / 2.0
        alcance = caja.alto / 2.0
        grosor = max(1, int(round(float(p.get("grosor_linea", 4)))))

        color_a = parametros.a_rgb(str(p["color"]))
        color_b = parametros.a_rgb(str(p["color_final"]))
        degradado = str(p.get("degradado", "altura"))
        con_relleno = bool(p.get("relleno", False))

        hs = valores * alcance
        ys_sup = eje - hs
        ys_inf = eje + hs

        puntos_sup = [(float(xs[i]), float(ys_sup[i])) for i in range(n)]
        puntos_inf = [(float(xs[i]), float(ys_inf[i])) for i in range(n)]

        d = ImageDraw.Draw(capa)

        # 1. Relleno bajo la línea (cuerpo de la onda)
        if con_relleno:
            if degradado == "ninguno":
                poligono = puntos_sup + list(reversed(puntos_inf))
                d.polygon(poligono, fill=color_a + (255,))
            else:
                for i in range(n - 1):
                    if degradado == "ancho":
                        t = i / max(1, n - 2)
                    else:  # "altura"
                        t = float((valores[i] + valores[i + 1]) / 2.0)
                    col = _mezclar(color_a, color_b, t) + (255,)
                    trapecio = [
                        (float(xs[i]), float(ys_sup[i])),
                        (float(xs[i + 1]), float(ys_sup[i + 1])),
                        (float(xs[i + 1]), float(ys_inf[i + 1])),
                        (float(xs[i]), float(ys_inf[i])),
                    ]
                    d.polygon(trapecio, fill=col)

        # 2. Línea continua de contorno (grosor_linea)
        if degradado == "ninguno":
            col_a = color_a + (255,)
            d.line(puntos_sup, fill=col_a, width=grosor)
            d.line(puntos_inf, fill=col_a, width=grosor)
            if hs[0] > 0:
                d.line([(float(xs[0]), float(ys_sup[0])),
                        (float(xs[0]), float(ys_inf[0]))], fill=col_a, width=grosor)
            if hs[-1] > 0:
                d.line([(float(xs[-1]), float(ys_sup[-1])),
                        (float(xs[-1]), float(ys_inf[-1]))], fill=col_a, width=grosor)
        else:
            for i in range(n - 1):
                if degradado == "ancho":
                    t = i / max(1, n - 2)
                else:  # "altura"
                    t = float((valores[i] + valores[i + 1]) / 2.0)
                col = _mezclar(color_a, color_b, t) + (255,)
                d.line([(float(xs[i]), float(ys_sup[i])),
                        (float(xs[i + 1]), float(ys_sup[i + 1]))], fill=col, width=grosor)
                d.line([(float(xs[i]), float(ys_inf[i])),
                        (float(xs[i + 1]), float(ys_inf[i + 1]))], fill=col, width=grosor)
            if hs[0] > 0:
                col_0 = (color_a + (255,) if degradado == "ancho"
                         else _mezclar(color_a, color_b, float(valores[0])) + (255,))
                d.line([(float(xs[0]), float(ys_sup[0])),
                        (float(xs[0]), float(ys_inf[0]))], fill=col_0, width=grosor)
            if hs[-1] > 0:
                col_1 = (color_b + (255,) if degradado == "ancho"
                         else _mezclar(color_a, color_b, float(valores[-1])) + (255,))
                d.line([(float(xs[-1]), float(ys_sup[-1])),
                        (float(xs[-1]), float(ys_inf[-1]))], fill=col_1, width=grosor)

    def _agregar_reflejo(self, capa: Image.Image, caja: Caja,
                         intensidad: float) -> None:
        """Copia atenuada y volteada, debajo del dibujo. Modifica la capa."""
        alto_reflejo = max(1, int(caja.alto * ALTO_REFLEJO))
        arriba = max(0, caja.y)
        abajo = min(capa.height, caja.abajo)
        if abajo <= arriba:
            return

        franja = capa.crop((0, arriba, capa.width, abajo))
        volteada = franja.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
        alto = min(alto_reflejo, volteada.height, capa.height - abajo - 2)
        if alto <= 0:
            return
        volteada = volteada.crop((0, 0, volteada.width, alto))

        rampa = np.linspace(1.0, 0.0, alto, dtype=np.float32) ** 1.6
        alfa = np.asarray(volteada.getchannel("A"), dtype=np.float32)
        alfa *= rampa[:, None] * intensidad
        volteada.putalpha(Image.fromarray(alfa.astype(np.uint8), mode="L"))

        capa.alpha_composite(volteada, dest=(0, abajo + 2))

    def _halo(self, capa: Image.Image, intensidad: float,
              radio: float) -> Image.Image:
        """El dibujo desenfocado a escala reducida para resplandor."""
        chico = (max(1, int(capa.width * ESCALA_RESPLANDOR)),
                 max(1, int(capa.height * ESCALA_RESPLANDOR)))
        halo = capa.resize(chico, Image.Resampling.BILINEAR)
        halo = halo.filter(ImageFilter.GaussianBlur(_sigma(radio)))
        halo = self._atenuar(halo, intensidad)
        return halo.resize(capa.size, Image.Resampling.BILINEAR)

    @staticmethod
    def _atenuar(imagen: Image.Image, factor: float) -> Image.Image:
        """Multiplica el canal alpha de la imagen."""
        alfa = np.asarray(imagen.getchannel("A"), dtype=np.float32) * factor
        salida = imagen.copy()
        salida.putalpha(Image.fromarray(alfa.astype(np.uint8), mode="L"))
        return salida
