# PLAN DE OPTIMIZACIÓN LYM AUTO CONTROL

**Fecha:** 2026-06-14  
**Repositorio:** `JonathanJosueGuardado/LYM`  
**Archivo principal:** `LYM_AUTO_CONTROL_V5_0_LEASING.py`

---

## 1. Objetivo

Convertir LYM AUTO CONTROL en un sistema más seguro, ordenado y confiable para producción, evitando pérdida de datos, cálculos incorrectos, duplicación de costos y corrupción por uso en carpetas compartidas.

Este plan debe ejecutarse por fases pequeñas, con respaldo antes de cada cambio.

---

## 2. Problema principal detectado

El sistema tiene muchas mejoras reales, pero están acumuladas dentro de un solo archivo por bloques de versiones. Varias funciones y clases se redefinen varias veces. Esto hace que el comportamiento final dependa del último bloque ejecutado.

Funciones que deben consolidarse:

- `create_vehicle_purchase`
- `vehicle_total_cost`
- `create_quote`
- `generate_inventory_excel`
- `generate_quotes_excel_report`
- `generate_quote_proposal_selected`
- `QuoteEditorDialog`
- `QuoteDetailDialog`
- `PurchasePage`
- `CatalogosPage`
- `MainWindow`

---

## 3. Fase 0 — Preparación segura

Antes de tocar código productivo:

1. Crear una rama de trabajo.
2. Guardar respaldo del archivo principal.
3. Ejecutar compilación del archivo.
4. Ejecutar el self-test existente.
5. Crear pruebas nuevas para reglas críticas.
6. No modificar datos reales durante pruebas.

Estado actual: desde este entorno no fue posible clonar ni compilar localmente. Por eso los cambios de código deben hacerse en un workspace completo de Codex o en una PC local con el repositorio clonado.

---

## 4. Fase 1 — Seguridad de datos y OneDrive

Crear una capa única para lectura y escritura segura de archivos.

Debe cubrir:

- Escritura temporal.
- Reemplazo seguro del archivo final.
- Respaldo antes de sobrescribir.
- Validación posterior de lectura.
- Mensajes claros si el archivo no está disponible.
- Manejo de errores cuando OneDrive no esté sincronizado.

Carpetas críticas:

- `DATOS`
- `DOCUMENTOS/2026`
- `REPORTES`
- `FOTOS`
- `PLANTILLAS`
- `RESPALDOS`
- catálogos JSON
- documentos asociados a vehículos

Resultado esperado:

- No perder vehículos.
- No corromper cotizaciones.
- No perder catálogos.
- No romper si falta un PDF o foto.

---

## 5. Fase 2 — Consolidar compra vehicular

Crear una sola función oficial de compra.

Debe manejar:

- Compra USA.
- Compra LOCAL.
- Servicio de importación.
- Comprobante de compra.
- OC.
- Características.
- Costo base único.

Reglas obligatorias:

- LOCAL no usa estado USA, subasta, tránsito ni aduana.
- LOCAL no queda disponible automáticamente.
- LOCAL debe pasar por precio final antes de disponible.
- Servicio importación debe separarse del inventario propio.

---

## 6. Fase 3 — Consolidar costo y ganancia

Crear una sola fuente de verdad para costo total.

Reglas:

- El precio ganado se cuenta una sola vez.
- El comprobante de compra no debe duplicar el costo.
- La etapa comprado no debe duplicar el costo.
- Todos los reportes deben usar la misma función de costo.

Crear una sola fuente de verdad para ganancia real.

Fórmula oficial:

`Ganancia real = precio final cliente - IVA a pagar - pago a cuenta - VTS - regalías - costo total`

---

## 7. Fase 4 — Cotizaciones leasing

Consolidar la lógica de cotización en una sola función.

Reglas obligatorias:

- Prima requerida = 20% del valor del vehículo + comisión.
- Gastos legales = 1.5% del valor + base fija 140, con tope 365.
- Opción de compra: si cuota mensual es menor a 500, usar la cuota; si es mayor o igual a 500, usar 500.
- La opción de compra debe seguir siendo editable al generar propuesta.
- Recalcular una cotización no debe borrar propuestas anteriores.
- Cliente sin interés debe poder reactivarse.

---

## 8. Fase 5 — Propuestas PDF y Word

Mantener únicamente:

- PDF
- Word

Eliminar o dejar como legado no visible:

- HTML de propuesta.
- Excel de propuesta.

Reglas de diseño:

- Máximo 2 páginas.
- Logo arriba.
- Sin texto innecesario junto al logo.
- Primera página sin foto grande del vehículo.
- Foto del vehículo en segunda página.
- Firmas de asesor y cliente lado a lado.
- Condiciones desde catálogo.
- Tasa dinámica según cotización.
- Cada propuesta debe guardarse en historial.

---

## 9. Fase 6 — Reportería

### Inventario Excel

Debe quedar una sola función oficial.

Hojas requeridas:

- `Inventario General`
- `Dashboard Gerencial`
- `Historial Disponible`
- `Reportes Detalle`

Correcciones:

- Si no está disponible la gráfica tipo dona, el reporte no debe romperse.
- Compra LOCAL debe mostrar fases USA/Aduana vacías o N/A.
- Servicio importación debe estar separado.
- Solo el estatus debe ir coloreado.

### Costos tipo COPART

Debe generar:

- `COPART INC`
- `COSTO`

Debe usar costo real sin duplicar precio de compra.

### Cotizaciones

Debe estudiar:

- clientes,
- medios de contacto,
- riesgos,
- propuestas generadas,
- clientes sin interés,
- conversión a venta,
- carro más cotizado.

---

## 10. Fase 7 — Login y ventanas fantasma

Agregar diagnóstico temporal para detectar ventanas abiertas al iniciar.

Puntos a revisar:

- Antes de crear el login.
- Después de crear el login.
- Antes de abrir la ventana principal.
- Después de abrir la ventana principal.

También revisar:

- mensajes sin ventana padre,
- diálogos de carpeta,
- configuración automática,
- carga de logo,
- validaciones de OneDrive.

---

## 11. Fase 8 — Migraciones seguras

Crear migración con respaldo previo.

Debe corregir datos antiguos:

- Compra duplicada en gastos detallados.
- Compra LOCAL antigua marcada como disponible automáticamente.
- Campos faltantes de venta.
- Campos faltantes de propuesta.
- Campos faltantes de servicio importación.
- Documentos faltantes marcados como `No cargado`.

Nunca borrar datos reales sin respaldo.

---

## 12. Fase 9 — Pruebas obligatorias

Pruebas mínimas:

1. Compilar archivo principal.
2. Ejecutar self-test.
3. Crear vehículo USA.
4. Crear vehículo LOCAL.
5. Confirmar que LOCAL no queda disponible sin precio final.
6. Confirmar que el costo de compra no se duplica.
7. Crear cotización leasing con prima 20% + comisión.
8. Generar PDF.
9. Generar Word.
10. Confirmar que el PDF tenga 2 páginas.
11. Generar Excel inventario.
12. Generar HTML gerencial.
13. Confirmar que el reporte no falle sin gráfica dona.
14. Vender vehículo una sola vez.
15. Bloquear edición operativa de vehículo vendido.
16. Probar buscador con más de 10 vehículos.
17. Probar historial de propuestas.
18. Probar cliente sin interés y reactivación.
19. Probar rutas OneDrive disponibles.
20. Probar rutas OneDrive no disponibles.

---

## 13. Estructura futura recomendada

Recomendación a mediano plazo:

- `app.py`
- `lym_config.py`
- `lym_storage.py`
- `lym_onedrive.py`
- `domain/vehicles.py`
- `domain/quotes.py`
- `domain/sales.py`
- `domain/costs.py`
- `domain/migrations.py`
- `reports/inventory_excel.py`
- `reports/costs_excel.py`
- `reports/quotes_excel.py`
- `reports/html_dashboard.py`
- `proposals/proposal_pdf.py`
- `proposals/proposal_docx.py`
- `ui/login.py`
- `ui/main_window.py`
- `ui/purchase_page.py`
- `ui/inventory_page.py`
- `ui/quotes_page.py`
- `ui/sales_page.py`
- `ui/catalogos_page.py`
- `tests/test_lym_business_rules.py`

---

## 14. Orden recomendado de implementación

1. Corregir reporte si falla la gráfica dona.
2. Agregar escritura segura con respaldo.
3. Agregar validación OneDrive.
4. Ampliar self-test.
5. Consolidar costo total.
6. Consolidar compra vehicular.
7. Consolidar cotización leasing.
8. Deprecar propuesta HTML/Excel.
9. Probar PDF/Word.
10. Refactorizar UI por módulos.

---

## 15. Criterio de éxito

El sistema estará listo cuando:

- compile sin errores,
- pase pruebas ampliadas,
- no duplique costo de compra,
- compra LOCAL no quede disponible sin precio final,
- PDF y Word se generen correctamente,
- reportes no fallen por dependencias opcionales,
- vehículo vendido no pueda venderse dos veces,
- vehículo vendido no permita editar etapas,
- OneDrive no corrompa archivos,
- cada propuesta quede en historial,
- documentos faltantes no rompan la app.
