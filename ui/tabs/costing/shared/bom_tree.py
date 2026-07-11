"""
ui/tabs/costing/shared/bom_tree.py
===================================
BomTree — شجرة عرض BOM مع كل السيناريوهات كنودات منفصلة.

[Refactor] استخدام tr() لكل النصوص + _C للألوان.
[Refactor] استخدام BomTreeService بدل SQL/repos مباشرة.
[Refactor] توفير data_fetcher لـ _scenario_node_builder بدل تمرير conn مباشرة،
           مما يزيل repo access من الـ builder تماماً.

[Fix #10] ربط bus.theme_changed لتحديث stylesheet ديناميكياً عند تغيير الثيم،
  توافقاً مع _OpRowsEditor و _RawVariantsPanel و ScenarioComparisonWidget.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTreeWidget, QTreeWidgetItem, QPushButton, QMessageBox,
    QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt

from services.costing.bom_tree_service import BomTreeService
from ui.theme import _C
from ui.widgets.core.i18n          import tr
from ui.widgets.dialogs.confirm    import confirm_delete
from ui.widgets.core.widget_mixin  import WidgetMixin
from ui.font import FS_XS, FS_SM, FS_MD
from ui.constants import (
    BOM_TREE_BTN_MIN_H, BOM_TREE_BTN_RADIUS, BOM_TREE_BTN_PAD_H,
    BOM_TREE_BTN_PAD_V, BOM_TREE_LEGEND_RADIUS, BOM_TREE_LEGEND_PAD_H,
    BOM_TREE_LEGEND_PAD_V, BOM_TREE_HDR_PAD_H, BOM_TREE_HDR_PAD_V,
    BOM_TREE_COL_QTY_W, BOM_TREE_COL_WASTE_W, BOM_TREE_COL_EFF_QTY_W,
    BOM_TREE_COL_COST_UNIT_W, BOM_TREE_COL_TOTAL_COST_W, BOM_TREE_COL_TYPE_W,
    BOM_TREE_MIN_SECTION_SIZE,
)

from ui.tabs.costing.shared.bom_tree_helper._scenario_node_builder import (
    BomNodeRawData,
    build_scenario_node,
    build_component_node,
)


class BomTree(QWidget, WidgetMixin):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pid  : int | None = None
        self._conn = None
        self._build()
        self._init_widget_mixin(lang=False, data=False)

    def _build(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QHBoxLayout()

        lbl = QLabel(f"{tr('bom_tree_header_icon')}{tr('bom_tree')}")
        lbl.setStyleSheet(
            f"font-weight:bold; font-size:{FS_MD}px; color:{_C['text_primary']};"
        )

        lbl_legend = QLabel(
            f"{tr('bom_tree_warning_icon')} = {tr('waste_pct')}   |   "
            f"{tr('effective_qty')} = {tr('qty')} {tr('bom_tree_multiply_sign')} (1 + {tr('waste_pct')}{tr('percent_sign')})   |   "
            f"{tr('bom_tree_star_icon')} = {tr('default_scenario')}"
        )
        lbl_legend.setStyleSheet(
            f"font-size:{FS_XS}px; color:{_C['orange']}; background:{_C['warning_bg']};"
            f"border:1px solid {_C['warning_border']}; border-radius:{BOM_TREE_LEGEND_RADIUS}px;"
            f"padding:{BOM_TREE_LEGEND_PAD_V}px {BOM_TREE_LEGEND_PAD_H}px;"
        )

        self.btn_expand   = QPushButton(f"{tr('bom_tree_expand_icon')}{tr('expand_all')}")
        self.btn_collapse = QPushButton(f"{tr('bom_tree_collapse_icon')}{tr('collapse_all')}")
        self.btn_del_node = self._make_danger_btn(f"{tr('bom_tree_del_icon')}{tr('delete_selected')}")

        for btn in (self.btn_expand, self.btn_collapse, self.btn_del_node):
            btn.setEnabled(False)
            btn.setMinimumHeight(BOM_TREE_BTN_MIN_H)

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
        self.tree.setAlternatingRowColors(True)

        hh = self.tree.header()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        for col in range(1, 7):
            hh.setSectionResizeMode(col, QHeaderView.Interactive)
        hh.setMinimumSectionSize(BOM_TREE_MIN_SECTION_SIZE)
        self.tree.setColumnWidth(1, BOM_TREE_COL_QTY_W)
        self.tree.setColumnWidth(2, BOM_TREE_COL_WASTE_W)
        self.tree.setColumnWidth(3, BOM_TREE_COL_EFF_QTY_W)
        self.tree.setColumnWidth(4, BOM_TREE_COL_COST_UNIT_W)
        self.tree.setColumnWidth(5, BOM_TREE_COL_TOTAL_COST_W)
        self.tree.setColumnWidth(6, BOM_TREE_COL_TYPE_W)

        self.tree.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.tree.setEditTriggers(QTreeWidget.NoEditTriggers)
        self.tree.setExpandsOnDoubleClick(True)
        self.tree.setWordWrap(True)
        self.tree.itemSelectionChanged.connect(self._on_selection)

        layout.addLayout(header)
        layout.addWidget(self.tree)

        # تطبيق الـ theme الأولي
        self._refresh_style()

    @staticmethod
    def _make_danger_btn(text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['danger_bg']};
                color: {_C['danger']};
                border: 1px solid {_C['danger_border']};
                border-radius: {BOM_TREE_BTN_RADIUS}px;
                padding: {BOM_TREE_BTN_PAD_V}px {BOM_TREE_BTN_PAD_H}px;
                font-size: {FS_SM}px;
            }}
            QPushButton:hover {{ background: {_C['danger']}; color: {_C['btn_primary_text']}; }}
            QPushButton:disabled {{
                background: {_C['bg_surface']};
                color: {_C['text_disabled']};
                border-color: {_C['border']};
            }}
        """)
        return btn

    # [Fix #10] دالة تطبيق الـ theme — تُستدعى عند البناء وعند تغيير الثيم
    def _refresh_style(self, _=None):
        """يُطبق الـ stylesheet عند تغيير الثيم."""
        if hasattr(self, "tree"):
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
                QTreeWidget::item:hover {{
                    background: {_C['bg_hover']};
                }}
            """)
            hh = self.tree.header()
            hh.setStyleSheet(
                f"QHeaderView::section {{"
                f"  background:{_C['bg_surface_2']}; color:{_C['text_sec']};"
                f"  border:none; border-bottom:1px solid {_C['border']};"
                f"  padding:{BOM_TREE_HDR_PAD_V}px {BOM_TREE_HDR_PAD_H}px;"
                f"  font-weight:bold; font-size:{FS_SM}px;"
                f"}}"
            )
        if hasattr(self, "btn_del_node"):
            self.btn_del_node.setStyleSheet(f"""
                QPushButton {{
                    background: {_C['danger_bg']};
                    color: {_C['danger']};
                    border: 1px solid {_C['danger_border']};
                    border-radius: {BOM_TREE_BTN_RADIUS}px;
                    padding: {BOM_TREE_BTN_PAD_V}px {BOM_TREE_BTN_PAD_H}px;
                    font-size: {FS_SM}px;
                }}
                QPushButton:hover {{ background: {_C['danger']}; color: {_C['btn_primary_text']}; }}
                QPushButton:disabled {{
                    background: {_C['bg_surface']};
                    color: {_C['text_disabled']};
                    border-color: {_C['border']};
                }}
            """)

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
    # data_fetcher — يوفر BomNodeRawData بدون repo access في builder
    # ══════════════════════════════════════════════════════

    def _fetch_node_data(self, child_type: str, child_id: int,
                         machine_op_row_id: int | None) -> BomNodeRawData | None:
        """
        يجلب بيانات المكوّن اللازمة لبناء الـ node.

        [إصلاح هيكلي] انتقل الاستدعاء المباشر لـ db/ و models/ إلى
        BomTreeService.get_node_data — هذا الملف (tabs/) لا يستدعي
        repos/ أو models/ مباشرة بعد الآن، فقط services/.
        """
        svc  = BomTreeService(self._conn)
        data = svc.get_node_data(child_type, child_id, machine_op_row_id)
        if data is None:
            return None
        return BomNodeRawData(
            name=data.name,
            unit_cost=data.unit_cost,
            op_row_label=data.op_row_label,
        )

    # ══════════════════════════════════════════════════════
    # _refresh — يستخدم BomTreeService + data_fetcher
    # ══════════════════════════════════════════════════════

    def _refresh(self):
        self.tree.clear()
        if self._pid is None:
            return

        # استخدام BomTreeService بدل SQL مباشر
        svc       = BomTreeService(self._conn)
        scenarios = svc.get_scenarios(self._pid)

        if not scenarios:
            # بدون سيناريوهات — عرض BOM مباشر
            bom_rows = svc.get_bom_for_scenario(None)
            for row in bom_rows:
                node = build_component_node(
                    data_fetcher=self._fetch_node_data,
                    child_type=row["child_type"],
                    child_id=row["child_id"],
                    qty=row["qty"],
                    waste_pct=row.get("waste_pct") or 0.0,
                    machine_op_row_id=row.get("machine_op_row_id"),
                    fetch_sub_bom_fn=self._get_sub_bom_for_item,
                )
                if node:
                    self.tree.addTopLevelItem(node)
            self.tree.expandToDepth(0)
            return

        for sc in scenarios:
            sc_node = build_scenario_node(sc)

            bom_rows      = svc.get_bom_for_scenario(sc["id"])
            total_sc_cost = 0.0

            for row in bom_rows:
                child_node = build_component_node(
                    data_fetcher=self._fetch_node_data,
                    child_type=row["child_type"],
                    child_id=row["child_id"],
                    qty=row["qty"],
                    waste_pct=row.get("waste_pct") or 0.0,
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
    # مساعدات جلب البيانات — عبر BomTreeService
    # ══════════════════════════════════════════════════════

    def _get_sub_bom_for_item(self, item_id: int) -> list:
        svc = BomTreeService(self._conn)
        return svc.get_sub_bom(item_id)

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
                # حذف من سيناريو محدد
                child_type, child_id = data
                sc_id      = parent_data[1]
                node_name  = node.text(0)
                sc_name    = parent.text(0).strip()

                if not confirm_delete(
                    self,
                    tr("bom_delete_from_scenario_msg").format(
                        node_name=node_name, sc_name=sc_name
                    )
                ):
                    return

                try:
                    svc = BomTreeService(self._conn)
                    svc.delete_bom_component(sc_id, child_type, child_id)
                except Exception as e:
                    QMessageBox.warning(self, tr("error"), str(e))
                self._refresh()
                return

            # مكون فرعي داخل نصف مصنع — لا يمكن حذفه من هنا
            QMessageBox.information(
                self, tr("notice"),
                tr("delete_sub_components_from_semi")
            )
            return

        # حذف من BOM الرئيسي (بدون سيناريوهات)
        child_type, child_id = data
        node_name = node.text(0)

        if not confirm_delete(self, node_name):
            return

        try:
            svc = BomTreeService(self._conn)
            svc.delete_bom_row_direct(self._pid, child_type, child_id)
        except Exception as e:
            QMessageBox.warning(self, tr("error"), str(e))
            return
        self._refresh()