"""Cuánto se corre el color de las barras al componerlas con la fusión Trama.

Responde una pregunta concreta del fundador: *"el tema es poder ajustar la
combinación de colores del fondo, cuando nuestro fondo sea de cierto color"*.

## De dónde sale la fórmula

No se inventó acá ni se sacó de un blog: está leída del compositor de Drift, en
`src/engine/GpuCompositor.cpp`, en el shader `kLayerFragShader`.

```glsl
vec3 blendRgb(vec3 base, vec3 src) {
    ...
    if (u_blendMode == 2) return 1.0 - (1.0 - base) * (1.0 - src);   // Trama
```

Dos detalles que importan y que hay que leer del shader para saberlos:

- **Opera sobre alpha recta y NO lineariza.** No hay conversión a luz lineal antes
  de mezclar: las cuentas van sobre los valores sRGB tal como vienen de la textura.
  Por eso este script, que trabaja en 0..1 sobre los bytes del color, reproduce
  exactamente lo que se ve en Drift.
- **Después compone source-over**: `outRgb = blended * sa + dstRgb * dst.a * (1-sa)`
  donde `sa = src.a * u_opacity`. Nuestro overlay llega opaco en todo el cuadro
  (fondo negro aplastado), así que con opacidad 1 queda `out = blended`, la fusión
  pura. Bajar la opacidad del clip en Drift mezcla de vuelta hacia el video.

## Las dos conclusiones que mide

1. **El fondo negro no se aproxima: desaparece exacto.** Donde el overlay es negro,
   `src = 0` y entonces `out = 1 - (1-base)(1-0) = base`. El video pasa intacto,
   bit por bit. No hay pérdida ni suciedad.
2. **El color de la barra sí se corre, siempre hacia el blanco, y nunca hacia el
   negro.** Cuánto depende del video debajo, y eso se mide acá.

## La compensación

Si se conoce el fondo `B` y se quiere obtener `D`, hay que dibujar:

    src = 1 - (1 - D) / (1 - B)

Sólo tiene solución cuando `D >= B` en cada canal. Trama únicamente suma luz: no
existe ningún color que dibujado sobre un fondo claro dé un resultado más oscuro
que ese fondo. Ése es el límite duro, y no es un defecto de Drift.

El error se reporta en ΔE76 (CIE Lab). Referencia de lectura: por debajo de 1 no se
distingue, 1 a 2 se distingue comparando lado a lado, 2 a 10 se ve, y arriba de 10
son colores distintos.

Uso:
    python tools\\medir_trama.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))

from visualizador.consola import preparar  # noqa: E402

SALIDA = RAIZ.parent / "docs" / "evidencia" / "T10_trama_corrimiento_de_color.png"

# Fondos de video realistas para un video musical. El nombre es lo que el fundador
# vería en su timeline, no un tecnicismo.
FONDOS = [
    ("negro puro", "#000000"),
    ("casi negro (sombra)", "#141414"),
    ("azul nocturno", "#101C38"),
    ("gris medio", "#808080"),
    ("piel iluminada", "#C89878"),
    ("blanco (cielo quemado)", "#F0F0F0"),
]

# Colores de barra que alguien elegiría de verdad.
BARRAS = [
    ("blanco", "#FFFFFF"),
    ("celeste", "#22D3EE"),
    ("rosa", "#F0509B"),
    ("amarillo", "#FFC83C"),
    ("rojo oscuro", "#8B1A1A"),
]


def a_rgb01(hexa: str) -> np.ndarray:
    h = hexa.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float64) / 255.0


def a_hex(rgb01: np.ndarray) -> str:
    v = np.clip(np.rint(rgb01 * 255.0), 0, 255).astype(int)
    return "#{:02X}{:02X}{:02X}".format(*v)


def trama(base: np.ndarray, src: np.ndarray) -> np.ndarray:
    """La fusión Trama de Drift, tal cual el shader."""
    return 1.0 - (1.0 - base) * (1.0 - src)


def compensar(deseado: np.ndarray, fondo: np.ndarray) -> tuple[np.ndarray, bool]:
    """Qué dibujar para que Trama sobre `fondo` dé `deseado`.

    Devuelve el color y si fue alcanzable sin recortar. `1-fondo` puede ser 0 en un
    canal saturado (fondo blanco): ahí no hay ningún valor que sirva y se recorta.
    """
    resto = 1.0 - fondo
    with np.errstate(divide="ignore", invalid="ignore"):
        src = np.where(resto > 1e-9, 1.0 - (1.0 - deseado) / resto, 1.0)
    alcanzable = bool(np.all(src >= -1e-9) and np.all(src <= 1.0 + 1e-9))
    return np.clip(src, 0.0, 1.0), alcanzable


def a_lab(rgb01: np.ndarray) -> np.ndarray:
    """sRGB → CIE Lab con blanco D65. Acá sí hay que linearizar: la distancia
    perceptual se define sobre luz, no sobre los bytes del archivo."""
    c = np.asarray(rgb01, dtype=np.float64)
    lin = np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    m = np.array([
        [0.4124564, 0.3575761, 0.1804375],
        [0.2126729, 0.7151522, 0.0721750],
        [0.0193339, 0.1191920, 0.9503041],
    ])
    xyz = m @ lin / np.array([0.95047, 1.0, 1.08883])
    d = 6.0 / 29.0
    f = np.where(xyz > d ** 3, np.cbrt(xyz), xyz / (3 * d * d) + 4.0 / 29.0)
    return np.array([116 * f[1] - 16, 500 * (f[0] - f[1]), 200 * (f[1] - f[2])])


def delta_e(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a_lab(a) - a_lab(b)))


def lectura(de: float) -> str:
    if de < 1.0:
        return "no se distingue"
    if de < 2.0:
        return "apenas, lado a lado"
    if de < 10.0:
        return "se ve"
    return "otro color"


def tabla() -> list[tuple]:
    filas = []
    for nombre_f, hex_f in FONDOS:
        fondo = a_rgb01(hex_f)
        for nombre_b, hex_b in BARRAS:
            deseado = a_rgb01(hex_b)
            crudo = trama(fondo, deseado)
            src, ok = compensar(deseado, fondo)
            corregido = trama(fondo, src)
            filas.append((nombre_f, hex_f, nombre_b, hex_b,
                          crudo, delta_e(deseado, crudo),
                          corregido, delta_e(deseado, corregido), ok))
    return filas


def imprimir(filas: list[tuple]) -> None:
    print("Corrimiento del color de la barra con la fusión Trama")
    print("  fórmula: out = 1-(1-fondo)(1-barra), leída de GpuCompositor.cpp:135")
    print("  error en ΔE76; <1 no se distingue, >10 es otro color\n")

    ancho = max(len(f[0]) for f in filas)
    fondo_actual = None
    for nf, hf, nb, hb, crudo, de_crudo, corr, de_corr, ok in filas:
        if nf != fondo_actual:
            print(f"  fondo {nf} {hf}".ljust(ancho + 16, "-"))
            fondo_actual = nf
        marca = "" if ok else "   <- imposible, se recortó"
        print(f"    {nb:<12} {hb} -> {a_hex(crudo)}  ΔE {de_crudo:6.1f}  "
              f"{lectura(de_crudo):<18} | compensado ΔE {de_corr:5.1f}{marca}")

    print("\nDonde el overlay es negro:")
    for nf, hf, *_ in filas[::len(BARRAS)]:
        fondo = a_rgb01(hf)
        paso = trama(fondo, np.zeros(3))
        print(f"    {nf:<24} {hf} -> {a_hex(paso)}   "
              f"{'intacto' if np.allclose(paso, fondo) else 'CAMBIÓ'}")


def dibujar(filas: list[tuple]) -> None:
    from PIL import Image, ImageDraw

    celda, alto_f, margen, etiqueta = 150, 112, 20, 210
    ancho = etiqueta + celda * len(BARRAS) + margen * 2
    alto = margen * 2 + 58 + alto_f * len(FONDOS)
    img = Image.new("RGB", (ancho, alto), "#1E1E1E")
    d = ImageDraw.Draw(img)

    d.text((margen, margen), "Fusión Trama: color pedido (arriba) vs. lo que sale (abajo)",
           fill="#F0F0F0")
    for j, (nb, hb) in enumerate(BARRAS):
        x = margen + etiqueta + j * celda
        d.text((x + 6, margen + 30), f"{nb}", fill="#A0A0A0")

    for i, (nf, hf) in enumerate(FONDOS):
        fondo = a_rgb01(hf)
        y = margen + 58 + i * alto_f
        d.rectangle([margen + etiqueta, y, ancho - margen, y + alto_f - 6], fill=hf)
        d.text((margen, y + 8), nf, fill="#F0F0F0")
        d.text((margen, y + 26), hf, fill="#808080")
        for j, (nb, hb) in enumerate(BARRAS):
            deseado = a_rgb01(hb)
            x = margen + etiqueta + j * celda
            # Mitad izquierda: el color pedido. Mitad derecha: el resultado real.
            d.rectangle([x + 8, y + 6, x + 8 + 56, y + alto_f - 26], fill=hb)
            d.rectangle([x + 68, y + 6, x + 68 + 56, y + alto_f - 26],
                        fill=a_hex(trama(fondo, deseado)))
            de = delta_e(deseado, trama(fondo, deseado))
            # "dE" y no "ΔE": la fuente por defecto de Pillow es un bitmap ASCII y
            # cualquier glifo fuera de eso sale como un cuadrito vacío.
            d.text((x + 8, y + alto_f - 22), f"dE {de:.0f}",
                   fill="#000000" if fondo.mean() > 0.5 else "#C0C0C0")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    img.save(SALIDA)
    print(f"\nevidencia: {SALIDA.relative_to(RAIZ.parent)}")


def main() -> int:
    preparar()
    filas = tabla()
    imprimir(filas)
    dibujar(filas)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
