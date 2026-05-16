"""
ui/tabs/design/designs/_design_detail_panel.py
==============================
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

# ── ألوان ──
_BLUE       = "#1565c0"
_BLUE_LIGHT = "#e8f0fe"
_BLUE_MID   = "#bbdefb"
_GRAY_BG    = "#f8f9fc"
_BORDER     = "#e0e7f3"
_TEXT_MUTED = "#7a869a"

# ══════════════════════════════════════════════════════════
# لوحة تفاصيل التصميم (يمين)
# ══════════════════════════════════════════════════════════

class _DesignDetailPanel(QWidget):
    """
    لوحة تفاصيل التصميم:
      - اسم + ملاحظات + تصنيف
      - قائمة المقاسات (بطاقات قابلة للتمرير)
    """

    saved   = pyqtSignal()
    cleared = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._design_id  = None
        self._cards      = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ══ القسم العلوي: بيانات التصميم (ثابت) ══
        top = QFrame()
        top.setStyleSheet(f"""
            QFrame {{
                background: {_BLUE_LIGHT};
                border-bottom: 1px solid {_BLUE_MID};
            }}
        """)
        top_lay = QVBoxLayout(top)
        top_lay.setContentsMargins(16, 12, 16, 12)
        top_lay.setSpacing(10)

        self.lbl_mode = QLabel("─── تصميم جديد ───")
        self.lbl_mode.setStyleSheet(
            f"font-weight: bold; font-size: 13px; color: {_BLUE}; "
            "background: transparent; border: none;"
        )

        # صف البيانات الأساسية
        info_row = QHBoxLayout()

        lbl_n = QLabel("الاسم:")
        lbl_n.setStyleSheet("background: transparent; border: none; font-weight: bold;")
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم التصميم...")
        self.inp_name.setMinimumHeight(32)

        lbl_c = QLabel("التصنيف:")
        lbl_c.setStyleSheet("background: transparent; border: none; font-weight: bold;")
        self.cmb_category = QComboBox()
        self.cmb_category.setMinimumHeight(32)
        self.cmb_category.setMinimumWidth(150)

        lbl_no = QLabel("ملاحظات:")
        lbl_no.setStyleSheet("background: transparent; border: none; font-weight: bold;")
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات...")
        self.inp_notes.setMinimumHeight(32)

        info_row.addWidget(lbl_n)
        info_row.addWidget(self.inp_name, stretch=2)
        info_row.addWidget(lbl_c)
        info_row.addWidget(self.cmb_category)
        info_row.addWidget(lbl_no)
        info_row.addWidget(self.inp_notes, stretch=1)

        # أزرار الحفظ
        self.btn_save   = QPushButton("💾  حفظ التصميم")
        self.btn_cancel = QPushButton("✖  إلغاء")
        self.btn_save.setMinimumHeight(32)
        self.btn_cancel.setMinimumHeight(32)
        self.btn_save.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE}; color: white; border: none;
                border-radius: 6px; padding: 4px 16px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #0d47a1; }}
        """)
        self.btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: white; color: {_BLUE};
                border: 1.5px solid {_BLUE_MID}; border-radius: 6px; padding: 4px 12px;
            }}
            QPushButton:hover {{ background: white; }}
        """)
        self.btn_cancel.setVisible(False)
        self.btn_save.clicked.connect(self._save)
        self.btn_cancel.clicked.connect(self.reset)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addStretch()

        top_lay.addWidget(self.lbl_mode)
        top_lay.addLayout(info_row)
        top_lay.addLayout(btn_row)
        root.addWidget(top)

        # ══ شريط المقاسات ══
        sizes_hdr = QFrame()
        sizes_hdr.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        sh_lay = QHBoxLayout(sizes_hdr)
        sh_lay.setContentsMargins(16, 8, 16, 8)

        lbl_sz = QLabel("📐  مقاسات التصميم")
        lbl_sz.setStyleSheet(
            f"font-weight: bold; font-size: 12px; color: {_BLUE}; "
            "background: transparent; border: none;"
        )

        self.btn_add_size = QPushButton("➕  إضافة مقاس")
        self.btn_add_size.setMinimumHeight(30)
        self.btn_add_size.setEnabled(False)
        self.btn_add_size.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE}; color: white; border: none;
                border-radius: 6px; font-weight: bold; font-size: 11px;
                padding: 4px 12px;
            }}
            QPushButton:hover {{ background: #0d47a1; }}
            QPushButton:disabled {{ background: #b0bec5; }}
        """)
        self.btn_add_size.clicked.connect(self._add_size)

        self.lbl_sizes_count = QLabel("")
        self.lbl_sizes_count.setStyleSheet(
            f"color: {_TEXT_MUTED}; font-size: 10px; background: transparent; border: none;"
        )

        sh_lay.addWidget(lbl_sz)
        sh_lay.addStretch()
        sh_lay.addWidget(self.lbl_sizes_count)
        sh_lay.addWidget(self.btn_add_size)
        root.addWidget(sizes_hdr)

        # ══ منطقة البطاقات (scroll) ══
        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet(f"background: {_GRAY_BG};")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setSpacing(8)
        self._cards_layout.setContentsMargins(12, 12, 12, 12)
        self._cards_layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self._cards_widget)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {_GRAY_BG}; }}
            QScrollBar:vertical {{
                background: #f0f0f0; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: #c5cae9; border-radius: 3px; min-height: 24px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        root.addWidget(scroll, stretch=1)

        # ── حالة فارغة ──
        self._empty_frame = QFrame()
        self._empty_frame.setStyleSheet(f"background: {_GRAY_BG}; border: none;")
        ef_lay = QVBoxLayout(self._empty_frame)
        ef_lay.setAlignment(Qt.AlignCenter)
        ef_icon = QLabel("🎨")
        ef_icon.setAlignment(Qt.AlignCenter)
        ef_icon.setStyleSheet("font-size: 40px; background: transparent;")
        ef_msg = QLabel("اختر تصميماً من القائمة\nأو أنشئ تصميماً جديداً")
        ef_msg.setAlignment(Qt.AlignCenter)
        ef_msg.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 12px; background: transparent;")
        ef_lay.addWidget(ef_icon)
        ef_lay.addWidget(ef_msg)
        root.addWidget(self._empty_frame)

        scroll.setVisible(False)
        sizes_hdr.setVisible(False)
        self._sizes_hdr = sizes_hdr
        self._scroll    = scroll

        self._reload_categories()

    # ── تحميل ──

    def _reload_categories(self):
        prev = self.cmb_category.currentData()
        self.cmb_category.blockSignals(True)
        self.cmb_category.clear()
        self.cmb_category.addItem("— بدون تصنيف —", None)
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)
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
        self.lbl_mode.setText(f"✏️  تعديل: {d['name']}")
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
        self.lbl_mode.setText("─── تصميم جديد ───")
        self.btn_cancel.setVisible(False)
        self.btn_add_size.setEnabled(False)
        self._clear_cards()
        self._empty_frame.setVisible(True)
        self._sizes_hdr.setVisible(False)
        self._scroll.setVisible(False)
        self.cleared.emit()

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
        sizes = fetch_design_sizes(self.conn, self._design_id)
        for s in sizes:
            self._add_card(s)
        cnt = len(sizes)
        self.lbl_sizes_count.setText(f"{cnt} مقاس" if cnt else "لا توجد مقاسات بعد")

    def _add_card(self, size_data):
        card = _SizeCard(self.conn, size_data)
        card.edit_requested.connect(self._edit_size)
        card.delete_requested.connect(self._delete_size)
        card.path_changed.connect(self._refresh_cards)
        self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)
        self._cards.append(card)

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
            self.lbl_mode.setText(f"✏️  تعديل: {name}")
        else:
            self._design_id = insert_design(self.conn, name, cat_id, notes)
            self.lbl_mode.setText(f"✏️  تعديل: {name}")
            self.btn_cancel.setVisible(True)
            self.btn_add_size.setEnabled(True)
            self._empty_frame.setVisible(False)
            self._sizes_hdr.setVisible(True)
            self._scroll.setVisible(True)
            self._refresh_cards()

        self.saved.emit()

