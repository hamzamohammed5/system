"""
ui/tabs/design/designs/_design_detail_panel.py  — v3
=====================================================
لوحة تفاصيل التصميم — يمين تبويب التصميمات.

التحسينات:
  - Header أنظف مع معلومات أوضح
  - Form fields بـ labels خارجية
  - قسم المقاسات مع counter بارز
  - Empty state أجمل لكل قسم
  - Palette موحدة مع باقي الملفات
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QComboBox, QMessageBox, QFrame,
    QScrollArea, QDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

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

# ── Palette ──────────────────────────────────────────────
_BG          = "#FFFFFF"
_BG_SURFACE  = "#F8F9FB"
_BG_HEADER   = "#FAFBFC"
_BORDER      = "#E5E9F0"
_BORDER_MED  = "#CDD3E0"
_TEXT_PRI    = "#1A2035"
_TEXT_SEC    = "#5A6680"
_TEXT_MUT    = "#9BA5BE"

_ACCENT      = "#4F6EF7"
_ACCENT_LT   = "#EEF2FF"
_ACCENT_BDR  = "#C7D2FE"
_ACCENT_DARK = "#3D5BEF"

_SUCCESS     = "#16A34A"
_SUCCESS_LT  = "#F0FDF4"
_SUCCESS_BDR = "#BBF7D0"

_DANGER      = "#DC2626"
_DANGER_LT   = "#FEF2F2"

_RADIUS      = "10px"
_RADIUS_SM   = "6px"
_RADIUS_XS   = "4px"


def _input_ss():
    return f"""
        QLineEdit {{
            background: {_BG_SURFACE};
            border: 1px solid {_BORDER_MED};
            border-radius: {_RADIUS_SM};
            padding: 0 12px;
            font-size: 12px;
            color: {_TEXT_PRI};
            min-height: 34px;
        }}
        QLineEdit:focus {{
            border-color: {_ACCENT};
            background: {_BG};
        }}
    """


def _combo_ss():
    return f"""
        QComboBox {{
            background: {_BG_SURFACE};
            border: 1px solid {_BORDER_MED};
            border-radius: {_RADIUS_SM};
            padding: 0 10px;
            font-size: 12px;
            color: {_TEXT_PRI};
            min-height: 34px;
        }}
        QComboBox:focus {{ border-color: {_ACCENT}; }}
        QComboBox::drop-down {{ border: none; width: 20px; }}
    """


def _btn_ss(bg, fg, bdr, hover_bg, height=34):
    return (
        f"QPushButton{{"
        f"  background:{bg}; color:{fg};"
        f"  border:1px solid {bdr}; border-radius:{_RADIUS_SM};"
        f"  padding:0 14px; font-size:12px; min-height:{height}px; font-weight:500;"
        f"}}"
        f"QPushButton:hover{{background:{hover_bg};}}"
        f"QPushButton:pressed{{opacity:0.85;}}"
    )


def _field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"font-size:10px; color:{_TEXT_MUT}; font-weight:600;"
        "background:transparent; letter-spacing:0.3px;"
    )
    return lbl


class _DesignDetailPanel(QWidget):
    """
    لوحة تفاصيل التصميم على اليمين.

    Signals:
      saved()   — بعد حفظ التصميم
      cleared() — بعد مسح الفورم
    """

    saved   = pyqtSignal()
    cleared = pyqtSignal()

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self._design_id  = None
        self._set_filter = None
        self._size_cards = []
        self._build()
        self._reload_categories()

    def connect_categories_panel(self, cats_panel):
        cats_panel.category_changed.connect(lambda _: self._reload_categories())

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── Header: عنوان + فورم ──────────────────
        hdr = QFrame()
        hdr.setStyleSheet(f"""
            QFrame {{
                background: {_BG};
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        hdr_lay = QVBoxLayout(hdr)
        hdr_lay.setContentsMargins(18, 14, 18, 16)
        hdr_lay.setSpacing(14)

        # ── صف العنوان + الأزرار ──
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self._lbl_title = QLabel("تصميم جديد")
        font_t = QFont()
        font_t.setPointSize(13)
        font_t.setWeight(QFont.Bold)
        self._lbl_title.setFont(font_t)
        self._lbl_title.setStyleSheet(
            f"color:{_TEXT_PRI}; background:transparent;"
        )

        self._lbl_badge = QLabel("جديد")
        self._lbl_badge.setStyleSheet(
            f"background:{_ACCENT_LT}; color:{_ACCENT};"
            f"border:1px solid {_ACCENT_BDR}; border-radius:{_RADIUS_XS};"
            "font-size:10px; font-weight:700; padding:2px 8px;"
        )
        self._lbl_badge.setVisible(False)

        title_row.addWidget(self._lbl_title, stretch=1)
        title_row.addWidget(self._lbl_badge)

        # أزرار الحفظ والجديد
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        self.btn_new = QPushButton("جديد")
        self.btn_new.setMinimumHeight(32)
        self.btn_new.setStyleSheet(
            _btn_ss(_BG_SURFACE, _TEXT_SEC, _BORDER, _BG, 32)
        )
        self.btn_new.clicked.connect(self.reset)

        self.btn_save = QPushButton("حفظ التصميم")
        self.btn_save.setMinimumHeight(32)
        self.btn_save.setStyleSheet(
            _btn_ss(_ACCENT, "#fff", _ACCENT, _ACCENT_DARK, 32)
        )
        self.btn_save.clicked.connect(self._save)

        btn_row.addWidget(self.btn_new)
        btn_row.addWidget(self.btn_save)

        hdr_lay.addLayout(title_row)

        # ── حقول الفورم ──────────────────────────────
        # صف 1: الاسم
        name_col = QVBoxLayout()
        name_col.setSpacing(4)
        name_col.addWidget(_field_label("الاسم"))
        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("اسم التصميم...")
        self.inp_name.setStyleSheet(_input_ss())
        name_col.addWidget(self.inp_name)
        hdr_lay.addLayout(name_col)

        # صف 2: التصنيف + الملاحظات
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        cat_col = QVBoxLayout()
        cat_col.setSpacing(4)
        cat_col.addWidget(_field_label("التصنيف"))
        self.cmb_cat = QComboBox()
        self.cmb_cat.setStyleSheet(_combo_ss())
        self.cmb_cat.setMinimumWidth(160)
        cat_col.addWidget(self.cmb_cat)

        notes_col = QVBoxLayout()
        notes_col.setSpacing(4)
        notes_col.addWidget(_field_label("ملاحظات"))
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("اختياري...")
        self.inp_notes.setStyleSheet(_input_ss())
        notes_col.addWidget(self.inp_notes)

        row2.addLayout(cat_col, stretch=1)
        row2.addLayout(notes_col, stretch=2)
        hdr_lay.addLayout(row2)

        hdr_lay.addLayout(btn_row)
        root.addWidget(hdr)

        # ── قسم المقاسات ────────────────────────────
        sizes_hdr = QFrame()
        sizes_hdr.setStyleSheet(f"""
            QFrame {{
                background: {_BG_SURFACE};
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        sh_lay = QHBoxLayout(sizes_hdr)
        sh_lay.setContentsMargins(18, 10, 18, 10)
        sh_lay.setSpacing(8)

        lbl_sizes = QLabel("المقاسات")
        font_s = QFont()
        font_s.setPointSize(11)
        font_s.setWeight(QFont.Medium)
        lbl_sizes.setFont(font_s)
        lbl_sizes.setStyleSheet(
            f"color:{_TEXT_PRI}; background:transparent;"
        )

        self.lbl_sizes_count = QLabel("")
        self.lbl_sizes_count.setStyleSheet(
            f"background:{_ACCENT_LT}; color:{_ACCENT};"
            f"border:1px solid {_ACCENT_BDR}; border-radius:10px;"
            "font-size:10px; font-weight:700; padding:2px 10px;"
        )
        self.lbl_sizes_count.setVisible(False)

        btn_add_size = QPushButton("+ إضافة مقاس")
        btn_add_size.setMinimumHeight(30)
        btn_add_size.setStyleSheet(
            _btn_ss(_SUCCESS_LT, _SUCCESS, _SUCCESS_BDR, "#DCFCE7", 30)
        )
        btn_add_size.clicked.connect(self._add_size)

        sh_lay.addWidget(lbl_sizes)
        sh_lay.addWidget(self.lbl_sizes_count)
        sh_lay.addStretch()
        sh_lay.addWidget(btn_add_size)
        root.addWidget(sizes_hdr)

        # ── Scroll منطقة المقاسات ──────────────────
        self._sizes_scroll = QScrollArea()
        self._sizes_scroll.setWidgetResizable(True)
        self._sizes_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._sizes_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: {_BG_SURFACE}; }}
            QScrollBar:vertical {{
                background: {_BG_SURFACE}; width: 5px; border-radius: 2px;
            }}
            QScrollBar::handle:vertical {{
                background: {_BORDER_MED}; border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        self._sizes_widget = QWidget()
        self._sizes_widget.setStyleSheet(f"background:{_BG_SURFACE};")
        self._sizes_layout = QVBoxLayout(self._sizes_widget)
        self._sizes_layout.setContentsMargins(14, 14, 14, 14)
        self._sizes_layout.setSpacing(10)
        self._sizes_layout.addStretch()

        self._sizes_scroll.setWidget(self._sizes_widget)
        root.addWidget(self._sizes_scroll, stretch=1)

        # ── Empty state للمقاسات ────────────────────
        self._empty_sizes = QFrame()
        self._empty_sizes.setStyleSheet("background:transparent; border:none;")
        es_lay = QVBoxLayout(self._empty_sizes)
        es_lay.setAlignment(Qt.AlignCenter)
        es_lay.setSpacing(6)

        es_icon = QLabel("📐")
        es_icon.setAlignment(Qt.AlignCenter)
        es_icon.setStyleSheet("font-size:28px; background:transparent;")

        es_lbl = QLabel("لا توجد مقاسات بعد")
        es_lbl.setAlignment(Qt.AlignCenter)
        es_lbl.setStyleSheet(
            f"font-size:12px; color:{_TEXT_SEC}; font-weight:500; background:transparent;"
        )
        es_sub = QLabel("اضغط «+ إضافة مقاس» لإضافة أول مقاس")
        es_sub.setAlignment(Qt.AlignCenter)
        es_sub.setStyleSheet(
            f"font-size:11px; color:{_TEXT_MUT}; background:transparent;"
        )

        es_lay.addWidget(es_icon)
        es_lay.addWidget(es_lbl)
        es_lay.addWidget(es_sub)

        self._sizes_layout.insertWidget(0, self._empty_sizes)

    # ══════════════════════════════════════════════════════
    # API خارجي
    # ══════════════════════════════════════════════════════

    def load_design(self, design_id: int):
        self._design_id = design_id
        design = fetch_design(self.conn, design_id)
        if not design:
            return

        self.inp_name.setText(design["name"])
        self.inp_notes.setText(design["notes"] or "")
        self._lbl_title.setText(design["name"])
        self._lbl_badge.setText("محفوظ")
        self._lbl_badge.setVisible(True)

        cat_id = design["item_category_id"]
        for i in range(self.cmb_cat.count()):
            if self.cmb_cat.itemData(i) == cat_id:
                self.cmb_cat.setCurrentIndex(i)
                break

        self._load_sizes()

    def reset(self):
        self._design_id = None
        self.inp_name.clear()
        self.inp_notes.clear()
        self.cmb_cat.setCurrentIndex(0)
        self._lbl_title.setText("تصميم جديد")
        self._lbl_badge.setVisible(False)
        self._clear_size_cards()
        self.cleared.emit()

    def filter_by_set(self, set_id):
        self._set_filter = set_id
        if self._design_id:
            self._load_sizes()

    def _reload_categories(self):
        prev = self.cmb_cat.currentData()
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.clear()
        self.cmb_cat.addItem("— بدون تصنيف —", None)

        rows = fetch_all_item_categories(self.conn)
        tree = build_item_category_tree(rows)
        self._add_cat_nodes(tree, 0)

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
            self.inp_name.setFocus()
            self.inp_name.setStyleSheet(
                _input_ss() + f"QLineEdit{{border-color:{_DANGER};}}"
            )
            QMessageBox.warning(self, "تنبيه", "أدخل اسم التصميم")
            return

        self.inp_name.setStyleSheet(_input_ss())
        cat_id = self.cmb_cat.currentData()
        notes  = self.inp_notes.text().strip()

        if self._design_id:
            update_design(self.conn, self._design_id, name, cat_id, notes)
        else:
            self._design_id = insert_design(self.conn, name, cat_id, notes)

        self._lbl_title.setText(name)
        self._lbl_badge.setText("محفوظ")
        self._lbl_badge.setVisible(True)
        self.saved.emit()

    # ══════════════════════════════════════════════════════
    # إدارة المقاسات
    # ══════════════════════════════════════════════════════

    def _load_sizes(self):
        self._clear_size_cards()
        if not self._design_id:
            return

        sizes = fetch_design_sizes(self.conn, self._design_id)

        if self._set_filter is not None:
            sizes = [s for s in sizes if s["set_id"] == self._set_filter]

        count = len(sizes)
        self._empty_sizes.setVisible(count == 0)

        if count > 0:
            self.lbl_sizes_count.setText(str(count))
            self.lbl_sizes_count.setVisible(True)
        else:
            self.lbl_sizes_count.setVisible(False)

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
        for card in self._size_cards:
            self._sizes_layout.removeWidget(card)
            card.deleteLater()
        self._size_cards = []
        self._empty_sizes.setVisible(True)
        self.lbl_sizes_count.setVisible(False)

    def _add_size(self):
        if not self._design_id:
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
        sizes = fetch_design_sizes(self.conn, self._design_id)
        size_data = next((s for s in sizes if s["id"] == size_id), None)
        if not size_data:
            return
        dlg = _SizeDialog(self.conn, self._design_id,
                          size_data=size_data, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            self._load_sizes()

    def _delete_size(self, size_id: int):
        if QMessageBox.question(
            self, "تأكيد الحذف",
            "حذف هذا المقاس من التصميم؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_design_size(self.conn, size_id)
            self._load_sizes()