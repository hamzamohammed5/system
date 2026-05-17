"""
models/costing_base.py
=======================
الحسابات الأساسية: أجر العامل بالساعة، سعر وحدة الخامة، الكمية مع الهادر.
"""

from db.shared.settings_repo import get_setting


def calc_worker_hourly_rate(conn) -> float:
    """يحسب معدل أجر العامل بالساعة بعد خصم الإجازات وإضافة الأعباء."""
    salary   = get_setting(conn, "monthly_salary",    3000.0)
    w_days   = get_setting(conn, "working_days",        25.0)
    h_days   = get_setting(conn, "holiday_days",         4.0)
    h_per_d  = get_setting(conn, "working_hours_day",    8.0)
    overhead = get_setting(conn, "overhead_factor",      1.10)
    net_hours = max(w_days - h_days, 1) * max(h_per_d, 1)
    return (salary / net_hours) * overhead if net_hours else 0.0


def raw_unit_price(item_row) -> float:
    """
    يحسب سعر الوحدة الواحدة من الخامة.
    لو total_qty محددة وأكبر من صفر:
        unit_price = price / total_qty
    غير كده:
        unit_price = price
    """
    price     = float(item_row["price"])
    total_qty = item_row["total_qty"]
    if total_qty and float(total_qty) > 0:
        return price / float(total_qty)
    return price


def effective_qty(qty: float, waste_pct: float) -> float:
    """
    الكمية الفعلية = qty × (1 + waste_pct / 100)
    مثال: qty=10، waste_pct=10 → 10 × 1.10 = 11
    """
    if waste_pct and waste_pct > 0:
        return qty * (1.0 + waste_pct / 100.0)
    return qty