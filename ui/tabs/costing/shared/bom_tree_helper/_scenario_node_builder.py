"""
ui/tabs/costing/shared/bom_tree/_scenario_node_builder.py
==========================================================
_ScenarioNodeBuilder — منطق بناء nodes السيناريو والمكونات في BOM tree.

مُستخرج من bom_tree.py لتقليل الحجم وتسهيل الاختبار.
يُستخدم فقط من BomTree.
"""

from PyQt5.QtWidgets import QTreeWidgetItem
from PyQt5.QtCore    import Qt
from PyQt5.QtGui     import QFont, QColor, QBrush

from db.shared.items_repo       import fetch_item
from db.costing.operations_repo import fetch_labor_op, fetch_machine_op
from models.costing import (
    calc_cost, calc_labor_op_cost, calc_machine_op_cost, raw_unit_price,
)
from models.costing_base import effective_qty


_TYPE_LABELS = {
    "raw":        "🧱 خامة",
    "semi":       "🔧 نصف مصنع",
    "labor_op":   "👷 عملية عمالة",
    "machine_op": "⚙️ عملية تشغيل",
}

_TYPE_COLORS = {
    "raw":        "#1565c0",
    "semi":       "#6a1b9a",
    "labor_op":   "#2e7d32",
    "machine_op": "#e65100",
}

SCENARIO_DEFAULT_BG = QColor("#e8f5e9")
SCENARIO_DEFAULT_FG = QColor("#1b5e20")
SCENARIO_NORMAL_BG  = QColor("#e3f2fd")
SCENARIO_NORMAL_FG  = QColor("#0d47a1")


def build_scenario_node(sc: dict) -> QTreeWidgetItem:
    """
    يبني QTreeWidgetItem لسيناريو معين.

    sc: dict من DB يحتوي id, name, is_default
    """
    sc_id      = sc["id"]
    sc_name    = sc["name"]
    is_default = bool(sc["is_default"])

    star   = "⭐ " if is_default else "📋 "
    suffix = "  (افتراضي)" if is_default else ""
    label  = f"{star}{sc_name}{suffix}"

    node = QTreeWidgetItem([label, "", "", "", "", "", ""])
    node.setData(0, Qt.UserRole, ("__scenario__", sc_id))

    font = node.font(0)
    font.setBold(True)
    font.setPointSize(font.pointSize() + 1)
    node.setFont(0, font)

    bg_color = SCENARIO_DEFAULT_BG if is_default else SCENARIO_NORMAL_BG
    fg_color = SCENARIO_DEFAULT_FG if is_default else SCENARIO_NORMAL_FG
    for col in range(7):
        node.setBackground(col, QBrush(bg_color))
        node.setForeground(col, fg_color)

    return node


def build_component_node(conn, child_type: str, child_id: int,
                          qty: float, waste_pct: float = 0.0,
                          qty_multiplier: float = 1.0,
                          machine_op_row_id: int = None,
                          fetch_sub_bom_fn=None) -> QTreeWidgetItem | None:
    """
    يبني QTreeWidgetItem لمكوّن BOM واحد.

    fetch_sub_bom_fn: دالة تجيب BOM الفرعي للنصف مصنع
                      fn(item_id) → list[dict]
    """
    if child_type == "raw":
        row = fetch_item(conn, child_id)
        if not row:
            return None
        name      = row["name"]
        unit_cost = raw_unit_price(row)

    elif child_type == "semi":
        row = fetch_item(conn, child_id)
        if not row:
            return None
        name      = row["name"]
        unit_cost = calc_cost(conn, child_id)

    elif child_type == "labor_op":
        op = fetch_labor_op(conn, child_id)
        if not op:
            return None
        name      = op["name"]
        unit_cost = calc_labor_op_cost(conn, child_id)

    elif child_type == "machine_op":
        op = fetch_machine_op(conn, child_id)
        if not op:
            return None
        name      = op["name"]
        unit_cost = calc_machine_op_cost(conn, child_id, row_id=machine_op_row_id)
        if machine_op_row_id is not None:
            try:
                row_info = conn.execute(
                    "SELECT label FROM machine_op_rows WHERE id=?",
                    (machine_op_row_id,)
                ).fetchone()
                if row_info and row_info["label"]:
                    name = f"{op['name']} [{row_info['label']}]"
            except Exception:
                pass
    else:
        return None

    eff_qty    = effective_qty(qty, waste_pct)
    total_eff  = eff_qty * qty_multiplier
    total_cost = unit_cost * total_eff

    qty_str     = _fmt_qty(qty)
    waste_str   = f"{waste_pct:.1f} %" if waste_pct > 0 else "—"
    eff_qty_str = _fmt_qty(eff_qty) if waste_pct > 0 else qty_str
    unit_c_str  = f"{unit_cost:.4f}"
    total_c_str = f"{total_cost:.4f}"
    type_lbl    = _TYPE_LABELS.get(child_type, "")

    node = QTreeWidgetItem([
        name, qty_str, waste_str, eff_qty_str,
        unit_c_str, total_c_str, type_lbl
    ])
    node.setData(0, Qt.UserRole, (child_type, child_id))

    # tooltips
    node.setToolTip(0, name)
    node.setToolTip(1, f"الكمية المدخلة: {qty_str}")
    if waste_pct > 0:
        node.setToolTip(
            2,
            f"هادر {waste_pct:.1f}%\n"
            f"الكمية الفعلية = {qty_str} × (1 + {waste_pct:.1f}/100) = {eff_qty_str}"
        )
        node.setToolTip(3, f"الكمية الفعلية = {eff_qty_str}")
    node.setToolTip(4, f"تكلفة الوحدة: {unit_c_str}")
    node.setToolTip(
        5,
        f"التكلفة الكلية = {unit_c_str} × {eff_qty_str} = {total_c_str}"
    )
    if child_type == "machine_op" and machine_op_row_id is not None:
        node.setToolTip(4, f"تكلفة الصف المحدد (ID:{machine_op_row_id}): {unit_c_str}")

    # ألوان
    color = QColor(_TYPE_COLORS.get(child_type, "#333"))
    node.setForeground(6, color)

    if waste_pct > 0:
        waste_color = QColor("#e65100")
        node.setForeground(2, waste_color)
        node.setForeground(3, waste_color)
        node.setBackground(2, QBrush(QColor("#fff8e1")))
        node.setBackground(3, QBrush(QColor("#fff8e1")))

    # نصف مصنع → bold + أبناء
    if child_type == "semi":
        font = node.font(0)
        font.setBold(True)
        node.setFont(0, font)
        node.setForeground(0, QColor(_TYPE_COLORS["semi"]))

        if fetch_sub_bom_fn:
            sub_bom = fetch_sub_bom_fn(child_id)
            for sub in sub_bom:
                sub_node = build_component_node(
                    conn,
                    sub["child_type"], sub["child_id"],
                    sub["qty"], sub.get("waste_pct") or 0.0,
                    qty_multiplier=total_eff,
                    machine_op_row_id=sub.get("machine_op_row_id"),
                    fetch_sub_bom_fn=fetch_sub_bom_fn,
                )
                if sub_node:
                    node.addChild(sub_node)

    return node


def _fmt_qty(qty: float) -> str:
    """تنسيق الكمية — بدون أصفار زائدة."""
    if qty == int(qty):
        return str(int(qty))
    return f"{qty:.4g}"