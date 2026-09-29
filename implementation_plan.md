# Plan de Implementación — Fase 1: Publicación en GitHub bajo Licencia No Comercial

**Documento canónico del ciclo de trabajo del Escuadrón Ani.**  
**Fecha:** 2026-09-29  
**Turno:** T46  
**Fase del Ciclo Core:** Fase 1 (Triage & Plan)  
**Autor:** Ani Arquitecta (Tech Lead)  
**Bóveda resuelta ($LOCAL_VAULT):** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory`  

---

## 📌 Pedido Original del Capitán (textual)
> "quedo muy bien. arme todo para publicar en github de manera publica, descripcion, instalación, capturas. licencia libre de uso, siempre y cuiando no se venda el software o se use como complemento de un producto comercial"

---

## 1. Justificación de Consulta en Fase 0
- **Veto de sobre-ingeniería / Justificación en una línea:** No se convocó a `ani-pensadora` ni a `ani-investigadora` porque los hechos fácticos del repositorio (arquitectura de la aplicación, identidad gráfica de marca "Visual Audio", tests pasando al 100% y requisitos de empaquetado) están completamente consolidados en disco, y la directiva del Capitán respecto a la licencia ("libre de uso no comercial, prohibida su venta o uso como complemento comercial") encaja con exactitud jurídica en la licencia estándar internacional **PolyForm Noncommercial License 1.0.0**, sin ambigüedades técnicas ni tradeoffs contrapuestos.

---

## 2. Diagnóstico y Estrategia de Publicación en GitHub

### 2.1 Estado Actual del Repositorio
1. **Identidad Visual y Denominación:**
   - La aplicación gráfica fue modernizada integralmente en el Turno T44 y certificada con PASS en T45 por Ani Mal Humor, consolidando el nombre oficial **"Visual Audio"**, el sistema de tokens Dark Zinc 950/900 con acentos cian/violeta y su logo vectorial paramétrico.
   - Sin embargo, el archivo `README.md` actual en la raíz aún titula el proyecto con el nombre genérico histórico (`# Visualizador de audio para Drift`), arrastra secciones desactualizadas de triage previas y carece de la estructura visual y de presentación que demanda un repositorio público moderno.
2. **Licenciamiento y Marco Legal:**
   - El proyecto carece actualmente de un archivo `LICENSE` o `LICENSE.md` en la raíz.
   - En `README.md` solo se menciona que Drift es GPLv3 y que este proyecto no incluye código de Drift.
   - Se requiere la formalización estricta de una licencia que otorgue libertad total de uso gratuito y estudio a personas creadoras, músicos y educadores, pero que prohíba de forma explícita y vinculante su venta, comercialización o integración como complemento de un producto comercial cerrado.
3. **Dependencias y Reproducibilidad:**
   - No existe un archivo `requirements.txt` ni `pyproject.toml` en la raíz del repositorio.
   - Quien clone el repositorio desde GitHub debe deducir manualmente las dependencias de Python (`numpy`, `pillow`, `scipy`) y las herramientas externas (`ffmpeg`, `ffplay`).
4. **Galería de Capturas de Pantalla (Showcase Visual):**
   - Existen los assets vectoriales y compilados (`assets/logo/visual_audio_logo.svg`, `visual_audio_512.png`, `visual_audio.ico` y `preview_animacion.html`), pero **no existe una carpeta `assets/screenshots/`** con capturas reales y en alta resolución de la nueva interfaz "Visual Audio" luciendo el tema Dark Zinc 950/900 y sus 3 estilos (`barras`, `espejadas`, `onda`).
5. **Higiene y Seguridad para Repositorio Público:**
   - Se constató empíricamente con `grep` que en `tools/`, `assets/`, `tests/` y `presets/` **no existen rutas locales absolutas** (cero menciones a rutas privadas del usuario).
   - El archivo `.gitignore` ya contempla exclusiones de builds, temporales y scratch, pero debe verificarse de cara al release público para garantizar que solo se publiquen los archivos de producto y documentación pertinentes.

---

## 3. Arquitectura Legal: Selección y Formalización de Licencia

### 3.1 Análisis Comparativo de Opciones
1. **PolyForm Noncommercial License 1.0.0 (Selección Primaria):**
   - Redactada específicamente para código de software por comités de abogados expertos en propiedad intelectual y código abierto (PolyForm Project / Heather Meeker).
   - Define *Noncommercial Purpose* con rigor jurídico: cualquier uso que no esté destinado primariamente a obtener una ventaja comercial o compensación monetaria directa o indirecta.
   - Prohíbe de forma taxativa la venta directa del software, el cobro por distribución o descarga, y su integración/empaquetado como complemento (*plugin* o *add-on*) de una suite o producto comercial.
   - Permite a cualquier creador de contenido, músico o aficionado usar la herramienta de forma 100% gratuita, clonar el repositorio, modificarlo para uso personal o no comercial y compartirlo.
2. **Creative Commons Attribution-NonCommercial 4.0 (CC BY-NC 4.0):**
   - Muy conocida entre creadores y diseñadores, pero la propia organización Creative Commons desaconseja expresamente su uso para código fuente debido a la falta de cláusulas sobre patentes, binarios y compilación.
3. **Decisión Arquitectónica:**
   - Se adopta formalmente **PolyForm Noncommercial License 1.0.0** como la licencia oficial del software en el archivo `LICENSE`.
   - Se incorpora un **Preámbulo y Guía de Convivencia para Creadores (Creator-Friendly Clarification)** tanto en `LICENSE` como en `README.md`, redactado en español e inglés, que clarifica sin dudas:
     * ✅ **PERMITIDO Y ALENTADO:** Músicos, artistas visuales, editores y creadores de contenido que usen "Visual Audio" para producir sus propios videos musicales, subirlos a YouTube, Instagram, TikTok o distribuirlos en sus plataformas (incluso en canales con monetización publicitaria estándar activa), ya que el software actúa como herramienta utilitaria para generar el metraje.
     * ❌ **ESTRICTAMENTE PROHIBIDO:** Vender este software, cobrar por licencias de uso, revenderlo compilado, empaquetarlo dentro de un producto o plugin comercial de pago, o prestarlo como servicio de pago (SaaS) sin un acuerdo comercial explícito por escrito con el autor (**Jonatan Córdoba**).

---

## 4. Diseño del Repositorio Público: Componentes y Especificación

### 4.1 Archivo `README.md` (Vitrina Pública)
El nuevo `README.md` se diseñará bajo estándares de repositorios *tier-1* de GitHub:
1. **Encabezado Visual:**
   - Logo oficial centrado (`assets/logo/visual_audio_512.png`).
   - Título formal: `# Visual Audio`.
   - Subtítulo: *Visualizador de audio reactivo de alto rendimiento para Drift y suites de video.*
   - Badges dinámicos/consistentes:
     * Licencia: `PolyForm Noncommercial 1.0.0`
     * Plataforma: `Windows 10 / 11`
     * Python: `3.10+`
     * Aceleración: `Viewport LOD @ 60 FPS`
     * Integración: `Drift 0.6.0+ (Modo Trama / Screen)`
2. **Propuesta de Valor:**
   - Explicación concisa y sin rodeos de qué problema resuelve: generar overlays de audio-reactividad (espectrograma FFT y osciloscopio de onda) con precisión matemática, soporte de canal transparente / modo Trama ($\Delta E \approx 0$) y previsualización interactiva a 60 fps con pre-bake en tiempo constante $O(1)$.
3. **Galería Visual (Screenshots):**
   - Captura principal de la interfaz "Visual Audio" con estilo Barras y tema Dark Zinc.
   - Comparativa o carrusel de estilos: Barras, Barras Espejadas y Onda.
   - Enlace/mención a la animación vectorial interactiva (`assets/logo/preview_animacion.html`).
4. **Guía de Instalación Paso a Paso (Windows):**
   - **Requisito 1: Python 3.10 o superior** (marcar "Add Python to PATH" durante la instalación).
   - **Requisito 2: FFmpeg** (`ffmpeg.exe` y `ffplay.exe` accesibles en el sistema).
   - **Paso 1: Clonar el repositorio** (`git clone ...`).
   - **Paso 2: Instalar dependencias** (`pip install -r requirements.txt`).
5. **Modo de Uso:**
   - **Lanzamiento rápido (GUI):** Doble clic en `visualizador.bat` (sin consola negra) o `python -m visualizador`.
   - **Línea de comandos (CLI):** Ejemplos de uso con argumentos (`visualizador.bat pista.wav -o salida.webm --preset barras_neon`).
   - **Flujo de Composición en Drift:** Importar el video WebM en una pista superior y fijar el modo de fusión en **Trama (Screen)**.
6. **Empaquetado y Requisitos del Sistema:**
   - Tabla clara de dependencias (`numpy`, `pillow`, `scipy`).
7. **Licencia y Créditos:**
   - Mención explícita a la autoría de Jonatan Córdoba.
   - Resumen claro de la licencia PolyForm Noncommercial 1.0.0.
   - Aclaración de independencia de CutWire Studios (creadores de Drift).

### 4.2 Archivo `requirements.txt` y `pyproject.toml`
1. `requirements.txt`:
   ```text
   # Dependencias de Visual Audio
   numpy>=1.24.0
   pillow>=10.0.0
   scipy>=1.10.0
   ```
2. `pyproject.toml`:
   - Configuración declarativa moderna bajo especificación PEP 517/518 y PEP 621.
   - Metadatos del proyecto: nombre `"visual-audio"`, versión `"0.1.0"`, autor `"Jonatan Córdoba"`, licencia `"PolyForm-Noncommercial-1.0.0"`.
   - Definición de entrypoints para CLI y GUI: `visual-audio = "visualizador.cli:main"`.

### 4.3 Estrategia y Generación de Capturas de Pantalla (`assets/screenshots/`)
Para evitar capturas manuales recortadas o con artefactos de compresión:
1. Crear el directorio `assets/screenshots/`.
2. Crear un script automatizado `tools/generar_capturas.py` que utilice la propia infraestructura de render y de `VentanaVisualizador` para generar capturas limpias y oficiales:
   - `01_interfaz_principal_barras.png`: Vista completa de la GUI con audio de muestra cargado, visualizador en barras cian y controles Dark Zinc.
   - `02_estilo_onda.png`: Vista de la GUI con el estilo Onda simétrica activa.
   - `03_estilo_barras_espejadas.png`: Vista de la GUI con el estilo de barras de frecuencia espejadas.
   - `04_composicion_drift_trama.png`: Gráfico/composición demostrativa del metraje renderizado sobre video en Drift con modo Trama.
3. Las imágenes se guardan optimizadas en formato PNG en `assets/screenshots/` y se enlazan de forma relativa en el `README.md`.

---

## 5. Estructura de Tareas para Fase 2 (Ejecución Especializada)

### Tarea 2.1 — Formalización de Licencia y Legal (`LICENSE`) (Ani Escritora / Ani Frontend)
- Redactar `LICENSE` en la raíz con el texto íntegro y oficial de **PolyForm Noncommercial License 1.0.0**.
- Incluir preámbulo canónico de autoría de Jonatan Córdoba y la clarificación expresa para creadores y músicos (Creator-Friendly FAQ).

### Tarea 2.2 — Empaquetado y Dependencias (`requirements.txt` y `pyproject.toml`) (Ani Programadora)
- Crear `requirements.txt` en la raíz con versiones compatibles de `numpy`, `pillow` y `scipy`.
- Crear `pyproject.toml` estructurado con metadatos del paquete y entrypoints.
- Verificar que la importación e instalación en limpio no presente advertencias ni dependencias circulares.

### Tarea 2.3 — Generación de Galería de Capturas de Pantalla (Ani Frontend)
- Crear el directorio `assets/screenshots/`.
- Desarrollar `tools/generar_capturas.py` para capturar programáticamente fotogramas y la interfaz con el tema oficial Dark Zinc 950/900 y los tres estilos (`barras`, `onda`, `espejadas`).
- Almacenar los 4 PNGs de alta fidelidad en `assets/screenshots/`.

### Tarea 2.4 — Redacción del Nuevo `README.md` Público (Ani Frontend / Ani Normal)
- Redactar el nuevo `README.md` profesional: encabezado con logo, badges, descripción de valor, galería de capturas, guía de instalación paso a paso en Windows, ejemplos de uso (GUI/CLI), guía de composición en Drift, tabla de estilos/presets y sección de licencia no comercial.
- Preservar los enlaces canónicos a la documentación extendida en `docs/` (`GUIA_DE_USO.md`, `COLOR_EN_TRAMA.md`, etc.).

### Tarea 2.5 — Auditoría de Higiene y Preparación de Repositorio (Ani DevOps)
- Verificar `.gitignore` para asegurar que el repositorio público quede limpio de archivos temporales, builds o secretos.
- Auditar que ningún archivo de documentación pública o empaquetado contenga rutas absolutas del usuario o dependencias no declaradas.
- Verificar la ejecución limpia de `visualizador.bat` y de la suite completa de pruebas.

---

## 6. Criterios de Aceptación Falsables para Fase 3 (Ani Mal Humor)

- **CA-PUB-1 (Licencia PolyForm Noncommercial 1.0.0):**
  * El archivo `LICENSE` existe en la raíz del repositorio.
  * Contiene textualmente la cláusula de "Noncommercial Purpose" de la licencia PolyForm Noncommercial 1.0.0.
  * Contiene el nombre del autor "Jonatan Córdoba" y la cláusula expresa que prohíbe su venta directa o integración como complemento de un producto comercial.
- **CA-PUB-2 (Empaquetado y Requisitos):**
  * El archivo `requirements.txt` existe en la raíz con `numpy`, `pillow` y `scipy`.
  * El archivo `pyproject.toml` existe con los metadatos oficiales del proyecto ("Visual Audio", versión 0.1.0, licencia PolyForm-Noncommercial-1.0.0).
  * La instalación con `pip install -r requirements.txt` o importación de librerías resuelve sin errores de dependencias faltantes.
- **CA-PUB-3 (Galería de Capturas de Pantalla):**
  * La carpeta `assets/screenshots/` existe en el repositorio y contiene al menos 3 capturas de pantalla reales en formato PNG (estilos barras, onda y espejadas con tema Dark Zinc).
  * Todas las imágenes son archivos PNG válidos de tamaño $> 10\text{ KB}$ y no archivos vacíos o corruptos.
- **CA-PUB-4 (Estructura y Calidad del README.md):**
  * `README.md` incluye el título "Visual Audio", badges de versión, plataforma, Python y licencia PolyForm Noncommercial 1.0.0.
  * Incluye la guía de instalación paso a paso para Windows (Python, FFmpeg, pip).
  * Incluye instrucciones claras de arranque tanto para GUI (`visualizador.bat`) como para CLI (`python -m visualizador`).
  * Incluye las imágenes de `assets/screenshots/` embebidas mediante rutas relativas válidas.
- **CA-PUB-5 (Ausencia de Rutas Locales en Archivos Públicos):**
  * La búsqueda de rutas absolutas de usuario (ej. `C:\Users\`) en `README.md`, `LICENSE`, `requirements.txt`, `pyproject.toml` y `tools/` retorna 0 coincidencias.
- **CA-PUB-6 (Invarianza de Lanzador y Entrypoint):**
  * `visualizador.bat` y `python -m visualizador` se ejecutan sin errores y levantan la ventana "Visual Audio" con icono y tema Dark Zinc.
- **CA-PUB-7 (Invarianza de la Suite Consolidada):**
  * La suite completa de 8 pruebas (`test_bake`, `test_analisis`, `test_render`, `test_proyecto`, `test_reproductor`, `test_lanzador`, `verificar_sincronia`, `test_gui`) ejecuta al 100% en verde (mínimo 462 comprobaciones exitosas, 0 fallas, exit code 0).

---

## 7. Protocolo de Gate del Capitán
Nadie modifica código de producto ni publica repositorios en remoto hasta que el Capitán revise este plan de arquitectura y emita su aprobación explícita ("procede" / "apruebo").
