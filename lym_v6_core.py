from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Mapping, Sequence

PERM_FECHAS_RETROACTIVAS = "fechas_retroactivas_ampliadas"
DEFAULT_RETROACTIVE_DAYS = 2
IVA_VENTA_DEFAULT = Decimal("13")
DUCA_SUBCATEGORY = "IMPUESTOS_ADUANA"
DUCA_TAX_TYPES = ("DAI", "IVA", "APM", "VTS", "ITS", "AIV", "OPM")


def norm(value: Any) -> str:
    import unicodedata
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return " ".join(text.upper().strip().split())


def money_decimal(value: Any, default: Decimal = Decimal("0")) -> Decimal:
    try:
        if value is None or value == "":
            return default
        if isinstance(value, Decimal):
            return value
        if isinstance(value, str):
            value = value.replace("$", "").replace(",", "").strip()
            if not value:
                return default
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return default


def q2(value: Any) -> Decimal:
    return money_decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def money(value: Any) -> float:
    return float(q2(value))


def parse_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None


def validate_operational_date(
    value: Any,
    *,
    has_extended_permission: bool,
    existing_values: Iterable[Any] = (),
    today: date | None = None,
    max_back_days: int = DEFAULT_RETROACTIVE_DAYS,
    allow_future: bool = False,
) -> tuple[bool, str]:
    """Valida la regla global de fechas de LYM.

    - Sin permiso: fecha de hoy o hasta ``max_back_days`` días atrás.
    - Con permiso: cualquier fecha histórica válida.
    - Fechas ya guardadas se permiten sin modificarlas para no dañar datos antiguos.
    - La fecha futura se bloquea salvo que el campo expresamente la permita.
    """
    selected = parse_date(value)
    if selected is None:
        return False, "La fecha no es válida."

    current = today or date.today()
    existing = {d for d in (parse_date(x) for x in existing_values) if d}
    if selected in existing:
        return True, "OK"

    if not allow_future and selected > current:
        return False, "La fecha no puede ser futura."

    if not has_extended_permission:
        minimum = current - timedelta(days=max(0, int(max_back_days)))
        if selected < minimum:
            return (
                False,
                f"Solo puedes registrar fechas desde {minimum.strftime('%d/%m/%Y')} "
                f"(máximo {max_back_days} días atrás). Solicita al administrador "
                "el permiso de fechas retroactivas ampliadas.",
            )
    return True, "OK"


def normalize_duca_lines(lines: Sequence[Mapping[str, Any]] | None) -> list[dict]:
    result: list[dict] = []
    for raw in lines or []:
        tax_type = norm(raw.get("tipo") or raw.get("tributo"))
        if not tax_type:
            continue
        pct = max(money_decimal(raw.get("porcentaje")), Decimal("0"))
        amount = max(money_decimal(raw.get("total") or raw.get("monto_usd")), Decimal("0"))
        payment = norm(raw.get("modalidad_pago") or raw.get("modalidad") or "EFECTIVO")
        result.append(
            {
                "tipo": tax_type,
                "porcentaje": float(pct),
                "total": float(q2(amount)),
                "modalidad_pago": payment or "EFECTIVO",
            }
        )
    return result


def calculate_duca_total(lines: Sequence[Mapping[str, Any]] | None) -> float:
    return float(q2(sum((money_decimal(x.get("total")) for x in normalize_duca_lines(lines)), Decimal("0"))))


def is_purchase_item(item: Mapping[str, Any]) -> bool:
    source = str(item.get("source") or "").lower()
    category = norm(item.get("categoria"))
    subcategory = norm(item.get("subcategoria")).replace(" ", "_")
    return (
        source in {"purchase", "stage:comprado"}
        or category == "COMPRA"
        or subcategory in {"PRECIO_GANADO", "COMPROBANTE_COMPRA", "PRECIO_GANADO_USD"}
    )


def is_duca_item(item: Mapping[str, Any]) -> bool:
    subcategory = norm(item.get("subcategoria")).replace(" ", "_")
    treatment = norm(item.get("tratamiento_fiscal"))
    return (
        subcategory == DUCA_SUBCATEGORY
        or bool(item.get("credito_fiscal_duca_usd"))
        or bool(item.get("duca_tributos"))
        or treatment == "DUCA CREDITO TOTAL"
    )


def expense_amounts(item: Mapping[str, Any]) -> dict[str, float]:
    gross = max(money_decimal(item.get("monto_usd")), Decimal("0"))

    if is_duca_item(item):
        duca_lines_total = money_decimal(calculate_duca_total(item.get("duca_tributos") or []))
        duca_credit = max(
            money_decimal(item.get("credito_fiscal_duca_usd")),
            money_decimal(item.get("credito_fiscal_usd")),
            duca_lines_total,
            gross,
        )
        # Regla aprobada: los impuestos de la DUCA se controlan como crédito fiscal DUCA
        # y no forman parte del costo neto usado para fijar el precio.
        return {
            "gross": float(q2(max(gross, duca_credit))),
            "credit": float(q2(duca_credit)),
            "duca_credit": float(q2(duca_credit)),
            "net": 0.0,
        }

    credit = max(money_decimal(item.get("credito_fiscal_usd")), Decimal("0"))
    if item.get("costo_neto_usd") not in (None, ""):
        net = max(money_decimal(item.get("costo_neto_usd")), Decimal("0"))
    else:
        net = max(gross - credit, Decimal("0"))

    return {
        "gross": float(q2(gross)),
        "credit": float(q2(min(credit, gross) if gross > 0 else credit)),
        "duca_credit": 0.0,
        "net": float(q2(net)),
    }


def _iter_unique_expenses(vehicle: Mapping[str, Any]) -> list[dict]:
    detailed = vehicle.get("gastos_detallados")
    extra = vehicle.get("gastos_extra")
    out: list[dict] = []
    seen: set[str] = set()

    # Los sistemas anteriores podían copiar el mismo gasto en ambas listas.
    # Si ya existe detalle estructurado, se considera la fuente oficial y no se
    # vuelve a sumar ``gastos_extra``.
    collections = [detailed] if isinstance(detailed, list) and detailed else [extra]
    for collection in collections:
        if not isinstance(collection, list):
            continue
        for raw in collection:
            if not isinstance(raw, dict):
                continue
            key = str(raw.get("id") or "")
            if key and key in seen:
                continue
            if key:
                seen.add(key)
            out.append(raw)
    return out


def summarize_vehicle_costs(vehicle: Mapping[str, Any]) -> dict:
    """Resume costo pagado, crédito fiscal y costo neto del vehículo.

    El precio de compra se toma una sola vez desde ``precio_ganado_usd``.
    Los registros antiguos de compra dentro de ``gastos_detallados`` se omiten
    para evitar duplicación.
    """
    purchase = max(money_decimal(vehicle.get("precio_ganado_usd")), Decimal("0"))
    gross_total = purchase
    net_total = purchase
    fiscal_credit_total = Decimal("0")
    duca_credit_total = Decimal("0")
    expenses: dict[str, dict[str, float]] = {}
    duca_taxes: dict[str, float] = {name: 0.0 for name in DUCA_TAX_TYPES}

    detailed_stage_keys: set[str] = set()
    for item in _iter_unique_expenses(vehicle):
        if is_purchase_item(item):
            continue
        stage_key = norm(item.get("stage_key"))
        if stage_key:
            detailed_stage_keys.add(stage_key)
        amounts = expense_amounts(item)
        gross = money_decimal(amounts["gross"])
        credit = money_decimal(amounts["credit"])
        duca_credit = money_decimal(amounts["duca_credit"])
        net = money_decimal(amounts["net"])

        subcategory = norm(item.get("subcategoria") or item.get("categoria") or "OTROS").replace(" ", "_")
        bucket = expenses.setdefault(subcategory, {"gross": 0.0, "credit": 0.0, "net": 0.0})
        bucket["gross"] = money(money_decimal(bucket["gross"]) + gross)
        bucket["credit"] = money(money_decimal(bucket["credit"]) + credit)
        bucket["net"] = money(money_decimal(bucket["net"]) + net)

        gross_total += gross
        fiscal_credit_total += credit
        duca_credit_total += duca_credit
        net_total += net

        if is_duca_item(item):
            for line in normalize_duca_lines(item.get("duca_tributos") or []):
                tax_type = norm(line.get("tipo"))
                duca_taxes[tax_type] = money(money_decimal(duca_taxes.get(tax_type, 0)) + money_decimal(line.get("total")))

    # Compatibilidad con registros antiguos: si una etapa tiene costo acumulado
    # pero todavía no tiene líneas detalladas, se incorpora una sola vez.
    stages = vehicle.get("etapas") if isinstance(vehicle.get("etapas"), dict) else {}
    for stage_key_raw, stage in stages.items():
        if not isinstance(stage, dict):
            continue
        stage_key = norm(stage_key_raw)
        if stage_key in {"", "COMPRADO"} or stage_key in detailed_stage_keys:
            continue
        legacy_amount = max(money_decimal(stage.get("costo_usd")), Decimal("0"))
        if legacy_amount <= 0:
            continue
        subcategory = f"LEGACY_{stage_key.replace(' ', '_')}"
        expenses[subcategory] = {
            "gross": float(q2(legacy_amount)),
            "credit": 0.0,
            "net": float(q2(legacy_amount)),
        }
        gross_total += legacy_amount
        net_total += legacy_amount

    # Si un registro DUCA antiguo no tiene desglose, se conserva en el total DUCA,
    # pero no se inventa una distribución entre tributos.
    generic_credit = max(fiscal_credit_total - duca_credit_total, Decimal("0"))

    return {
        "purchase_cost": float(q2(purchase)),
        "gross_paid": float(q2(gross_total)),
        "generic_fiscal_credit": float(q2(generic_credit)),
        "duca_fiscal_credit": float(q2(duca_credit_total)),
        "total_fiscal_credit": float(q2(fiscal_credit_total)),
        "net_vehicle_cost": float(q2(net_total)),
        "expenses": expenses,
        "duca_taxes": duca_taxes,
    }


def calculate_sale_price(
    total_cost_paid: Any,
    utility_pct: Any,
    *,
    iva_pct: Any = IVA_VENTA_DEFAULT,
    fiscal_credit: Any = 0,
    manual_final_price: Any = 0,
) -> dict:
    """Calcula el precio correcto: costo neto + utilidad y después IVA.

    Mantiene precisión completa hasta el resultado final para coincidir con el
    Excel de COPART. Los importes mostrados se redondean a dos decimales.
    """
    gross = max(money_decimal(total_cost_paid), Decimal("0"))
    credit = max(money_decimal(fiscal_credit), Decimal("0"))
    net_cost = max(gross - credit, Decimal("0"))
    utility_rate = max(money_decimal(utility_pct), Decimal("0")) / Decimal("100")
    iva_rate = max(money_decimal(iva_pct), Decimal("0")) / Decimal("100")

    utility_raw = net_cost * utility_rate
    subtotal_raw = net_cost + utility_raw
    iva_raw = subtotal_raw * iva_rate
    calculated_final_raw = subtotal_raw + iva_raw

    manual = max(money_decimal(manual_final_price), Decimal("0"))
    manual_applied = manual > Decimal("0") and manual >= calculated_final_raw
    final_raw = manual if manual_applied else calculated_final_raw

    return {
        "gross_cost_paid": float(q2(gross)),
        "fiscal_credit": float(q2(credit)),
        "net_cost": float(q2(net_cost)),
        "utility_pct": float(money_decimal(utility_pct)),
        "utility": float(q2(utility_raw)),
        "subtotal_before_iva": float(q2(subtotal_raw)),
        "iva_pct": float(money_decimal(iva_pct)),
        "iva_sale": float(q2(iva_raw)),
        "calculated_final_price": float(q2(calculated_final_raw)),
        "manual_final_price": float(q2(manual)),
        "manual_applied": manual_applied,
        "final_price": float(q2(final_raw)),
        "raw": {
            "utility": str(utility_raw),
            "subtotal_before_iva": str(subtotal_raw),
            "iva_sale": str(iva_raw),
            "calculated_final_price": str(calculated_final_raw),
        },
    }


def validate_manual_price(calculation: Mapping[str, Any]) -> tuple[bool, str]:
    manual = money_decimal(calculation.get("manual_final_price"))
    calculated = money_decimal(calculation.get("calculated_final_price"))
    if manual > 0 and manual < calculated:
        return (
            False,
            "El precio final manual no puede ser menor al precio calculado con "
            "costo neto, utilidad e IVA.",
        )
    return True, "OK"


def migrate_cost_item_v6(item: Mapping[str, Any]) -> dict:
    migrated = deepcopy(dict(item))
    amounts = expense_amounts(migrated)
    migrated.setdefault("credito_fiscal_usd", amounts["credit"])
    migrated.setdefault("credito_fiscal_duca_usd", amounts["duca_credit"])
    migrated.setdefault("costo_neto_usd", amounts["net"])
    migrated.setdefault("factura_numero", "")
    migrated.setdefault("factura_documento", "")
    migrated.setdefault("factura_documento_nombre", "")
    migrated.setdefault("comentario_gasto", "")
    if is_duca_item(migrated):
        migrated["tratamiento_fiscal"] = "DUCA_CREDITO_TOTAL"
    return migrated


def workbook_validation_examples() -> list[dict]:
    """Tres carros del Excel modificado aportado por el usuario."""
    source = [
        ("HYUNDAI TUCSON 2019", "9347.76", "1913.71", "11302.376616"),
        ("HYUNDAI ELANTRA 2015", "8149.866666666667", "1661.25", "9854.003786666667"),
        ("CHEVROLET SPARK 2019", "6799.166666666667", "1063.63", "8220.872416666667"),
    ]
    out: list[dict] = []
    for name, cost, duca, excel_expected in source:
        legacy = calculate_sale_price(cost, 7, iva_pct=13, fiscal_credit=0)
        net = calculate_sale_price(cost, 7, iva_pct=13, fiscal_credit=duca)
        out.append(
            {
                "vehicle": name,
                "excel_total_cost": money(cost),
                "duca_credit": money(duca),
                "excel_expected_final": money(excel_expected),
                "calculated_gross_final": legacy["final_price"],
                "new_net_fiscal_final": net["final_price"],
            }
        )
    return out
