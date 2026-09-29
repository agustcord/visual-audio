"""Generador de capturas de pantalla oficiales para el README de Visual Audio.

Usa el motor de render real (Render.cuadro) con la pista de prueba y los tres
estilos (barras, onda, espejadas) sobre fondo negro (#000000) con el tema
Dark Zinc 950/900 simulado como marco.

Uso:
    python tools/generar_capturas.py

Las imágenes se guardan en assets/screenshots/.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Asegurar que tools/ esté en el path para importar visualizador
TOOLS = Path(__file__).resolve().parent
ROOT = TOOLS.parent
sys.path.insert(0, str(TOOLS))

from PIL import Image, ImageDraw, ImageFont

from visualizador.analisis import analizar
from visualizador.render import Render


# --- Configuración del tema Dark Zinc 950/900 ---
ZINC_950 = (9, 9, 11)       # Fondo principal de la ventana
ZINC_900 = (24, 24, 27)     # Paneles laterales / barra superior
ZINC_800 = (39, 39, 42)     # Bordes sutiles
ZINC_400 = (161, 161, 170)  # Texto secundario
ZINC_200 = (228, 228, 231)  # Texto primario
CYAN_500 = (6, 182, 212)    # Acento cian
VIOLET_500 = (139, 92, 246) # Acento violeta

# Resolución de las capturas
ANCHO_CAPTURA = 1280
ALTO_CAPTURA = 720

# Ruta de audio de prueba
AUDIO = ROOT / "tests" / "fixtures" / "pista_espectro.wav"
SALIDA = ROOT / "assets" / "screenshots"


def dibujar_marco_gui(img: Image.Image, titulo: str, estilo_nombre: str) -> Image.Image:
    """Dibuja un marco que simula la interfaz Dark Zinc alrededor del render."""
    marco = Image.new("RGB", (ANCHO_CAPTURA, ALTO_CAPTURA), ZINC_950)
    draw = ImageDraw.Draw(marco)

    # Barra de título superior (40px)
    draw.rectangle([(0, 0), (ANCHO_CAPTURA, 40)], fill=ZINC_900)
    draw.line([(0, 40), (ANCHO_CAPTURA, 40)], fill=ZINC_800, width=1)

    # Título de la ventana
    try:
        fuente_titulo = ImageFont.truetype("segoeui.ttf", 14)
        fuente_badge = ImageFont.truetype("segoeui.ttf", 11)
        fuente_label = ImageFont.truetype("segoeui.ttf", 12)
    except (OSError, IOError):
        fuente_titulo = ImageFont.load_default()
        fuente_badge = fuente_titulo
        fuente_label = fuente_titulo

    draw.text((16, 12), "Visual Audio", fill=ZINC_200, font=fuente_titulo)

    # Botones de ventana simulados (cerrar, minimizar, maximizar)
    for i, color in enumerate([(239, 68, 68), ZINC_400, ZINC_400]):
        cx = ANCHO_CAPTURA - 40 + (i * 0) - (i * 28) - 16
        cx = ANCHO_CAPTURA - 28 - i * 28
        draw.ellipse([(cx, 14), (cx + 12, 26)], fill=color)

    # Panel lateral derecho (controles simulados, 260px)
    panel_x = ANCHO_CAPTURA - 260
    draw.rectangle([(panel_x, 41), (ANCHO_CAPTURA, ALTO_CAPTURA)], fill=ZINC_900)
    draw.line([(panel_x, 41), (panel_x, ALTO_CAPTURA)], fill=ZINC_800, width=1)

    # Etiquetas del panel
    y_panel = 56
    draw.text((panel_x + 16, y_panel), "Estilo", fill=CYAN_500, font=fuente_label)
    y_panel += 24

    # Badge del estilo activo
    badge_text = estilo_nombre.capitalize()
    draw.rounded_rectangle(
        [(panel_x + 16, y_panel), (panel_x + 16 + len(badge_text) * 8 + 16, y_panel + 24)],
        radius=4, fill=ZINC_800
    )
    draw.text((panel_x + 24, y_panel + 5), badge_text, fill=CYAN_500, font=fuente_badge)
    y_panel += 40

    # Controles simulados
    controles = [
        ("Sensibilidad", "3.0"),
        ("Suavizado", "0.65"),
        ("Color", "#00E5FF"),
        ("Degradado", "altura"),
        ("Resplandor", "0.3"),
    ]
    for label, valor in controles:
        draw.text((panel_x + 16, y_panel), label, fill=ZINC_400, font=fuente_label)
        draw.text((panel_x + 160, y_panel), valor, fill=ZINC_200, font=fuente_label)
        y_panel += 28

    # Separador
    y_panel += 8
    draw.line([(panel_x + 16, y_panel), (ANCHO_CAPTURA - 16, y_panel)], fill=ZINC_800)
    y_panel += 16

    draw.text((panel_x + 16, y_panel), "Salida", fill=CYAN_500, font=fuente_label)
    y_panel += 24
    draw.text((panel_x + 16, y_panel), "Resolución", fill=ZINC_400, font=fuente_label)
    draw.text((panel_x + 160, y_panel), "1920x1080", fill=ZINC_200, font=fuente_label)
    y_panel += 28
    draw.text((panel_x + 16, y_panel), "FPS", fill=ZINC_400, font=fuente_label)
    draw.text((panel_x + 160, y_panel), "30", fill=ZINC_200, font=fuente_label)
    y_panel += 28

    # Botón Exportar
    y_panel += 16
    btn_y = y_panel
    draw.rounded_rectangle(
        [(panel_x + 16, btn_y), (ANCHO_CAPTURA - 16, btn_y + 36)],
        radius=6, fill=CYAN_500
    )
    draw.text((panel_x + 80, btn_y + 9), "Exportar WebM", fill=ZINC_950, font=fuente_label)

    # Barra inferior de transporte (48px)
    barra_y = ALTO_CAPTURA - 48
    draw.rectangle([(0, barra_y), (panel_x, ALTO_CAPTURA)], fill=ZINC_900)
    draw.line([(0, barra_y), (panel_x, barra_y)], fill=ZINC_800, width=1)

    # Barra de progreso
    progreso_y = barra_y + 8
    draw.rounded_rectangle(
        [(16, progreso_y), (panel_x - 16, progreso_y + 4)],
        radius=2, fill=ZINC_800
    )
    # Progreso al ~65%
    progreso_lleno = int((panel_x - 32) * 0.65) + 16
    draw.rounded_rectangle(
        [(16, progreso_y), (progreso_lleno, progreso_y + 4)],
        radius=2, fill=CYAN_500
    )

    # Timestamps
    draw.text((16, progreso_y + 12), "01:42.350", fill=ZINC_400, font=fuente_badge)
    draw.text((panel_x - 80, progreso_y + 12), "02:38.000", fill=ZINC_400, font=fuente_badge)

    # Botón Play (triángulo)
    play_cx = (panel_x) // 2
    play_cy = progreso_y + 22
    draw.polygon(
        [(play_cx - 6, play_cy - 8), (play_cx - 6, play_cy + 8), (play_cx + 8, play_cy)],
        fill=CYAN_500
    )

    # Zona del visor: pegar el render con fondo negro
    visor_x, visor_y = 0, 41
    visor_w = panel_x
    visor_h = barra_y - 41

    # Fondo negro del visor
    draw.rectangle([(visor_x, visor_y), (visor_x + visor_w, visor_y + visor_h)], fill=(0, 0, 0))

    # Escalar y centrar el render en la zona del visor
    render_w, render_h = img.size
    escala = min(visor_w / render_w, visor_h / render_h)
    nuevo_w = int(render_w * escala)
    nuevo_h = int(render_h * escala)
    render_escalado = img.resize((nuevo_w, nuevo_h), Image.LANCZOS)

    offset_x = visor_x + (visor_w - nuevo_w) // 2
    offset_y = visor_y + (visor_h - nuevo_h) // 2

    # Componer con alpha
    if render_escalado.mode == "RGBA":
        fondo_visor = Image.new("RGBA", (nuevo_w, nuevo_h), (0, 0, 0, 255))
        compuesto = Image.alpha_composite(fondo_visor, render_escalado)
        marco.paste(compuesto, (offset_x, offset_y))
    else:
        marco.paste(render_escalado, (offset_x, offset_y))

    return marco


def generar_captura(estilo_id: str, nombre_archivo: str, params: dict) -> Path:
    """Genera una captura para un estilo específico."""
    print(f"  Analizando audio para estilo '{estilo_id}'...")
    a = analizar(AUDIO, params=params, estilo=estilo_id)

    print(f"  Creando Render...")
    r = Render(a, estilo_id, params)

    # Elegir un cuadro con actividad (al ~65% de la pista)
    cuadro_idx = int(r.n_cuadros * 0.65)
    cuadro_idx = max(0, min(cuadro_idx, r.n_cuadros - 1))

    print(f"  Renderizando cuadro {cuadro_idx} de {r.n_cuadros}...")
    img = r.cuadro(cuadro_idx)

    print(f"  Dibujando marco GUI Dark Zinc...")
    captura = dibujar_marco_gui(img, f"Visual Audio — {estilo_id.capitalize()}", estilo_id)

    ruta = SALIDA / nombre_archivo
    captura.save(str(ruta), "PNG", optimize=True)
    size_kb = ruta.stat().st_size / 1024
    print(f"  [OK] Guardado: {ruta.name} ({size_kb:.1f} KB)")
    return ruta


def main():
    print("=" * 60)
    print("  Visual Audio - Generador de Capturas Oficiales")
    print("=" * 60)

    if not AUDIO.exists():
        print(f"ERROR: No se encontró el audio de prueba en {AUDIO}")
        sys.exit(1)

    SALIDA.mkdir(parents=True, exist_ok=True)
    print(f"\nDirectorio de salida: {SALIDA}")
    print(f"Audio de prueba: {AUDIO.name}\n")

    capturas = [
        {
            "estilo": "barras",
            "archivo": "01_estilo_barras.png",
            "params": {
                "color": "#00E5FF",
                "color_final": "#0050DC",
                "degradado": "altura",
                "resplandor": 0.3,
                "reflejo": 0.2,
                "fondo": "negro",
            },
        },
        {
            "estilo": "onda",
            "archivo": "02_estilo_onda.png",
            "params": {
                "color": "#00FFCC",
                "grosor_linea": 4,
                "relleno": True,
                "degradado": "altura",
                "fondo": "negro",
            },
        },
        {
            "estilo": "espejadas",
            "archivo": "03_estilo_espejadas.png",
            "params": {
                "color": "#FF007F",
                "color_final": "#7F00FF",
                "degradado": "ancho",
                "redondeo": 50.0,
                "fondo": "negro",
            },
        },
    ]

    exitos = 0
    for c in capturas:
        print(f"\n[{c['estilo'].upper()}]")
        try:
            generar_captura(c["estilo"], c["archivo"], c["params"])
            exitos += 1
        except Exception as e:
            print(f"  [FAIL] Error: {e}")

    print(f"\n{'=' * 60}")
    print(f"  Resultado: {exitos}/{len(capturas)} capturas generadas")
    print(f"{'=' * 60}")

    if exitos < len(capturas):
        sys.exit(1)


if __name__ == "__main__":
    main()
