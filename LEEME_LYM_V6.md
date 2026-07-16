# LYM AUTO CONTROL V6.0

## Archivos principales

- `LYM_AUTO_CONTROL_V6_0_FINAL.py`: punto de entrada actualizado.
- `lym_v6_runtime.py`: fachada de integración V6.
- `lym_v6_runtime_base.py`: almacenamiento fiscal, fechas, documentos y compatibilidad V5.
- `lym_v6_reports.py`: reportes de gastos, crédito fiscal y repuestos.
- `lym_v6_gui_expenses.py`: ventanas de gastos, DUCA, repuestos, etapas y precio.
- `lym_v6_gui_pages.py`: compra, venta, línea de tiempo y reportería.
- `lym_v6_core.py`: reglas financieras, crédito fiscal, DUCA y fechas.
- `test_lym_v6_core.py`: pruebas automáticas.
- `VALIDACION_FINANCIERA_LYM_V6.xlsx`: comparación de los tres vehículos.
- `VALIDACION_ACTUALIZACION_LYM_V6.md`: resultados y alcance de pruebas.

El archivo original `LYM_AUTO_CONTROL_V5_0_LEASING.py` debe permanecer en la misma carpeta. La V6 no elimina ni transforma destructivamente los datos existentes.

## Instalación

1. Extrae todos los archivos en la carpeta actual del sistema LYM.
2. Confirma que ahí también esté `LYM_AUTO_CONTROL_V5_0_LEASING.py`.
3. Ejecuta `PROBAR_LYM_V6.bat`.
4. Cuando aparezca `PRUEBAS LYM V6 FINALIZADAS CORRECTAMENTE`, abre `INICIAR_LYM_V6.bat`.

## Ejecución manual

```powershell
python LYM_AUTO_CONTROL_V6_0_FINAL.py
```

## Prueba integral

```powershell
python LYM_AUTO_CONTROL_V6_0_FINAL.py --self-test-v6
```

## Cambios incluidos

- Permiso `Permitir fechas retroactivas mayores a 2 días`.
- Regla predeterminada de máximo 2 días atrás.
- Conservación de fechas históricas ya guardadas.
- Color del vehículo en lista editable, solo letras.
- LOTE USA oculta país de compra local.
- Ventana de detalle para cada gasto.
- Factura, OC y comprobante de pago separados.
- Crédito fiscal separado del costo neto.
- Ventana DUCA por tributo y total automático.
- Crédito fiscal DUCA separado.
- Precio correcto: costo neto + utilidad + IVA.
- Reporte horizontal de gastos y crédito fiscal.
- Reporte general de repuestos.
- Línea de tiempo visual en cotizaciones.
- Simulador leasing intacto.

## Dependencias

Se conservan las dependencias de la V5:

```powershell
pip install PySide6 cryptography openpyxl reportlab python-docx pillow
```
