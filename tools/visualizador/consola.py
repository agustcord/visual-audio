"""Salida de consola que no se rompe en Windows.

La consola de Windows usa `cp1252` por defecto, que no tiene acentos en algunos
contextos ni símbolos como `≈`, `→` o `⚠`. Eso produce dos problemas distintos:

1. **Acentos ilegibles.** Todas las salidas del proyecto se venían viendo como
   "Alineaci?n" y "m?ximo". Molesto pero inofensivo.
2. **Caída con `UnicodeEncodeError`.** Con un carácter que `cp1252` no tiene
   siquiera un reemplazo, el `print` lanza excepción y el programa **muere**.

Lo segundo pasó de verdad: una prueba que había pasado todas sus comprobaciones se
cayó al imprimir el resultado. Un programa que funciona pero se muere al contarlo
es peor que uno que falla, porque parece que falló lo medido.

Se llama una sola vez, desde el punto de entrada. **No lo llames desde un módulo
de biblioteca**: reconfigurar la salida global es decisión del programa, no de una
pieza que alguien importa.
"""

from __future__ import annotations

import sys


def preparar() -> None:
    """Pasa la salida a UTF-8, y si no se puede degrada a reemplazar caracteres."""
    for flujo in (sys.stdout, sys.stderr):
        reconfigurar = getattr(flujo, "reconfigure", None)
        if reconfigurar is None:
            continue
        try:
            reconfigurar(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            # Salida redirigida a algo que no admite reconfiguración. Se sigue:
            # tener acentos raros es aceptable, morir imprimiendo no.
            pass
