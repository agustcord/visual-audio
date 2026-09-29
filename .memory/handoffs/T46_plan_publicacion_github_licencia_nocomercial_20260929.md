# Handoff T46 — Plan de Publicación en GitHub bajo Licencia No Comercial

- **Fecha**: 2026-09-29
- **Turno**: T46
- **Rol**: Ani Arquitecta (Tech Lead)
- **Estado**: OK (Plan maestro completado para Gate del Capitán)
- **Fase del Ciclo Core**: Fase 1 (Triage & Plan)
- **Entregables generados**:
  * `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\implementation_plan.md` (Plan rector canónico)
  * `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\handoffs\T46_plan_publicacion_github_licencia_nocomercial_20260929.md` (Este handoff)
- **Entregables actualizados (SMF)**:
  * `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\RETOMAR.md`
  * `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\log.md`
  * `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory\wiki\MOC_Handoffs.md`

---

## 📌 Pedido Original del Capitán (textual)
> "quedo muy bien. arme todo para publicar en github de manera publica, descripcion, instalación, capturas. licencia libre de uso, siempre y cuiando no se venda el software o se use como complemento de un producto comercial"

---

## 1. Resumen Ejecutivo del Triage

1. **Línea Base Verificada en Disco:**
   - Se ejecutó la suite completa de 8 pruebas antes de planificar: **462 comprobaciones automáticas pasando al 100% en verde con 0 fallas (exit code 0)**.
   - La identidad visual de "Visual Audio" (Dark Zinc 950/900 con acentos cian/violeta e iconos oficiales) fue completada en T44 y certificada con PASS en T45 por Ani Mal Humor.
   - El código en `tools/` y `tests/` cuenta con 0 rutas absolutas de usuario o datos sensibles.
2. **Definición de Licencia No Comercial:**
   - Se evaluó el requerimiento legal del Capitán ("libre de uso, siempre y cuando no se venda el software o se use como complemento de un producto comercial").
   - Se seleccionó la licencia estándar de la industria de software **PolyForm Noncommercial License 1.0.0**, diseñada específicamente para código y con cláusula de uso no comercial vinculante.
   - Se definió un preámbulo canónico (*Creator-Friendly Clarification*) que autoriza expresamente a músicos y creadores de video a utilizar la herramienta para generar sus piezas audiovisuales (incluso para canales monetizados con anuncios en YouTube/redes), prohibiendo de forma taxativa la venta del código/binario o su integración como complemento de productos comerciales.
3. **Estrategia de Documentación Pública y Presentación:**
   - Reemplazo del `README.md` actual por un documento de primer nivel: título oficial "Visual Audio", badges de release, plataforma, Python y licencia; propuesta de valor; carrusel de capturas de pantalla de la GUI con los 3 estilos; guía paso a paso de instalación en Windows (Python, FFmpeg, dependencias pip); comandos de arranque (GUI con doble clic en `visualizador.bat` y CLI con `python -m visualizador`); y guía de composición en Drift en modo Trama (Screen).
4. **Empaquetado y Reproducibilidad:**
   - Formalización de `requirements.txt` (`numpy>=1.24.0`, `pillow>=10.0.0`, `scipy>=1.10.0`) y `pyproject.toml` con metadatos PEP 517/621.
5. **Galería Oficial de Capturas:**
   - Creación de la carpeta `assets/screenshots/` y diseño de un script de captura desatendida (`tools/generar_capturas.py`) para registrar capturas de pantalla en alta resolución de la GUI con audio cargado y los tres estilos (`barras`, `onda`, `espejadas`).
6. **Frontera Estricta de Turno 1:**
   - **Cero líneas de código de producto modificadas en este turno.** Respeto absoluto al Gate del Capitán.

---

## 2. Asignación de Roles para Fase 2 (Ejecución)

- **Ani Escritora / Ani Frontend:**
  * Redacción de `LICENSE` con PolyForm Noncommercial 1.0.0 y cláusula explicativa para creadores.
  * Redacción del nuevo `README.md` público estructurado.
- **Ani Programadora:**
  * Creación de `requirements.txt` y `pyproject.toml`.
  * Verificación de reproducibilidad de importación y entrypoints.
- **Ani Frontend:**
  * Generación programática de la galería oficial de screenshots en `assets/screenshots/`.
  * Vinculación de capturas relativas en `README.md`.
- **Ani DevOps:**
  * Auditoría final de higiene de `.gitignore` para GitHub y verificación de suite.

---

## 3. Criterios de Aceptación Falsables para Fase 3 (Ani Mal Humor)

- **CA-PUB-1:** `LICENSE` existe en la raíz con PolyForm Noncommercial 1.0.0, autor Jonatan Córdoba y prohibición expresa de venta/integración comercial.
- **CA-PUB-2:** `requirements.txt` y `pyproject.toml` existen en la raíz con dependencias exactas y sin dependencias no declaradas.
- **CA-PUB-3:** `assets/screenshots/` contiene al menos 3 capturas reales en formato PNG (> 10 KB cada una) de los estilos con tema Dark Zinc.
- **CA-PUB-4:** `README.md` contiene la estructura completa de presentación, instalación paso a paso, comandos de arranque y enlaces relativos válidos a las capturas.
- **CA-PUB-5:** Cero rutas locales absolutas del entorno de desarrollo en los archivos públicos versionados.
- **CA-PUB-6:** `visualizador.bat` y `python -m visualizador` ejecutan limpiamente levantando la interfaz "Visual Audio".
- **CA-PUB-7:** Suite completa de 8 pruebas ejecutando al 100% en verde (462 checks, 0 fallas, exit code 0).

---

## 4. Dónde Retomar
Nos encontramos en el **🚦 GATE DEL CAPITÁN**.
Ani Recepcionista presentará el plan `implementation_plan.md` al Capitán y esperará su aprobación formal ("procede" o "apruebo") antes de iniciar la ejecución técnica en Fase 2.
