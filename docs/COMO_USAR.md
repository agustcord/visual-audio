# Cómo usar el visualizador de audio

Guía de uso para **Drift 0.6.0** (la versión publicada e instalada).

> **Sobre la transparencia y Drift:**  
> Drift 0.6.0 **no soporta video con canal alpha** en su timeline (al importar video transparente lo procesa con fondo negro). Por esta razón, el método de composición estándar, verificado y más liviano es generar sobre **fondo negro** y aplicar el modo de fusión **Trama (Screen)** en Drift. Cuando esté disponible Drift 0.7.0, el modo `transparente` ya está implementado en la herramienta y listo para usarse directamente.

---

## 1. Cómo abrir la aplicación

Hacé **doble clic** en el archivo:

```
visualizador.bat
```

en la raíz del proyecto.

El lanzador abre directamente la interfaz gráfica utilizando `pythonw.exe`, de modo que **no queda ninguna ventana de consola negra abierta de fondo**.

---

## 2. Flujo de trabajo principal (Interfaz Gráfica)

La aplicación está diseñada para que puedas generar tus visualizadores sin necesidad de programar ni usar la terminal:

1. **Cargar audio:** Hacé clic en el botón superior *"Cargar audio"* y seleccioná tu canción (`.mp3`, `.wav`, `.flac`, etc.).
2. **Vista previa inmediata:** De inmediato verás en el visor la onda generada con el preset por defecto.
3. **Reproducción de audio sincronizada y scrubbing:** Presioná el botón **"▶ Reproducir"** (o pulsá la **barra espaciadora**) para escuchar la canción y ver en tiempo real cómo bailan las ondas al ritmo del sonido de forma continua. Arrastrá la barra de tiempo para hacer scrubbing instantáneo con el mouse; al soltar, la música continúa en ese instante exacto.
4. **Elegir estilo:** Seleccioná entre **Barras**, **Barras espejadas** u **Onda**.
5. **Personalizar valores:** Modificá sensibilidad, suavizado, número de barras, colores, resplandor (*glow*), reflejo y redondeo. La vista previa refleja cada cambio al instante.
6. **Compensación de color (`compensar_fondo`):** Si tu video en Drift tiene un fondo oscuro o con tono (por ejemplo `#101827`), ingresá ese color en el campo `compensar_fondo`. El motor ajustará automáticamente los tonos para que en la fusión Trama se vea exactamente el color que elegiste.
7. **Presets:** Podés seleccionar presets de fábrica (`barras_blancas`, `barras_neon`, `espejadas_frecuencia`, `onda_suave`) o guardar tus propios proyectos.
8. **Exportar video:** Presioná *"Exportar video"*, elegí el nombre de archivo `.webm` y aguardá la finalización (podés cancelar en cualquier momento de manera limpia).

---

## 3. Composición en Drift (Modo Trama)

El flujo de integración en Drift toma dos clics:

1. Abrí Drift e importá el archivo `.webm` que exportaste.
2. Colocá el clip en una pista **por encima** de tu pista de video musical.
3. En las propiedades del clip, cambiá el modo de fusión a **Trama** (*Screen*).

**Resultado:** El fondo negro desaparece de forma matemáticamente exacta y la onda queda superpuesta sobre el video musical, sin halos ni bordes extraños.

### ¿Cuándo usar Chroma Key?
Si tu video de fondo es extremadamente luminoso o blanco, el modo Trama se fundirá con el fondo. En ese caso:
1. En el visualizador, configurá **Fondo** en `color` y seleccioná un tono de contraste (ej. Magenta `#FF00FF`).
2. En Drift, mantené el modo de fusión en *Normal*, agregá el efecto **Chroma Key** (`key.chroma`) y ajustá el tono a 300° con tolerancia adecuada.

---

## 4. Apéndice: Comandos por consola (CLI)

Para automatizaciones o scripts por lotes, podés usar `visualizador.bat` o el módulo de Python:

```powershell
# Listar estilos, presets y parámetros disponibles
visualizador.bat --listar

# Renderizar un archivo con valores por defecto
visualizador.bat tests\fixtures\pista_espectro.wav -o build\onda.webm

# Renderizar aplicando un preset de fábrica
visualizador.bat tests\fixtures\pista_espectro.wav --preset barras_neon -o build\onda_neon.webm

# Obtener ayuda de todas las opciones CLI
visualizador.bat --help
```

---

## 5. Verificación del sistema

Para comprobar que el motor, el render y la sincronía estén funcionando correctamente:

```powershell
python tests\test_analisis.py
python tests\test_render.py --export
python tests\verificar_sincronia.py
python tests\test_proyecto.py
python tests\test_gui.py
python tests\test_lanzador.py
```
