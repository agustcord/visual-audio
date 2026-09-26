# Plan de Implementación y Triage Factual (T12)

## 📌 Pedido Original del Capitán (textual)
> "C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins declara en que estado se encuentra el proyecto luego dime como vas a proseguir"

---

## 🧭 PASO 0: Bóveda Resuelta ($VAULT)
- **VAULT Local Resuelto:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\`
- **Estructura base verificada:** `index.md` (presente), `log.md` (presente, 147 líneas, última entrada T11).

---

## 🔍 Declaración Factual del Estado del Proyecto

### 1. Identidad, Entorno y Gobernanza
- **Propósito:** Creación de un visualizador de audio reactivo (onda y espectro) para el editor de video Drift (Drift 0.6.0 instalado en `C:\Program Files\Drift\drift.exe`), destinado a la edición de videos musicales propios.
- **Autor y Fundador:** Jonatan Córdoba (`sobre_este_plugins.txt`).
- **Arquitectura de Integración:** Herramienta externa desacoplada basada en Python 3.14 + FFmpeg 8.0.1 que genera overlays de video listos para importar y componer en Drift.
- **Modo de Fusión Ratificado:** Modo Trama (Screen) sobre fondo negro ratificado como default por el fundador en el Punto de Control T10. Modo Chroma Key disponible como ruta secundaria. Modo transparente (VP9 con alpha) ya implementado y testeado, a la espera del release de Drift 0.7.0.

### 2. Estado del Repositorio y Código en Disco
- **Rama:** `master`.
- **Árbol de trabajo:** Limpio (`working tree clean`).
- **Último commit:** `52c191c` ("T11: como se abre la herramienta (.bat en el MVP, .exe despues) y distribuir fuera de objetivos").
- **Módulos implementados y operando en `tools/visualizador/`:**
  - `analisis.py`: Análisis FFT en bandas logarítmicas, energía espectral ponderada, ventana causal (desvío 0 en ataques rítmicos), extracción de amplitud y forma de onda.
  - `parametros.py`: Esquema declarativo canónico (~25 parámetros) con tipado, rangos, valores por defecto, grupos y grafo de dependencias condicionales (`depende_de`).
  - `render.py`: Función determinista `cuadro(i)` sin estado interno entre cuadros, apta tanto para previsualización instantánea como exportación secuencial.
  - `salida.py`: Pipeline de exportación WebM/FFmpeg con soporte verificado en los tres modos de fondo (negro/trama, color/chroma, transparente).
  - `cli.py`: Interfaz de línea de comandos construida directamente desde el esquema declarativo.
  - `consola.py`: Manejo seguro de codificación Unicode en la consola de Windows (evita caídas por `cp1252`).
  - `estilos/base.py`: Contrato abstracto base para estilos de renderizado.
  - `estilos/barras.py`: Estilo `Barras` completo (gradientes, redondeo, tapas de pico, resplandor gaussiano acotado, reflejos) y subclase `Espejadas` (centrado vertical simétrico).

### 3. Evidencia Empírica de Pruebas Automáticas (55/55 verificaciones en verde)
- `python tests/test_analisis.py`: **36 comprobaciones pasadas, 0 fallas** (cuadros exactos en 24/25/30/60 fps, rango numérico 0..1 sin NaNs, alineación temporal causal sin pre-eco, respuesta plana con ruido rosa y curva log).
- `python tests/test_render.py --export`: **19 comprobaciones pasadas, 0 fallas** (`cuadro(i)` idempotente suelto vs secuencia, barrido exhaustivo de 70 combinaciones de parámetros, export exacto en WebM para los 3 fondos: 480 cuadros en 2.0s a 3.6s).
- `python tests/verificar_sincronia.py --motor propio`: **Alineación temporal perfecta (desvío +0 cuadros)** sobre 8 ataques rítmicos independientes de `pista_prueba.wav`.

### 4. Posición en la Ruta de Trabajo (`docs/RUTA_DE_TRABAJO.md`)
- Etapas concluidas:
  - Etapa 0 / PoC (T1-T6): Concluida.
  - Gate 2 (T7): Concluido (aprobación de MVP, presupuesto de 10 turnos, total 16-17 turnos).
  - Etapa 1 — Análisis de audio (T8): Concluida y cerrada.
  - Etapa 2 — Motor de dibujo y estilo Barras + Espejadas (T9): Concluida y cerrada (consumió 1 turno en lugar de los 2 presupuestados).
  - Punto de Control del Fundador (T10): Aprobado (aspecto Barras aceptado, Trama confirmada, corrimiento medido en `docs/COLOR_EN_TRAMA.md`).
  - T11 — Acceso y distribución: Cerrado (`visualizador.bat` asignado a Etapa 6, `.exe` a post-MVP, distribución excluida según Regla 16).
- **Hito Actual:** **ETAPA 3 — Estilo Onda**.
  - Precondiciones: Etapa 2 cerrada y Punto de Control aprobado (ambas cumplidas).
  - Estado: Lista para comenzar ejecución de código en Turno 2 tras aprobación del Gate.

---

## 🗺️ Propuesta de Próximos Pasos: Ejecución de Etapa 3 (Estilo Onda)

El Ciclo Core del Escuadrón Ani exige que Ani Arquitecta presente el plan para el Gate de aprobación del Capitán y asigne las ejecutoras en el documento sin invocarlas directamente en Turno 1.

### Justificación de Consulta Previa (Reglas 4 y 28 de SKILL.md)
No se invoca a `ani-pensadora` ni a `ani-investigadora` en esta fase porque todos los hechos técnicos, dependencias, contratos de interfaz y decisiones de diseño ya han sido establecidos, medidos y formalizados en `docs/ARQUITECTURA.md`, `docs/MVP.md` y `docs/RUTA_DE_TRABAJO.md`. No existen bifurcaciones arquitectónicas ni incógnitas de API pendientes para la Etapa 3.

---

### Desglose de Tareas Micro-Planificadas (Bite-Sized Tasks)

#### Tarea 3.1 — Implementación del Módulo de Estilo Onda
- **Responsable Asignada:** Ani Programadora (Fase 2 - Ejecución).
- **Archivo a crear:** `tools/visualizador/estilos/onda.py`
- **Especificación técnica:**
  - Clase `Onda(EstiloBase)` heredando de `tools.visualizador.estilos.base.EstiloBase`.
  - Método `dibujar(lienzo, datos, params)`:
    - Extrae la serie de forma de onda temporal (`datos.onda[i]`), un array normalizado de amplitud.
    - Calcula las coordenadas continuas `(x, y)` escaladas al ancho y alto definidos por los parámetros de posición (`ancho`, `alto`, `x`, `y`).
    - Dibuja la línea continua con el grosor configurado (`grosor_linea`, default 4 px).
    - Aplica color primario (`color`) y si `relleno == True`, cierra el polígono contra el eje base y rellena con opacidad configurada.
    - Soporta resplandor si `resplandor > 0`.
- **Criterio de Aceptación:** `Onda.dibujar(...)` genera una imagen PIL RGBA sin alterar el lienzo original y sin almacenar estado mutable entre llamadas.

#### Tarea 3.2 — Registro de Estilo y Declaración de Parámetros
- **Responsable Asignada:** Ani Programadora.
- **Archivos a modificar:**
  - `tools/visualizador/estilos/__init__.py`: Importar `Onda` y registrarla en el diccionario `ESTILOS` y la función `disponibles()`.
  - `tools/visualizador/parametros.py`:
    - Verificar que los parámetros específicos `grosor_linea` y `relleno` tengan declarada la tupla `estilos=("onda",)`.
    - Verificar que los parámetros exclusivos de barras (`n_barras`, `separacion`, `tapas_pico`) mantengan `estilos=("barras", "espejadas")`.
- **Criterio de Aceptación:** `python -m visualizador.cli --listar` muestra los tres estilos: `barras`, `espejadas`, `onda`.

#### Tarea 3.3 — Integración en la Suite de Pruebas y Validación Empírica
- **Responsable Asignada:** Ani Programadora.
- **Archivos a modificar/ejecutar:**
  - `tests/test_render.py`:
    - Incorporar casos específicos para el estilo `onda`.
    - Ejecutar el barrido de parámetros sobre los 3 estilos (`test_render.py` ya itera sobre `disponibles()`).
  - `tests/verificar_sincronia.py`:
    - Ejecutar `--motor propio --estilo onda` asegurando desvío 0 en los ataques conocidos.
- **Criterio de Aceptación:**
  - `python tests/test_render.py` pasa 100% en verde con los 3 estilos.
  - `python tests/verificar_sincronia.py --motor propio` confirma sincronía idéntica para `onda`.
  - `python -m visualizador.cli tests/fixtures/pista_espectro.wav --estilo onda --cuadro 150 -o build/prueba_onda.png` genera el fotograma correctamente.

#### Tarea 3.4 — Auditoría de Calidad y Criterios de Salida (Fase 3 - QA)
- **Responsable Asignada:** Ani Mal Humor (Fase 3 - QA).
- **Alcance de Auditoría:**
  - Criterio 3.1: Los tres estilos exportan a WebM en modo trama sin error.
  - Criterio 3.2: Cambiar de estilo con los mismos valores mantiene sincronía temporal exacta (MVP-3).
  - Criterio 3.3: Barrido de parámetros pasa en los tres estilos sin excepciones.
  - Criterio 3.4: Parámetros ajenos a `onda` son ignorados de forma limpia sin corromper el fotograma.

---

## 📋 Lista de Cotejo Previa a Emitir el Plan (8 Puntos Canónicos)
1. ¿Alguna tarea contradice una regla escrita de un documento canónico? -> **No**. Se respeta estrictamente `docs/RUTA_DE_TRABAJO.md`, `docs/MVP.md` y `docs/ARQUITECTURA.md`.
2. ¿Las herramientas, rutas, skills y comandos que nombro existen y hacen lo que digo? -> **Sí**. Verificados empíricamente con Python 3.14.6, FFmpeg 8.0.1 y suites automáticas.
3. ¿Cubre todos los requisitos del pedido, incluidos los que una corrida anterior ya cumplía? -> **Sí**. Diagnóstico factual completo de las 7 carpetas/archivos y plan de la siguiente etapa.
4. ¿Cada criterio de aceptación puede fallar (falsable)? -> **Sí**. Pruebas automatizadas por aserción matemática sobre píxeles y cuadros.
5. ¿Alguna tarea borra, sobrescribe o mueve algo, y si sí, está autorizado por el Capitán? -> **No**. Turno 1 mantiene producción intacta. En Turno 2 sólo se añade el nuevo estilo.
6. ¿Cité el documento canónico que gobierna? -> **Sí**. `docs/RUTA_DE_TRABAJO.md` y `docs/MVP.md`.
7. ¿Si el entregable corre desatendido, prevé detección de fallas, muerte silenciosa y plan de supervisión? -> **Sí**. `tests/test_render.py` y `verificar_sincronia.py` atrapan regresiones de rendimiento y alineación.
8. ¿El plan de validación emite veredicto definitivo en <= 48h? -> **Sí**. Las pruebas automáticas emiten veredicto en ~20 segundos.

---

## 🚦 Gate de Decisión del Capitán

Para avanzar a la **Fase 2 (Ejecución)** en el siguiente turno:
1. **Aprobación del Plan:** El Capitán autoriza formalmente la ejecución de la Etapa 3 (Estilo Onda) según los criterios de aceptación y el desglose de tareas presentado.
2. **Despacho del Escuadrón:** Tras la confirmación del Capitán, Ani Recepcionista derivará la tarea de implementación a **Ani Programadora** y la posterior verificación a **Ani Mal Humor**.
