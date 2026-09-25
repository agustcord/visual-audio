# Material de prueba

Archivos de prueba del proyecto. **Todo lo que hay acá es sintético y reproducible**: no hay material con derechos en el repositorio, y cualquier agente puede regenerar los archivos de forma idéntica.

## `pista_prueba.wav`

El audio de prueba del proyecto, pedido por el fundador en el Gate del turno T2.

| Propiedad | Valor | Verificado con |
|---|---|---|
| Duración | 16.000 s | `ffprobe` |
| Formato | PCM s16le, 48000 Hz, 2 canales | `ffprobe` |
| Tamaño | 3.072.044 bytes | `ffprobe` |
| Nivel medio | −18.0 dB | `ffmpeg -af volumedetect` |
| Pico | −1.0 dB (sin clipping) | `ffmpeg -af volumedetect` |
| Tempo | 120 BPM, 8 compases de 4/4 | por construcción |

### Por qué está construida así

No es ruido genérico: cada decisión apunta a hacer visible una propiedad del visualizador que estamos construyendo.

- **Transientes nítidos.** El kick tiene un barrido de tono descendente y un click de 320 Hz de decaimiento; los hats son ruido diferenciado con cola muy corta. Eso le da a la detección de onsets de Drift picos inequívocos que encontrar, en vez de una envolvente blanda donde cualquier umbral es discutible.
- **Bandas separadas.** Kick en graves (52–147 Hz), bajo en 110 Hz con su armónico, acordes en el registro medio (261–440 Hz), hats en agudos. Un visualizador de **espectro** tiene que mostrar algo distinto en cada banda; con una fuente de banda ancha se vería una mancha uniforme y no sabríamos si funciona.
- **Un respiro en el compás 4.** Casi silencio, con un solo kick. Es el control negativo: si la onda no se achica visiblemente ahí, el visualizador está mintiendo.
- **Un tramo intenso al final** (compases 5–7, con semicorcheas continuas en el 7). El control positivo, y donde se ve si la representación se satura.
- **Movimiento estéreo.** Los hats alternan lados con paneo de potencia constante. Sirve si alguna vez se prueba un visualizador por canal.
- **16 segundos, no 3.** Drift necesita al menos **4 segundos** para estimar tempo (`kMinAnalysisSec` en `src/engine/AudioOnsets.cpp`). Con menos devuelve bpm 0 y sin grilla de beats, y las pruebas fallarían por una razón que no tiene nada que ver con lo que se está probando.
- **Pico en −1 dBFS.** Deja headroom, así que si algo se ve recortado en la visualización es culpa nuestra, no de la fuente.

### Regenerar

```powershell
python tests\fixtures\generar_audio_prueba.py
```

El resultado es **determinista**: el ruido de los hats usa un generador congruencial lineal con semilla derivada del índice de muestra, no `random`. Dos corridas producen bytes idénticos.

Opciones:

```powershell
python tests\fixtures\generar_audio_prueba.py --bpm 128          # otro tempo
python tests\fixtures\generar_audio_prueba.py -o otra_pista.wav  # otro destino
```

### Nota sobre el control de versiones

El `.wav` **sí** se versiona, aunque sea derivado de un script de unos pocos KB. Es deliberado: el fundador pidió que el proyecto tuviera su archivo de audio, y que exista sin necesidad de correr nada vale más que los 3 MB que ocupa. El `.gitignore` excluye audio y video en general, y re-incluye `tests/fixtures/**` justamente para esto.
