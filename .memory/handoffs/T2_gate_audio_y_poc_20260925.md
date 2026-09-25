---
tipo: "handoff"
turno: 2
agente: "Kiro"
fecha: 2026-09-25
estado: "cerrado — PoC-1..3 verdes, PoC-4..6 esperan a Drift"
---

# T2 — Gate registrado, audio de prueba, y PoC del generador

Segundo turno. El fundador aprobó el plan y habilitó el camino A. Este turno registró el Gate, creó el archivo de audio que pidió, y construyó el generador de overlay verificando los criterios que no necesitan Drift.

Cubre lo planificado como T2, T3 y T4.

## Frontera declarada

**Creado:**
- `tests/fixtures/generar_audio_prueba.py` — sintetizador del audio de prueba
- `tests/fixtures/pista_prueba.wav` — el audio (16 s, 48 kHz, estéreo)
- `tests/fixtures/README.md` — qué es y por qué está construido así
- `tools/generar_overlay.py` — el generador de overlay
- `docs/POC_RESULTADOS.md` — mediciones y hallazgos del PoC
- `docs/evidencia/T2_poc_overlay_compuesto.png`, `docs/evidencia/T2_comparacion_modos.png`
- `.memory/handoffs/T2_gate_audio_y_poc_20260925.md` (este archivo)

**Modificado:**
- `docs/PLAN_ETAPA1.md` — §1 con las decisiones resueltas, §6 reclasificando el camino B, §7 con el registro del Gate, §8 nueva sobre el material de prueba
- `RETOMAR.md`, `.memory/log.md`, `README.md`

**NO se tocó:**
- `sobre_este_plugins.txt`
- `C:\Program Files\Drift\` — **sólo lectura**, no se escribió nada
- `C:\Users\Jonatan Agustín\AppData\Roaming\CutWire Drift\` — no se escribió nada
- `_reference/drift-src/` — sólo lectura; se citó, no se editó
- **No se abrió Drift. No se activó su servidor MCP.** El fundador preguntó si hacía falta y se le respondió que no para T5.
- No se forkeó ni compiló Drift, ni se contactó a CutWire Studios (compromiso nulo con terceros, por decisión del fundador).
- `docs/VIABILIDAD.md` — sigue vigente, no hizo falta corregirlo.

## El Gate, y la premisa que corregí

El fundador aprobó el plan, eligió el camino A, dejó el C a futuro con **compromiso nulo con terceros**, y descartó el B con una condición: *"según entendí puede consumir muchos recursos? si es asi lo descarto"*.

**La condición no se cumple: el camino B no consume muchos recursos.** Tanto `VIABILIDAD.md` §7 como el plan lo clasifican con costo **bajo**, igual que el A. Se lo informé en el mismo intercambio y **mantuve el descarte**, porque la conclusión no cambia por otro motivo: el camino A ya cubre el objetivo y el B no puede dibujar espectro. Quedó reclasificado en `PLAN_ETAPA1.md` §6 como *añadido barato*, no como descartado por costo, con su punto de entrada anotado.

Registro verbatim completo en `docs/PLAN_ETAPA1.md` §7.

## El audio de prueba

Sintético y determinista a propósito: no entra material con derechos al repositorio, y se regenera idéntico en cualquier máquina (el ruido de los hats usa un generador congruencial con semilla derivada del índice de muestra, no `random`). **Determinismo verificado**: dos corridas dan SHA-256 idéntico, `692C1F12E20CBBFF…`.

Está construido para hacer visible lo que el visualizador tiene que mostrar: transientes nítidos para la detección de onsets, bandas separadas (kick en graves, bajo en 110 Hz, acordes en el medio, hats en agudos) para que un espectro muestre algo distinto en cada banda, un compás de casi silencio como control negativo, un tramo intenso como control positivo, y 16 segundos porque Drift necesita al menos 4 para estimar tempo.

Medido: 16.000 s, pico −1.0 dBFS, medio −18.0 dB, sin clipping.

## El generador

`tools/generar_overlay.py`. Toma audio, produce WebM VP9 `yuva420p` con la onda sobre fondo transparente. Verifica su propio resultado y devuelve código 1 si algún criterio falla, 2 ante error de uso.

**PoC-1, PoC-2 y PoC-3: verdes.** Duración con **0.0 ms de desvío**. Alpha de 0 a 255 con 70–97% de píxeles transparentes según el momento. Números completos en `docs/POC_RESULTADOS.md`.

### Tres diagnósticos que conviene no repetir

Están desarrollados en `docs/POC_RESULTADOS.md`; acá el resumen para que quede en el registro:

1. **`-shortest` no corta un `filter_complex`.** El primer diseño usaba una fuente `color` infinita; no terminaba nunca (21 MB de un audio de 16 s antes de matarlo). El generador pasa `-t` explícito, porque además `showwaves` se pasa 100 ms por su cuenta.
2. **`alphamerge` daba alpha 255 en todo el cuadro, y no hacía falta.** `showwaves` **ya emite RGBA con fondo transparente** y acepta `colors=` directo. Se eliminó toda la cadena de máscara + color plano. **Si a alguien se le ocurre usar `alphamerge` para esto: ya se probó y no funciona.**
3. **`draw=full` no es opcional.** El default `scale` de FFmpeg reparte la intensidad entre las ~1600 muestras de cada cuadro y dibuja un pelo con alpha máximo 153 y cero píxeles opacos. Con `full`: 255 y 179.173 opacos, misma transparencia.

### Y una trampa de medición que casi me hizo errar

Medir un cuadro con `-ss` **antes** de `showwaves` devuelve un cuadro **incompleto**: después del salto el filtro arranca con el buffer vacío y la onda sale apretada contra un borde. Llegué a mirar una imagen que parecía un visualizador roto cuando el roto era mi método.

Se detectó **porque el dibujo no tenía sentido físico**, no porque los números fallaran — las mediciones numéricas daban valores plausibles. Re-verifiqué la conclusión sobre `draw=full` con cuadro establecido y **se sostiene**.

Forma correcta: dejar correr el filtro y elegir el cuadro con `select='gte(n\,<N>)'`. Saltar sobre el `.webm` ya codificado sí es válido.

## Lo que queda abierto

| Tema | Estado |
|---|---|
| **PoC-4, PoC-5, PoC-6** | Requieren Drift abierto. **PoC-5 es el punto de control duro**: si Drift no compone la transparencia, el camino A cae |
| Peso del archivo | 11.6 MB / 16 s → ~130 MB por canción. Estructural: cada cuadro es una ventana nueva y VP9 no puede predecir. Palancas: `--alto`, `--fps`, `--crf` |
| Modos de espectro | `showfreqs` renderiza amontonado en el 12% izquierdo e ignora el color; `showspectrum` falló. **No se declara funcionando.** Trabajo del MVP (MVP-1) |
| Desvío de color ~1.5% | Se pidió G=229, sale G=225. Anotado, no investigado |
| Preview con alpha | Drift niega proxies a clips transparentes. El costo real se mide en T5 |

## Dónde retomar

`RETOMAR.md`. El próximo turno es **T5** y es el que **necesita al fundador con Drift abierto**. El agente que lo tome debe avisarle al empezar, como el fundador pidió explícitamente.

Si PoC-5 pasa, sigue el MVP (T6–T9), y el primer trabajo real ahí es arreglar los modos de espectro.
