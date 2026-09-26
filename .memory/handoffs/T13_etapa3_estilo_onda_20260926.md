---
tipo: "handoff"
turno: 13
agente: "Ani Programadora"
fecha: 2026-09-26
estado: "cerrado — etapa 3 (Estilo Onda) completa; el proyecto queda listo para la etapa 4 (Proyectos y presets)"
---

# T13 — Etapa 3: Estilo Onda

Implementación completa del tercer estilo del visualizador: la forma de onda continua centrada en el eje.
Los 4 criterios de salida de la Etapa 3 están cumplidos y verificados con pruebas automáticas: **75 comprobaciones automáticas en verde, 0 fallas**.

---

## 🎯 Frontera declarada

### Creado:
- `tools/visualizador/estilos/onda.py`: Clase `Onda(Estilo)` (id `"onda"`, usa `("onda",)`).
  - Remuestreo exacto de `datos.onda` al ancho del lienzo en píxeles.
  - Trazado de línea simétrica alrededor del eje central (`eje = caja.y + caja.alto / 2`).
  - Soporte de `grosor_linea` (1 a 20 px, default 4).
  - Soporte de `relleno` del cuerpo de la onda contra el eje.
  - Soporte completo de degradados (`"ninguno"`, `"altura"`, `"ancho"`).
  - Soporte de `resplandor` (halo desenfocado optimizado a escala 1/6) y `reflejo` inferior atenuado.
  - Función pura determinista e idempotente sin estado interno mutable entre cuadros (`cuadro(i)` repetible).

### Modificado:
- `tools/visualizador/estilos/__init__.py`: Importación y registro de `Onda` (`registrar(Onda())`), agregada a `__all__`.
- `tools/visualizador/parametros.py`:
  - Incorporados al esquema en grupo `forma`: `grosor_linea` (1..20 px, default 4, `estilos=("onda",)`) y `relleno` (bool, default False, `estilos=("onda",)`).
  - Restringidos parámetros específicos de barras a `estilos=("barras", "espejadas")`: `caida_picos`, `frec_min`, `frec_max` (junto a los ya existentes `n_barras`, `grosor_barra`, `redondeo`, `tapas_pico`).
  - Actualizada función `validar`: cuando `permitir_desconocidos=True`, los parámetros de otros estilos se ignoran limpiamente; cuando `permitir_desconocidos=False`, se rechazan con `ErrorDeParametro` claro.
- `tools/visualizador/analisis.py`:
  - Lectura segura con `.get(...)` y valores por defecto para `frec_min`, `frec_max` y `caida_picos`, permitiendo analizar audios directamente para el estilo `onda`.
- `tests/test_render.py`:
  - Incorporadas verificaciones de `criterio_3_4`: parámetros ajenos a un estilo no modifican el dibujo y son rechazados en validación estricta.
  - Ampliada `estructura_del_dibujo`: límites de caja, alpha, superficie de `relleno` vs línea (19307 vs 4373 px) y grosor de línea (11078 vs 2403 px).
  - Ampliado `criterio_export` para codificar WebM en los tres fondos (negro, color, transparente) tanto en `barras` como en `onda`.
- `tests/verificar_sincronia.py`:
  - Agregado `"relleno": True` en `perfil_del_motor_propio` para medir la energía superficial de forma análoga a `showwaves ... draw=full` de FFmpeg.
- `docs/RUTA_DE_TRABAJO.md` y `RETOMAR.md`:
  - Actualizada tabla de estado: Etapa 3 marcada como cerrada en T13; Etapa 4 marcada como siguiente hito.

### NO se tocó:
- `tests/fixtures/pista_prueba.wav` ni `pista_espectro.wav` (hashes y estructuras intactas).
- `tools/generar_overlay.py` (camino legado intacto).
- `C:\Program Files\Drift\`, sin tocar; sin dependencias externas de Python adicionales (`numpy` y `Pillow`).

---

## 📊 Resultados de los Criterios de la Etapa 3

| # | Criterio | Comando de verificación | Resultado observable |
|---|---|---|---|
| **3.1** | Export en los tres modos de fondo sin error | `python tests\test_render.py --export` | ✅ **OK** 480/480 cuadros exactos en negro (529 KB), color (336 KB) y transparente (1444 KB con `alpha_mode='1'`). |
| **3.2** | Sincronía idéntica al motor propio en Barras | `python tests\verificar_sincronia.py --estilo onda` | ✅ **OK** 8 saltos rítmicos independientes con **desvío +0 cuadros** (exacto al compás y bombo), y salto mayor en 10.000s con desvío +0 cuadros. |
| **3.3** | Barrido de parámetros pasa en los tres estilos | `python tests\test_render.py` | ✅ **OK** 56 combinaciones probadas en Onda, 70 en Barras, 70 en Espejadas (196 total). Cero excepciones, todos los valores modifican el fotograma. |
| **3.4** | Parámetros ajenos a Onda no tienen efecto | `python tests\test_render.py` (`criterio_3_4`) | ✅ **OK** Huella SHA-256 de fotograma 430 idéntica con parámetros ajenos (`huella_base == huella_con_ajenos`). Validación estricta falla claro con `ErrorDeParametro`. |

---

## 🔬 Evidencia Empírica de Ejecución

1. **Suite de Análisis:**
   ```powershell
   python tests\test_analisis.py
   # 36 comprobaciones pasadas, 0 fallas
   ```
2. **Suite de Render y Export:**
   ```powershell
   python tests\test_render.py --export
   # 36 comprobaciones pasadas, 0 fallas (196 barridos, 6 exports WebM a 480 cuadros exactos)
   ```
3. **Alineación de Sincronía:**
   ```powershell
   python tests\verificar_sincronia.py               # barras: desvío +0 cuadros
   python tests\verificar_sincronia.py --estilo espejadas # espejadas: desvío +0 cuadros
   python tests\verificar_sincronia.py --estilo onda     # onda: desvío +0 cuadros
   ```
4. **Generación de Vista Previa CLI:**
   ```powershell
   python -c "import sys; sys.path.insert(0, 'tools'); from visualizador import cli; sys.argv = ['cli.py', 'tests/fixtures/pista_espectro.wav', '--estilo', 'onda', '--cuadro', '150', '-o', 'build/prueba_onda.png']; sys.exit(cli.main())"
   # Genera build/prueba_onda.png (23.536 bytes) en 0.12s
   ```
