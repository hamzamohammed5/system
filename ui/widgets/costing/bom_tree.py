"""
ui/widgets/costing/bom_tree.py  — مع عرض كل السيناريوهات كنودات منفصلة

التغيير الجوهري:
  - _refresh: بتجيب كل السيناريوهات وتعمل لكل واحد top-level node
  - كل سيناريو node قابل للـ expand/collapse
  - السيناريو الـ default له أيقونة ⭐ مميزة
  - باقي منطق حساب التكلفة والـ machine_op_row_id بدون تغيير
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QPushButton, QMessageBox,
    QHeaderView, QAbstractItemView, QSizePolicy,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui  import QFont, QColor, QBrush

from db.shared.items_repo      import fetch_bom, fetch_item, delete_bom_row
from db.costing.operations_repo import fetch_labor_op, fetch_machine_op
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

# ألوان السيناريو node
_SCENARIO_DEFAULT_BG  = QColor("#e8f5e9")   # أخضر فاتح للـ default
_SCENARIO_DEFAULT_FG  = QColor("#1b5e20")
_SCENARIO_NORMAL_BG   = QColor("#e3f2fd")   # أزرق فاتح للباقي
_SCENARIO_NORMAL_FG   = QColor("#0d47a1")


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

        lbl_legend = QLabel("⚠️ = نسبة هادر   |   الكمية الفعلية = الكمية × (1 + هادر%)   |   ⭐ = السيناريو الافتراضي")
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
            "المكون / السيناريو", "الكمية", "هادر %", "الكمية الفعلية",
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

    # ══════════════════════════════════════════════════════
    # _refresh — الجوهر: كل سيناريو = node منفصل
    # ══════════════════════════════════════════════════════

    def _refresh(self):
        self.tree.clear()
        if self._pid is None:
            return

        scenarios = self._fetch_all_scenarios(self._pid)

        if not scenarios:
            # Fallback: لو مفيش scenarios خالص، اعرض BOM العادي
            bom_rows = self._fetch_bom_with_row_id_by_scenario(None)
            for row in bom_rows:
                node = self._build_node(
                    row["child_type"], row["child_id"],
                    row["qty"], row.get("waste_pct") or 0.0,
                    machine_op_row_id=row.get("machine_op_row_id")
                )
                if node:
                    self.tree.addTopLevelItem(node)
            self.tree.expandToDepth(0)
            return

        for sc in scenarios:
            sc_id         = sc["id"]
            sc_name       = sc["name"]
            is_default    = bool(sc["is_default"])

            # ── إنشاء node السيناريو ──
            star   = "⭐ " if is_default else "📋 "
            suffix = "  (افتراضي)" if is_default else ""
            sc_label = f"{star}{sc_name}{suffix}"

            sc_node = QTreeWidgetItem([sc_label, "", "", "", "", "", ""])
            sc_node.setData(0, Qt.UserRole, ("__scenario__", sc_id))

            # تنسيق node السيناريو
            font = sc_node.font(0)
            font.setBold(True)
            font.setPointSize(font.pointSize() + 1)
            sc_node.setFont(0, font)

            bg_color = _SCENARIO_DEFAULT_BG if is_default else _SCENARIO_NORMAL_BG
            fg_color = _SCENARIO_DEFAULT_FG if is_default else _SCENARIO_NORMAL_FG
            for col in range(7):
                sc_node.setBackground(col, QBrush(bg_color))
                sc_node.setForeground(col, fg_color)

            # ── مكونات السيناريو ──
            bom_rows = self._fetch_bom_with_row_id_by_scenario(sc_id)
            total_sc_cost = 0.0

            for row in bom_rows:
                child_node = self._build_node(
                    row["child_type"], row["child_id"],
                    row["qty"], row.get("waste_pct") or 0.0,
                    machine_op_row_id=row.get("machine_op_row_id")
                )
                if child_node:
                    sc_node.addChild(child_node)
                    # جمع التكلفة الكلية للسيناريو
                    try:
                        total_sc_cost += float(child_node.text(5))
                    except (ValueError, TypeError):
                        pass

            # عرض التكلفة الكلية للسيناريو في العمود 5
            sc_node.setText(5, f"{total_sc_cost:.4f}")
            sc_node.setFont(5, font)
            sc_node.setForeground(5, QColor("#1b5e20") if is_default else QColor("#0d47a1"))

            self.tree.addTopLevelItem(sc_node)
            sc_node.setExpanded(is_default)   # الـ default يكون مفتوح تلقائياً

    # ══════════════════════════════════════════════════════
    # جلب السيناريوهات
    # ══════════════════════════════════════════════════════

    def _fetch_all_scenarios(self, item_id: int) -> list:
        """يجيب كل السيناريوهات لمنتج معين مرتبة."""
        try:
            rows = self._conn.execute(
                "SELECT id, item_id, name, is_default "
                "FROM bom_scenarios WHERE item_id=? ORDER BY id",
                (item_id,)
            ).fetchall()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def _fetch_bom_with_row_id_by_scenario(self, scenario_id) -> list:
        """
        يجيب BOM لسيناريو محدد (أو fallback للـ parent_id القديم).
        يرجع list of dicts.
        """
        try:
            if scenario_id is not None:
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
                        (scenario_id,)
                    ).fetchall()
                elif has_row_id:
                    rows = self._conn.execute(
                        "SELECT child_type, child_id, qty, "
                        "COALESCE(waste_pct,0) as waste_pct, "
                        "NULL as variant_id, machine_op_row_id "
                        "FROM bom WHERE scenario_id=? ORDER BY id",
                        (scenario_id,)
                    ).fetchall()
                else:
                    rows = self._conn.execute(
                        "SELECT child_type, child_id, qty, "
                        "COALESCE(waste_pct,0) as waste_pct, "
                        "NULL as variant_id, NULL as machine_op_row_id "
                        "FROM bom WHERE scenario_id=? ORDER BY id",
                        (scenario_id,)
                    ).fetchall()

                if rows:
                    return [dict(r) for r in rows]
        except Exception:
            pass

        # Fallback: BOM القديم بدون scenarios
        old_rows = fetch_bom(self._conn, self._pid)
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

    # ══════════════════════════════════════════════════════
    # بناء node المكون — بدون تغيير عن النسخة الأصلية
    # ══════════════════════════════════════════════════════

    def _build_node(self, child_type: str, child_id: int,
                    qty: float, waste_pct: float = 0.0,
                    qty_multiplier: float = 1.0,
                    machine_op_row_id: int = None) -> QTreeWidgetItem | None:

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
            unit_cost = calc_machine_op_cost(
                self._conn, child_id, row_id=machine_op_row_id
            )
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
        eff_qty    = effective_qty(qty, waste_pct)
        total_eff  = eff_qty * qty_multiplier
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
            node.setBackground(2, QBrush(QColor("#fff8e1")))
            node.setBackground(3, QBrush(QColor("#fff8e1")))

        # نصف مصنع → bold + لون + أبناء
        if child_type == "semi":
            font = node.font(0)
            font.setBold(True)
            node.setFont(0, font)
            node.setForeground(0, QColor(_TYPE_COLORS["semi"]))

            sub_bom = self._fetch_bom_with_row_id_by_scenario(
                self._get_scenario_id_for_item(child_id)
            )
            for sub in sub_bom:
                sub_type   = sub["child_type"]
                sub_id     = sub["child_id"]
                sub_qty    = sub["qty"]
                sub_waste  = sub.get("waste_pct") or 0.0
                sub_row_id = sub.get("machine_op_row_id")

                child_node = self._build_node(
                    sub_type, sub_id, sub_qty, sub_waste,
                    qty_multiplier=total_eff,
                    machine_op_row_id=sub_row_id
                )
                if child_node:
                    node.addChild(child_node)

        return node

    def _get_scenario_id_for_item(self, item_id: int):
        """يجيب id الـ default scenario لمنتج معين."""
        try:
            sc = self._conn.execute(
                "SELECT id FROM bom_scenarios WHERE item_id=? AND is_default=1 LIMIT 1",
                (item_id,)
            ).fetchone()
            if not sc:
                sc = self._conn.execute(
                    "SELECT id FROM bom_scenarios WHERE item_id=? ORDER BY id LIMIT 1",
                    (item_id,)
                ).fetchone()
            return sc["id"] if sc else None
        except Exception:
            return None

    # ══════════════════════════════════════════════════════
    # Selection & Delete
    # ══════════════════════════════════════════════════════

    def _on_selection(self):
        item = self.tree.currentItem()
        if not item:
            self.btn_del_node.setEnabled(False)
            return

        data = item.data(0, Qt.UserRole)
        # نفعّل الحذف فقط لو:
        # - أبوه هو node سيناريو (مش top-level مباشرة)
        # - أو مفيش scenarios وهو top-level عادي
        is_scenario_node = (data and isinstance(data, tuple)
                            and data[0] == "__scenario__")
        if is_scenario_node:
            self.btn_del_node.setEnabled(False)
            return

        parent = item.parent()
        if parent is None:
            # top-level بدون scenarios
            self.btn_del_node.setEnabled(True)
        else:
            parent_data = parent.data(0, Qt.UserRole)
            if parent_data and parent_data[0] == "__scenario__":
                # مكون مباشر داخل سيناريو → قابل للحذف
                self.btn_del_node.setEnabled(True)
            else:
                # مكون فرعي داخل نصف مصنع
                self.btn_del_node.setEnabled(False)

    def _delete_node(self):
        node = self.tree.currentItem()
        if not node or self._pid is None:
            return

        data = node.data(0, Qt.UserRole)
        if not data:
            return

        kind = data[0]
        if kind == "__scenario__":
            return

        parent = node.parent()

        # لو أبوه node سيناريو → احذف من ذلك السيناريو
        if parent is not None:
            parent_data = parent.data(0, Qt.UserRole)
            if parent_data and parent_data[0] == "__scenario__":
                child_type, child_id = data
                sc_id = parent_data[1]
                reply = QMessageBox.question(
                    self, "تأكيد الحذف",
                    f"حذف «{node.text(0)}» من السيناريو «{parent.text(0).strip()}»؟",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    try:
                        self._conn.execute(
                            "DELETE FROM bom WHERE scenario_id=? AND child_type=? AND child_id=?",
                            (sc_id, child_type, child_id)
                        )
                        self._conn.commit()
                    except Exception as e:
                        QMessageBox.warning(self, "خطأ", str(e))
                    self._refresh()
                return

            # مكون فرعي داخل نصف مصنع → لا نحذفه من هنا
            QMessageBox.information(
                self, "تنبيه",
                "حذف المكونات الفرعية يتم من تبويب النصف مصنع مباشرةً."
            )
            return

        # top-level بدون scenarios (السلوك القديم)
        child_type, child_id = data
        delete_bom_row(self._conn, self._pid, child_type, child_id)
        self._refresh()


def _fmt_qty(qty: float) -> str:
    """تنسيق الكمية — بدون أصفار زائدة."""
    if qty == int(qty):
        return str(int(qty))
    return f"{qty:.4g}"