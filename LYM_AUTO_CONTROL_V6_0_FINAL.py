from __future__ import annotations

"""Punto de entrada de LYM AUTO CONTROL V6.0 fiscal."""

from lym_v6_runtime import *
from lym_v6_gui_expenses import *
from lym_v6_gui_pages import *

def install_v6_patch() -> None:
    base.APP_VERSION = APP_VERSION_V6
    base.PERM_FECHAS_RETROACTIVAS = PERM_FECHAS_RETROACTIVAS
    if PERM_FECHAS_RETROACTIVAS not in base.ALL_PERMISSION_KEYS:
        base.ALL_PERMISSION_KEYS.append(PERM_FECHAS_RETROACTIVAS)
    base.PERM_LABELS[PERM_FECHAS_RETROACTIVAS] = (
        "Permitir fechas retroactivas mayores a 2 días"
    )

    # El permiso no se entrega automáticamente a usuarios operativos.
    # ADMIN conserva permisos completos por la lógica existente.
    base.vehicle_total_cost = vehicle_total_cost_v6
    base._sync_stage_cost_items = sync_stage_cost_items_v6
    base.generate_spare_parts_excel_v6 = generate_spare_parts_excel_v6
    base.generate_horizontal_expense_excel_v6 = generate_horizontal_expense_excel_v6

    if base.PYSIDE_OK:
        base.WorkshopItemDialog = SparePartDialog
        base.CostBreakdownDialog = CostBreakdownDialogV6
        base.StageUpdateDialog = StageUpdateDialogV6
        base.PurchasePage = PurchasePageV6
        base.SaleClosingDialog = SaleClosingDialogV6
        base.QuoteDetailDialog = QuoteDetailDialogTimelineV6
        base.ReporteriaPage = ReporteriaPageV6


def run_self_test_v6() -> int:
    failures: list[str] = []

    # 1) Tres vehículos del Excel modificado.
    for row in workbook_validation_examples():
        if row["calculated_gross_final"] != row["excel_expected_final"]:
            failures.append(
                f"Excel {row['vehicle']}: {row['calculated_gross_final']} != {row['excel_expected_final']}"
            )

    # 2) DUCA del ejemplo aportado.
    duca_lines = [
        {"tipo": "DAI", "porcentaje": 25, "total": 1031.82},
        {"tipo": "IVA", "porcentaje": 13, "total": 670.68},
        {"tipo": "APM", "porcentaje": 4, "total": 206.36},
        {"tipo": "VTS", "porcentaje": 0, "total": 15.93},
        {"tipo": "ITS", "porcentaje": 0, "total": 2.07},
        {"tipo": "AIV", "porcentaje": 1, "total": 41.27},
        {"tipo": "OPM", "porcentaje": 0, "total": 0.00},
    ]
    if calculate_duca_total(duca_lines) != 1968.13:
        failures.append("El total DUCA no coincide con 1,968.13.")

    # 3) Regla del 15% + IVA 13%.
    calc = calculate_sale_price(10000, 15, iva_pct=13)
    if calc["final_price"] != 12995.00:
        failures.append(f"Precio 15% + IVA incorrecto: {calc['final_price']}")

    # 4) Integración base: compra, etapas y reportes.
    try:
        result = base.run_self_test()
        if result != 0:
            failures.append(f"Self-test heredado devolvió {result}.")
        else:
            vehicles = base.load_vehicles()
            if vehicles:
                vehicle = vehicles[0]
                vehicle.setdefault("gastos_detallados", []).extend([
                    {
                        "id": uuid.uuid4().hex,
                        "source": f"stage:{base.STAGE_ADUANA}",
                        "stage_key": base.STAGE_ADUANA,
                        "categoria": "ADUANA",
                        "subcategoria": DUCA_SUBCATEGORY,
                        "descripcion": "DUCA prueba",
                        "monto_usd": 1968.13,
                        "credito_fiscal_usd": 1968.13,
                        "credito_fiscal_duca_usd": 1968.13,
                        "costo_neto_usd": 0.0,
                        "duca_tributos": duca_lines,
                        "fecha": date.today().isoformat(),
                    },
                    {
                        "id": uuid.uuid4().hex,
                        "source": f"stage:{base.STAGE_ADUANA}",
                        "stage_key": base.STAGE_ADUANA,
                        "categoria": "ADUANA",
                        "subcategoria": "NAVIERA_FLETE",
                        "descripcion": "Flete prueba",
                        "monto_usd": 1000,
                        "credito_fiscal_usd": 130,
                        "costo_neto_usd": 870,
                        "fecha": date.today().isoformat(),
                    },
                    {
                        "id": uuid.uuid4().hex,
                        "source": f"stage:{base.STAGE_PREPARACION}",
                        "stage_key": base.STAGE_PREPARACION,
                        "categoria": "TALLER",
                        "subcategoria": "REPUESTO_DETALLE",
                        "descripcion": "Repuesto prueba",
                        "monto_usd": 200,
                        "credito_fiscal_usd": 26,
                        "costo_neto_usd": 174,
                        "fecha": date.today().isoformat(),
                    },
                ])
                base.save_vehicle(vehicle)
                user = {"usuario": "admin", "rol": base.ROLE_ADMIN, "permissions": {k: True for k in base.ALL_PERMISSION_KEYS}}
                ok_h, msg_h, path_h = generate_horizontal_expense_excel_v6(base.load_vehicles(), user)
                ok_r, msg_r, path_r = generate_spare_parts_excel_v6(base.load_vehicles(), user)
                if not ok_h or not path_h or not path_h.exists():
                    failures.append(f"Reporte horizontal: {msg_h}")
                if not ok_r or not path_r or not path_r.exists():
                    failures.append(f"Reporte repuestos: {msg_r}")
    except Exception as exc:
        failures.append(f"Integración V6: {type(exc).__name__}: {exc}")

    if failures:
        print("SELF TEST V6 CON ERRORES")
        for failure in failures:
            print(" -", failure)
        return 1

    print("SELF TEST V6 OK")
    for row in workbook_validation_examples():
        print(
            row["vehicle"],
            "Excel=", row["calculated_gross_final"],
            "Nuevo neto fiscal=", row["new_net_fiscal_final"],
        )
    return 0


install_v6_patch()


if __name__ == "__main__":
    if "--self-test" in sys.argv or "--self-test-v6" in sys.argv:
        raise SystemExit(run_self_test_v6())
    raise SystemExit(base.main())
