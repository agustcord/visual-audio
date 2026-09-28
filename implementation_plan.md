# Plan de Implementación — Fase 1: Triage de Publicación No Comercial en GitHub & Corrección de Selección de Color en GUI

**Documento canónico del ciclo de trabajo del Escuadrón Ani.**
**Fecha:** 2026-09-27  
**Fase del Ciclo Core:** Fase 1 (Triage & Plan)  
**Autor:** Ani Arquitecta (Tech Lead)  
**Bóveda resuelta ($LOCAL_VAULT):** `C:\Users\Jonatan Agustín\Desktop\Proyectos\Drift\Plugins\.memory`

---

## 📌 Pedido Original del Capitán (textual)
> "Ok, entonces lo publiqueremos en github pero solo para uso no comercial, es decir nadie puede vender o integrarlo en un producto comercial. si puede usarlo de forma gratuita. Declara eso un pendiente, luego una cosa a arreglar, y es que el editor de colores de la barras y/ondas, no funciona, si lo hace el de fondo, pero no el de las barras"

---

## 1. Justificación de Delegación de Consulta en Fase 0
- **Veto de sobre-ingeniería / Justificación en una línea:** No se convocó a `ani-pensadora` ni a `ani-investigadora` porque la decisión de licencia ya fue fijada taxativamente por el Capitán ("publicar en github pero solo para uso no comercial"), y la causa raíz del bug de selección de color se localizó empíricamente de forma directa e inequívoca en la línea 537 de `tools/visualizador/gui.py` (`colorchooser.askcolor` desempaquetado de tupla RGB en variable string), sin dependencias externas ni bifurcaciones complejas de arquitectura.

---

## 2. Formalización del Pendiente Estratégico: Publicación No Comercial en GitHub

### 2.1 Contexto y Decisión del Capitán
En la definición inicial del proyecto (Regla 16 en `docs/RUTA_DE_TRABAJO.md` y `docs/MVP.md`), la distribución a terceros figuraba fuera del alcance inmediato, concibiéndose para uso propio. Tras el cierre exitoso del MVP (`v0.1.0-mvp`) y la certificación de rendimiento determinista a 60 fps (PASS rotundo en T39), el Capitán instruye la publicación pública en GitHub bajo un modelo estricto de **licencia no comercial**.

### 2.2 Directrices del Pendiente de Publicación
1. **Modelo de Licencia:** Publicación bajo licencia que garantice uso libre y gratuito para personas creadoras, músicos y editores, pero prohíba de forma terminante la venta comercial directa, la reventa o la integración/embebido en productos comerciales cerrados o privativos de terceros (ej. PolyForm Noncommercial License 1.0.0 o CC BY-NC 4.0 con salvaguardas operativas de código).
2. **Catalogación:** Se incorpora en la sección de pendientes de la fase de distribución de `RETOMAR.md` y en la memoria del proyecto, para ser abordada al preparar el empaquetado final y los metadatos públicos del repositorio.
3. **Acciones asociadas para su turno correspondiente:**
   - Redacción de `LICENSE.md` con los términos no comerciales explícitos.
   - Ajuste de `README.md` detallando las libertades concedidas (creación musical, videos propios, uso libre personal/creativo) y las prohibiciones (software comercial pago, bundles comerciales).
   - Limpieza de historial y preparación de releases públicos.

---

## 3. Diagnóstico Factual de Causa Raíz del Bug de Color en GUI

### 3.1 Localización del Fallo
El fallo reside exclusivamente en el método `_elegir_color` de `tools/visualizador/gui.py` (líneas 535 a 543):

```python
535: def _elegir_color(self, nombre: str) -> None:
536:     actual = str(self._variables[nombre].get())
537:     nuevo, _ = colorchooser.askcolor(color=actual, title=f"Elegir {nombre}")
538:     if nuevo:
539:         hex_mayus = nuevo.upper()
540:         self._variables[nombre].set(hex_mayus)
541:         self._actualizar_muestra_color(nombre, hex_mayus)
542:         self._al_cambiar_parametro(nombre)
```

### 3.2 Mecanismo del Error
1. **Firma y retorno de Tkinter:** El diálogo nativo `tkinter.colorchooser.askcolor(color=..., title=...)` retorna una tupla de dos elementos: `((r, g, b), hex_color_string)` (por ejemplo `((255, 0, 0), '#ff0000')`), o `(None, None)` en caso de que el usuario presione "Cancelar".
2. **Desempaquetado invertido / erróneo:** En la línea 537, el código realiza `nuevo, _ = colorchooser.askcolor(...)`. Esto asigna:
   - `nuevo = (r, g, b)` (una tupla de 3 enteros).
   - `_ = '#rrggbb'` (el string hexadecimal con el color elegido, descartado en la variable muda `_`).
3. **Excepción inmediata en tiempo de ejecución:** En la línea 539, se ejecuta `hex_mayus = nuevo.upper()`. Dado que `nuevo` es una tupla (`<class 'tuple'>`), Python eleva:
   ```text
   AttributeError: 'tuple' object has no attribute 'upper'
   ```
4. **Consecuencia visible para el usuario:** El bucle de eventos de Tkinter captura la excepción internamente o la envía a stderr sin romper la ventana, pero la ejecución de `_elegir_color` se interrumpe de forma fulminante **antes** de mutar `self._variables[nombre].set(...)`, antes de actualizar la muestra gráfica (`_actualizar_muestra_color`) y antes de notificar al pipeline de renderizado (`_al_cambiar_parametro`). La selección se anula por completo y el color no cambia.
5. **Por qué el selector de fondo sí funciona:** En la interfaz, "Modo de fondo" (`fondo`) es un desplegable `ttk.Combobox` con opciones `"negro"`, `"color"`, `"transparente"`. Su cambio no invoca `colorchooser.askcolor`, sino `_al_cambiar_parametro("fondo")`, el cual actualiza inmediatamente el canvas en `_proyectar_en_canvas` aplicando el color de base correspondiente. Si el usuario modifica el modo de fondo, el visor responde; pero si intenta elegir el color de las barras o de la onda mediante el botón o la muestra de color, el diálogo falla por el `AttributeError`.

### 3.3 Verificación de Motores de Render
Se verificó empíricamente mediante pruebas directas en consola que los motores `Render`, `Barras`, `Espejadas` y `Onda` en `tools/visualizador/render.py` y `tools/visualizador/estilos/` consumen y renderizan correctamente los colores cuando reciben cadenas hexadecimales válidas en `p["color"]` o `p["color_final"]`. El problema no es de render ni de shaders ni de LOD: es estrictamente el manejo del diálogo en `gui.py`.

---

## 4. Especificación Técnica de Corrección (Fase 2)

### 4.1 Asignación de Roles
- **Ani Frontend:**
  - Corrección de `tools/visualizador/gui.py` en `_elegir_color(nombre)`.
  - Incorporación de pruebas automáticas en `tests/test_gui.py` que emulen la interacción con el selector de color (`colorchooser.askcolor`) para `color`, `color_final` y `color_fondo`, validando tanto la selección efectiva como la cancelación.
- **Ani Programadora:**
  - Sin tareas en el motor de render (`render.py` o `analisis.py`), dado que el backend opera de forma correcta e invariante. Apoyo en verificación si surgieran detalles en contratos.

### 4.2 Detalle de la Corrección en `tools/visualizador/gui.py`
En `_elegir_color`, se reemplaza el desempaquetado defectuoso por una lectura segura del componente hexadecimal:

```python
    def _elegir_color(self, nombre: str) -> None:
        actual = str(self._variables[nombre].get())
        resultado = colorchooser.askcolor(color=actual, title=f"Elegir {nombre}")
        # resultado es ((r, g, b), '#rrggbb') o (None, None) / None si se cancela
        if resultado and resultado[1]:
            hex_str = str(resultado[1])
            hex_mayus = hex_str.upper()
            self._variables[nombre].set(hex_mayus)
            self._actualizar_muestra_color(nombre, hex_mayus)
            self._al_cambiar_parametro(nombre)
```

Beneficios de esta implementación:
1. Extrae explícitamente `resultado[1]`, que contiene la cadena `#rrggbb`.
2. Si el usuario cancela (`resultado[1]` es `None` o vacío), la función retorna de forma limpia sin arrojar excepciones ni alterar el valor actual.
3. Convierte a mayúsculas de forma segura (`.upper()`) y persiste en `self._variables[nombre]`.
4. Actualiza la muestra de color en la UI con cálculo de contraste de luminancia (`_es_color_oscuro`).
5. Dispara `_al_cambiar_parametro(nombre)`, respetando el debounce cosmético adaptativo de 30 ms y encolando el render en el worker asíncrono.

---

## 5. Criterios de Aceptación Falsables para Fase 3 (Ani Mal Humor)

| ID | Criterio | Verificación / Evidencia Falsable |
|---|---|---|
| **CA-COLOR-1** | **Selección exitosa de color en diálogo:** Al invocarse `_elegir_color("color")` simulando retorno `((255, 0, 0), '#ff0000')`, la variable Tkinter `app.obtener_variable("color").get()` muta a `"#FF0000"`. | Aserción en `tests/test_gui.py` con `patch("tkinter.colorchooser.askcolor")`. |
| **CA-COLOR-2** | **Cancelación limpia de diálogo:** Al invocarse `_elegir_color("color")` simulando cancelación `(None, None)`, la variable `app.obtener_variable("color").get()` preserva su valor original y no se lanzan excepciones. | Aserción en `tests/test_gui.py` con `patch("tkinter.colorchooser.askcolor", return_value=(None, None))`. |
| **CA-COLOR-3** | **Actualización de muestra visual y accesibilidad:** La etiqueta de muestra de color (`_muestras_color[nombre]`) actualiza su fondo `bg`, su texto y su color de texto `fg` con contraste accesible según luminancia (blanco para oscuros, negro para claros). | Aserción en `tests/test_gui.py` inspeccionando `lbl.cget("bg")` y `lbl.cget("fg")`. |
| **CA-COLOR-4** | **Regeneración de fotograma y render con nuevo color:** Tras cambiar el color a rojo (`#FF0000`) en estilo Barras y esperar el render asíncrono, el fotograma proyectado en el canvas contiene píxeles con canal rojo activo correspondientes a las barras. | Comprobación en `tests/test_gui.py` analizando los píxeles del cuadro resultante o invocación a `Render`. |
| **CA-COLOR-5** | **Suite integral al 100% en verde:** Todos los 8 scripts de la suite de pruebas pasan sin fallas (`exit code 0`, 388+ checks). | Ejecución completa de la suite sin regresiones. |

---

## 6. Lista de Cotejo Previa a Emitir un Plan (8 Puntos Obligatorios)
1. **¿Alguna tarea contradice una regla escrita de un documento canónico?** No. Se respeta la arquitectura desacoplada, la no adición de librerías externas (Regla 13) y la invarianza de exportación (MVP-5).
2. **¿Las herramientas, rutas, skills y comandos que nombro existen y hacen lo que digo?** Sí, verificado en disco con Python 3.14.6 y Tkinter.
3. **¿Cubre todos los requisitos del pedido?** Sí: registra el pendiente de publicación no comercial en GitHub e investiga y planifica la solución al bug de colores de barras y ondas.
4. **¿Cada criterio de aceptación puede fallar (falsable)?** Sí, si `askcolor` sigue devolviendo tupla a `nuevo.upper()`, los tests CA-COLOR-1 a CA-COLOR-4 fallan de inmediato con `AttributeError`.
5. **¿Alguna tarea borra, sobrescribe o mueve algo, y si sí, está autorizado?** No se borra nada; solo se corrige la función en `gui.py` y se agregan pruebas.
6. **¿Cité el documento canónico que gobierna?** Sí (`docs/ARQUITECTURA.md`, `docs/MVP.md`, `RETOMAR.md`).
7. **¿Si el entregable corre desatendido, prevé detección de fallas?** Sí, el manejo de cancelación y retorno None previene excepciones desatendidas.
8. **¿El plan de validación emite veredicto definitivo en <= 48h?** Sí, se valida en menos de 5 segundos mediante la suite de tests automáticos.

---

## 🚦 Gate del Capitán
Este plan requiere la aprobación formal del Capitán ("procede" / "adelante") para habilitar a Ani Frontend a aplicar la corrección en `tools/visualizador/gui.py` y los tests asociados en `tests/test_gui.py`.
