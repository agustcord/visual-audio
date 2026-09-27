"""
Entrypoint canónico para ejecutar el paquete visualizador directamente con:
    python -m visualizador
"""
from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
