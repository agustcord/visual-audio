"""Registro de estilos.

Agregar un estilo es: escribir el archivo, importarlo acá, y registrarlo. Nada más
del motor necesita cambiar — ni la línea de comandos, ni la interfaz, ni las
pruebas, porque todos consultan este registro.
"""

from .barras import Barras, Espejadas
from .base import Caja, DatosCuadro, Estilo, disponibles, obtener, registrar

registrar(Barras())
registrar(Espejadas())

__all__ = [
    "Caja", "DatosCuadro", "Estilo",
    "disponibles", "obtener", "registrar",
    "Barras", "Espejadas",
]
