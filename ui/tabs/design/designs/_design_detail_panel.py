"""
ui/tabs/design/designs/_design_detail_panel.py
==============================
لوحة تفاصيل التصميم — تصميم Modern/Flat محسّن.

التحسينات:
  - header أوضح مع اسم التصميم كبير
  - بطاقات المقاسات بشريط حالة ملوّن
  - شريط filters نظيف في صف واحد
  - مؤشر الفلتر النشط بـ chip واضح
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QComboBox, QMessageBox, QDialog,
    QScrollArea, QFrame
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.designs.dimension_sets_repo import (
    fetch_all_design_categories,
    build_category_tree,
)
from db.designs.designs_repo import (
    fetch_design, insert_design, update_design,
)
from db.designs.designs_sizes_repo import (
    fetch_design_sizes, fetch_design_size,
    delete_design_size,
)

from ._size_card   import _SizeCard
from ._size_dialog import _SizeDialog

# ── ألوان النظام ──
_BG         = "#ffffff"
_BG_SUBTLE  = "#f8fafc"
_BORDER     = "#e2e8f0"
_BORDER_MED = "#cbd5e1"
_TEXT       = "#0f172a"
_TEXT_MED   = "#475569"
_TEXT_MUTED = "#94a3b8"
_BLUE       = "#3b82f6"
_BLUE_LT    = "#eff6ff"
_BLUE_MED   = "#bfdbfe"
_ORANGE     = "#ea580c"
_ORANGE_LT  = "#fff7ed"
_RED        = "#dc2626"
_RED_LT     = "#fef2f2"
_PURPLE     = "#7c3aed"
_PURPLE_LT  = "#f5f3ff"


def _field_style():
    return f"""
        QLineEdit, QComboBox {{
            background: {_BG_SUBTLE};
            border: 1px solid {_BORDER_MED};
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 12px;
            color: {_TEXT};
            min-height: 32px;
        }}
        QLineEdit:focus, QComboBox:focus {{
            border-color: {_BLUE};
            background: {_BG};
        }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
    """


class _DesignDetailPanel(QWidget):
    saved   = pyqtSignal()
    cleared = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn           = conn
        self._design_id     = None
        self._cards         = []
        self._active_set_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══ Header: اسم التصميم + أزرار ══
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: {_BG};
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        header_lay = QVBoxLayout(header)
        header_lay.setContentsMargins(20, 14, 20, 14)
        header_lay.setSpacing(12)

        # صف العنوان
        title_row = QHBoxLayout()
        self.lbl_mode = QLabel("تصميم جديد")
        self.lbl_mode.setStyleSheet(
            f"font-size:15px; font-weight:600; color:{_TEXT}; background:transparent;"
        )
        title_row.addWidget(self.lbl_mode)
        title_row.addStretch()

        self.btn_cancel = QPushButton("إلغاء")
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background:{_BG_SUBTLE}; color:{_TEXT_MED};
                border:1px solid {_BORDER_MED}; border-radius:6px;
                padding:4px 14px; font-size:12px;
            }}
            QPushButton:hover {{ background:{_BG}; color:{_TEXT}; }}
        """)
        self.btn_cancel.setVisible(False)
        self.btn_cancel.clicked.connect(self.reset)

        self.btn_save = QPushButton("💾  حفظ التصميم")
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background:{_BLUE}; color:#fff;
                border:none; border-radius:6px;
                padding:4px 16px; font-size:12px; font-weight:500;
            }}
            QPushButton:hover {{ background:#2563eb; }}
        """)
        self.btn_save.clicked.connect(self._save)

        title_row.addWidget(self.btn_cancel)
        title_row.addWidget(self.btn_save)
        header_lay.addLayout(title_row)

        # صف حقول البيانات
        fields_row = QHBoxLayout()
        fields_row.setSpacing(10)

        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        lbl_n = QLabel("الاسم")
        lbl_n.setStyleSheet(f"font-size:11px; color:{_TEXT_MUTED}; background:transparent;")
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم التصميم...")
        self.inp_name.setStyleSheet(_field_style())
        name_col.addWidget(lbl_n)
        name_col.addWidget(self.inp_name)

        cat_col = QVBoxLayout()
        cat_col.setSpacing(4)
        lbl_c = QLabel("التصنيف")
        lbl_c.setStyleSheet(f"font-size:11px; color:{_TEXT_MUTED}; background:transparent;")
        self.cmb_category = QComboBox()
        self.cmb_category.setStyleSheet(_field_style())
        cat_col.addWidget(lbl_c)
        cat_col.addWidget(self.cmb_category)

        notes_col = QVBoxLayout()
        notes_col.setSpacing(4)
        lbl_no = QLabel("ملاحظات")
        lbl_no.setStyleSheet(f"font-size:11px; color:{_TEXT_MUTED}; background:transparent;")
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات اختيارية...")
        self.inp_notes.setStyleSheet(_field_style())
        notes_col.addWidget(lbl_no)
        notes_col.addWidget(self.inp_notes)

        fields_row.addLayout(name_col, 2)
        fields_row.addLayout(cat_col, 1)
        fields_row.addLayout(notes_col, 1)
        header_lay.addLayout(fields_row)

        root.addWidget(header)

        # ══ شريط المقاسات ══
        self._sizes_hdr = QFrame()
        self._sizes_hdr.setStyleSheet(f"""
            QFrame {{
                background: {_BG_SUBTLE};
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        sh_lay = QHBoxLayout(self._sizes_hdr)
        sh_lay.setContentsMargins(20, 8, 20, 8)
        sh_lay.setSpacing(8)

        lbl_sz = QLabel("مقاسات التصميم")
        lbl_sz.setStyleSheet(
            f"font-size:12px; font-weight:600; color:{_TEXT_MED}; "
            "background:transparent;"
        )

        self.lbl_sizes_count = QLabel("")
        self.lbl_sizes_count.setStyleSheet(
            f"color:{_TEXT_MUTED}; font-size:11px; background:transparent;"
        )

        # مؤشر الفلتر النشط
        self.lbl_filter_badge = QLabel("")
        self.lbl_filter_badge.setStyleSheet(f"""
            QLabel {{
                color: {_ORANGE};
                background: {_ORANGE_LT};
                border: 1px solid #fed7aa;
                border-radius: 12px;
                padding: 2px 10px;
                font-size: 10px;
                font-weight: 500;
            }}
        """)
        self.lbl_filter_badge.setVisible(False)

        self.btn_add_size = QPushButton("➕  إضافة مقاس")
        self.btn_add_size.setEnabled(False)
        self.btn_add_size.setStyleSheet(f"""
            QPushButton {{
                background:{_BLUE}; color:#fff;
                border:none; border-radius:6px;
                padding:4px 14px; font-size:11px; font-weight:500;
            }}
            QPushButton:hover {{ background:#2563eb; }}
            QPushButton:disabled {{
                background:{_BORDER_MED}; color:{_TEXT_MUTED};
            }}
        """)
        self.btn_add_size.clicked.connect(self._add_size)

        sh_lay.addWidget(lbl_sz)
        sh_lay.addWidget(self.lbl_sizes_count)
        sh_lay.addWidget(self.lbl_filter_badge)
        sh_lay.addStretch()
        sh_lay.addWidget(self.btn_add_size)
        root.addWidget(self._sizes_hdr)

        # ══ منطقة البطاقات ══
        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet(f"background:{_BG_SUBTLE};")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setSpacing(10)
        self._cards_layout.setContentsMargins(16, 16, 16, 16)
        self._cards_layout.addStretch()

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setWidget(self._cards_widget)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{_BG_SUBTLE}; }}
            QScrollBar:vertical {{
                background:{_BG_SUBTLE}; width:6px; border-radius:3px;
            }}
            QScrollBar::handle:vertical {{
                background:{_BORDER_MED}; border-radius:3px; min-height:24px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height:0; }}
        """)
        root.addWidget(self._scroll, stretch=1)

        # ── حالة فارغة ──
        self._empty_frame = QFrame()
        self._empty_frame.setStyleSheet(f"background:{_BG_SUBTLE}; border:none;")
        ef_lay = QVBoxLayout(self._empty_frame)
        ef_lay.setAlignment(Qt.AlignCenter)

        ef_icon = QLabel("🎨")
        ef_icon.setAlignment(Qt.AlignCenter)
        ef_icon.setStyleSheet("font-size:44px; background:transparent;")

        ef_msg = QLabel("اختر تصميماً من القائمة\nأو أنشئ تصميماً جديداً")
        ef_msg.setAlignment(Qt.AlignCenter)
        ef_msg.setStyleSheet(
            f"color:{_TEXT_MUTED}; font-size:13px; background:transparent; line-height:1.6;"
        )

        ef_lay.addWidget(ef_icon)
        ef_lay.addSpacing(10)
        ef_lay.addWidget(ef_msg)
        root.addWidget(self._empty_frame)

        self._scroll.setVisible(False)
        self._sizes_hdr.setVisible(False)

        self._reload_categories()

    # ── تحميل التصنيفات ──

    def _reload_categories(self):
        prev = self.cmb_category.currentData()
        self.cmb_category.blockSignals(True)
        self.cmb_category.clear()
        self.cmb_category.addItem("— بدون تصنيف —", None)
        tree = build_category_tree(fetch_all_design_categories(self.conn))
        self._add_cat_nodes(tree, 0)
        for i in range(self.cmb_category.count()):
            if self.cmb_category.itemData(i) == prev:
                self.cmb_category.setCurrentIndex(i)
                break
        self.cmb_category.blockSignals(False)

    def _add_cat_nodes(self, nodes, depth):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_category.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_cat_nodes(node["children"], depth + 1)

    # ── API خارجي ──

    def load_design(self, design_id: int):
        d = fetch_design(self.conn, design_id)
        if not d:
            return
        self._design_id = design_id
        self.inp_name.setText(d["name"])
        self.inp_notes.setText(d["notes"] or "")
        for i in range(self.cmb_category.count()):
            if self.cmb_category.itemData(i) == d["category_id"]:
                self.cmb_category.setCurrentIndex(i)
                break
        self.lbl_mode.setText(f"✏️  تعديل:  {d['name']}")
        self.btn_cancel.setVisible(True)
        self.btn_add_size.setEnabled(True)
        self._empty_frame.setVisible(False)
        self._sizes_hdr.setVisible(True)
        self._scroll.setVisible(True)
        self._refresh_cards()

    def reset(self):
        self._design_id = None
        self.inp_name.clear()
        self.inp_notes.clear()
        self.cmb_category.setCurrentIndex(0)
        self.lbl_mode.setText("تصميم جديد")
        self.btn_cancel.setVisible(False)
        self.btn_add_size.setEnabled(False)
        self._clear_cards()
        self._empty_frame.setVisible(True)
        self._sizes_hdr.setVisible(False)
        self._scroll.setVisible(False)
        self.cleared.emit()

    def filter_by_set(self, set_id):
        self._active_set_id = set_id
        self._refresh_cards()

    # ── بطاقات المقاسات ──

    def _clear_cards(self):
        for card in self._cards:
            self._cards_layout.removeWidget(card)
            card.deleteLater()
        self._cards = []
        self.lbl_sizes_count.setText("")

    def _refresh_cards(self):
        self._clear_cards()
        if not self._design_id:
            return

        all_sizes = fetch_design_sizes(self.conn, self._design_id)
        visible   = (
            [s for s in all_sizes if s["set_id"] == self._active_set_id]
            if self._active_set_id is not None
            else all_sizes
        )

        for s in visible:
            self._add_card(s)

        total = len(all_sizes)
        shown = len(visible)

        if self._active_set_id is not None:
            try:
                row = self.conn.execute(
                    "SELECT name FROM dimension_sets WHERE id=?",
                    (self._active_set_id,)
                ).fetchone()
                set_name = row["name"] if row else f"#{self._active_set_id}"
            except Exception:
                set_name = f"#{self._active_set_id}"
            self.lbl_filter_badge.setText(f"📐 {set_name}")
            self.lbl_filter_badge.setVisible(True)
            self.lbl_sizes_count.setText(
                f"{shown} من {total} مقاس" if shown != total else f"{shown} مقاس"
            )
        else:
            self.lbl_filter_badge.setVisible(False)
            self.lbl_sizes_count.setText(
                f"{total} مقاس" if total else "لا توجد مقاسات بعد"
            )

    def _add_card(self, size_data):
        card = _SizeCard(self.conn, size_data)
        card.edit_requested.connect(self._edit_size)
        card.delete_requested.connect(self._delete_size)
        card.path_changed.connect(self._refresh_cards)
        self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)
        self._cards.append(card)

    # ── CRUD المقاسات ──

    def _add_size(self):
        if not self._design_id:
            return
        dlg = _SizeDialog(self.conn, self._design_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh_cards()
            self.saved.emit()

    def _edit_size(self, size_id: int):
        s = fetch_design_size(self.conn, size_id)
        if not s:
            return
        dlg = _SizeDialog(self.conn, self._design_id, size_data=s, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._refresh_cards()
            self.saved.emit()

    def _delete_size(self, size_id: int):
        s = fetch_design_size(self.conn, size_id)
        if not s:
            return
        name = s["instance_name"] or f"مقاس #{size_id}"
        if QMessageBox.question(
            self, "تأكيد الحذف", f"حذف مقاس «{name}» من هذا التصميم؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_design_size(self.conn, size_id)
            self._refresh_cards()
            self.saved.emit()

    # ── حفظ التصميم ──

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصميم")
            return
        cat_id = self.cmb_category.currentData()
        notes  = self.inp_notes.text().strip()

        if self._design_id:
            update_design(self.conn, self._design_id, name, cat_id, notes)
            self.lbl_mode.setText(f"✏️  تعديل:  {name}")
        else:
            self._design_id = insert_design(self.conn, name, cat_id, notes)
            self.lbl_mode.setText(f"✏️  تعديل:  {name}")
            self.btn_cancel.setVisible(True)
            self.btn_add_size.setEnabled(True)
            self._empty_frame.setVisible(False)
            self._sizes_hdr.setVisible(True)
            self._scroll.setVisible(True)
            self._refresh_cards()

        self.saved.emit()