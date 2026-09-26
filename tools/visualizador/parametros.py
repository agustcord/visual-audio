"""Esquema de parámetros: la única fuente de verdad sobre qué se puede ajustar.

Todo el producto lee de acá: la línea de comandos arma su `--ayuda` con esto, la
interfaz gráfica **construye su panel recorriéndolo**, los proyectos se validan
contra esto, y la prueba de barrido saca de acá los valores a probar.

Por eso es declarativo y no una lista de argumentos sueltos: **agregar un valor
nuevo es agregar una fila**, y aparece solo en los cinco lugares. Si estuviera
cableado a mano en cada cliente, agregar un valor serían cinco ediciones y una se
olvidaría.

La lista de valores con su justificación de diseño vive en `docs/MVP.md` §3, que
es el documento que gobierna. Este archivo es su implementación.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ErrorDeParametro(ValueError):
    """Un parámetro inválido. Se reporta con el nombre y lo que se esperaba."""


@dataclass(frozen=True)
class Valor:
    """Un parámetro ajustable.

    `estilos` vacío significa que aplica a todos. Si tiene nombres, el parámetro
    sólo existe para esos estilos — así la interfaz puede esconder lo que no
    corresponde en vez de mostrar controles que no hacen nada.
    """

    etiqueta: str
    tipo: type
    default: Any
    grupo: str
    ayuda: str
    minimo: float | None = None
    maximo: float | None = None
    opciones: tuple[str, ...] = ()
    estilos: tuple[str, ...] = ()
    unidad: str = ""

    def aplica_a(self, estilo: str | None) -> bool:
        return not self.estilos or estilo is None or estilo in self.estilos

    def validar(self, nombre: str, valor: Any) -> Any:
        """Devuelve el valor convertido al tipo correcto, o falla explicando."""
        if self.opciones:
            if valor not in self.opciones:
                raise ErrorDeParametro(
                    f"'{nombre}' recibió {valor!r}; las opciones son "
                    f"{', '.join(map(repr, self.opciones))}"
                )
            return valor

        if self.tipo is bool:
            if not isinstance(valor, bool):
                raise ErrorDeParametro(f"'{nombre}' tiene que ser verdadero o falso, recibí {valor!r}")
            return valor

        try:
            convertido = self.tipo(valor)
        except (TypeError, ValueError):
            esperado = "un número entero" if self.tipo is int else "un número"
            raise ErrorDeParametro(f"'{nombre}' tiene que ser {esperado}, recibí {valor!r}") from None

        if self.minimo is not None and convertido < self.minimo:
            raise ErrorDeParametro(
                f"'{nombre}' = {convertido} está por debajo del mínimo ({self.minimo})"
            )
        if self.maximo is not None and convertido > self.maximo:
            raise ErrorDeParametro(
                f"'{nombre}' = {convertido} está por encima del máximo ({self.maximo})"
            )
        return convertido

    def valores_de_barrido(self) -> list[Any]:
        """Mínimo, default y máximo — lo que prueba el barrido del criterio MVP-4."""
        if self.opciones:
            return list(self.opciones)
        if self.tipo is bool:
            return [False, True]
        vs = [self.default]
        if self.minimo is not None:
            vs.insert(0, self.tipo(self.minimo))
        if self.maximo is not None:
            vs.append(self.tipo(self.maximo))
        # dict.fromkeys preserva el orden y saca repetidos (default == mínimo, por ejemplo)
        return list(dict.fromkeys(vs))


# Los grupos, en el orden en que van en la interfaz.
GRUPOS = {
    "audio": "Reacción al audio",
    "forma": "Forma",
    "posicion": "Posición y tamaño",
    "color": "Color",
    "salida": "Salida",
}


# --------------------------------------------------------------------------- #
# El esquema
#
# ETAPA 1 define el grupo `audio` completo, más los valores de otros grupos que
# el análisis necesita para trabajar (`fps` y `n_barras`). Los grupos `forma`,
# `posicion` y `color` se completan en la etapa 2, cuando exista el motor de
# dibujo que los consume. Ver `docs/RUTA_DE_TRABAJO.md`.
# --------------------------------------------------------------------------- #

ESQUEMA: dict[str, Valor] = {
    # ---- Reacción al audio -------------------------------------------------
    "sensibilidad": Valor(
        etiqueta="Sensibilidad",
        tipo=float, default=3.0, minimo=0.5, maximo=10.0, grupo="audio",
        ayuda="Cuánto salta el dibujo con el sonido. Es el valor que más cambia el "
              "carácter del resultado. Con 3.0 el momento más fuerte de la canción "
              "llega justo al tope; más alto recorta los picos y se ve más agresivo, "
              "más bajo deja aire.",
    ),
    "suavizado": Valor(
        etiqueta="Suavizado",
        tipo=float, default=0.65, minimo=0.0, maximo=1.0, grupo="audio",
        ayuda="Inercia del movimiento. 0 sigue el audio exacto y se ve nervioso; "
              "1 es muy fluido y llega tarde a todo.",
    ),
    "caida_picos": Valor(
        etiqueta="Caída de picos",
        tipo=float, default=0.4, minimo=0.0, maximo=1.0, grupo="audio",
        ayuda="Cuánto MÁS lento baja que lo que sube. 0 baja igual de rápido que "
              "sube; 1 deja los picos colgados. Es lo que le da el aire de medidor "
              "de audio de verdad.",
    ),
    "curva_respuesta": Valor(
        etiqueta="Curva de respuesta",
        tipo=str, default="raiz", opciones=("lineal", "raiz", "log"), grupo="audio",
        ayuda="Cuánto se levantan los pasajes suaves. 'lineal' es fiel y se ve "
              "vacío en música tranquila; 'raiz' es el punto medio; 'log' levanta "
              "mucho y aplana las diferencias.",
    ),
    "frec_min": Valor(
        etiqueta="Frecuencia mínima",
        tipo=float, default=40.0, minimo=20.0, maximo=2000.0, grupo="audio", unidad="Hz",
        ayuda="Dónde empieza el espectro. Subirla a 60-80 Hz saca el retumbe que no "
              "aporta nada visual.",
    ),
    "frec_max": Valor(
        etiqueta="Frecuencia máxima",
        tipo=float, default=14000.0, minimo=1000.0, maximo=20000.0, grupo="audio", unidad="Hz",
        ayuda="Dónde termina. Bajarla a 10 kHz concentra el dibujo donde hay energía "
              "de verdad, porque arriba de eso casi siempre está vacío.",
    ),

    # ---- Valores de otros grupos que el análisis necesita ------------------
    "n_barras": Valor(
        etiqueta="Cantidad de barras",
        tipo=int, default=64, minimo=5, maximo=240, grupo="forma",
        estilos=("barras", "espejadas"),
        ayuda="Cuántas bandas de frecuencia se dibujan. Pocas se ve estilizado, "
              "muchas se ve como un analizador de espectro.",
    ),
    "fps": Valor(
        etiqueta="Cuadros por segundo",
        tipo=int, default=30, opciones=(), minimo=1, maximo=120, grupo="salida",
        ayuda="Los del proyecto de Drift. 30 es el estándar; 24 da archivos más "
              "chicos y 60 un movimiento más fluido.",
    ),
}


# --------------------------------------------------------------------------- #
# Interfaz pública
# --------------------------------------------------------------------------- #

def defaults(estilo: str | None = None) -> dict[str, Any]:
    """Todos los valores por defecto que aplican a `estilo`."""
    return {n: v.default for n, v in ESQUEMA.items() if v.aplica_a(estilo)}


def validar(params: dict[str, Any], estilo: str | None = None,
            permitir_desconocidos: bool = False) -> dict[str, Any]:
    """Completa los que falten y valida los presentes.

    **Falla en vez de corregir en silencio.** Un valor fuera de rango es un error
    del que lo escribió, y taparlo con un `clamp` hace que el resultado no se
    parezca a lo que pidió sin que se entere. La interfaz gráfica ya impide salir
    del rango con sus propios controles, así que si acá llega algo inválido es que
    viene de un proyecto escrito a mano o de un cliente con un bug — y en los dos
    casos conviene enterarse.
    """
    salida = defaults(estilo)

    for nombre, valor in params.items():
        definicion = ESQUEMA.get(nombre)
        if definicion is None:
            if permitir_desconocidos:
                continue
            raise ErrorDeParametro(
                f"'{nombre}' no es un parámetro conocido. "
                f"Los válidos son: {', '.join(sorted(ESQUEMA))}"
            )
        if not definicion.aplica_a(estilo):
            raise ErrorDeParametro(
                f"'{nombre}' no aplica al estilo '{estilo}' "
                f"(sólo a {', '.join(definicion.estilos)})"
            )
        salida[nombre] = definicion.validar(nombre, valor)

    _validar_coherencia(salida)
    return salida


def _validar_coherencia(p: dict[str, Any]) -> None:
    """Reglas que involucran a más de un parámetro."""
    if "frec_min" in p and "frec_max" in p and p["frec_min"] >= p["frec_max"]:
        raise ErrorDeParametro(
            f"'frec_min' ({p['frec_min']:g} Hz) tiene que ser menor que "
            f"'frec_max' ({p['frec_max']:g} Hz)"
        )


def por_grupo(estilo: str | None = None) -> dict[str, list[tuple[str, Valor]]]:
    """El esquema agrupado y en orden. Es lo que recorre la interfaz para armarse."""
    salida: dict[str, list[tuple[str, Valor]]] = {g: [] for g in GRUPOS}
    for nombre, valor in ESQUEMA.items():
        if valor.aplica_a(estilo):
            salida[valor.grupo].append((nombre, valor))
    return {g: vs for g, vs in salida.items() if vs}
