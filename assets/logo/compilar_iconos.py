"""
compilar_iconos.py - Generador y compilador de iconos para Visual Audio.
Convierte visual_audio_logo.svg en:
  - visual_audio_512.png (512x512 RGBA de alta fidelidad)
  - visual_audio.ico (multi-resolución Windows: 16x16, 24x24, 32x32, 48x48, 64x64, 128x128, 256x256)
"""

import os
import sys
import subprocess
from PIL import Image

def encontrar_navegador():
    candidatos = [
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
    ]
    for ruta in candidatos:
        if os.path.exists(ruta):
            return ruta
    return None

def compilar_assets():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    svg_path = os.path.join(script_dir, "visual_audio_logo.svg")
    png_path = os.path.join(script_dir, "visual_audio_512.png")
    ico_path = os.path.join(script_dir, "visual_audio.ico")

    if not os.path.exists(svg_path):
        print(f"ERROR: No se encontró el SVG maestro en {svg_path}")
        sys.exit(1)

    navegador = encontrar_navegador()
    if not navegador:
        print("ERROR: No se encontró un navegador compatible para rasterizar SVG")
        sys.exit(1)

    print(f"[1/3] Rasterizando {svg_path} a 512x512 usando {os.path.basename(navegador)}...")
    cmd = [
        navegador,
        "--headless=new",
        "--disable-gpu",
        f"--screenshot={png_path}",
        "--window-size=512,512",
        "--default-background-color=00000000",
        f"file:///{svg_path.replace(os.sep, '/')}"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0 or not os.path.exists(png_path):
        print(f"ERROR al renderizar PNG: {res.stderr}")
        sys.exit(1)

    print(f"  -> Generado: {png_path} ({os.path.getsize(png_path)} bytes)")

    print("[2/3] Procesando imagen base con Pillow...")
    img = Image.open(png_path)
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    print("[3/3] Compilando icono multi-resolución Windows (visual_audio.ico)...")
    tamanos_ico = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    img.save(ico_path, format="ICO", sizes=tamanos_ico)
    print(f"  -> Generado: {ico_path} ({os.path.getsize(ico_path)} bytes)")

    print("\nVerificación de entregables:")
    print(f"  - SVG: {os.path.exists(svg_path)} | {os.path.getsize(svg_path):,} bytes")
    print(f"  - PNG: {os.path.exists(png_path)} | {os.path.getsize(png_path):,} bytes ({img.size[0]}x{img.size[1]})")
    print(f"  - ICO: {os.path.exists(ico_path)} | {os.path.getsize(ico_path):,} bytes ({len(tamanos_ico)} resoluciones)")
    print("\nCompilación completada con éxito.")

if __name__ == "__main__":
    compilar_assets()
