"""
ui/tabs/companies/shared_items_manager.py
==========================================
SharedItemsManagerDialog — نافذة إدارة كل العناصر المشتركة.

تُفتح من زر «🔗 العناصر المشتركة» في الـ sidebar.

الوظائف:
  - عرض كل العناصر المشتركة مجمّعة بالنوع
  - إضافة عنصر مشترك جديد
  - تعديل عنصر موجود (يفتح SharedItemsDialog)
  - حذف عنصر مشترك
  - إدارة ربط الشركات من خلال SharedItemsDialog
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QLabel, QPushButton, QTreeWidget, QTreeWidgetItem,
    QTabWidget, QWidget, QMessageBox, QFrame,
    QHeaderView, QAbstractItemView,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QColor, QFont, QBrush

from db.companies.shared_items_repo import (
    fetch_all_shared_items, delete_shared_item,
    fetch_linked_companies,
)
from ui.widgets.core.events import emit_company_data_changed
from ui.widgets.core.i18n import tr
from ui.font import FS_SM, FS_LG
from ui.constants import (
    SHARED_MGR_MIN_W, SHARED_MGR_MIN_H,
    SHARED_MGR_BODY_MARGIN, SHARED_MGR_BODY_SPACING,
    SHARED_MGR_HINT_RADIUS, SHARED_MGR_HINT_PAD_V, SHARED_MGR_HINT_PAD_H,
    SHARED_MGR_BTN_MIN_H, SHARED_MGR_BTN_ADD_RADIUS, SHARED_MGR_BTN_ADD_PAD_H,
    SHARED_MGR_BTN_DEL_RADIUS, SHARED_MGR_BTN_DEL_PAD_H,
    SHARED_MGR_TREE_RADIUS, SHARED_MGR_TREE_ITEM_PAD_V, SHARED_MGR_TREE_ITEM_PAD_H,
    SHARED_MGR_COL1_W, SHARED_MGR_COL2_W, SHARED_MGR_COL3_W, SHARED_MGR_COL4_W,
    SHARED_MGR_HDR_H, SHARED_MGR_HDR_MARGIN_H, SHARED_MGR_CLOSE_BTN_H,
    MARGIN_ZERO, SPACING_ZERO, SHARED_MGR_TREE_TYPE_FONT_DELTA,
    SHARED_MGR_HDR_BORDER_W, SHARED_MGR_HINT_BORDER_W, SHARED_MGR_BTN_DEL_BORDER_W,
)


def _type_label(t: str) -> str:
    return {
        "raw":        f"{tr('shared_type_icon_raw')}  {tr('shared_type_raw')}",
        "machine":    f"{tr('shared_type_icon_machine')}  {tr('shared_type_machine')}",
        "labor_op":   f"{tr('shared_type_icon_labor_op')}  {tr('shared_type_labor_op')}",
        "machine_op": f"{tr('shared_type_icon_machine_op')}  {tr('shared_type_machine_op')}",
    }.get(t, t)


def _type_color(t: str) -> str:
    from ui.theme import _C   # lazy import — يُقرأ عند كل استدعاء
    return {
        "raw":        _C["acc_type_asset"],
        "machine":    _C["purple"],
        "labor_op":   _C["success"],
        "machine_op": _C["orange"],
    }.get(t, _C["text_primary"])


class SharedItemsManagerDialog(QDialog):
    """
    نافذة إدارة العناصر المشتركة بين الشركات.

    الاستخدام:
        central = get_central_connection()
        dlg = SharedItemsManagerDialog(central, parent=self)
        dlg.items_changed.connect(lambda: bus.data_changed.emit())
        dlg.exec_()
        central.close()
    """

    items_changed = pyqtSignal()

    def __init__(self, central_conn, parent=None):
        super().__init__(parent)
        self._conn = central_conn
        self.setWindowTitle(tr("shared_item_header"))
        self.setMinimumSize(SHARED_MGR_MIN_W, SHARED_MGR_MIN_H)
        self.setModal(True)
        self.setLayoutDirection(Qt.RightToLeft)
        self._build()
        self._load()

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(*MARGIN_ZERO)
        root.setSpacing(SPACING_ZERO)

        root.addWidget(self._build_header())

        from ui.theme import _C
        body = QWidget()
        body.setStyleSheet(f"background:{_C['bg_page']};")
        body_lay = QVBoxLayout(body)
        body_lay.setContentsMargins(*SHARED_MGR_BODY_MARGIN)
        body_lay.setSpacing(SHARED_MGR_BODY_SPACING)

        # ── شرح ──
        lbl_hint = QLabel(tr("shared_item_hint"))
        lbl_hint.setWordWrap(True)
        lbl_hint.setStyleSheet(
            f"background:{_C['success_bg']}; border:{SHARED_MGR_HINT_BORDER_W}px solid {_C['success_border']};"
            f"border-radius:{SHARED_MGR_HINT_RADIUS}px; padding:{SHARED_MGR_HINT_PAD_V}px {SHARED_MGR_HINT_PAD_H}px; color:{_C['success']}; font-size:{FS_SM}px;"
        )
        body_lay.addWidget(lbl_hint)

        # ── أزرار ──
        btn_row = QHBoxLayout()

        self.btn_add = QPushButton(tr("shared_add_btn"))
        self.btn_add.setMinimumHeight(SHARED_MGR_BTN_MIN_H)
        self.btn_add.setStyleSheet(
            f"background:{_C['accent']}; color:{_C['bg_surface']}; font-weight:bold;"
            f"border-radius:{SHARED_MGR_BTN_ADD_RADIUS}px; padding:0 {SHARED_MGR_BTN_ADD_PAD_H}px;"
        )
        self.btn_add.clicked.connect(self._add_item)

        self.btn_edit = QPushButton(tr("shared_edit_btn"))
        self.btn_edit.setMinimumHeight(SHARED_MGR_BTN_MIN_H)
        self.btn_edit.clicked.connect(self._edit_item)

        self.btn_delete = QPushButton(tr("shared_delete_btn"))
        self.btn_delete.setMinimumHeight(SHARED_MGR_BTN_MIN_H)
        self.btn_delete.setStyleSheet(
            f"background:{_C['danger_bg']}; color:{_C['danger']};"
            f"border:{SHARED_MGR_BTN_DEL_BORDER_W}px solid {_C['danger_border']};"
            f"border-radius:{SHARED_MGR_BTN_DEL_RADIUS}px; padding:0 {SHARED_MGR_BTN_DEL_PAD_H}px; font-weight:bold;"
        )
        self.btn_delete.clicked.connect(self._delete_item)

        self.btn_refresh = QPushButton(tr("shared_refresh_btn"))
        self.btn_refresh.setMinimumHeight(SHARED_MGR_BTN_MIN_H)
        self.btn_refresh.clicked.connect(self._load)

        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_refresh)
        body_lay.addLayout(btn_row)

        # ── الشجرة ──
        self.tree = QTreeWidget()
        self.tree.setColumnCount(5)
        self.tree.setHeaderLabels([
            tr("name"),
            tr("type"),
            tr("shared_main_data_col"),
            tr("shared_companies_col"),
            tr("shared_last_update_col"),
        ])
        self.tree.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tree.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemDoubleClicked.connect(self._on_double_click)
        self.tree.setStyleSheet(f"""
            QTreeWidget {{
                border:1px solid {_C['border']}; border-radius:{SHARED_MGR_TREE_RADIUS}px;
                background:{_C['bg_input']};
                alternate-background-color:{_C['bg_surface']};
            }}
            QTreeWidget::item {{ padding:{SHARED_MGR_TREE_ITEM_PAD_V}px {SHARED_MGR_TREE_ITEM_PAD_H}px; }}
            QTreeWidget::item:selected {{
                background:{_C['accent_light']}; color:{_C['accent_text']};
            }}
        """)

        hh = self.tree.header()
        hh.setSectionResizeMode(0, QHeaderView.Stretch)
        hh.setSectionResizeMode(1, QHeaderView.Interactive)
        hh.setSectionResizeMode(2, QHeaderView.Interactive)
        hh.setSectionResizeMode(3, QHeaderView.Interactive)
        hh.setSectionResizeMode(4, QHeaderView.Interactive)
        self.tree.setColumnWidth(1, SHARED_MGR_COL1_W)
        self.tree.setColumnWidth(2, SHARED_MGR_COL2_W)
        self.tree.setColumnWidth(3, SHARED_MGR_COL3_W)
        self.tree.setColumnWidth(4, SHARED_MGR_COL4_W)

        body_lay.addWidget(self.tree, stretch=1)

        btn_close = QPushButton(tr("shared_close_btn"))
        btn_close.setMinimumHeight(SHARED_MGR_CLOSE_BTN_H)
        btn_close.clicked.connect(self.accept)
        close_row = QHBoxLayout()
        close_row.addStretch()
        close_row.addWidget(btn_close)
        body_lay.addLayout(close_row)

        root.addWidget(body, stretch=1)

    def _build_header(self) -> QFrame:
        from ui.theme import _C
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: {_C['accent']};
                border-bottom: {SHARED_MGR_HDR_BORDER_W}px solid {_C['accent_hover']};
            }}
        """)
        header.setFixedHeight(SHARED_MGR_HDR_H)
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(SHARED_MGR_HDR_MARGIN_H, 0, SHARED_MGR_HDR_MARGIN_H, 0)
        lbl = QLabel(tr("shared_item_header"))
        lbl.setStyleSheet(
            f"font-size:{FS_LG}px; font-weight:bold; color:{_C['bg_surface']};"
            "background:transparent; border:none;"
        )
        h_lay.addWidget(lbl)
        h_lay.addStretch()
        return header

    # ══════════════════════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════════════════════

    def _load(self):
        from ui.theme import _C
        self.tree.clear()
        items = fetch_all_shared_items(self._conn)

        # تجميع بالنوع
        by_type: dict = {}
        for item in items:
            t = item["shared_type"]
            by_type.setdefault(t, []).append(item)

        for shared_type, type_items in sorted(by_type.items()):
            # نود النوع
            type_label = _type_label(shared_type)
            type_node  = QTreeWidgetItem([
                f"{type_label}  ({len(type_items)})", "", "", "", ""
            ])
            font = QFont()
            font.setBold(True)
            font.setPointSize(font.pointSize() + SHARED_MGR_TREE_TYPE_FONT_DELTA)
            type_node.setFont(0, font)
            color = QColor(_type_color(shared_type))
            type_node.setForeground(0, color)
            type_node.setBackground(0, QBrush(QColor(_C["bg_surface_2"])))
            type_node.setData(0, Qt.UserRole, ("__type__", shared_type))

            for item in type_items:
                linked_cos = fetch_linked_companies(self._conn, item["id"])
                co_names   = ", ".join(c["name"] for c in linked_cos) or tr("dash")

                try:
                    import json
                    data = json.loads(item["data"]) if item["data"] else {}
                except Exception:
                    data = {}

                data_summary = self._data_summary(shared_type, data)
                type_short = _type_label(shared_type).split("  ", 1)[-1] if "  " in _type_label(shared_type) else shared_type

                child = QTreeWidgetItem([
                    item["name"],
                    type_short,
                    data_summary,
                    f"{tr('shared_company_prefix')}{co_names}  ({len(linked_cos)} {tr('companies')})",
                    item["updated_at"][:16] if item["updated_at"] else tr("dash"),
                ])
                child.setData(0, Qt.UserRole, ("item", item["id"]))
                child.setToolTip(0, item["name"])
                child.setToolTip(3, co_names)
                type_node.addChild(child)

            self.tree.addTopLevelItem(type_node)
            type_node.setExpanded(True)

    def _data_summary(self, shared_type: str, data: dict) -> str:
        """ملخص قصير لبيانات العنصر."""
        sep = f"  {tr('vertical_separator')}  "
        if shared_type == "raw":
            price = data.get("price", 0)
            tq    = data.get("total_qty")
            if tq:
                return f"{tr('price')}: {price:.2f}{sep}{tr('quantity')}: {tq}"
            return f"{tr('price')}: {price:.2f}"
        elif shared_type == "machine":
            rh = data.get("rate_per_hour", 0)
            ru = data.get("rate_per_unit", 0)
            return f"{rh:.2f} / {tr('hour')}{sep}{ru:.2f} / {tr('unit')}"
        elif shared_type == "labor_op":
            m = data.get("minutes", 0)
            return f"{m:.2f} {tr('labor_time_lbl').split('(')[-1].rstrip(')')}"
        elif shared_type == "machine_op":
            v = data.get("value", 0)
            m = data.get("mode", "time")
            mode_label = tr("hour") if m == "time" else tr("unit")
            return f"{mode_label}: {v:.4g}"
        return tr("dash")

    # ══════════════════════════════════════════════════════
    # أحداث
    # ══════════════════════════════════════════════════════

    def _selected_item_id(self) -> int | None:
        item = self.tree.currentItem()
        if not item:
            return None
        data = item.data(0, Qt.UserRole)
        if data and data[0] == "item":
            return data[1]
        return None

    def _on_double_click(self, item, col):
        data = item.data(0, Qt.UserRole)
        if data and data[0] == "item":
            self._open_edit_dialog(data[1])

    def _add_item(self):
        """إضافة عنصر مشترك جديد."""
        try:
            from ui.tabs.companies.shared_items_manager_helper._add_shared_item_dialog import (
                PublishAsSharedDialog
            )
        except ImportError:
            # fallback بسيط لو الملف مش موجود
            self._add_item_simple()
            return

        # نفتح نافذة الإضافة مع نوع = raw افتراضياً
        dlg = PublishAsSharedDialog(
            central_conn=self._conn,
            shared_type="raw",
            item_name="",
            item_data={},
            parent=self,
        )
        if dlg.exec_():
            self._load()
            self.items_changed.emit()
            emit_company_data_changed()

    def _add_item_simple(self):
        """إضافة بسيطة بدون نافذة خاصة — يُستخدم كـ fallback."""
        from PyQt5.QtWidgets import QInputDialog
        types = ["raw", "machine", "labor_op", "machine_op"]
        type_labels = [
            tr("shared_type_raw"), tr("shared_type_machine"),
            tr("shared_type_labor_op"), tr("shared_type_machine_op"),
        ]
        t, ok = QInputDialog.getItem(
            self, tr("type"), tr("select"),
            type_labels, 0, False
        )
        if not ok:
            return
        shared_type = types[type_labels.index(t)]

        name, ok = QInputDialog.getText(self, tr("name"), tr("name"))
        if not ok or not name.strip():
            return

        from db.companies.shared_items_repo import insert_shared_item
        new_id = insert_shared_item(self._conn, name.strip(), shared_type)
        self._load()
        emit_company_data_changed()
        self._open_edit_dialog(new_id)

    def _edit_item(self):
        item_id = self._selected_item_id()
        if item_id is None:
            QMessageBox.information(self, tr("notice"), tr("select_item_first"))
            return
        self._open_edit_dialog(item_id)

    def _open_edit_dialog(self, item_id: int):
        from ui.tabs.companies.shared_items_dialog import SharedItemsDialog
        dlg = SharedItemsDialog(self._conn, item_id, parent=self)
        dlg.item_updated.connect(self._load)
        dlg.item_updated.connect(self.items_changed.emit)
        dlg.exec_()

    def _delete_item(self):
        item_id = self._selected_item_id()
        if item_id is None:
            QMessageBox.information(self, tr("notice"), tr("select_item_first"))
            return

        # تحقق من وجود شركات مرتبطة
        linked = fetch_linked_companies(self._conn, item_id)
        if linked:
            co_names = ", ".join(c["name"] for c in linked)
            reply = QMessageBox.question(
                self, tr("confirm_delete"),
                tr("shared_delete_with_companies").format(count=len(linked)) + f"\n{co_names}",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
        else:
            reply = QMessageBox.question(
                self, tr("confirm_delete"), tr("shared_delete_simple"),
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        delete_shared_item(self._conn, item_id)
        self._load()
        self.items_changed.emit()
        emit_company_data_changed()
        QMessageBox.information(self, tr("done"), tr("shared_deleted_msg"))