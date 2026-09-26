"""El contrato que cumple todo estilo de dibujo.

## Las dos reglas, y por qué

**1. Un estilo dibuja y nada más.** No abre archivos, no llama a FFmpeg, no decide
el fondo, no sabe qué cuadro vino antes. Recibe números y pinta sobre un lienzo.

**2. Un estilo no guarda estado entre cuadros.** Ésta es la importante, y es la que
hace posible la vista previa de la interfaz.

Si un estilo recordara algo del cuadro anterior —una envolvente, una posición de
pico, cualquier cosa— entonces dibujar el cuadro 300 exigiría haber dibujado los
299 anteriores. La interfaz tendría que renderizar media canción cada vez que movés
un deslizador, o mentir mostrando algo distinto de lo que va a exportar.

Todo lo que dependa del tiempo ya viene resuelto en el análisis. El estilo recibe
el cuadro `i` completo y listo, y lo dibuja. El criterio 2.4 de la ruta verifica
esto de forma directa: `cuadro(i)` tiene que dar el mismo resultado llamado suelto
o en secuencia.

**3. Un estilo dibuja siempre con alpha.** El modo de fondo (transparente, negro
para Trama, color para Chroma Key) lo aplica `salida.py` después. Así un estilo
sirve para los tres modos sin enterarse de que existen.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

import numpy as np
from PIL import Image


@dataclass(frozen=True)
class DatosCuadro:
    """Lo que el análisis dice de un cuadro. Todo en 0..1."""

    indice: int
    bandas: np.ndarray    # (n_bandas,) — energía por banda de frecuencia
    amplitud: float       # el pico del cuadro
    onda: np.ndarray      # (n_columnas,) — la forma de onda del cuadro

    @property
    def n_bandas(self) -> int:
        return int(self.bandas.size)


@dataclass(frozen=True)
class Caja:
    """Dónde va el dibujo dentro del lienzo, en píxeles.

    `x` e `y` pueden ser negativos y el dibujo puede pasarse de los bordes: es
    deliberado, para poder sacar medio visualizador del cuadro a propósito.
    """

    x: int
    y: int
    ancho: int
    alto: int

    @property
    def derecha(self) -> int:
        return self.x + self.ancho

    @property
    def abajo(self) -> int:
        return self.y + self.alto


class Estilo(ABC):
    """Un estilo de dibujo."""

    id: str = ""
    nombre: str = ""
    # Qué del análisis necesita: "bandas" o "onda". Lo usa la interfaz para saber
    # qué parámetros mostrar, y las pruebas para armar datos de mentira.
    usa: tuple[str, ...] = ()

    @abstractmethod
    def dibujar(self, lienzo: Image.Image, datos: DatosCuadro,
                caja: Caja, p: dict[str, Any]) -> None:
        """Dibuja UN cuadro sobre `lienzo`, que es RGBA y ya mide lo que va a salir.

        `lienzo` llega transparente. El estilo pinta encima y no devuelve nada.
        """


# Registro de estilos. `estilos/__init__.py` lo llena; el resto del motor lo
# consulta por id, así que agregar un estilo es agregar un archivo y una línea.
_REGISTRO: dict[str, Estilo] = {}


def registrar(estilo: Estilo) -> Estilo:
    if not estilo.id:
        raise ValueError("un estilo necesita un id")
    if estilo.id in _REGISTRO:
        raise ValueError(f"el estilo '{estilo.id}' ya estaba registrado")
    _REGISTRO[estilo.id] = estilo
    return estilo


def obtener(id_estilo: str) -> Estilo:
    if id_estilo not in _REGISTRO:
        disponibles = ", ".join(sorted(_REGISTRO)) or "ninguno"
        raise KeyError(f"no existe el estilo '{id_estilo}'. Disponibles: {disponibles}")
    return _REGISTRO[id_estilo]


def disponibles() -> list[Estilo]:
    return [_REGISTRO[k] for k in sorted(_REGISTRO)]
