"""
ui/widgets/costing/bom_tree.py  — مع عرض نسبة الهادر والكمية الفعلية

الإصلاح:
  - _refresh: بتقرأ BOM من الـ default scenario عشان تجيب machine_op_row_id
  - _build_node: بتاخد machine_op_row_id وبتمرره لـ calc_machine_op_cost
  - النتيجة: التكلفة المعروضة في الشجرة تطابق الصف المحدد فعلاً
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QPushButton, QMessageBox,
    QHeaderView, QAbstractItemView, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont, QColor

from db.items_repo      import fetch_bom, fetch_item, delete_bom_row
from db.operations_repo import fetch_labor_op, fetch_machine_op
from models.costing     import (
    calc_cost, calc_labor_op_cost, calc_machine_op_cost, raw_unit_price
)
from models.costing_base import effective_qty
from ui.helpers import danger_button


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


class BomTree(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pid  : int | None = None
        self._conn = None
        self._build()

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()
        lbl = QLabel("🔩 هيكل BOM")
        lbl.setStyleSheet("font-weight:bold; font-size:13px;")

        lbl_legend = QLabel("⚠️ = نسبة هادر   |   الكمية الفعلية = الكمية × (1 + هادر%)")
        lbl_legend.setStyleSheet(
            "font-size:9px; color:#e65100; background:#fff8e1;"
            "border:1px solid #ffe082; border-radius:3px; padding:2px 6px;"
        )

        self.btn_expand   = QPushButton("⊞ توسيع")
        self.btn_collapse = QPushButton("⊟ طي")
        self.btn_del_node = danger_button("🗑 حذف المحدد")

        for btn in (self.btn_expand, self.btn_collapse, self.btn_del_node):
            btn.setEnabled(False)

        self.btn_expand.clicked.connect(lambda: self.tree.expandAll())
        self.btn_collapse.clicked.connect(lambda: self.tree.collapseAll())
        self.btn_del_node.clicked.connect(self._delete_node)

        header.addWidget(lbl)
        header.addWidget(lbl_legend)
        header.addStretch()
        for btn in (self.btn_expand, self.btn_collapse, self.btn_del_node):
            header.addWidget(btn)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels([
            "المكون", "الكمية", "هادر %", "الكمية الفعلية",
            "تكلفة/وحدة", "التكلفة الكلية", "النوع"
        ])
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)

        hh = self.tree.header()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, 7):
            hh.setSectionResizeMode(col, QHeaderView.Interactive)
        hh.setMinimumSectionSize(50)
        self.tree.setColumnWidth(1, 65)
        self.tree.setColumnWidth(2, 65)
        self.tree.setColumnWidth(3, 95)
        self.tree.setColumnWidth(4, 90)
        self.tree.setColumnWidth(5, 95)
        self.tree.setColumnWidth(6, 130)

        self.tree.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tree.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.setWordWrap(True)
        self.tree.itemSelectionChanged.connect(self._on_selection)

        layout.addLayout(header)
        layout.addWidget(self.tree)

    def load(self, conn, parent_id: int):
        self._conn = conn
        self._pid  = parent_id
        for btn in (self.btn_expand, self.btn_collapse):
            btn.setEnabled(True)
        self._refresh()

    def clear_tree(self):
        self._pid = None
        self.tree.clear()
        for btn in (self.btn_expand, self.btn_collapse, self.btn_del_node):
            btn.setEnabled(False)

    def notify_refresh(self):
        if self._pid is not None:
            self._refresh()

    def _refresh(self):
        self.tree.clear()
        if self._pid is None:
            return

        # ✅ نقرأ من الـ default scenario عشان نجيب machine_op_row_id الصحيح
        bom_rows = self._fetch_bom_with_row_id(self._pid)

        for row in bom_rows:
            child_type        = row["child_type"]
            child_id          = row["child_id"]
            qty               = row["qty"]
            waste_pct         = row.get("waste_pct") or 0.0
            machine_op_row_id = row.get("machine_op_row_id")

            node = self._build_node(
                child_type, child_id, qty, waste_pct,
                machine_op_row_id=machine_op_row_id
            )
            if node:
                self.tree.addTopLevelItem(node)

        self.tree.expandToDepth(0)

    def _fetch_bom_with_row_id(self, item_id: int) -> list:
        """
        يجيب BOM مع machine_op_row_id من الـ default scenario.
        Fallback للـ BOM القديم لو مفيش scenarios.
        يرجع list of dicts.
        """
        try:
            # نحاول نجيب من الـ default scenario
            sc = self._conn.execute(
                "SELECT id FROM bom_scenarios WHERE item_id=? AND is_default=1 LIMIT 1",
                (item_id,)
            ).fetchone()
            if not sc:
                sc = self._conn.execute(
                    "SELECT id FROM bom_scenarios WHERE item_id=? ORDER BY id LIMIT 1",
                    (item_id,)
                ).fetchone()

            if sc:
                # تحقق من وجود عمود machine_op_row_id
                cols = {r["name"] for r in
                        self._conn.execute("PRAGMA table_info(bom)").fetchall()}
                has_row_id  = "machine_op_row_id" in cols
                has_variant = "variant_id" in cols

                if has_row_id and has_variant:
                    rows = self._conn.execute(
                        "SELECT child_type, child_id, qty, "
                        "COALESCE(waste_pct,0) as waste_pct, "
                        "variant_id, machine_op_row_id "
                        "FROM bom WHERE scenario_id=? ORDER BY id",
                        (sc["id"],)
                    ).fetchall()
                elif has_row_id:
                    rows = self._conn.execute(
                        "SELECT child_type, child_id, qty, "
                        "COALESCE(waste_pct,0) as waste_pct, "
                        "NULL as variant_id, machine_op_row_id "
                        "FROM bom WHERE scenario_id=? ORDER BY id",
                        (sc["id"],)
                    ).fetchall()
                else:
                    rows = self._conn.execute(
                        "SELECT child_type, child_id, qty, "
                        "COALESCE(waste_pct,0) as waste_pct, "
                        "NULL as variant_id, NULL as machine_op_row_id "
                        "FROM bom WHERE scenario_id=? ORDER BY id",
                        (sc["id"],)
                    ).fetchall()

                if rows:
                    # نحوّل لـ dicts
                    return [dict(r) for r in rows]

        except Exception:
            pass

        # Fallback: الطريقة القديمة (بدون machine_op_row_id)
        old_rows = fetch_bom(self._conn, item_id)
        result = []
        for r in old_rows:
            d = {
                "child_type":        r[0] if isinstance(r, tuple) else r["child_type"],
                "child_id":          r[1] if isinstance(r, tuple) else r["child_id"],
                "qty":               r[2] if isinstance(r, tuple) else r["qty"],
                "waste_pct":         r[3] if isinstance(r, tuple) else (r["waste_pct"] if "waste_pct" in r.keys() else 0.0),
                "variant_id":        None,
                "machine_op_row_id": None,
            }
            result.append(d)
        return result

    def _build_node(self, child_type: str, child_id: int,
                    qty: float, waste_pct: float = 0.0,
                    qty_multiplier: float = 1.0,
                    machine_op_row_id: int = None) -> QTreeWidgetItem | None:
        """
        qty_multiplier: للمكونات الفرعية داخل نصف مصنع
        machine_op_row_id: ✅ الصف المحدد لعملية التشغيل
        """

        if child_type == "raw":
            row = fetch_item(self._conn, child_id)
            if not row:
                return None
            name      = row["name"]
            unit_cost = raw_unit_price(row)

        elif child_type == "semi":
            row = fetch_item(self._conn, child_id)
            if not row:
                return None
            name      = row["name"]
            unit_cost = calc_cost(self._conn, child_id)

        elif child_type == "labor_op":
            op = fetch_labor_op(self._conn, child_id)
            if not op:
                return None
            name      = op["name"]
            unit_cost = calc_labor_op_cost(self._conn, child_id)

        elif child_type == "machine_op":
            op = fetch_machine_op(self._conn, child_id)
            if not op:
                return None
            name = op["name"]
            # ✅ الإصلاح: نمرر machine_op_row_id عشان يحسب تكلفة الصف الصحيح
            unit_cost = calc_machine_op_cost(
                self._conn, child_id, row_id=machine_op_row_id
            )
            # نضيف اسم الصف للعرض لو موجود
            if machine_op_row_id is not None:
                try:
                    row_info = self._conn.execute(
                        "SELECT label FROM machine_op_rows WHERE id=?",
                        (machine_op_row_id,)
                    ).fetchone()
                    if row_info and row_info["label"]:
                        name = f"{op['name']} [{row_info['label']}]"
                except Exception:
                    pass

        else:
            return None

        # حساب الكميات
        eff_qty   = effective_qty(qty, waste_pct)
        total_eff = eff_qty * qty_multiplier
        total_cost = unit_cost * total_eff

        # تنسيق النصوص
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
            node.setToolTip(2, f"هادر {waste_pct:.1f}%\nالكمية الفعلية = {qty_str} × (1 + {waste_pct:.1f}/100) = {eff_qty_str}")
            node.setToolTip(3, f"الكمية الفعلية = {eff_qty_str}")
        node.setToolTip(4, f"تكلفة الوحدة: {unit_c_str}")
        node.setToolTip(5, f"التكلفة الكلية = {unit_c_str} × {eff_qty_str} = {total_c_str}")
        if child_type == "machine_op" and machine_op_row_id is not None:
            node.setToolTip(4, f"تكلفة الصف المحدد (ID:{machine_op_row_id}): {unit_c_str}")

        # ألوان
        color = QColor(_TYPE_COLORS.get(child_type, "#333"))
        node.setForeground(6, color)

        if waste_pct > 0:
            waste_color = QColor("#e65100")
            node.setForeground(2, waste_color)
            node.setForeground(3, waste_color)
            from PyQt5.QtGui import QBrush
            node.setBackground(2, QBrush(QColor("#fff8e1")))
            node.setBackground(3, QBrush(QColor("#fff8e1")))

        # نصف مصنع → bold + لون + أبناء
        if child_type == "semi":
            font = node.font(0)
            font.setBold(True)
            node.setFont(0, font)
            node.setForeground(0, QColor(_TYPE_COLORS["semi"]))

            # أبناء النصف المصنع — نجيبهم مع machine_op_row_id
            sub_bom = self._fetch_bom_with_row_id(child_id)
            for sub in sub_bom:
                sub_type  = sub["child_type"]
                sub_id    = sub["child_id"]
                sub_qty   = sub["qty"]
                sub_waste = sub.get("waste_pct") or 0.0
                sub_row_id = sub.get("machine_op_row_id")

                child_node = self._build_node(
                    sub_type, sub_id, sub_qty, sub_waste,
                    qty_multiplier=total_eff,
                    machine_op_row_id=sub_row_id
                )
                if child_node:
                    node.addChild(child_node)

        return node

    def _on_selection(self):
        item = self.tree.currentItem()
        self.btn_del_node.setEnabled(
            bool(item) and item.parent() is None
        )

    def _delete_node(self):
        node = self.tree.currentItem()
        if not node or self._pid is None:
            return
        if node.parent() is not None:
            QMessageBox.information(
                self, "تنبيه",
                "حذف المكونات الفرعية يتم من تبويب النصف مصنع مباشرةً."
            )
            return

        data = node.data(0, Qt.UserRole)
        if not data:
            return
        child_type, child_id = data
        delete_bom_row(self._conn, self._pid, child_type, child_id)
        self._refresh()


def _fmt_qty(qty: float) -> str:
    """تنسيق الكمية — بدون أصفار زائدة."""
    if qty == int(qty):
        return str(int(qty))
    return f"{qty:.4g}"