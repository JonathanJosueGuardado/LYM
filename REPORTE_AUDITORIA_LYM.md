# REPORTE DE AUDITORÍA LYM AUTO CONTROL

**Fecha:** 2026-06-14  
**Repositorio:** `JonathanJosueGuardado/LYM`  
**Archivo principal auditado:** `LYM_AUTO_CONTROL_V5_0_LEASING.py`  
**Tipo de revisión:** Auditoría estática profunda desde GitHub, con lectura del archivo principal y verificación de reglas de negocio críticas.

> Nota honesta: desde el entorno actual no fue posible clonar el repositorio por consola ni ejecutar `py_compile`, porque el entorno local no resolvió `github.com`. Por eso este reporte deja hallazgos técnicos verificables por lectura de código y marca como pendientes las pruebas de runtime/GUI/OneDrive real.

---

## 1. Resumen ejecutivo

El sistema LYM AUTO CONTROL ya contiene varias mejoras importantes solicitadas en versiones acumuladas: flujo de compra local, cotizaciones leasing, historial de propuestas, propuestas PDF/Word, ventas con comprobante/foto, reportes Excel/HTML y endurecimiento de tablas.

Sin embargo, el riesgo principal del sistema no está solo en una función aislada, sino en la **arquitectura acumulada por parches**: el mismo archivo contiene bloques V3/V4/V5 que redefinen constantes, clases y funciones varias veces. Esto puede funcionar por orden de ejecución, pero vuelve el sistema frágil, difícil de probar y propenso a regresiones.

La prioridad de producción debe ser:

1. Consolidar reglas críticas en funciones únicas.
2. Blindar escritura/lectura de JSON y archivos cifrados para OneDrive.
3. Corregir reportes que pueden fallar por dependencias opcionales.
4. Ampliar el self-test para cubrir compra local, leasing, propuestas, ventas y reportes.
5. Refactorizar progresivamente sin borrar compatibilidad con datos existentes.

---

## 2. Alcance revisado

Se revisaron los siguientes componentes dentro de `LYM_AUTO_CONTROL_V5_0_LEASING.py`:

- Configuración base, carpetas y rutas.
- Usuarios, roles y permisos.
- Guardado JSON y guardado cifrado.
- Flujo de compra vehicular USA / LOCAL / servicio importación.
- Cálculo de costos y prevención de duplicidad del precio ganado.
- Cotizaciones leasing.
- Propuestas PDF/Word.
- Historial de propuestas.
- Ventas y cierre comercial.
- Reportes Excel y HTML.
- Login y arranque.
- Self-test actual.

---

## 3. Bugs críticos encontrados

### 3.1. Riesgo crítico: OneDrive no está implementado como capa segura

No se encontró una capa explícita de validación OneDrive. Actualmente `get_active_folder()` solo valida si la ruta existe y `get_data_folder()` devuelve la subcarpeta del sistema. Esto no valida si OneDrive está abierto, sincronizado, si el archivo está solo en la nube, si hubo error de hidratación o si una escritura se cortó a medias.

Impacto:

- Riesgo de leer JSON incompleto.
- Riesgo de sobrescribir archivos mientras OneDrive sincroniza.
- Riesgo de que documentos PDF/Word/fotos existan como placeholders no disponibles localmente.
- Riesgo de corrupción silenciosa si una operación falla a mitad.

Prioridad: **CRÍTICA**.

### 3.2. Escritura JSON parcialmente atómica, pero incompleta para OneDrive

`_write_json_file()` usa archivo temporal y `replace`, lo cual es mejor que escribir directo. Sin embargo, no hace `flush`, `fsync`, backup previo ni validación posterior de lectura. En OneDrive esto sigue siendo riesgoso.

Impacto:

- Corrupción de catálogos, usuarios, correlativos o configuración local.
- Pérdida de datos si `tmp.replace(path)` ocurre mientras OneDrive bloquea o sincroniza.

Prioridad: **CRÍTICA**.

### 3.3. Escritura cifrada también requiere hardening

`save_encrypted_json_path()` escribe un temporal cifrado y reemplaza el archivo final, pero tampoco hace `fsync`, backup anterior ni verificación posterior de descifrado.

Impacto:

- Riesgo de perder registros de vehículos, cotizaciones o auditoría cifrada.
- Si falla la llave/cifrado/replace, el sistema puede devolver `default` y ocultar el problema.

Prioridad: **CRÍTICA**.

### 3.4. Arquitectura por parches acumulados

El archivo tiene bloques sucesivos que redefinen `APP_VERSION`, `create_vehicle_purchase`, `vehicle_total_cost`, `create_quote`, `generate_inventory_excel`, `QuoteEditorDialog`, `QuoteDetailDialog`, `PurchasePage`, `CatalogosPage` y `MainWindow`.

Impacto:

- El comportamiento real depende del último bloque ejecutado.
- Hay código viejo que sigue presente aunque ya no debería usarse.
- Es fácil que una futura edición toque la función vieja y no la función realmente activa.
- Dificulta pruebas, auditoría y mantenimiento.

Prioridad: **ALTA**.

### 3.5. Bug potencial en DoughnutChart

El sistema intenta importar `DoughnutChart` y, si falla, lo deja en `None`. Pero el reporte de inventario usa `DoughnutChart()` sin validar si realmente existe. Si la versión de openpyxl no lo trae, el reporte puede romperse.

Prioridad: **ALTA**.

### 3.6. Self-test insuficiente

El self-test actual solo prueba usuario, autenticación, compra USA, dos etapas, reporte HTML, Excel KPI y backup. No cubre compra local, no duplicidad de costo, cotización leasing, PDF/Word, reporte inventario, doble venta, bloqueo de edición de vendido, historial de propuestas, cliente sin interés/reactivación ni OneDrive.

Prioridad: **ALTA**.

---

## 4. Riesgos de pérdida de dinero

### 4.1. Precio ganado duplicado

El sistema base registra el precio ganado en `precio_ganado_usd`, también lo agrega como gasto detallado `source = purchase` y también registra costo en la etapa `COMPRADO`. Versiones posteriores intentan corregirlo eliminando o ignorando gastos de compra duplicados.

Estado actual:

- Hay mitigaciones en V4.8 y V5.0.
- El riesgo sigue existiendo para datos antiguos o para futuras funciones que lean `gastos_detallados` directamente sin usar `vehicle_total_cost()`.

Recomendación:

- Crear migración segura que marque explícitamente el gasto de compra como `no_sumar = true` o que lo convierta en documento histórico, no gasto financiero.
- Todo reporte debe usar una única función oficial de costo.

### 4.2. Ganancia real depende de usar función oficial

El cierre de venta avanzado calcula precio vendido, regalía, ganancia y margen. Esto es correcto como intención, pero toda pantalla/reporte debe consumir esa misma función oficial.

Riesgo:

- Reportes viejos pueden calcular margen con otra fórmula.
- Funciones duplicadas pueden mostrar ganancias diferentes.

Recomendación:

- Crear `vehicle_profit_summary()` como única fuente de verdad y prohibir cálculos manuales repetidos en reportes.

### 4.3. Servicio de importación necesita separación contable/comercial

El código reconoce `SERVICIO DE IMPORTACION`, pero aún debe revisarse si todos los reportes, KPIs, cotizaciones y estados lo excluyen de inventario propio cuando corresponde.

Riesgo:

- Mezclar inventario propio con servicio a terceros.
- Inflar capital activo, utilidad o disponibilidad.

---

## 5. Problemas visuales

### 5.1. Ventanas fantasma al login

En la lectura del `LoginDialog` no se encontró un `show()` doble directo. El login usa `QTimer.singleShot(80, self._try_autofill)`, pero ese método solo autocompleta usuario/contraseña. El `main()` crea `LoginDialog`, ejecuta `login.exec()` y luego muestra `MainWindow`.

Hipótesis más probable:

- Algún diálogo auxiliar se crea durante `bootstrap_system()`, `ResourceManager.find_logo()`, lectura de catálogos o configuración.
- Alguna clase duplicada vieja puede estar inicializando widgets antes de tiempo.
- Algún `QMessageBox` sin parent o validación de carpeta puede aparecer/cerrarse rápido.

Recomendación:

- Instrumentar temporalmente `QApplication.topLevelWidgets()` al inicio y después de login.
- Agregar logging de creación de `QDialog`/`QMessageBox` en login/configuración.
- Evitar cualquier `QFileDialog` o `QMessageBox` automático antes de que el usuario lo solicite.

### 5.2. Tablas

Existe endurecimiento de tablas con `setMouseTracking(False)`, `SelectRows` y `NoEditTriggers`, lo cual ayuda a evitar selección por hover. Debe aplicarse de forma global a todas las tablas, no solo a algunas.

---

## 6. Problemas con propuestas PDF/Word

Estado positivo:

- V4.9 ya cambia el flujo a PDF + Word.
- Excel legacy se mapea a Word.
- Hay catálogo de firmas, condiciones y opciones de venta.
- La foto del vehículo se mueve a la segunda página.
- Se registra cada propuesta generada en `quote['propuestas']`.

Riesgos pendientes:

- Las funciones viejas de propuesta HTML/Excel siguen existiendo.
- El flujo viejo de botones aún aparece en bloques anteriores, aunque después se sobreescribe.
- No hay prueba automática que confirme que el PDF final tenga exactamente 2 páginas.
- No hay validación automática de que la propuesta Word respete máximo 2 páginas.

Recomendación:

- Mantener solo `generate_quote_proposal_pdf`, `generate_quote_proposal_docx` y `generate_quote_proposal_selected` finales.
- Marcar funciones HTML/Excel legacy como deprecated o eliminarlas tras migración controlada.
- Agregar prueba con `pypdf` o `PyPDF2` para contar páginas del PDF.

---

## 7. Problemas con cotizaciones

Estado positivo:

- La prima por defecto se calcula como 20% + comisión.
- Se guarda `prima_requerida_usd`.
- Los gastos legales usan 1.5% + $140 con tope $365.
- La opción de compra se calcula como cuota si es menor a $500, de lo contrario $500.
- Existe historial de propuestas y seguimiento.
- Existe cliente sin interés y reactivación en bloques finales.

Riesgos pendientes:

- Existen varias capas de `create_quote()` envolviendo la anterior. Esto funciona por orden, pero no es limpio.
- Si una pantalla vieja llama una referencia anterior, puede saltarse reglas nuevas.
- La opción de compra debe validarse visualmente antes de generar propuesta.

Recomendación:

- Consolidar `create_quote()` en una sola función.
- Crear pruebas unitarias para prima, legal, opción compra y recalcular meses.

---

## 8. Problemas con reportes

### 8.1. Excel Inventario

Estado positivo:

- Existe una versión avanzada que genera hojas: `Inventario General`, `Dashboard Gerencial`, `Reportes Detalle` e `Historial Disponible`.
- El status se pinta por celda, no necesariamente toda la fila.
- Incluye fechas lineales, días por fase, vendidos y disponibilidad semanal.

Riesgos:

- Existen varias versiones anteriores de `generate_inventory_excel()` en el mismo archivo.
- `DoughnutChart` puede fallar si no está disponible.
- Para compra LOCAL, se debe asegurar que fechas USA/Aduana queden vacías o N/A en todos los reportes.

### 8.2. Reporte tipo COPART

Estado positivo:

- Hay función para generar hojas `COPART INC` y `COSTO`.

Riesgos:

- Debe confirmarse que siempre use `vehicle_total_cost()` final.
- Debe mostrar estado de OC/comprobante sin romper si falta archivo.

### 8.3. Reporte cotizaciones

Estado positivo:

- Hay reporte Excel y HTML comercial.
- Mantiene cotizaciones aunque el vehículo se venda.

Riesgos:

- Debe completarse KPI de conversión, medios, carro más cotizado y clientes sin interés.

---

## 9. Pruebas ejecutadas / no ejecutadas

| Prueba solicitada | Resultado actual |
|---|---|
| `python -m py_compile LYM_AUTO_CONTROL_V5_0_LEASING.py` | Pendiente. No se pudo clonar/ejecutar por limitación DNS del entorno. |
| Self-test existente | Revisado estáticamente. Cubre solo flujo básico USA. |
| Carga de JSON | Revisada estáticamente. Falta validación OneDrive/fsync/backup. |
| Creación vehículo USA | Cubierta parcialmente por self-test actual. |
| Creación vehículo LOCAL | Pendiente en self-test. La lógica final V5 parece corregida. |
| LOCAL no disponible sin precio final | Cumplido por lectura en override V5, pendiente prueba real. |
| Costo de compra no duplicado | Mitigado por funciones V4.8/V5, pendiente prueba real con datos viejos. |
| Cotización leasing 20% + comisión | Cumplido por lectura, pendiente prueba automatizada. |
| PDF | Implementado, pendiente generación real. |
| Word | Implementado, pendiente generación real. |
| Confirmar PDF 2 páginas | Pendiente. |
| Reporte Excel inventario | Implementado, pendiente ejecución real y bug DoughnutChart. |
| Reporte HTML | Implementado, pendiente ejecución real. |
| DoughnutChart | Riesgo encontrado. Falta guard clause. |
| Doble venta | Bloqueada por lectura en función avanzada. Pendiente prueba real. |
| Vehículo vendido no editar etapas | Bloqueado por lectura en `update_vehicle_stage`. Pendiente prueba real. |
| Buscador +10 vehículos | Implementado con combo editable/completer. Pendiente prueba GUI. |
| Historial propuestas | Implementado. Pendiente prueba real. |
| Cliente sin interés/reactivación | Implementado en bloques finales. Pendiente prueba real. |
| OneDrive rutas existentes/no disponibles | Pendiente. No existe capa OneDrive dedicada. |

---

## 10. Recomendaciones prioritarias

### Prioridad 1 — Seguridad de datos

- Crear `atomic_write_text()` y `atomic_write_bytes()` con:
  - temporal en misma carpeta,
  - `flush`,
  - `os.fsync`,
  - backup `.bak`,
  - replace atómico,
  - verificación posterior.
- Usar estas funciones en JSON, cifrados y catálogos.
- Agregar validación OneDrive antes de guardar.

### Prioridad 2 — Reportes

- Corregir `DoughnutChart` para que si no existe use `PieChart` o no cree la gráfica.
- Consolidar una sola versión de `generate_inventory_excel()`.
- Agregar pruebas con datos fake.

### Prioridad 3 — Reglas de negocio

- Consolidar `create_vehicle_purchase()`, `vehicle_total_cost()`, `create_quote()` y `mark_quote_won_and_vehicle_sold()`.
- Crear migración segura para datos antiguos.
- Separar servicio importación de inventario propio.

### Prioridad 4 — Propuestas

- Mantener PDF/Word únicamente.
- Deprecar propuesta HTML/Excel legacy.
- Agregar test de conteo de páginas PDF.

### Prioridad 5 — Login

- Instrumentar widgets top-level para localizar ventanas fantasma.
- Revisar `bootstrap_system()` y configuración inicial para evitar diálogos sin parent.

---

## 11. Conclusión

El sistema tiene una base funcional avanzada, pero para producción con dinero, inventario y ventas necesita endurecimiento de almacenamiento, limpieza de arquitectura y pruebas obligatorias. La mayor amenaza actual es que los parches acumulados hacen difícil saber qué función es la autoridad real. La siguiente fase debe ser implementar fixes pequeños, probables y reversibles, empezando por OneDrive/JSON y DoughnutChart.
