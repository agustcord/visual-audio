"""Visualizador de audio — motor de render.

Genera un video con la onda o el espectro de un audio, para importar como overlay
en el editor Drift.

La arquitectura son tres etapas que no se conocen entre sí:

    ANÁLISIS            DIBUJO              SALIDA
    audio → números     números → píxeles   píxeles → archivo

El contrato completo está en `docs/ARQUITECTURA.md`. Las dos reglas que más
importan, porque de ellas depende que la vista previa sea posible:

1. El análisis produce **exactamente** `round(duracion * fps)` cuadros, y el
   cuadro `i` cubre el audio de `i/fps` a `(i+1)/fps`.
2. Los estilos **no guardan estado entre cuadros**. Todo lo temporal (suavizado,
   caída de picos) se resuelve en el análisis, así que cualquier cuadro se puede
   dibujar suelto sin haber dibujado los anteriores.
"""

__version__ = "0.1.0"
