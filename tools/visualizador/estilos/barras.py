"""Estilo Barras: el espectro como barras verticales.

Es el estilo principal — el que las siete herramientas relevadas tratan como el
básico, y el que se ve en los videos musicales.

## Cómo se arma un cuadro

El dibujo se compone en capas, de atrás hacia adelante:

    1. reflejo    copia atenuada y volteada, debajo del eje
    2. resplandor el dibujo desenfocado, para el halo
    3. barras     las barras en sí
    4. tapas      la marquita de pico arriba de cada barra

El resplandor se dibuja **a resolución reducida y después se agranda**. Desenfocar
es lo más caro de todo el cuadro, y a un halo difuso no le hace ninguna falta
resolución completa: nadie nota la diferencia y el render va varias veces más
rápido.

## Por qué el degradado se calcula por barra y no por píxel

Un degradado píxel a píxel exigiría pintar cada barra con una máscara y componer,
lo que multiplica el costo por cuadro. En cambio se le da **un color a cada barra
entera**, elegido según su altura o su posición. Visualmente el resultado es casi
el mismo —las barras son angostas— y cuesta una fracción.

`degradado="altura"` tiñe según lo alto que llegó la barra, así el color informa
intensidad. `degradado="ancho"` tiñe según la frecuencia, de graves a agudos.
"""

from __future__ import annotations

from typing import Any

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from .. import parametros
from .base import Caja, DatosCuadro, Estilo

# A qué fracción se dibuja el resplandor antes de agrandarlo. Un sexto es
# suficiente para un halo y hace el desenfoque unas 36 veces más barato.
ESCALA_RESPLANDOR = 1 / 6

# Alto de la tapa de pico, como fracción del grosor de la barra.
ALTO_TAPA = 0.22

# Separación de la tapa respecto de la punta de la barra, en fracción del grosor.
SEPARACION_TAPA = 0.28

# Cuánto mide el reflejo respecto del dibujo.
ALTO_REFLEJO = 0.32


def _sigma(radio: float) -> float:
    """Desviación del desenfoque, a la escala reducida, para que el halo llegue
    hasta `radio` píxeles del dibujo.

    **`resplandor_radio` es hasta dónde llega el halo, no la desviación del
    gaussiano.** Es lo que dice su ayuda y lo que espera cualquiera que mueva el
    control, y hay que traducirlo: un gaussiano se extiende unas tres desviaciones,
    así que la desviación es un tercio del alcance pedido.

    Sin esta conversión el halo se derramaba **tres veces más lejos** de lo pedido y
    el margen de la región lo recortaba, dejando un corte recto visible en el borde.
    De paso, desenfocar con una desviación tres veces menor es más barato.
    """
    return max(0.5, radio * ESCALA_RESPLANDOR / 3.0)


def _mezclar(a: tuple[int, int, int], b: tuple[int, int, int],
             t: float) -> tuple[int, int, int]:
    """Interpola dos colores. `t` va de 0 (a) a 1 (b)."""
    t = min(1.0, max(0.0, t))
    return (round(a[0] + (b[0] - a[0]) * t),
            round(a[1] + (b[1] - a[1]) * t),
            round(a[2] + (b[2] - a[2]) * t))


class Barras(Estilo):
    id = "barras"
    nombre = "Barras"
    usa = ("bandas",)

    # Desde dónde crece la barra: el piso de la caja. `Espejadas` hereda de esta
    # clase y sólo cambia esto, porque el resto del dibujo es idéntico.
    centrado = False

    def dibujar(self, lienzo: Image.Image, datos: DatosCuadro,
                caja: Caja, p: dict[str, Any]) -> None:
        valores = self._valores(datos, p)
        if valores.size == 0:
            return

        # El camino corto: sin reflejo, sin resplandor y sin transparencia, las
        # barras se pintan derecho sobre el lienzo. Se ahorra una capa entera y su
        # composición, que a 1920x1080 son dos millones de píxeles por cuadro.
        if (p["reflejo"] <= 0.0 and p["resplandor"] <= 0.0
                and float(p["opacidad"]) >= 1.0):
            self._dibujar_barras(lienzo, valores, caja, p)
            return

        # Con adornos hace falta una capa intermedia, pero **sólo del tamaño de la
        # zona que puede recibir tinta**, no del lienzo entero.
        #
        # Esto era el cuello de botella: con la capa a tamaño completo, un lienzo
        # de 1080 filas se copiaba tres o cuatro veces por cuadro cuando el dibujo
        # ocupa una banda de 320. Medido, el caso típico pasó de 86 ms a una
        # fracción por cuadro. La zona incluye la banda, el reflejo si está, y un
        # margen para que el desenfoque del resplandor no se corte en el borde.
        region = self._region(lienzo.size, caja, p)
        if region is None:
            return

        capa = Image.new("RGBA", (region.ancho, region.alto), (0, 0, 0, 0))
        caja_rel = Caja(caja.x - region.x, caja.y - region.y, caja.ancho, caja.alto)
        self._dibujar_barras(capa, valores, caja_rel, p)

        if p["reflejo"] > 0.0:
            self._agregar_reflejo(capa, caja_rel, float(p["reflejo"]))

        opacidad = float(p["opacidad"])
        destino = (region.x, region.y)

        # El halo va DEBAJO del dibujo, así que se compone primero.
        if p["resplandor"] > 0.0:
            halo = self._halo(capa, float(p["resplandor"]) * opacidad,
                              float(p["resplandor_radio"]))
            lienzo.alpha_composite(halo, dest=destino)

        if opacidad < 1.0:
            capa = self._atenuar(capa, opacidad)

        lienzo.alpha_composite(capa, dest=destino)

    # -- piezas ------------------------------------------------------------- #

    def _region(self, tamano: tuple[int, int], caja: Caja,
                p: dict[str, Any]) -> Caja | None:
        """La zona del lienzo que puede recibir tinta, acotada a sus bordes."""
        margen = 0
        if p["resplandor"] > 0.0:
            # El desenfoque se derrama; sin margen se vería un corte recto.
            margen = int(float(p["resplandor_radio"])) + 2
        cola = 0
        if p["reflejo"] > 0.0:
            cola = int(caja.alto * ALTO_REFLEJO) + 4

        x0 = max(0, caja.x - margen)
        y0 = max(0, caja.y - margen)
        x1 = min(tamano[0], caja.derecha + margen)
        y1 = min(tamano[1], caja.abajo + cola + margen)
        if x1 <= x0 or y1 <= y0:
            return None      # el dibujo cae entero fuera del lienzo
        return Caja(x0, y0, x1 - x0, y1 - y0)

    def _valores(self, datos: DatosCuadro, p: dict[str, Any]) -> np.ndarray:
        """Las alturas 0..1, una por barra.

        El análisis ya entrega tantas bandas como barras pide `n_barras`, pero se
        remuestrea igual por si alguien construye un `Render` con un análisis hecho
        para otra cantidad. Es una línea y evita un error confuso.
        """
        pedidas = int(p["n_barras"])
        bandas = datos.bandas
        if bandas.size == pedidas:
            return bandas
        origen = np.linspace(0.0, 1.0, bandas.size)
        destino = np.linspace(0.0, 1.0, pedidas)
        return np.interp(destino, origen, bandas).astype(np.float32)

    def _dibujar_barras(self, capa: Image.Image, valores: np.ndarray,
                        caja: Caja, p: dict[str, Any]) -> None:
        n = valores.size
        paso = caja.ancho / n
        grosor = max(1.0, paso * float(p["grosor_barra"]) / 100.0)
        radio = grosor * float(p["redondeo"]) / 100.0

        color_a = parametros.a_rgb(str(p["color"]))
        color_b = parametros.a_rgb(str(p["color_final"]))
        degradado = str(p["degradado"])
        con_tapas = bool(p["tapas_pico"])

        d = ImageDraw.Draw(capa)
        # La barra crece hacia arriba desde el piso, o hacia los dos lados desde
        # el centro. Es la única diferencia entre Barras y Espejadas.
        eje = caja.y + caja.alto / 2 if self.centrado else caja.abajo
        alcance = caja.alto / 2 if self.centrado else caja.alto

        for i, v in enumerate(valores):
            largo = float(v) * alcance
            # Piso de grosor: una barra en silencio se ve como un punto y no
            # desaparece, que es lo que hace que la fila de barras se lea como
            # una fila incluso cuando no suena nada.
            largo = max(largo, grosor * 0.5)

            x0 = caja.x + i * paso + (paso - grosor) / 2
            x1 = x0 + grosor

            if degradado == "ninguno":
                color = color_a
            elif degradado == "ancho":
                color = _mezclar(color_a, color_b, i / max(1, n - 1))
            else:   # "altura"
                color = _mezclar(color_a, color_b, float(v))

            if self.centrado:
                y0, y1 = eje - largo, eje + largo
            else:
                y0, y1 = eje - largo, eje

            self._barra(d, x0, y0, x1, y1, radio, color)

            if con_tapas:
                self._tapa(d, x0, x1, y0, y1, grosor, radio)

    @staticmethod
    def _barra(d: ImageDraw.ImageDraw, x0: float, y0: float, x1: float, y1: float,
               radio: float, color: tuple[int, int, int]) -> None:
        """Una barra con puntas redondeadas.

        `rounded_rectangle` exige que el radio quepa en las dos dimensiones; con
        una barra más baja que ancha, pedirle el radio completo lanza excepción. De
        ahí el acotado, y el rectángulo plano cuando el radio queda en nada.
        """
        r = min(radio, abs(x1 - x0) / 2, abs(y1 - y0) / 2)
        caja = (x0, y0, x1, y1)
        if r < 0.5:
            d.rectangle(caja, fill=color + (255,))
        else:
            d.rounded_rectangle(caja, radius=r, fill=color + (255,))

    @staticmethod
    def _tapa(d: ImageDraw.ImageDraw, x0: float, x1: float, y0: float, y1: float,
              grosor: float, radio: float) -> None:
        """La marquita de pico, arriba de la barra.

        Va en blanco y no en el color de la barra a propósito: contra un dibujo de
        color, el blanco es lo que la hace leerse como un indicador aparte y no
        como parte de la barra.
        """
        alto = max(1.0, grosor * ALTO_TAPA)
        sep = grosor * SEPARACION_TAPA
        arriba = y0 - sep - alto
        r = min(radio * 0.4, grosor / 2, alto / 2)
        caja = (x0, arriba, x1, arriba + alto)
        if r < 0.5:
            d.rectangle(caja, fill=(255, 255, 255, 235))
        else:
            d.rounded_rectangle(caja, radius=r, fill=(255, 255, 255, 235))

    def _agregar_reflejo(self, capa: Image.Image, caja: Caja,
                         intensidad: float) -> None:
        """Copia volteada y atenuada, debajo del dibujo. Modifica la capa."""
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

        # Desvanecido vertical: el reflejo se apaga a medida que se aleja.
        rampa = np.linspace(1.0, 0.0, alto, dtype=np.float32) ** 1.6
        alfa = np.asarray(volteada.getchannel("A"), dtype=np.float32)
        alfa *= rampa[:, None] * intensidad
        volteada.putalpha(Image.fromarray(alfa.astype(np.uint8), mode="L"))

        capa.alpha_composite(volteada, dest=(0, abajo + 2))

    def _halo(self, capa: Image.Image, intensidad: float,
              radio: float) -> Image.Image:
        """El dibujo desenfocado, listo para ir debajo de él.

        Se reduce, se desenfoca, **se atenúa mientras todavía es chico**, y sólo
        entonces se agranda.

        El orden importa y se midió: atenuar después de agrandar costaba una vuelta
        completa por numpy sobre la región grande, y el resplandor era el 26 de los
        40 ms que tardaba el peor caso — el dibujo de las barras en sí eran 2,9 ms.
        Atenuando en chico, esa operación pasa a costar treinta y seis veces menos.

        La escala reducida no se nota: a un halo difuso no le hace falta resolución,
        y el desenfoque gaussiano es lo más caro de todo el cuadro.
        """
        chico = (max(1, int(capa.width * ESCALA_RESPLANDOR)),
                 max(1, int(capa.height * ESCALA_RESPLANDOR)))
        halo = capa.resize(chico, Image.Resampling.BILINEAR)
        halo = halo.filter(ImageFilter.GaussianBlur(_sigma(radio)))
        halo = self._atenuar(halo, intensidad)
        return halo.resize(capa.size, Image.Resampling.BILINEAR)

    @staticmethod
    def _atenuar(imagen: Image.Image, factor: float) -> Image.Image:
        """Multiplica el canal alpha. `putalpha` es más barato que componer."""
        alfa = np.asarray(imagen.getchannel("A"), dtype=np.float32) * factor
        salida = imagen.copy()
        salida.putalpha(Image.fromarray(alfa.astype(np.uint8), mode="L"))
        return salida


class Espejadas(Barras):
    """Barras simétricas que crecen desde el centro hacia arriba y abajo.

    Es literalmente el mismo dibujo con otro origen, así que hereda todo y sólo
    cambia el eje. Por eso en la ruta figura como "casi gratis" una vez que existen
    las barras.
    """

    id = "espejadas"
    nombre = "Barras espejadas"
    centrado = True
