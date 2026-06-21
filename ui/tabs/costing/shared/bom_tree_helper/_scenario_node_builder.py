"""
ui/tabs/costing/shared/bom_tree_helper/_scenario_node_builder.py
==========================================================
_ScenarioNodeBuilder — منطق بناء nodes السيناريو والمكونات في BOM tree.

مُستخرج من bom_tree.py لتقليل الحجم وتسهيل الاختبار.
يُستخدم فقط من BomTree.

[Refactor] إزالة استدعاء repos مباشرة من هذا الملف:
  - fetch_item, fetch_labor_op, fetch_machine_op من repos → محذوفة
  - منطق الحساب (calc_cost, calc_labor_op_cost, calc_machine_op_cost, raw_unit_price)
    يُمرَّر عبر دالة data_fetcher من BomTree الذي يملك الـ conn

  الواجهة الجديدة:
    build_component_node(data_fetcher, child_type, child_id, qty, waste_pct, ...)
    حيث data_fetcher: Callable[[str, int, int|None], BomNodeRawData | None]

  BomNodeRawData — dataclass بسيط يحمل:
    name, unit_cost, [op_row_label]

[Fix i18n] كل النصوص (تسميات الأنواع، التولتيبس، نص "افتراضي") انتقلت
  إلى مفاتيح ترجمة في ar.py/en.py — لا نص مكتوب مباشرة في الكود.
[Fix colors] كل الألوان (خلفية/نص node السيناريو، ألوان الأنواع،
  لون الهادر) أصبحت تُقرأ من _C (ui.theme) بدل القيم الست عشرية المباشرة.
  المصدر الوحيد لكل الألوان هو ui/theme_manager.py.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing      import Callable, Optional

from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QColor, QBrush

from models.costing_base import effective_qty
from ui.widgets.core.i18n import tr


# ══════════════════════════════════════════════════════════
# Data containers
# ══════════════════════════════════════════════════════════

@dataclass
class BomNodeRawData:
    """
    البيانات الأولية اللازمة لبناء node واحد في شجرة BOM.
    تُملأ من BomTree الذي يملك الـ conn.
    """
    name:            str
    unit_cost:       float
    op_row_label:    Optional[str] = None    # للـ machine_op فقط


# ══════════════════════════════════════════════════════════
# مساعد ألوان الثيم — قراءة كسولة لتفادي استيراد دائري
# ══════════════════════════════════════════════════════════

def _theme_colors() -> dict:
    """يرجع dict الألوان الحالي (_C) من ui.theme — قراءة كسولة."""
    from ui.theme import _C
    return _C


def _type_label(child_type: str) -> str:
    """يبني تسمية النوع (أيقونة + نص مترجم) من مفاتيح i18n."""
    base_key = {
        "raw":        "raw_material",
        "semi":       "semi_product",
        "labor_op":   "labor_op",
        "machine_op": "machine_op",
    }.get(child_type)
    if base_key is None:
        return ""
    icon_key = f"bom_type_label_{child_type}"
    return t(icon_key).format(label=t(base_key))


def _type_color(child_type: str, colors: dict) -> str:
    """يرجع لون النوع من ثيم التطبيق."""
    return {
        "raw":        colors["blue"],
        "semi":       colors["purple"],
        "labor_op":   colors["acc_type_capital"],
        "machine_op": colors["orange"],
    }.get(child_type, colors["text_primary"])


# ══════════════════════════════════════════════════════════
# بناء node السيناريو
# ══════════════════════════════════════════════════════════

def build_scenario_node(sc: dict) -> QTreeWidgetItem:
    """
    يبني QTreeWidgetItem لسيناريو معين.

    sc: dict من DB يحتوي id, name, is_default
    """
    sc_id      = sc["id"]
    sc_name    = sc["name"]
    is_default = bool(sc["is_default"])

    star   = t("bom_scenario_star_icon") if is_default else t("bom_scenario_normal_icon")
    suffix = t("bom_scenario_default_suffix") if is_default else ""
    label  = f"{star}{sc_name}{suffix}"

    node = QTreeWidgetItem([label, "", "", "", "", "", ""])
    node.setData(0, Qt.UserRole, ("__scenario__", sc_id))

    font = node.font(0)
    font.setBold(True)
    font.setPointSize(font.pointSize() + 1)
    node.setFont(0, font)

    colors   = _theme_colors()
    bg_color = QColor(colors["bom_scenario_default_bg"] if is_default else colors["bom_scenario_normal_bg"])
    fg_color = QColor(colors["bom_scenario_default_fg"] if is_default else colors["bom_scenario_normal_fg"])
    for col in range(7):
        node.setBackground(col, QBrush(bg_color))
        node.setForeground(col, fg_color)

    return node


# ══════════════════════════════════════════════════════════
# بناء node المكوّن — نسخة جديدة بدون repos مباشرة
# ══════════════════════════════════════════════════════════

def build_component_node(
    data_fetcher:       Callable[[str, int, Optional[int]], Optional[BomNodeRawData]],
    child_type:         str,
    child_id:           int,
    qty:                float,
    waste_pct:          float = 0.0,
    qty_multiplier:     float = 1.0,
    machine_op_row_id:  Optional[int] = None,
    fetch_sub_bom_fn:   Optional[Callable[[int], list]] = None,
) -> Optional[QTreeWidgetItem]:
    """
    يبني QTreeWidgetItem لمكوّن BOM واحد.

    المعاملات:
        data_fetcher      : دالة تجيب BomNodeRawData بدون DB access مباشر
                            fn(child_type, child_id, machine_op_row_id) → BomNodeRawData | None
        fetch_sub_bom_fn  : دالة تجيب BOM الفرعي للنصف مصنع
                            fn(item_id) → list[dict]
    """
    node_data = data_fetcher(child_type, child_id, machine_op_row_id)
    if node_data is None:
        return None

    name      = node_data.name
    unit_cost = node_data.unit_cost

    # لو machine_op بصف محدد — إضافة label الصف للاسم
    if child_type == "machine_op" and machine_op_row_id is not None:
        if node_data.op_row_label:
            name = f"{name} [{node_data.op_row_label}]"

    eff_qty    = effective_qty(qty, waste_pct)
    total_eff  = eff_qty * qty_multiplier
    total_cost = unit_cost * total_eff

    qty_str     = _fmt_qty(qty)
    waste_str   = f"{waste_pct:.1f} %" if waste_pct > 0 else t("bom_qty_no_value")
    eff_qty_str = _fmt_qty(eff_qty) if waste_pct > 0 else qty_str
    unit_c_str  = f"{unit_cost:.4f}"
    total_c_str = f"{total_cost:.4f}"
    type_lbl    = _type_label(child_type)

    node = QTreeWidgetItem([
        name, qty_str, waste_str, eff_qty_str,
        unit_c_str, total_c_str, type_lbl
    ])
    node.setData(0, Qt.UserRole, (child_type, child_id))

    # tooltips
    node.setToolTip(0, name)
    node.setToolTip(1, t("bom_tooltip_qty_entered").format(qty=qty_str))
    if waste_pct > 0:
        node.setToolTip(
            2,
            t("bom_tooltip_waste").format(pct=f"{waste_pct:.1f}", qty=qty_str, eff_qty=eff_qty_str)
        )
        node.setToolTip(3, t("bom_tooltip_effective_qty").format(eff_qty=eff_qty_str))
    node.setToolTip(4, t("bom_tooltip_unit_cost").format(cost=unit_c_str))
    node.setToolTip(
        5,
        t("bom_tooltip_total_cost").format(unit_cost=unit_c_str, eff_qty=eff_qty_str, total_cost=total_c_str)
    )
    if child_type == "machine_op" and machine_op_row_id is not None:
        node.setToolTip(
            4,
            t("bom_tooltip_machine_op_row_cost").format(row_id=machine_op_row_id, cost=unit_c_str)
        )

    # ألوان
    colors = _theme_colors()
    color  = QColor(_type_color(child_type, colors))
    node.setForeground(6, color)

    if waste_pct > 0:
        waste_color = QColor(colors["orange"])
        waste_bg    = QColor(colors["waste_low_bg"])
        node.setForeground(2, waste_color)
        node.setForeground(3, waste_color)
        node.setBackground(2, QBrush(waste_bg))
        node.setBackground(3, QBrush(waste_bg))

    # نصف مصنع → bold + أبناء
    if child_type == "semi":
        font = node.font(0)
        font.setBold(True)
        node.setFont(0, font)
        node.setForeground(0, QColor(_type_color("semi", colors)))

        if fetch_sub_bom_fn:
            sub_bom = fetch_sub_bom_fn(child_id)
            for sub in sub_bom:
                sub_node = build_component_node(
                    data_fetcher=data_fetcher,
                    child_type=sub["child_type"],
                    child_id=sub["child_id"],
                    qty=sub["qty"],
                    waste_pct=sub.get("waste_pct") or 0.0,
                    qty_multiplier=total_eff,
                    machine_op_row_id=sub.get("machine_op_row_id"),
                    fetch_sub_bom_fn=fetch_sub_bom_fn,
                )
                if sub_node:
                    node.addChild(sub_node)

    return node


# ══════════════════════════════════════════════════════════
# مساعد تنسيق
# ══════════════════════════════════════════════════════════

def _fmt_qty(qty: float) -> str:
    """تنسيق الكمية — بدون أصفار زائدة."""
    if qty == int(qty):
        return str(int(qty))
    return f"{qty:.4g}"
