---
tipo: "handoff"
turno: "T11"
fecha: 2026-09-25
agente: "Kiro"
tema: "Cómo se lanza la herramienta: .bat en el MVP, .exe después; distribuir no es objetivo"
commit: "pendiente al escribir; ver git log"
---

# T11 — Cómo se abre la herramienta, y qué no es objetivo

Turno de alcance, sin código. Nace de una pregunta del fundador al cerrar T10: *"consulta ya es un archivo ejecutable? o eso en que etapa viene?"*.

## El punto ciego que destapó la pregunta

Busqué `.exe`, `ejecutable`, `PyInstaller`, `empaquet`, `doble clic`, `instalador` y `.bat` en todo el repositorio. **Ninguna aparición referida a nuestra herramienta.** No estaba en `MVP.md`, ni en la ruta, ni en la lista de post-MVP.

No era una omisión inocente: el MVP promete *"sin programación para el usuario final"*, y abrir una terminal para arrancar el programa también es programación para quien no programa. Estaba prometido el fondo y no la puerta de entrada.

## Lo que decidió el fundador, verbatim

> *"para esta primer etapa dejemos documentado que el mvp va a tener un interfaz. que primero sera un .bat. y luego cuando el desarrollo pase a una etapa más avanzada, sera un .exe. El día de mañana puede que quiera distribuir esto, pero eso depende del resultado final, y no es una ruta que este proyecto actualmente este trabajando como un objetivo"*

Tres decisiones separadas:

| | Qué | Dónde queda |
|---|---|---|
| **El MVP tiene interfaz gráfica** | Confirmado, no recortable | ya era etapa 5; ahora también está dicho en `MVP.md` §4 |
| **Se lanza con un `.bat`** | Doble clic, dentro del MVP | **tarea nueva de la etapa 6**, criterios 6.4 y 6.5 |
| **`.exe` más adelante** | Etapa más avanzada, post-MVP | punto 3 de `RUTA_DE_TRABAJO.md` §5 |
| **Distribuir no es objetivo** | Posible a futuro, **no se trabaja para eso** | **regla 16**, nueva |

## Por qué el `.bat` alcanza y el `.exe` no aporta todavía

Verificado en disco:

```powershell
Get-Command python, pythonw, py
# python.exe   C:\Users\Jonatan Agustín\AppData\Local\Programs\Python\Python314\python.exe
# pythonw.exe  C:\Users\Jonatan Agustín\AppData\Local\Programs\Python\Python314\pythonw.exe
# py.exe       C:\WINDOWS\py.exe
```

**`pythonw.exe` existe**, y es el detalle que hace viable la opción barata: abre una ventana Tk **sin dejar una consola negra detrás**. Con `python.exe` quedaría una, y se lee como un programa a medio terminar.

El `.exe` resuelve **distribución**, no uso: sirve para correr en una máquina sin Python, y la del fundador tiene Python. Empaquetar antes de terminar la herramienta obliga a rehacer el empaquetado con cada cambio.

Costos del `.exe` anotados para cuando llegue, y que no son especulación: PyInstaller es **dependencia nueva** (regla 13, necesita aprobación), 80–150 MB porque empaqueta Python + `numpy` + `Pillow`, arranque más lento en frío, y falsos positivos de antivirus con cierta frecuencia.

## La trampa que dejé anotada como criterio 6.5

El `.bat` tiene que funcionar **con espacios en la ruta** y desde cualquier directorio de trabajo. La ruta del proyecto tiene un espacio en `Jonatan Agustín`, así que un `.bat` sin comillas y sin `%~dp0` falla **ahí y en ningún otro lado** — es el error que se descubre justo al entregar, cuando ya se declaró listo. Por eso es criterio y no comentario.

## Frontera: qué se tocó y qué no

**Modificado**
- `docs/MVP.md` §4 — dos secciones nuevas: cómo se abre (tabla `.bat` vs `.exe` con costos) y por qué distribuir no es objetivo. Más una línea al principio de diseño: el `.bat` y el `.exe` **sólo lanzan `gui.py`**, sin lógica propia, que es lo que hace que empaquetar no cueste rediseñar
- `docs/RUTA_DE_TRABAJO.md` — tarea del `.bat` en la etapa 6 con la ruta de `pythonw.exe` verificada; criterios **6.4 y 6.5** nuevos; el `.exe` como punto 3 de post-MVP; **regla 16**; nota de que distribuir está fuera de la lista a propósito. Corregida una numeración duplicada en §5 (había dos puntos «4»)
- `RETOMAR.md` — dos filas nuevas en la tabla de decisiones cerradas
- `.memory/index.md`, `.memory/wiki/MOC_Handoffs.md`, `.memory/log.md`

**NO se tocó**
- **Nada de código.** No se escribió el `.bat`: es tarea de la etapa 6, cuando exista `gui.py` a la cual apuntar. Escribirlo ahora sería un archivo que lanza algo que no existe
- `tools/visualizador/`, las pruebas, la evidencia
- La etapa 3, que sigue siendo el próximo trabajo real

## Una nota legal, para que nadie se asuste después

Lo dejé en `MVP.md` §4 porque es el tipo de duda que aparece sola el día que se piense en distribuir: **la herramienta no incluye ni enlaza código de Drift**, así que no es obra derivada y la GPLv3 de Drift no le impone condiciones. Distinto es empaquetarla como *addon* de Drift, que está cerrado para un tercero por la firma Ed25519 (ver [[Extensibilidad_de_Drift]]).

## Para el próximo agente

**Sigue la etapa 3, estilo Onda.** Esto no la movió ni la retrasó: fue un turno de alcance en paralelo.

Y cuando llegues a la etapa 6, el `.bat` ya está especificado con sus dos criterios. No hace falta volver a pensarlo.
