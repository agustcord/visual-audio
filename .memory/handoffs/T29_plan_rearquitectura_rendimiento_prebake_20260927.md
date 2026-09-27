# Handoff T29 — Fase 1 Triage & Plan: Re-arquitectura de Rendimiento, Pre-Bake Persistente y Viewport LOD

- **Fecha:** 2026-09-27
- **Turno:** T29
- **Fase del Ciclo Core:** Fase 1 (Triage & Plan Estructurado)
- **Agente:** Ani Arquitecta (Tech Lead)
- **Estado de la entrega:** ✅ **PLAN DE IMPLEMENTACIÓN ESTRUCTURADO Y REGISTRADO EN MEMORIA**
- **Entregables Canónicos:**
  - `implementation_plan.md` (Raíz del proyecto)
  - `.memory/handoffs/T29_plan_rearquitectura_rendimiento_prebake_20260927.md` (Este handoff)
  - Actualización de `.memory/wiki/MOC_Handoffs.md` y `.memory/log.md`

---

## 1. Pedido Textual del Capitán y Marco de Trabajo

> "Buen día, si creo que lo que hace la industria, crea un archivo nuevo con el audio que le damos. Ok, que arquitecta haga el plan"

Tras el dictamen formal de FAIL emitido por el Capitán en T27 y la investigación técnica de estándares de la industria completada por Ani Investigadora en T28 (`.memory/wiki/Investigacion_estandar_industria_audio_reactividad.md`), el Capitán ha instruido explícitamente adoptar la estrategia estándar del software profesional de generar un archivo nuevo con el análisis del audio (Pre-Baking) y encomendó a Ani Arquitecta la confección del plan de re-arquitectura.

---

## 2. Frontera Declarada

### Archivos Creados / Modificados (Documentación, Planificación y Memoria):
- `implementation_plan.md`: Plan estructurado integral de re-arquitectura, especificando el formato de pre-bake persistente en disco (`.driftbake.npz`), el cómputo en memoria en tiempo constante $O(1)$, el pipeline gráfico de Viewport LOD en Tkinter Canvas, el desglose de tareas ordenadas para Ani Programadora y Ani Frontend en Fase 2, y los criterios de aceptación falsables para Ani Mal Humor en Fase 3.
- `.memory/handoffs/T29_plan_rearquitectura_rendimiento_prebake_20260927.md`: Este handoff durable de auditoría técnica.
- `.memory/wiki/MOC_Handoffs.md`: Índice de auditoría actualizado con la entrada del turno T29.
- `.memory/log.md`: Bitácora histórica append-only actualizada con el registro del turno T29.

### Archivos Intactos (Explícitamente NO tocados):
- Cero líneas modificadas en el código fuente de producción (`tools/visualizador/analisis.py`, `render.py`, `gui.py`, `reproductor.py`, `parametros.py`, `proyecto.py`, `salida.py`, `estilos/`).
- Cero líneas modificadas en la suite de pruebas automatizadas (`tests/`).
- Cero archivos modificados en presets (`presets/`) o lanzador (`visualizador.bat`).
- Respeto estricto del candado de Fase 1: cero mutaciones en código antes de la aprobación del Gate del Capitán.

---

## 3. Lo que se verificó vs. lo que se infirió

### Verificado Factualmente (Evidencia Empírica de Disco y Contexto):
1. **Punto de Partida Factual:** Se constató el informe de investigación técnica de Ani Investigadora en T28 (`.memory/wiki/Investigacion_estandar_industria_audio_reactividad.md`, commit `97cc0d8`).
2. **Causa Raíz Espectral:** La FFT completa en CPU de una pista de 3 minutos toma 1.251,09 ms en NumPy 2.5.1 sobre Python 3.14.6; recalcular la FFT completa ante cada movimiento de slider genera congelamientos continuos.
3. **Causa Raíz Gráfica:** El dibujo a 1080p en Pillow toma 38,78 ms y la transferencia `ImageTk.PhotoImage` al `Canvas` de Tkinter toma 22,84 ms (total 61,62 ms por cuadro), imponiendo un límite físico estricto de 16,2 FPS en CPU.
4. **Viabilidad de Pre-Bake y Proyección Matricial:** La matriz STFT densa $\mathbf{S} \in \mathbb{R}^{F \times 2049}$ de una canción de 3 minutos ocupa 84,42 MB en RAM. Su proyección contra un banco de 64 bandas ($\mathbf{S} \times \mathbf{M}$) se completa en 7,82 ms para toda la canción y en 0,018 ms para un cuadro individual.
5. **Viabilidad de Viewport LOD:** A resolución nativa de visor (~640×360), el tiempo total de render + blit en Canvas desciende a 7,72 ms por cuadro, habilitando > 120 FPS teóricos en CPU y liberando más del 50% del presupuesto de 16,66 ms correspondiente a 60 FPS estables.
6. **Entorno y Dependencias:** Se constató que no se requieren dependencias binarias externas (Regla 13 intacta).

### Inferido:
- Se infiere que la reducción del tiempo de recálculo de 1.251 ms a < 10 ms (una aceleración de 160x) sumada al renderizado directo a resolución del viewport erradica de forma definitiva cualquier sensación de congelamiento o trabas en la interfaz gráfica experimentada por el Capitán.

---

## 4. Decisiones Tomadas y Justificación

1. **Adopción de la Directriz del Capitán: Archivo `.driftbake.npz` Persistente en Disco:**
   - En lugar de limitarse a una caché volátil en memoria RAM, se define un formato estructurado comprimido persistido en disco (`<ruta_audio>.driftbake.npz`). Al volver a abrir la aplicación o cargar el mismo archivo, el tiempo de apertura desciende a menos de 100 ms con cero llamadas a FFmpeg y cero recálculos de Fourier.
   - Incluye hash SHA-256 (tamaño + mtime + bytes iniciales) para invalidación automática si el usuario edita o reemplaza el audio original.
2. **Desacople en Dos Fases del Motor de Audio (`analisis.py` / `bake.py`):**
   - *Fase de Horneado (Bake):* Decodificación PCM y cálculo de la matriz STFT causal densa y envolvente de onda cruda (ejecutada 1 sola vez en la vida del archivo).
   - *Fase de Proyección Dinámica:* Operaciones de álgebra lineal puras sobre la matriz densa en RAM ($O(1)$), evaluadas en milisegundos ante cambios de sliders.
3. **Viewport-Native LOD en Tkinter Canvas sin Pérdida de Invarianza (MVP-5):**
   - Se erradica el costoso e ineficiente patrón de renderizar a 1080p para luego achicar con `Image.resize` bilineal en CPU.
   - La previsualización interactiva renderiza directamente a la escala visible del widget Canvas (`cw`, `ch`), reduciendo en 9x el volumen de píxeles procesados por Pillow.
   - La exportación final a video continúa ejecutando el mismo algoritmo a resolución completa (1920×1080) fotograma a fotograma hacia FFmpeg, garantizando que el video exportado sea idéntico y de máxima fidelidad.
4. **Desglose Estricto de Roles para la Fase 2:**
   - **Ani Programadora:** Implementación del subsistema de pre-bake (`bake.py`), desacople de capas en `analisis.py`, refactorización de `Render` con soporte de Viewport LOD y suite de tests unitarios/benchmarks.
   - **Ani Frontend:** Integración en `gui.py` del flujo de carga/horneado, conexión de Viewport LOD en Canvas a 60 FPS, desacople reactivo de sliders y sincronía de transporte con `reproductor.py`.
   - **Ani Mal Humor:** Auditoría técnica de QA en Fase 3 verificando los criterios falsables CA-REARQ-1 a CA-REARQ-6 con instrumental de medición de tiempos.

---

## 5. Dónde Retomar (Próximo Paso Inmediato)

1. **Gate del Capitán:** Ani Recepcionista presenta el plan estructurado `implementation_plan.md` al Capitán y aguarda su aprobación explícita (*"procede"*).
2. **Fase 2 de Ejecución Técnica:** Una vez otorgada la aprobación del Capitán, Ani Recepcionista deriva secuencialmente las tareas técnicas:
   - Primero a **Ani Programadora** para el Bloque 1 (Motor de Audio, Pre-Bake y Render LOD).
   - Luego a **Ani Frontend** para el Bloque 2 (Integración en GUI Tkinter y Transporte a 60 FPS).
3. **Fase 3 de QA:** Derivación a **Ani Mal Humor** para la auditoría exhaustiva con los 6 criterios falsables.

---

## 6. Lo que quedó abierto

- Ningún bloqueo arquitectónico pendiente. El diseño respeta al 100% las directrices del Capitán, las reglas de gobernanza del Escuadrón Ani y las restricciones del entorno local.
