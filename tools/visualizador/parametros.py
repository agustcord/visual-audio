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

import re
from dataclasses import dataclass
from typing import Any


class ErrorDeParametro(ValueError):
    """Un parámetro inválido. Se reporta con el nombre y lo que se esperaba."""


RE_COLOR = re.compile(r"^#[0-9a-fA-F]{6}$")


def a_rgb(color: str) -> tuple[int, int, int]:
    """'#00E5FF' → (0, 229, 255)."""
    if not RE_COLOR.match(color):
        raise ErrorDeParametro(f"color inválido: {color!r}. Se espera '#RRGGBB'.")
    return int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)


@dataclass(frozen=True)
class Valor:
    """Un parámetro ajustable.

    `estilos` vacío significa que aplica a todos. Si tiene nombres, el parámetro
    sólo existe para esos estilos — así la interfaz puede esconder lo que no
    corresponde en vez de mostrar controles que no hacen nada.

    `formato` le dice a la interfaz qué control usar cuando el tipo no alcanza:
    `"color"` pide una paleta en vez de un campo de texto.
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
    formato: str = ""
    # Nombre de otro parámetro del que éste depende para tener efecto. El radio del
    # resplandor no hace nada si el resplandor está en 0.
    #
    # Lo descubrió el barrido de la etapa 2: reportó que `resplandor_radio` no
    # cambiaba el dibujo, y tenía razón — con el resplandor apagado por defecto, no
    # podía cambiarlo. El barrido ahora activa la dependencia antes de probar, y la
    # interfaz puede deshabilitar el control en vez de ofrecer algo que no responde.
    depende_de: str = ""

    def aplica_a(self, estilo: str | None) -> bool:
        return not self.estilos or estilo is None or estilo in self.estilos

    def validar(self, nombre: str, valor: Any) -> Any:
        """Devuelve el valor convertido al tipo correcto, o falla explicando."""
        if self.formato == "color":
            texto = str(valor)
            a_rgb(texto)   # valida y descarta: sólo interesa que no explote
            return texto

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
        if self.formato == "color":
            # Negro y blanco además del default: los dos extremos de luminancia,
            # que es donde se rompen los degradados si están mal calculados.
            return [self.default, "#000000", "#FFFFFF"]
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
        tipo=str, default="log", opciones=("lineal", "raiz", "log"), grupo="audio",
        ayuda="Cuánto se levantan los pasajes suaves. 'log' es el default porque es "
              "el único que llena el espectro: la música tiene los graves 10 a 20 "
              "veces más fuertes que los agudos, y con 'raiz' o 'lineal' los dos "
              "tercios derechos del dibujo quedan planos. 'raiz' es más fiel a la "
              "energía real, útil si querés que se vea que la canción es grave.",
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

    # ---- Forma -------------------------------------------------------------
    "n_barras": Valor(
        etiqueta="Cantidad de barras",
        tipo=int, default=64, minimo=5, maximo=240, grupo="forma",
        estilos=("barras", "espejadas"),
        ayuda="Cuántas bandas de frecuencia se dibujan. Pocas se ve estilizado, "
              "muchas se ve como un analizador de espectro.",
    ),
    "grosor_barra": Valor(
        etiqueta="Grosor de barra",
        tipo=float, default=62.0, minimo=10.0, maximo=100.0, grupo="forma", unidad="%",
        estilos=("barras", "espejadas"),
        ayuda="Qué porcentaje del espacio disponible ocupa cada barra. El resto es "
              "aire entre barras: con 100 se tocan y se ve como un bloque macizo.",
    ),
    "redondeo": Valor(
        etiqueta="Redondeo de puntas",
        tipo=float, default=50.0, minimo=0.0, maximo=50.0, grupo="forma", unidad="%",
        estilos=("barras", "espejadas"),
        ayuda="Del grosor de la barra. Con 50 la punta es un semicírculo perfecto; "
              "con 0 es un rectángulo con esquinas vivas.",
    ),

    # ---- Posición y tamaño -------------------------------------------------
    "lienzo_ancho": Valor(
        etiqueta="Ancho del lienzo",
        tipo=int, default=1920, minimo=16, maximo=7680, grupo="posicion", unidad="px",
        ayuda="El del proyecto de Drift. Generar al tamaño exacto evita que Drift "
              "tenga que escalar o rellenar el clip.",
    ),
    "lienzo_alto": Valor(
        etiqueta="Alto del lienzo",
        tipo=int, default=1080, minimo=16, maximo=4320, grupo="posicion", unidad="px",
        ayuda="El del proyecto de Drift.",
    ),
    "ancho": Valor(
        etiqueta="Ancho del dibujo",
        tipo=int, default=1920, minimo=16, maximo=7680, grupo="posicion", unidad="px",
        ayuda="El largo de la banda de visualización. Puede ser menor que el lienzo.",
    ),
    "alto": Valor(
        etiqueta="Alto del dibujo",
        tipo=int, default=320, minimo=8, maximo=4320, grupo="posicion", unidad="px",
        ayuda="La altura máxima que alcanza el dibujo en su punto más fuerte.",
    ),
    "x": Valor(
        etiqueta="Posición horizontal",
        tipo=int, default=0, minimo=-7680, maximo=7680, grupo="posicion", unidad="px",
        ayuda="Desde el borde izquierdo del lienzo hasta el borde izquierdo del "
              "dibujo. Admite negativos, para que el dibujo se salga del cuadro.",
    ),
    "y": Valor(
        etiqueta="Posición vertical",
        tipo=int, default=700, minimo=-4320, maximo=4320, grupo="posicion", unidad="px",
        ayuda="Desde el borde superior. El default de 700 deja una banda de 320 px "
              "a 60 px del piso en un lienzo de 1080.",
    ),

    # ---- Color -------------------------------------------------------------
    "color": Valor(
        etiqueta="Color",
        tipo=str, default="#00E5FF", grupo="color", formato="color",
        ayuda="El color principal. Con degradado, es el extremo de abajo.",
    ),
    "color_final": Valor(
        etiqueta="Color final",
        tipo=str, default="#0050DC", grupo="color", formato="color",
        depende_de="degradado",
        ayuda="El otro extremo del degradado. Poniéndolo igual al principal, el "
              "dibujo queda de un solo color.",
    ),
    "degradado": Valor(
        etiqueta="Degradado",
        tipo=str, default="altura", opciones=("ninguno", "altura", "ancho"),
        grupo="color",
        ayuda="'altura' tiñe según lo alto que llegue cada barra, así el color "
              "informa intensidad; 'ancho' tiñe según la frecuencia, de graves a "
              "agudos; 'ninguno' usa sólo el color principal.",
    ),
    "opacidad": Valor(
        etiqueta="Opacidad",
        tipo=float, default=1.0, minimo=0.0, maximo=1.0, grupo="color",
        ayuda="De todo el dibujo. También se puede ajustar en Drift sobre el clip, "
              "y ahí es más cómodo porque se ve en vivo.",
    ),
    "resplandor": Valor(
        etiqueta="Resplandor",
        tipo=float, default=0.0, minimo=0.0, maximo=1.0, grupo="color",
        ayuda="Halo alrededor del dibujo. En 0 está apagado y el render es más "
              "rápido, porque el desenfoque es lo más caro de cada cuadro.",
    ),
    "resplandor_radio": Valor(
        etiqueta="Radio del resplandor",
        tipo=float, default=18.0, minimo=1.0, maximo=80.0, grupo="color", unidad="px",
        depende_de="resplandor",
        ayuda="Qué tan lejos llega el halo. Sólo tiene efecto si el resplandor es "
              "mayor que 0.",
    ),
    "tapas_pico": Valor(
        etiqueta="Tapas de pico",
        tipo=bool, default=False, grupo="color",
        estilos=("barras", "espejadas"),
        ayuda="La marquita que queda arriba de cada barra. Es lo que le da el aire "
              "de medidor de audio de equipo.",
    ),
    "reflejo": Valor(
        etiqueta="Reflejo",
        tipo=float, default=0.0, minimo=0.0, maximo=1.0, grupo="color",
        ayuda="Copia atenuada debajo del dibujo, como sobre un piso brillante. Es "
              "la opacidad del reflejo: en 0 está apagado.",
    ),

    # ---- Salida ------------------------------------------------------------
    "fps": Valor(
        etiqueta="Cuadros por segundo",
        tipo=int, default=30, minimo=1, maximo=120, grupo="salida",
        ayuda="Los del proyecto de Drift. 30 es el estándar; 24 da archivos más "
              "chicos y 60 un movimiento más fluido.",
    ),
    "fondo": Valor(
        etiqueta="Modo de fondo",
        tipo=str, default="negro", opciones=("transparente", "negro", "color"),
        grupo="salida",
        ayuda="Cómo se recorta el fondo en Drift. 'negro' se compone con la fusión "
              "Trama; 'color' se recorta con el efecto Chroma Key; 'transparente' "
              "usa canal alpha y NECESITA Drift 0.7.0 o superior — en 0.6.0 el alpha "
              "se descarta y el clip sale como un rectángulo negro.",
    ),
    "color_fondo": Valor(
        etiqueta="Color del fondo",
        tipo=str, default="#FF00FF", grupo="color", formato="color",
        ayuda="Para el modo Chroma Key. Conviene un tono lejano al del dibujo: el "
              "Chroma Key de Drift recorta por tono, así que si están cerca se come "
              "parte de la onda. Con dibujo cian, magenta es buena elección.",
    ),
    "calidad": Valor(
        etiqueta="Calidad",
        tipo=str, default="media", opciones=("alta", "media", "baja"), grupo="salida",
        ayuda="Alta pesa alrededor del doble que media; baja, la mitad. El overlay "
              "pesa bastante igual, porque cada cuadro es un dibujo nuevo y la "
              "compresión de video no puede predecirlo.",
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

    # Los formatos de video con submuestreo de croma (yuv420p, yuva420p) exigen
    # dimensiones pares. Vale más fallar acá con una explicación que dejar que
    # FFmpeg lo rechace a mitad del render con un mensaje suyo.
    for nombre in ("lienzo_ancho", "lienzo_alto"):
        if nombre in p and p[nombre] % 2 != 0:
            raise ErrorDeParametro(
                f"'{nombre}' = {p[nombre]} tiene que ser par.\n"
                f"  El formato de video que usa Drift submuestrea el color, y eso "
                f"pide lados pares."
            )


def esta_activo(params: dict[str, Any], nombre: str) -> bool:
    """Si ese parámetro está en un valor que habilita a los que dependen de él.

    Cuenta como apagado el 0, el `False` y la opción `"ninguno"`.
    """
    valor = params.get(nombre)
    if valor is None:
        return False
    if isinstance(valor, str):
        return valor != "ninguno"
    return bool(valor)


def tiene_efecto(params: dict[str, Any], nombre: str) -> bool:
    """Si ese parámetro puede cambiar algo con los valores actuales.

    La interfaz lo usa para deshabilitar controles que no responderían.
    """
    definicion = ESQUEMA.get(nombre)
    if definicion is None or not definicion.depende_de:
        return True
    return esta_activo(params, definicion.depende_de)


def valor_activador(nombre: str) -> Any:
    """Un valor de `nombre` que habilite a los que dependen de él.

    Lo usa el barrido para poder probar los parámetros dependientes.
    """
    definicion = ESQUEMA[nombre]
    if definicion.opciones:
        for opcion in definicion.opciones:
            if opcion != "ninguno":
                return opcion
        return definicion.default
    if definicion.tipo is bool:
        return True
    return definicion.tipo(definicion.maximo if definicion.maximo is not None else 1)


def por_grupo(estilo: str | None = None) -> dict[str, list[tuple[str, Valor]]]:
    """El esquema agrupado y en orden. Es lo que recorre la interfaz para armarse."""
    salida: dict[str, list[tuple[str, Valor]]] = {g: [] for g in GRUPOS}
    for nombre, valor in ESQUEMA.items():
        if valor.aplica_a(estilo):
            salida[valor.grupo].append((nombre, valor))
    return {g: vs for g, vs in salida.items() if vs}
