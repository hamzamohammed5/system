"""
ui/tabs/costing/shared/bom_tree.py
===================================
BomTree — شجرة عرض BOM مع كل السيناريوهات كنودات منفصلة.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QPushButton, QMessageBox,
    QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt

from db.shared.items_repo import fetch_bom, delete_bom_row
from ui.helpers import danger_button
from ui.app_settings import _C
from ui.widgets.core.i18n import tr

from ui.tabs.costing.shared.bom_tree_helper._scenario_node_builder import (
    build_scenario_node,
    build_component_node,
)


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
        lbl = QLabel(f"🔩 {tr('bom_tree')}")
        lbl.setStyleSheet(
            f"font-weight:bold; font-size:13px; color:{_C['text_primary']};"
        )

        lbl_legend = QLabel(
            f"⚠️ = {tr('waste_pct')}   |   "
            f"{tr('effective_qty')} = {tr('qty')} × (1 + {tr('waste_pct')}%)   |   "
            f"⭐ = {tr('default_scenario')}"
        )
        lbl_legend.setStyleSheet(
            f"font-size:9px; color:{_C['orange']}; background:{_C['warning_bg']};"
            f"border:1px solid {_C['warning_border']}; border-radius:3px; padding:2px 6px;"
        )

        self.btn_expand   = QPushButton(f"⊞ {tr('expand_all')}")
        self.btn_collapse = QPushButton(f"⊟ {tr('collapse_all')}")
        self.btn_del_node = danger_button(f"🗑 {tr('delete_selected')}")

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
            tr("component_scenario"),
            tr("qty"),
            tr("waste_pct_col"),
            tr("effective_qty"),
            tr("cost_per_unit"),
            tr("total_cost"),
            tr("type"),
        ])
        self.tree.setSelectionMode(QTreeWidget.SingleSelection)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                background: {_C['bg_surface']};
                border: 1px solid {_C['border']};
                color: {_C['text_primary']};
            }}
            QTreeWidget::item:selected {{
                background: {_C['accent_light']};
                color: {_C['accent']};
            }}
        """)

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

    # ── API عام ──────────────────────────────────────────

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
    # _refresh
    # ══════════════════════════════════════════════════════

    def _refresh(self):
        self.tree.clear()
        if self._pid is None:
            return

        scenarios = self._fetch_all_scenarios(self._pid)

        if not scenarios:
            bom_rows = self._fetch_bom_with_row_id_by_scenario(None)
            for row in bom_rows:
                node = build_component_node(
                    self._conn,
                    row["child_type"], row["child_id"],
                    row["qty"], row.get("waste_pct") or 0.0,
                    machine_op_row_id=row.get("machine_op_row_id"),
                    fetch_sub_bom_fn=self._get_sub_bom_for_item,
                )
                if node:
                    self.tree.addTopLevelItem(node)
            self.tree.expandToDepth(0)
            return

        for sc in scenarios:
            sc_node = build_scenario_node(sc)

            bom_rows      = self._fetch_bom_with_row_id_by_scenario(sc["id"])
            total_sc_cost = 0.0

            for row in bom_rows:
                child_node = build_component_node(
                    self._conn,
                    row["child_type"], row["child_id"],
                    row["qty"], row.get("waste_pct") or 0.0,
                    machine_op_row_id=row.get("machine_op_row_id"),
                    fetch_sub_bom_fn=self._get_sub_bom_for_item,
                )
                if child_node:
                    sc_node.addChild(child_node)
                    try:
                        total_sc_cost += float(child_node.text(5))
                    except (ValueError, TypeError):
                        pass

            sc_node.setText(5, f"{total_sc_cost:.4f}")

            font = sc_node.font(0)
            sc_node.setFont(5, font)

            self.tree.addTopLevelItem(sc_node)
            sc_node.setExpanded(bool(sc["is_default"]))

    # ══════════════════════════════════════════════════════
    # مساعدات جلب البيانات
    # ══════════════════════════════════════════════════════

    def _fetch_all_scenarios(self, item_id: int) -> list:
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

        old_rows = fetch_bom(self._conn, self._pid)
        result = []
        for r in old_rows:
            d = {
                "child_type":        r[0] if isinstance(r, tuple) else r["child_type"],
                "child_id":          r[1] if isinstance(r, tuple) else r["child_id"],
                "qty":               r[2] if isinstance(r, tuple) else r["qty"],
                "waste_pct":         (
                    r[3] if isinstance(r, tuple)
                    else (r["waste_pct"] if "waste_pct" in r.keys() else 0.0)
                ),
                "variant_id":        None,
                "machine_op_row_id": None,
            }
            result.append(d)
        return result

    def _get_sub_bom_for_item(self, item_id: int) -> list:
        sc_id = self._get_scenario_id_for_item(item_id)
        return self._fetch_bom_with_row_id_by_scenario(sc_id)

    def _get_scenario_id_for_item(self, item_id: int):
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
        is_scenario_node = (
            data and isinstance(data, tuple) and data[0] == "__scenario__"
        )
        if is_scenario_node:
            self.btn_del_node.setEnabled(False)
            return

        parent = item.parent()
        if parent is None:
            self.btn_del_node.setEnabled(True)
        else:
            parent_data = parent.data(0, Qt.UserRole)
            if parent_data and parent_data[0] == "__scenario__":
                self.btn_del_node.setEnabled(True)
            else:
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

        if parent is not None:
            parent_data = parent.data(0, Qt.UserRole)
            if parent_data and parent_data[0] == "__scenario__":
                child_type, child_id = data
                sc_id = parent_data[1]
                reply = QMessageBox.question(
                    self, tr("confirm_delete"),
                    f"{tr('delete_from_scenario')} «{node.text(0)}» "
                    f"{tr('from_scenario')} «{parent.text(0).strip()}»؟",
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
                        QMessageBox.warning(self, tr("error"), str(e))
                    self._refresh()
                return

            QMessageBox.information(
                self, tr("notice"),
                tr("delete_sub_components_from_semi")
            )
            return

        child_type, child_id = data
        delete_bom_row(self._conn, self._pid, child_type, child_id)
        self._refresh()


def _get_tr_keys() -> set:
    """يرجع مجموعة مفاتيح الترجمة المتوفرة — للتحقق الآمن."""
    try:
        from ui.widgets.core.i18n import _TRANSLATIONS
        return set(_TRANSLATIONS.keys())
    except Exception:
        return set()