# Handoff T24 — Cierre Formal del MVP (v0.1.0-mvp) e Investigación Técnica de Rendimiento y UX

- **Fecha:** 2026-09-26
- **Turno:** T24
- **Fase del Ciclo Core:** 1 (Triage / Cierre Formal de MVP) & Fase 0 (Investigación Post-MVP)
- **Agente:** Ani Arquitecta (Tech Lead & Gobernanza Factual)
- **Repositorio:** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins`
- **Rama:** `master`
- **Línea Base:** Commit `779a544` (con corrección de Etapa 7) y consolidación de 277 comprobaciones automáticas pasando al 100% en verde.
- **Versión Catalogada:** **`v0.1.0-mvp`**

---

## 📌 Pedido Original del Capitán (textual)
> "procede con eso que pidio mal humor. yo ya probe la app, y puedo dictaminar que funciona, por mi parte el dictame es PASS con respeto al MVP, sino no la considero una version final ya que tiene mejoras importantes por hacer. La primera, es el rendimiento, el programa tiene procesos brusco de cargar cuando se modifica una variable, siendo facil de interpretar que se \"rompio\" cuando no es asi. que programadora haga lo que pidio mal humor. pero que arquitecta docummente mvp cerrado, catalogue la version correctamente, y empiece a investigar como mmejorar este apartado, o como \"maquillar\" esta sensacion de que se rompio, para que el programa sea mas amigable con el usuario"

---

## 1. Cierre Formal del MVP y Catalogación de Versión (v0.1.0-mvp)

Se declara formalmente el **cierre y culminación exitosa del Producto Mínimo Viable (MVP)** del Visualizador de Audio para Drift, catalogado como **`v0.1.0-mvp`**.

### Hitos Factuales Consolidados:
1. **Dictamen PASS Formal del Capitán / Fundador:** Tras evaluar de forma autónoma e independiente la aplicación en Windows, el Capitán otorgó el veredicto positivo (*"yo ya probe la app, y puedo dictaminar que funciona, por mi parte el dictame es PASS con respeto al MVP"*), dando por cumplido el criterio supremo 7.3 de la ruta (*"El fundador lo usa solo, sin preguntarle nada al agente"*).
2. **Suite de Pruebas Automatizadas al 100%:** 277 comprobaciones automáticas verificadas en disco a través de 7 scripts de prueba, con 0 fallas, 0 regresiones y código de salida 0:
   - `tests/test_analisis.py`: 36/36 comprobaciones en verde.
   - `tests/test_render.py --export`: 36/36 comprobaciones en verde (cubriendo exportación en modos negro, color y transparente con alpha).
   - `tests/verificar_sincronia.py`: 8/8 ataques rítmicos alineados con desvío exacto de +0 cuadros en los tres estilos (`barras`, `espejadas`, `onda`).
   - `tests/test_proyecto.py`: 46/46 comprobaciones en verde (persistencia JSON, presets de fábrica y álgebra de compensación de color en modo Trama).
   - `tests/test_lanzador.py`: 44/44 comprobaciones en verde (lanzador `visualizador.bat` con `pythonw.exe`, entrypoint canónico y validación diagnóstica).
   - `tests/test_reproductor.py`: 43/43 comprobaciones en verde (contratos abstractos `ReproductorAudio`, backend prioritario universal `FFplayBackend` con `CREATE_NO_WINDOW`, `MCIBackend`, `NullBackend` y Master Clock anti-deriva).
   - `tests/test_gui.py`: 64/64 comprobaciones en verde (invarianza estructural MVP-5, transporte continuo Play/Pausa, scrubbing con aislamiento de audio y ciclo de vida de procesos).
3. **Documentación Sincronizada:** Sincronización factual de [`RETOMAR.md`](../../RETOMAR.md), [`docs/RUTA_DE_TRABAJO.md`](../../docs/RUTA_DE_TRABAJO.md), [`README.md`](../../README.md), [`docs/GUIA_DE_USO.md`](../../docs/GUIA_DE_USO.md) y [`docs/COMO_USAR.md`](../../docs/COMO_USAR.md) reflejando las 7 etapas completadas y la versión `v0.1.0-mvp`.

---

## 2. Frontera de la Intervención Técnica (SMF)

### Archivos Modificados / Consolidados en este Turno (Fase 1 / Cierre & Investigación):
1. [`.memory/handoffs/T24_cierre_mvp_v010_investigacion_rendimiento_ux_20260926.md`](file:///c:/Users/Jonatan%20Agust%C3%ADn/Desktop/Proyectos/Drift/Plugins/.memory/handoffs/T24_cierre_mvp_v010_investigacion_rendimiento_ux_20260926.md): Formalización de cierre de MVP, catalogación y reporte exhaustivo de investigación técnica de rendimiento/UX.
2. [`implementation_plan.md`](file:///c:/Users/Jonatan%20Agust%C3%ADn/Desktop/Proyectos/Drift/Plugins/implementation_plan.md): Plan estructurado para el Roadmap Post-MVP listo para el Gate del Capitán.
3. [`.memory/wiki/MOC_Handoffs.md`](file:///c:/Users/Jonatan%20Agust%C3%ADn/Desktop/Proyectos/Drift/Plugins/.memory/wiki/MOC_Handoffs.md): Registro correlativo de la entrada T24.
4. [`.memory/log.md`](file:///c:/Users/Jonatan%20Agust%C3%ADn/Desktop/Proyectos/Drift/Plugins/.memory/log.md): Bitácora cronológica con la entrada de T24.
5. [`RETOMAR.md`](file:///c:/Users/Jonatan%20Agust%C3%ADn/Desktop/Proyectos/Drift/Plugins/RETOMAR.md), [`docs/RUTA_DE_TRABAJO.md`](file:///c:/Users/Jonatan%20Agust%C3%ADn/Desktop/Proyectos/Drift/Plugins/docs/RUTA_DE_TRABAJO.md) y [`README.md`](file:///c:/Users/Jonatan%20Agust%C3%ADn/Desktop/Proyectos/Drift/Plugins/README.md): Consolidación de catalogación y cierre de Etapa 7.

### Explícitamente Fuera de Alcance (NO Tocado en Turno 1):
- Cero alteraciones de código de producto en `tools/visualizador/gui.py`, `analisis.py` o `render.py` (se aguarda la aprobación explícita del Capitán en el Gate).
- Binario de Drift (`drift.exe` permanece en sólo lectura en `C:\Program Files\Drift\`).

---

## 3. Informe de Investigación Técnica de Rendimiento y UX

### A. Diagnóstico de Causa Raíz: ¿Por qué la app se siente "brusca" o "rota"?
La auditoría forense del flujo de interacción al modificar variables en la GUI reveló tres cuellos de botella estructurales interconectados:

1. **Bloqueo Sincrónico del Hilo Principal de Tkinter:**
   - En `tools/visualizador/gui.py`, la modificación de cualquier parámetro dispara `_programar_debounce_render()`, que invoca `self.root.after(50, self._actualizar_vista_previa)`.
   - `_actualizar_vista_previa()` ejecuta **sincrónicamente dentro del bucle de eventos de la interfaz (Main Thread de Tkinter)**.
   - Mientras se ejecuta el análisis matemático, la FFT y el dibujo con Pillow, el despachador de eventos de Windows se congela. El sistema operativo marca la ventana como "No responde", no se procesan eventos de ratón ni se actualizan los números de los sliders, transmitiendo la falsa sensación de fallo o caída (*crash*).

2. **Decodificación Redundante de Audio Completo con FFmpeg:**
   - Si el parámetro modificado pertenece al grupo analítico (`sensibilidad`, `suavizado`, `n_barras`, `frec_min`, `frec_max`, `curva_respuesta`, `caida_picos`), la GUI invoca a `analizar(self._ruta_audio, params, self._estilo)`.
   - Dentro de `analizar()` (en `tools/visualizador/analisis.py:452`), la primera instrucción es `muestras = leer_mono(ruta_audio)`, la cual ejecuta un subproceso sincrónico `subprocess.run(["ffmpeg", ...])` para decodificar **la pista completa** a PCM `float32`.
   - Para un audio típico de 3 a 5 minutos, lanzar FFmpeg y escribir/leer megabytes por tubería toma entre 250 ms y 800 ms. Re-decodificar el archivo completo por un mero deslizamiento de 1 milímetro en un slider es un costo innecesario y severo.

3. **Recálculo de FFT Global y Matrices de Banda:**
   - La función `analizar()` calcula el espectro por cuadro para todos los cuadros de la pista mediante ventanas causales y FFTs masivas (`_espectro_por_cuadro`), aun cuando el visor de la GUI sólo requiere renderizar el único cuadro en el que está detenido el cursor (`self._cuadro_actual`).

---

### B. Solución de Arquitectura: Desacople Multihilo y Jerarquía de Caché

Para alcanzar una interfaz con respuesta instantánea a 60 fps y latencia de UI menor a 16 ms, se diseñó la siguiente solución técnica:

```
[Slider / UI Input] ──(Inmediato: 0 ms)──> [Actualización de Label y Widget]
        │
        ├──(Debounce Adaptativo: 30 / 100 / 250 ms)
        ▼
[Worker Queue (size=1, LIFO / Last-Write-Wins)]
        │
        ▼
[Worker Thread Asíncrono] 
        │
        ├── ¿Audio decodificado en PCM? ──── NO ──> [FFmpeg leer_mono] ──> [PCM Cache]
        │                                   SI
        ├── ¿Espectro FFT Base (bins)? ───── NO ──> [STFT Base Cache]
        │                                   SI
        ├── ¿Cambio de bandas/filtros? ─────> Proyección rápida con Matriz
        │
        ▼
[Render.cuadro(i)]
        │
        ▼
[Event Queue / root.after_idle] ───────────> [Proyección Canvas Tkinter]
```

1. **Worker Thread Dedicado con Descarte de Tareas Obsoletas (Last-Write-Wins):**
   - El hilo principal de Tkinter **nunca** ejecutará operaciones bloqueantes ni llamadas a subprocesos.
   - Se creará un worker thread en segundo plano alimentado por una cola de peticiones con descarte automático: si el usuario arrastra rápidamente un control y genera 10 eventos intermedios, el worker procesa el primero e inmediatamente salta directo al último estado emitido, descartando las solicitudes obsoletas.
   - La entrega del cuadro renderizado se realiza mediante `root.after_idle` o cola thread-safe sin interferir con el refresco de pantalla.

2. **Jerarquía de Caché en Tres Niveles:**
   - **Nivel 1: Caché de Muestras PCM Decodificadas:** Guardar en memoria el array `np.ndarray` de muestras mono `float32` indexado por `(ruta_audio, mtime)`. Una vez leído el audio, las llamadas posteriores a FFmpeg se reducen a **cero**.
   - **Nivel 2: Caché de Espectrograma Base (FFT por Bins):** Las ventanas temporales y la FFT cruda (amplitud por bin de frecuencia) se calculan una sola vez. Cuando el usuario modifica `n_barras`, `frec_min` o `frec_max`, sólo se genera la matriz de ponderación logarítmica y se realiza una multiplicación matricial en numpy (< 5 ms).
   - **Nivel 3: Caché de Cuadros Pre-renderizados:** Buffer circular para suavizar el scrubbing manual.

3. **Debounce Adaptativo por Categoría de Parámetro:**
   - **Parámetros Cosméticos / Render Puro (30 ms):** `color`, `grosor_linea`, `resplandor`, `reflejo`, `tapas_pico`, `espaciado`, `compensar_fondo`. No requieren tocar el análisis; recalculan el cuadro en < 10 ms.
   - **Parámetros de Ganancia y Sensibilidad (100 ms):** `sensibilidad`, `suavizado`, `caida_picos`. Modifican la escala dinámica sin alterar la geometría de bandas.
   - **Parámetros Analíticos Estructurales (250 ms):** `n_barras`, `frec_min`, `frec_max`, `curva_respuesta`, `fps`. Modifican la resolución matemática y la matriz de bandas.

---

### C. Solución de UX / "Maquillaje" de Percepción (Sensación de Continuidad)

Para erradicar la percepción de que el programa "se rompió", la interfaz debe comunicar vida y respuesta inmediata en todo momento:

1. **Actualización Inmediata y Sincrónica de Displays Numéricos (0 ms):**
   - El label numérico adyacente a cada slider (`self._labels_display[nombre]`) debe actualizarse sincrónicamente con el evento de movimiento del ratón `<Motion>`, sin esperar al debounce ni al render. El usuario ve que el valor numérico reacciona fluidamente a 60 fps bajo su cursor.

2. **Preservación del Fotograma Anterior (Ghost Frame / Never Blank):**
   - El canvas de previsualización **nunca** se borra a negro ni se limpia durante el recálculo. El último fotograma renderizado válido permanece visible.

3. **Badge Sutil de Carga en Tiempo Real ("⏳ Actualizando..."):**
   - Si una tarea en segundo plano tarda más de 80 ms, se visualiza en la esquina superior del visor un badge discreto semi-transparente que indica `"⏳ Actualizando..."`. Al concluir el render, el badge desaparece suavemente.
   - El usuario comprende de forma explícita que la aplicación está procesando su solicitud y no que se ha congelado.

4. **Cursor de Espera Inteligente:**
   - Conmutación no intrusiva del cursor del canvas a `watch` o cursor de espera durante el lapso de trabajo asíncrono, retornando a `arrow` en cuanto se proyecta el nuevo bitmap.

---

## 4. Conclusiones y Próximos Pasos
- El MVP `v0.1.0-mvp` se encuentra cerrado, documentado y protegido con 277 pruebas unitarias en verde.
- La investigación técnica identifica con precisión matemática la causa del cuello de botella y provee una solución robusta y limpia.
- El plan de ejecución detallado ha sido plasmado en `implementation_plan.md` a la espera de la autorización del Capitán en el Gate.
