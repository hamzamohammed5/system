"""
ui/tabs/design/designs/_design_detail_panel.py
===============================================
لوحة تفاصيل التصميم — يمين تبويب التصميمات.

تعرض:
  - فورم إضافة / تعديل التصميم (الاسم، التصنيف، الملاحظات)
  - قائمة المقاسات المرتبطة (_SizeCard لكل مقاس)
  - إضافة مقاسات جديدة عبر _SizeDialog
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QComboBox, QMessageBox, QFrame,
    QScrollArea, QDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.designs.designs_repo import (
    fetch_design, insert_design, update_design,
)
from db.designs.designs_sizes_repo import (
    fetch_design_sizes, delete_design_size,
)
from db.designs.design_item_categories_repo import (
    fetch_all_item_categories,
    build_item_category_tree,
)
from ._size_card   import _SizeCard
from ._size_dialog import _SizeDialog

# ── ألوان ──
_BG          = "#ffffff"
_BG_SUBTLE   = "#f8fafc"
_BORDER      = "#e2e8f0"
_BORDER_MED  = "#cbd5e1"
_TEXT        = "#0f172a"
_TEXT_MED    = "#475569"
_TEXT_MUTED  = "#94a3b8"
_BLUE        = "#3b82f6"
_BLUE_LT     = "#eff6ff"
_BLUE_MED    = "#bfdbfe"
_GREEN       = "#16a34a"
_GREEN_LT    = "#f0fdf4"
_PURPLE      = "#7c3aed"
_PURPLE_LT   = "#f5f3ff"
_RED         = "#dc2626"
_RED_LT      = "#fef2f2"


def _btn_ss(bg, fg, border, hover_bg):
    return (
        f"QPushButton {{ background:{bg}; color:{fg}; border:1px solid {border};"
        f" border-radius:8px; padding:5px 14px; font-size:12px; }}"
        f"QPushButton:hover {{ background:{hover_bg}; }}"
    )


class _DesignDetailPanel(QWidget):
    """
    لوحة تفاصيل التصميم على اليمين.

    Signals:
      saved()   — بعد حفظ التصميم (إضافة أو تعديل)
      cleared() — بعد مسح الفورم (new design)
    """

    saved   = pyqtSignal()
    cleared = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._design_id  = None
        self._set_filter = None   # فلتر مجموعة المقاسات (من _DesignsTable)
        self._size_cards = []
        self._build()
        self._reload_categories()

    def connect_categories_panel(self, cats_panel):
        """
        يربط الـ panel بـ signal من DesignsCategoriesPanel
        حتى يتحدث الـ combo لما تتغير التصنيفات.
        يُستدعى من designs_tab.py بعد إنشاء الـ widgets.
        """
        cats_panel.category_changed.connect(lambda _: self._reload_categories())

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── رأس ──
        hdr = QFrame()
        hdr.setStyleSheet(f"""
            QFrame {{
                background: {_BG};
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        hdr_lay = QVBoxLayout(hdr)
        hdr_lay.setContentsMargins(16, 14, 16, 14)
        hdr_lay.setSpacing(10)

        # عنوان + أزرار رئيسية
        title_row = QHBoxLayout()
        self._lbl_title = QLabel("تصميم جديد")
        self._lbl_title.setStyleSheet(
            f"font-size:15px; font-weight:700; color:{_TEXT}; background:transparent;"
        )
        btn_save  = QPushButton("💾  حفظ")
        btn_save.setMinimumHeight(34)
        btn_save.setStyleSheet(_btn_ss(_BLUE, "#fff", _BLUE, "#2563eb"))
        btn_save.clicked.connect(self._save)

        btn_new = QPushButton("✨  جديد")
        btn_new.setMinimumHeight(34)
        btn_new.setStyleSheet(_btn_ss(_BG_SUBTLE, _TEXT_MED, _BORDER_MED, _BG))
        btn_new.clicked.connect(self.reset)

        title_row.addWidget(self._lbl_title, stretch=1)
        title_row.addWidget(btn_save)
        title_row.addWidget(btn_new)
        hdr_lay.addLayout(title_row)

        # ── حقول الفورم ──
        form_row = QHBoxLayout()
        form_row.setSpacing(10)

        # الاسم
        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        lbl_name = QLabel("الاسم")
        lbl_name.setStyleSheet(f"font-size:11px; color:{_TEXT_MUTED}; background:transparent;")
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم التصميم...")
        self.inp_name.setMinimumHeight(34)
        self.inp_name.setStyleSheet(f"""
            QLineEdit {{
                background:{_BG_SUBTLE}; border:1px solid {_BORDER_MED};
                border-radius:8px; padding:0 12px;
                font-size:13px; color:{_TEXT};
            }}
            QLineEdit:focus {{ border-color:{_BLUE}; background:{_BG}; }}
        """)
        name_col.addWidget(lbl_name)
        name_col.addWidget(self.inp_name)

        # التصنيف
        cat_col = QVBoxLayout()
        cat_col.setSpacing(4)
        lbl_cat = QLabel("التصنيف")
        lbl_cat.setStyleSheet(f"font-size:11px; color:{_TEXT_MUTED}; background:transparent;")
        self.cmb_cat = QComboBox()
        self.cmb_cat.setMinimumHeight(34)
        self.cmb_cat.setMinimumWidth(180)
        self.cmb_cat.setStyleSheet(f"""
            QComboBox {{
                background:{_BG_SUBTLE}; border:1px solid {_BORDER_MED};
                border-radius:8px; padding:0 10px;
                font-size:12px; color:{_TEXT};
            }}
            QComboBox:focus {{ border-color:{_BLUE}; }}
            QComboBox::drop-down {{ border:none; width:20px; }}
        """)
        cat_col.addWidget(lbl_cat)
        cat_col.addWidget(self.cmb_cat)

        # الملاحظات
        notes_col = QVBoxLayout()
        notes_col.setSpacing(4)
        lbl_notes = QLabel("ملاحظات")
        lbl_notes.setStyleSheet(f"font-size:11px; color:{_TEXT_MUTED}; background:transparent;")
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات اختيارية...")
        self.inp_notes.setMinimumHeight(34)
        self.inp_notes.setStyleSheet(f"""
            QLineEdit {{
                background:{_BG_SUBTLE}; border:1px solid {_BORDER_MED};
                border-radius:8px; padding:0 12px;
                font-size:12px; color:{_TEXT};
            }}
            QLineEdit:focus {{ border-color:{_BLUE}; background:{_BG}; }}
        """)
        notes_col.addWidget(lbl_notes)
        notes_col.addWidget(self.inp_notes)

        form_row.addLayout(name_col, stretch=2)
        form_row.addLayout(cat_col, stretch=1)
        form_row.addLayout(notes_col, stretch=2)
        hdr_lay.addLayout(form_row)

        root.addWidget(hdr)

        # ── قسم المقاسات ──
        sizes_hdr = QFrame()
        sizes_hdr.setStyleSheet(f"""
            QFrame {{
                background: {_BG_SUBTLE};
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        sh_lay = QHBoxLayout(sizes_hdr)
        sh_lay.setContentsMargins(16, 10, 16, 10)

        lbl_sizes = QLabel("📐  المقاسات")
        lbl_sizes.setStyleSheet(
            f"font-size:13px; font-weight:600; color:{_TEXT}; background:transparent;"
        )

        self.lbl_sizes_count = QLabel("")
        self.lbl_sizes_count.setStyleSheet(
            f"font-size:11px; color:{_TEXT_MUTED}; background:transparent;"
        )

        btn_add_size = QPushButton("➕  إضافة مقاس")
        btn_add_size.setMinimumHeight(30)
        btn_add_size.setStyleSheet(_btn_ss(_GREEN_LT, _GREEN, "#86efac", "#dcfce7"))
        btn_add_size.clicked.connect(self._add_size)

        sh_lay.addWidget(lbl_sizes)
        sh_lay.addWidget(self.lbl_sizes_count)
        sh_lay.addStretch()
        sh_lay.addWidget(btn_add_size)
        root.addWidget(sizes_hdr)

        # ── منطقة المقاسات (scroll) ──
        self._sizes_scroll = QScrollArea()
        self._sizes_scroll.setWidgetResizable(True)
        self._sizes_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._sizes_scroll.setStyleSheet(f"""
            QScrollArea {{ border:none; background:{_BG_SUBTLE}; }}
            QScrollBar:vertical {{
                background:#f0f0f0; width:6px; border-radius:3px;
            }}
            QScrollBar::handle:vertical {{
                background:#c5cae9; border-radius:3px; min-height:20px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height:0; }}
        """)

        self._sizes_widget = QWidget()
        self._sizes_widget.setStyleSheet(f"background:{_BG_SUBTLE};")
        self._sizes_layout = QVBoxLayout(self._sizes_widget)
        self._sizes_layout.setContentsMargins(12, 12, 12, 12)
        self._sizes_layout.setSpacing(10)
        self._sizes_layout.addStretch()

        self._sizes_scroll.setWidget(self._sizes_widget)
        root.addWidget(self._sizes_scroll, stretch=1)

        # ── حالة فارغة ──
        self._empty_sizes = QLabel("لا توجد مقاسات — اضغط «إضافة مقاس»")
        self._empty_sizes.setAlignment(Qt.AlignCenter)
        self._empty_sizes.setStyleSheet(
            f"color:{_TEXT_MUTED}; font-size:12px; padding:20px; background:transparent;"
        )
        self._sizes_layout.insertWidget(0, self._empty_sizes)

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def load_design(self, design_id: int):
        """تحميل تصميم موجود."""
        self._design_id = design_id
        design = fetch_design(self.conn, design_id)
        if not design:
            return

        self.inp_name.setText(design["name"])
        self.inp_notes.setText(design["notes"] or "")
        self._lbl_title.setText(design["name"])

        # اختيار التصنيف
        cat_id = design["item_category_id"]
        for i in range(self.cmb_cat.count()):
            if self.cmb_cat.itemData(i) == cat_id:
                self.cmb_cat.setCurrentIndex(i)
                break

        self._load_sizes()

    def reset(self):
        """مسح الفورم لتصميم جديد."""
        self._design_id = None
        self.inp_name.clear()
        self.inp_notes.clear()
        self.cmb_cat.setCurrentIndex(0)
        self._lbl_title.setText("تصميم جديد")
        self._clear_size_cards()
        self.cleared.emit()

    def filter_by_set(self, set_id):
        """فلترة المقاسات حسب مجموعة مقاسات محددة (من _DesignsTable)."""
        self._set_filter = set_id
        if self._design_id:
            self._load_sizes()

    def _reload_categories(self):
        """إعادة تحميل التصنيفات في الـ combo."""
        prev = self.cmb_cat.currentData()
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.clear()
        self.cmb_cat.addItem("— بدون تصنيف —", None)

        rows = fetch_all_item_categories(self.conn)
        tree = build_item_category_tree(rows)
        self._add_cat_nodes(tree, 0)

        # استعادة الاختيار السابق
        for i in range(self.cmb_cat.count()):
            if self.cmb_cat.itemData(i) == prev:
                self.cmb_cat.setCurrentIndex(i)
                break
        self.cmb_cat.blockSignals(False)

    def _add_cat_nodes(self, nodes, depth):
        indent = "    " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_cat.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_cat_nodes(node["children"], depth + 1)

    # ══════════════════════════════════════════════════════
    # حفظ التصميم
    # ══════════════════════════════════════════════════════

    def _save(self):
        name = self.inp_name.text().strip()
        if not name:
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصميم")
            return

        cat_id = self.cmb_cat.currentData()
        notes  = self.inp_notes.text().strip()

        if self._design_id:
            update_design(self.conn, self._design_id, name, cat_id, notes)
        else:
            self._design_id = insert_design(self.conn, name, cat_id, notes)

        self._lbl_title.setText(name)
        self.saved.emit()

    # ══════════════════════════════════════════════════════
    # إدارة المقاسات
    # ══════════════════════════════════════════════════════

    def _load_sizes(self):
        """تحميل مقاسات التصميم الحالي."""
        self._clear_size_cards()
        if not self._design_id:
            return

        sizes = fetch_design_sizes(self.conn, self._design_id)

        # فلترة حسب مجموعة المقاسات لو محدد
        if self._set_filter is not None:
            sizes = [s for s in sizes if s["set_id"] == self._set_filter]

        self._empty_sizes.setVisible(not sizes)
        self.lbl_sizes_count.setText(f"({len(sizes)})" if sizes else "")

        for size_data in sizes:
            card = _SizeCard(self.conn, size_data)
            card.edit_requested.connect(self._edit_size)
            card.delete_requested.connect(self._delete_size)
            card.path_changed.connect(lambda: self._load_sizes())
            self._sizes_layout.insertWidget(
                self._sizes_layout.count() - 1, card
            )
            self._size_cards.append(card)

    def _clear_size_cards(self):
        """حذف كل بطاقات المقاسات من الواجهة."""
        for card in self._size_cards:
            self._sizes_layout.removeWidget(card)
            card.deleteLater()
        self._size_cards = []
        self._empty_sizes.setVisible(True)
        self.lbl_sizes_count.setText("")

    def _add_size(self):
        """إضافة مقاس جديد."""
        if not self._design_id:
            # احفظ التصميم أولاً لو جديد
            name = self.inp_name.text().strip()
            if not name:
                QMessageBox.warning(self, "تنبيه", "احفظ التصميم أولاً قبل إضافة مقاسات")
                return
            self._save()
            if not self._design_id:
                return

        dlg = _SizeDialog(self.conn, self._design_id, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_sizes()

    def _edit_size(self, size_id: int):
        """تعديل مقاس موجود."""
        sizes = fetch_design_sizes(self.conn, self._design_id)
        size_data = next((s for s in sizes if s["id"] == size_id), None)
        if not size_data:
            return
        dlg = _SizeDialog(self.conn, self._design_id,
                          size_data=size_data, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_sizes()

    def _delete_size(self, size_id: int):
        """حذف مقاس."""
        if QMessageBox.question(
            self, "تأكيد الحذف",
            "حذف هذا المقاس من التصميم؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_design_size(self.conn, size_id)
            self._load_sizes()