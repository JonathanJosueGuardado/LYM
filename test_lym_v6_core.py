from __future__ import annotations

import unittest
from datetime import date, timedelta

from lym_v6_core import (
    calculate_duca_total,
    calculate_sale_price,
    expense_amounts,
    summarize_vehicle_costs,
    validate_manual_price,
    validate_operational_date,
    workbook_validation_examples,
)


class TestFinancialRules(unittest.TestCase):
    def test_three_excel_vehicles_match(self):
        expected = [11302.38, 9854.00, 8220.87]
        rows = workbook_validation_examples()
        self.assertEqual([row["calculated_gross_final"] for row in rows], expected)
        for row in rows:
            self.assertEqual(row["calculated_gross_final"], row["excel_expected_final"])

    def test_price_adds_utility_before_iva(self):
        calc = calculate_sale_price(10000, 15, iva_pct=13)
        self.assertEqual(calc["utility"], 1500.00)
        self.assertEqual(calc["subtotal_before_iva"], 11500.00)
        self.assertEqual(calc["iva_sale"], 1495.00)
        self.assertEqual(calc["final_price"], 12995.00)

    def test_duca_credit_reduces_cost_base(self):
        calc = calculate_sale_price(10000, 15, iva_pct=13, fiscal_credit=1000)
        self.assertEqual(calc["net_cost"], 9000.00)
        self.assertEqual(calc["final_price"], 11695.50)

    def test_manual_price_cannot_be_lower(self):
        calc = calculate_sale_price(10000, 15, manual_final_price=12000)
        ok, _ = validate_manual_price(calc)
        self.assertFalse(ok)
        calc2 = calculate_sale_price(10000, 15, manual_final_price=13000)
        ok2, _ = validate_manual_price(calc2)
        self.assertTrue(ok2)
        self.assertEqual(calc2["final_price"], 13000.00)

    def test_duca_total(self):
        lines = [
            {"tipo": "DAI", "porcentaje": 25, "total": 1031.82},
            {"tipo": "IVA", "porcentaje": 13, "total": 670.68},
            {"tipo": "APM", "porcentaje": 4, "total": 206.36},
            {"tipo": "VTS", "porcentaje": 0, "total": 15.93},
            {"tipo": "ITS", "porcentaje": 0, "total": 2.07},
            {"tipo": "AIV", "porcentaje": 1, "total": 41.27},
            {"tipo": "OPM", "porcentaje": 0, "total": 0},
        ]
        self.assertEqual(calculate_duca_total(lines), 1968.13)

    def test_duca_is_credit_and_zero_net_cost(self):
        item = {
            "subcategoria": "IMPUESTOS_ADUANA",
            "monto_usd": 1968.13,
            "duca_tributos": [{"tipo": "IVA", "total": 1968.13}],
        }
        amounts = expense_amounts(item)
        self.assertEqual(amounts["credit"], 1968.13)
        self.assertEqual(amounts["duca_credit"], 1968.13)
        self.assertEqual(amounts["net"], 0.0)

    def test_vehicle_summary_avoids_purchase_duplicate(self):
        vehicle = {
            "precio_ganado_usd": 5000,
            "gastos_detallados": [
                {"source": "purchase", "categoria": "COMPRA", "monto_usd": 5000},
                {"subcategoria": "FLETE", "monto_usd": 1000, "credito_fiscal_usd": 130},
                {"subcategoria": "IMPUESTOS_ADUANA", "monto_usd": 600},
            ],
        }
        result = summarize_vehicle_costs(vehicle)
        self.assertEqual(result["gross_paid"], 6600.00)
        self.assertEqual(result["total_fiscal_credit"], 730.00)
        self.assertEqual(result["net_vehicle_cost"], 5870.00)

    def test_legacy_stage_cost_is_preserved(self):
        vehicle = {
            "precio_ganado_usd": 5000,
            "gastos_detallados": [],
            "etapas": {
                "COMPRADO": {"costo_usd": 5000},
                "TRANSITO": {"costo_usd": 900},
                "ADUANA": {"costo_usd": 300},
            },
        }
        result = summarize_vehicle_costs(vehicle)
        self.assertEqual(result["gross_paid"], 6200.00)
        self.assertEqual(result["net_vehicle_cost"], 6200.00)

    def test_date_permission(self):
        today = date(2026, 7, 16)
        ok, _ = validate_operational_date(today - timedelta(days=2), has_extended_permission=False, today=today)
        self.assertTrue(ok)
        ok, _ = validate_operational_date(today - timedelta(days=3), has_extended_permission=False, today=today)
        self.assertFalse(ok)
        ok, _ = validate_operational_date(today - timedelta(days=30), has_extended_permission=True, today=today)
        self.assertTrue(ok)

    def test_existing_old_date_not_corrupted(self):
        today = date(2026, 7, 16)
        old = date(2026, 1, 1)
        ok, _ = validate_operational_date(old, has_extended_permission=False, existing_values=[old], today=today)
        self.assertTrue(ok)


if __name__ == "__main__":
    unittest.main(verbosity=2)
