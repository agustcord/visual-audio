# Guía de Uso del Visualizador de Audio para Drift

Guía paso a paso para generar y componer visualizadores de audio en **Drift 0.6.0** (y versiones superiores) utilizando la aplicación gráfica oficial del proyecto.

---

## 1. Inicio Rápido: Lanzar la Aplicación

Para abrir la herramienta gráfica, simplemente hacé **doble clic en el archivo:**

```
visualizador.bat
```

ubicado en la carpeta raíz del proyecto.

> **¿Qué hace este lanzador?**  
> En Windows, `visualizador.bat` detecta automáticamente tu instalación de Python y utiliza `pythonw.exe`. Esto permite que la ventana gráfica de la aplicación se abra de forma limpia e instantánea, **sin dejar ninguna ventana de consola negra abierta detrás**. Además, comprueba que cuentes con Python 3.10+ y FFmpeg en el sistema, avisándote con un mensaje claro si falta alguna dependencia.

---

## 2. Flujo de Trabajo en la Interfaz Gráfica

La interfaz gráfica fue diseñada para que no tengas que programar ni escribir comandos en la terminal:

### Paso 1: Cargar el Audio
1. Hacé clic en el botón **"Cargar audio"** en la barra superior.
2. Seleccioná tu pista musical (`.wav`, `.mp3`, `.flac`, `.ogg`, etc.).
3. **Previsualización inmediata:** Tan pronto como el audio se carga, la aplicación analiza la pista en fracciones de segundo y te muestra de inmediato la onda visualizada con el preset por defecto en el primer cuadro.

### Paso 2: Navegar la Canción (Scrubbing y Fragmento Animado)
- **Barra de tiempo:** Arrastrá el control deslizante horizontal inferior para desplazarte por cualquier punto de la canción y ver cómo reacciona el dibujo en ese segundo exacto.
- **Botones `<` y `>`:** Avanzá o retrocedé cuadro a cuadro (a 30 fps cada paso son 33 ms).
- **Probar fragmento (2s):** Hacé clic en este botón para reproducir una animación de prueba de 2 segundos en el visor sin congelar la ventana.

### Paso 3: Elegir el Estilo
En el panel derecho, en la sección **Estilo**, podés alternar entre los tres estilos incluidos:
- **Barras:** El clásico espectro ecualizador de barras logarítmicas (graves a la izquierda, agudos a la derecha).
- **Barras espejadas:** Mismo análisis de frecuencias pero simétrico, desplegándose desde el eje central.
- **Onda:** Dibuja la forma de onda continua en el tiempo, ideal para líneas minimalistas o con relleno de energía.

### Paso 4: Ajustar Parámetros y Colores
El panel derecho expone los parámetros agrupados. Cada vez que movés un control, la vista previa se actualiza al instante:
- **Reacción al audio:**
  - *Sensibilidad:* Multiplicador de escala de la música.
  - *Suavizado:* Qué tan suave o reactivo es el movimiento temporal entre cuadros.
  - *Caída de picos:* Velocidad a la que bajan las barras tras un golpe musical.
  - *Curva de respuesta:* Modo de compresión dinámica (`log` recomendado para ver todo el espectro lleno).
- **Forma:**
  - Cantidad de barras, grosor, separación y redondeo de esquinas (en Barras/Espejadas).
  - Grosor de línea y relleno sólido inferior (en Onda).
- **Posición y tamaño:**
  - Dimensiones del lienzo (`1920x1080` por defecto para calzar directo en tu proyecto de Drift).
  - Alto y posición vertical (`y`) para ubicar la banda en la parte inferior o centrada.
- **Color y Efectos:**
  - Colores primario y secundario con degradado (`ninguno`, `altura` o `ancho`).
  - *Resplandor (Glow):* Halo luminoso difuso con radio regulable.
  - *Tapas de pico:* Pequeños marcadores flotantes que retienen los picos transitorios.
  - *Reflejo:* Efecto de espejo tenue hacia abajo.

### Paso 5: Usar Presets de Fábrica o Guardar Proyectos
- **Presets de fábrica:** En el menú desplegable de presets podés elegir configuraciones listas para usar:
  - `barras_blancas`: Barras limpias sobre fondo negro (inmunes a cambios de color en Trama).
  - `barras_neon`: Estilo electrizante con resplandor cian y tapas de pico.
  - `espejadas_frecuencia`: Barras dobles simétricas con degradado transversal.
  - `onda_suave`: Forma de onda fluida con relleno tenue.
- **Guardar / Abrir:** Podés guardar tu proyecto completo (audio + valores) en formato `.json` o exportar solo el aspecto como un preset personalizado.

### Paso 6: Exportar el Video
1. Hacé clic en el botón verde **"Exportar video"**.
2. Elegí el nombre y destino del archivo (por defecto formato `.webm`).
3. Aparecerá una barra de progreso que indica el porcentaje y cuadro actual.
4. **No bloquea el sistema:** Podés cancelar la exportación en cualquier momento con el botón "Cancelar"; el proceso se detendrá limpiamente y eliminará el archivo temporal incompleto.

---

## 3. Composición en Drift 0.6.0

Drift 0.6.0 no procesa video con canal alpha nativo en su timeline. Por ello, la integración óptima, ligera y de máxima calidad se realiza mediante el **Modo de Fusión Trama (Screen)** sobre fondo negro.

### Pasos dentro de Drift:
1. Abrí tu proyecto en **Drift**.
2. Importá el video `.webm` que exportaste.
3. Arrastrá el clip a una pista de video **por encima** de tu metraje musical.
4. En el panel de propiedades del clip, cambiá el **Modo de Fusión (Blend Mode)** de *Normal* a **Trama** (*Screen*).
5. **¡Listo!** El fondo negro desaparece por completo con exactitud matemática, y la onda queda dibujada flotando perfectamente sobre tu metraje.

### ¿Por qué funciona el modo Trama?
La fórmula matemática de Trama es:
$$\text{Resultado} = 1 - (1 - \text{Video}) \times (1 - \text{Visualizador})$$

Cuando el fondo es negro ($\text{Visualizador} = 0$), el término $(1 - 0) = 1$, por lo que $\text{Resultado} = 1 - (1 - \text{Video}) = \text{Video}$. El fondo negro se anula al 100% sin dejar bordes ni requerir recortes.

### Cómo mantener los colores exactos con `compensar_fondo`
Si tu video de fondo tiene zonas con luminosidad (por ejemplo, tonos grises, azul noche o texturas), el modo Trama suma luz y puede aclarar ligeramente el tono de las barras.
- Para evitar esto, en la interfaz del visualizador tenés el campo **`compensar_fondo`**.
- Escribí allí el color hexadecimal promedio del fondo de tu video (por ejemplo `#1A1A2E`).
- El motor del visualizador pre-oscurecerá matemáticamente los colores del dibujo para que, al aplicarse la fusión Trama en Drift, el color resultante sobre tu video coincida **exactamente (ΔE < 1.0)** con el color que elegiste.
- Si usás barras blancas (`#FFFFFF`), el color es inmune al modo Trama y se verá blanco puro sobre cualquier metraje.

### Alternativa: Chroma Key (Fondos de Color)
Si tu metraje tiene un fondo excesivamente claro o blanco donde Trama se perdería:
1. En el visualizador, cambiá **Modo de Fondo** a `color` y asigná un color de contraste (ej. Magenta `#FF00FF`).
2. En Drift, mantené el modo de fusión en *Normal* y agregale al clip el efecto **Chroma Key** (`key.chroma`).
3. Configurá el tono en 300° (para magenta) y ajustá la tolerancia hasta recortar el fondo.

---

## 4. Apéndice Técnico: Uso por Línea de Comandos (CLI)

Si necesitás integrar el visualizador en scripts desatendidos o pipelines por lotes, podés usar el lanzador o Python directamente desde la consola:

### Sintaxis básica:
```powershell
# Usando el lanzador .bat
visualizador.bat mi_cancion.mp3 -o salida.webm

# Usando el módulo canónico de Python
python -m visualizador.cli mi_cancion.mp3 -o salida.webm

# Usando el entrypoint del paquete
python -m visualizador mi_cancion.mp3 -o salida.webm
```

### Comandos de utilidad:
```powershell
# Listar todos los estilos, presets y parámetros disponibles
visualizador.bat --listar

# Ver la ayuda completa de opciones
visualizador.bat --help

# Generar un solo cuadro estático (PNG) para previsualización rápida
visualizador.bat mi_cancion.mp3 --cuadro 150 -o cuadro_150.png

# Renderizar aplicando un preset de fábrica
visualizador.bat mi_cancion.mp3 --preset barras_neon -o salida_neon.webm

# Renderizar a partir de un archivo de proyecto guardado
visualizador.bat --proyecto mi_proyecto.json -o salida.webm
```

---

## 5. Verificación de Integridad

Para comprobar que todas las funciones, el análisis de audio, el motor gráfico y la sincronía temporal estén operando al 100%:

```powershell
python tests/test_analisis.py
python tests/test_render.py --export
python tests/verificar_sincronia.py
python tests/test_proyecto.py
python tests/test_gui.py
python tests/test_lanzador.py
```
Todas las pruebas deben pasar en verde con 0 fallas.
