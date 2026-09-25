---
tipo: "MOC"
estado: "activo"
proyecto: "Visualizador de audio para Drift"
creado: 2026-09-25
---

# Índice de la memoria

Esta carpeta es la **memoria técnica del proyecto**, y este archivo es su **documento principal**: no reporta el avance, **estructura la documentación** y dice dónde vive cada cosa.

- **Si sos una persona:** los enlaces de la tabla son clicables en Obsidian. Orden de lectura sugerido: este índice → `RETOMAR.md` (fuera de la bóveda) → `docs/VIABILIDAD.md` → `docs/PLAN_ETAPA1.md`.
- **Si sos un agente:** extraé el bloque delimitado `INDICE-MAQUINA` y leé la tercera columna: cada fila trae la **ruta absoluta**, lista para abrir. No hace falta interpretar prosa.
- **El avance no se declara acá.** Una cifra tipeada envejece en silencio. El estado vive en `RETOMAR.md` y en la bitácora.

## Qué es este proyecto

Un **visualizador de audio** para el editor de video **Drift** (CutWire Studios, Qt6 + FFmpeg, GPLv3): dibujar la onda o el espectro del audio sobre el video para seguir visualmente la pista musical. Uso previsto por el fundador: edición de videos musicales propios.

El documento fundacional, firmado por Jonatan Córdoba, es `sobre_este_plugins.txt` en la raíz. **Es la fuente de autoridad sobre el propósito**; esta bóveda documenta cómo se ejecuta.

## MOCs de dominio

- **[[MOC_Handoffs]]** — índice del registro de auditoría: alcanza cada handoff sin listarlo acá.
- **[[Drift_editor]]** — qué es Drift, su stack, dónde está instalado, su licencia.
- **[[Extensibilidad_de_Drift]]** — los cuatro mecanismos de extensión reales y sus límites. **Léelo antes de proponer cualquier arquitectura.**
- **[[Audio_reactividad_en_Drift]]** — cómo Drift convierte audio en movimiento hoy, y el bloqueo central que condiciona todo el proyecto.
- **[[Caminos_de_implementacion]]** — las tres rutas candidatas, con su costo y su techo.

Las notas se alcanzan por su MOC de dominio, así que este índice no engorda cuando aparecen notas nuevas.

<!-- INICIO INDICE-MAQUINA -->
| Qué | Wikilink (humano) | Ruta absoluta (agente) |
|---|---|---|
| Documento principal de la bóveda | [[index]] | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\index.md` |
| Bitácora de la bóveda (append-only) | [[log]] | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\log.md` |
| Índice del registro de handoffs | [[MOC_Handoffs]] | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\wiki\MOC_Handoffs.md` |
| Generador de overlay (fuera de la bóveda) | — | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\tools\generar_overlay.py` |
| Audio de prueba del proyecto (fuera de la bóveda) | — | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\tests\fixtures\pista_prueba.wav` |
| Resultados del PoC (fuera de la bóveda) | — | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\docs\POC_RESULTADOS.md` |
| Registro de handoffs (la carpeta) | — | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\handoffs\` |
| Nota: el editor Drift | [[Drift_editor]] | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\wiki\Drift_editor.md` |
| Nota: extensibilidad de Drift | [[Extensibilidad_de_Drift]] | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\wiki\Extensibilidad_de_Drift.md` |
| Nota: audio-reactividad en Drift | [[Audio_reactividad_en_Drift]] | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\wiki\Audio_reactividad_en_Drift.md` |
| Nota: caminos de implementación | [[Caminos_de_implementacion]] | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\wiki\Caminos_de_implementacion.md` |
| Documento fundacional (fuera de la bóveda) | — | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\sobre_este_plugins.txt` |
| Puerta del repositorio (fuera de la bóveda) | — | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\README.md` |
| Dónde retomar (fuera de la bóveda) | — | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\RETOMAR.md` |
| Informe de viabilidad (fuera de la bóveda) | — | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\docs\VIABILIDAD.md` |
| Plan y presupuesto de la Etapa 1 (fuera de la bóveda) | — | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\docs\PLAN_ETAPA1.md` |
| Clon de referencia de Drift (NO versionado) | — | `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\_reference\drift-src\` |
| Instalación de Drift (sólo lectura) | — | `C:\Program Files\Drift\` |
| Carpeta de datos de Drift (escribible) | — | `C:\Users\Jonatan Agustín\AppData\Roaming\CutWire Drift\` |
<!-- FIN INDICE-MAQUINA -->

## Reglas de esta bóveda

1. **`log.md` es append-only.** Las entradas fechadas no se editan ni se reordenan. Si algo quedó mal dicho, se apenda la corrección.
2. **Todo turno de agente deja un handoff** en `handoffs/` con el formato `T<N>_<tema>_<YYYYMMDD>.md`, y una entrada en `log.md` que lo cita.
3. **Las cifras no se tipean donde puedan envejecer.** Se derivan por comando y se cita el comando.
4. **`_reference/drift-src/` es de sólo lectura.** Es código de terceros bajo GPLv3. No se edita, no se versiona, se reconstruye.
5. **Ningún agente borra trabajo previo sin declararlo.** Si una decisión se revierte, la nota vieja queda marcada `superseded` con el motivo, no se elimina.
