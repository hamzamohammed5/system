"""
ui/tabs/design/dimension_sets/_values_panel.py
=====================================
لوحة إدخال قيم المقاسات — تصميم جديد:

  يسار : قايمة مجموعات المقاسات (بطاقات واضحة)
  يمين : جدول instances + قيمها لما تختار مجموعة
  Popup: نافذة تعديل/إضافة instance
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QLineEdit, QDoubleSpinBox,
    QMessageBox, QScrollArea, QFrame, QListWidget,
    QListWidgetItem, QInputDialog, QDialog, QDialogButtonBox,
    QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QAbstractItemView, QSizePolicy, QToolButton, QGridLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QColor, QIcon

from db.designs.dimension_sets_repo import (
    fetch_all_dimension_sets,
    fetch_fields_for_set,
    fetch_instances_for_set, fetch_instance,
    insert_instance, update_instance, delete_instance, duplicate_instance,
    fetch_instance_values, save_instance_values, calc_instance_cross_auto,
    fetch_field_dep,
    fetch_all_design_categories, build_category_tree,
)


# ──────────────────────────────────────────────────────────
# ثوابت الستايل
# ──────────────────────────────────────────────────────────

_BLUE       = "#1565c0"
_BLUE_LIGHT = "#e8f0fe"
_BLUE_MID   = "#bbdefb"
_GREEN      = "#2e7d32"
_GREEN_LT   = "#e8f5e9"
_RED        = "#c62828"
_RED_LT     = "#fdecea"
_ORANGE_LT  = "#fff3e0"
_ORANGE     = "#e65100"
_GRAY_BG    = "#f8f9fc"
_BORDER     = "#e0e7f3"
_TEXT       = "#1a2340"
_TEXT_MUTED = "#7a869a"

_CARD_SELECTED = f"""
    QFrame {{
        background: {_BLUE_LIGHT};
        border: 2px solid {_BLUE};
        border-radius: 10px;
    }}
"""
_CARD_NORMAL = f"""
    QFrame {{
        background: white;
        border: 1.5px solid {_BORDER};
        border-radius: 10px;
    }}
    QFrame:hover {{
        border-color: {_BLUE_MID};
        background: #f5f8ff;
    }}
"""

_BTN_PRIMARY = f"""
    QPushButton {{
        background: {_BLUE};
        color: white;
        border: none;
        border-radius: 7px;
        padding: 6px 18px;
        font-weight: bold;
        font-size: 12px;
    }}
    QPushButton:hover  {{ background: #0d47a1; }}
    QPushButton:disabled {{ background: #b0bec5; }}
"""
_BTN_SUCCESS = f"""
    QPushButton {{
        background: {_GREEN};
        color: white;
        border: none;
        border-radius: 7px;
        padding: 6px 14px;
        font-weight: bold;
        font-size: 12px;
    }}
    QPushButton:hover {{ background: #1b5e20; }}
    QPushButton:disabled {{ background: #b0bec5; }}
"""
_BTN_GHOST = f"""
    QPushButton {{
        background: white;
        color: {_BLUE};
        border: 1.5px solid {_BLUE_MID};
        border-radius: 7px;
        padding: 5px 14px;
        font-size: 12px;
    }}
    QPushButton:hover {{ background: {_BLUE_LIGHT}; }}
"""
_BTN_DANGER = f"""
    QPushButton {{
        background: {_RED_LT};
        color: {_RED};
        border: 1.5px solid #ef9a9a;
        border-radius: 7px;
        padding: 5px 14px;
        font-size: 12px;
    }}
    QPushButton:hover {{ background: #ffcdd2; }}
"""
_BTN_ICON = f"""
    QToolButton {{
        background: transparent;
        border: none;
        color: {_TEXT_MUTED};
        font-size: 14px;
        border-radius: 5px;
        padding: 3px 6px;
    }}
    QToolButton:hover {{ background: {_BLUE_LIGHT}; color: {_BLUE}; }}
"""


def _row_val(row, key, default=None):
    try:
        v = row[key]
        return v if v is not None else default
    except (IndexError, KeyError):
        return default


# ══════════════════════════════════════════════════════════
# Popup — تعديل / إضافة Instance
# ══════════════════════════════════════════════════════════

class _InstancePopup(QDialog):
    """
    نافذة popup لإدخال / تعديل قيم instance واحد.
    """

    saved = pyqtSignal(int)   # instance_id

    def __init__(self, conn, set_id: int,
                 instance_id: int = None, parent=None):
        super().__init__(parent)
        self.conn        = conn
        self.set_id      = set_id
        self.instance_id = instance_id
        self._spins      = {}   # field_id → QDoubleSpinBox

        title = "تعديل مجموعة قيم" if instance_id else "إضافة مجموعة قيم جديدة"
        self.setWindowTitle(title)
        self.setMinimumWidth(520)
        self.setMinimumHeight(400)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background: {_GRAY_BG};
            }}
            QLabel {{
                color: {_TEXT};
            }}
        """)
        self._build()
        if instance_id:
            self._load_values()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        # ── رأس ──
        hdr = QLabel(
            "✏️  تعديل القيم" if self.instance_id
            else "➕  إضافة مجموعة قيم جديدة"
        )
        hdr.setStyleSheet(f"""
            font-size: 14px;
            font-weight: bold;
            color: {_BLUE};
            background: {_BLUE_LIGHT};
            border-radius: 8px;
            padding: 8px 14px;
        """)
        root.addWidget(hdr)

        # ── اسم المجموعة ──
        name_row = QHBoxLayout()
        lbl_name = QLabel("الاسم:")
        lbl_name.setFixedWidth(90)
        lbl_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_name.setStyleSheet("font-weight: bold;")

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText("مثال: A4، مقاس L، النموذج الأول...")
        self.inp_name.setMinimumHeight(36)
        self.inp_name.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {_BORDER};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: 13px;
                background: white;
            }}
            QLineEdit:focus {{ border-color: {_BLUE}; }}
        """)

        if self.instance_id:
            inst = fetch_instance(self.conn, self.instance_id)
            if inst:
                self.inp_name.setText(inst["name"])

        name_row.addWidget(lbl_name)
        name_row.addWidget(self.inp_name)
        root.addLayout(name_row)

        # ── فاصل ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {_BORDER};")
        root.addWidget(sep)

        # ── حقول الإدخال ──
        fields_lbl = QLabel("القيم:")
        fields_lbl.setStyleSheet(f"font-weight: bold; color: {_TEXT_MUTED}; font-size: 11px;")
        root.addWidget(fields_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: #f0f0f0; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: #bdbdbd; border-radius: 3px; min-height: 24px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        fields_w = QWidget()
        fields_w.setStyleSheet("background: transparent;")
        grid = QGridLayout(fields_w)
        grid.setSpacing(10)
        grid.setContentsMargins(0, 4, 0, 4)

        fields = fetch_fields_for_set(self.conn, self.set_id)
        num_fields = [f for f in fields if f["field_type"] == "number"]

        for i, f in enumerate(num_fields):
            lbl = QLabel(f["label"])
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setStyleSheet(f"font-weight: 500; color: {_TEXT};")
            lbl.setFixedWidth(130)

            spin = QDoubleSpinBox()
            spin.setRange(-99999, 99999)
            spin.setDecimals(4)
            spin.setMinimumHeight(36)
            spin.setStyleSheet(f"""
                QDoubleSpinBox {{
                    border: 1.5px solid {_BORDER};
                    border-radius: 8px;
                    padding: 4px 10px;
                    font-size: 13px;
                    background: white;
                }}
                QDoubleSpinBox:focus {{ border-color: {_BLUE}; }}
            """)

            unit_lbl = QLabel(f["unit"] or "")
            unit_lbl.setFixedWidth(38)
            unit_lbl.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 11px;")
            unit_lbl.setAlignment(Qt.AlignVCenter)

            # زر الحساب التلقائي لو في اعتمادية
            has_dep = bool(_row_val(f, "source_field_id"))
            if has_dep:
                btn_auto = QToolButton()
                btn_auto.setText("⟳")
                btn_auto.setFixedSize(32, 32)
                btn_auto.setStyleSheet(_BTN_ICON)
                btn_auto.setToolTip("حساب تلقائي من المصدر")
                fid = f["id"]
                btn_auto.clicked.connect(
                    lambda _, fid_=fid, sp_=spin: self._calc_one(fid_, sp_)
                )
                grid.addWidget(lbl,      i, 0)
                grid.addWidget(spin,     i, 1)
                grid.addWidget(unit_lbl, i, 2)
                grid.addWidget(btn_auto, i, 3)
            else:
                grid.addWidget(lbl,      i, 0)
                grid.addWidget(spin,     i, 1)
                grid.addWidget(unit_lbl, i, 2)

            self._spins[f["id"]] = spin

        if not num_fields:
            empty = QLabel("هذه المجموعة ليس لها حقول رقمية.")
            empty.setStyleSheet(f"color: {_TEXT_MUTED}; padding: 12px;")
            empty.setAlignment(Qt.AlignCenter)
            grid.addWidget(empty, 0, 0, 1, 3)

        scroll.setWidget(fields_w)
        root.addWidget(scroll, stretch=1)

        # ── أزرار الحفظ ──
        btn_row = QHBoxLayout()

        has_auto = any(bool(_row_val(f, "source_field_id"))
                       for f in num_fields)
        if has_auto:
            btn_calc_all = QPushButton("⟳  حساب الكل تلقائياً")
            btn_calc_all.setStyleSheet(_BTN_GHOST)
            btn_calc_all.setMinimumHeight(36)
            btn_calc_all.clicked.connect(self._calc_all_auto)
            btn_row.addWidget(btn_calc_all)

        btn_row.addStretch()

        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setStyleSheet(_BTN_GHOST)
        btn_cancel.setMinimumHeight(36)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾  حفظ")
        btn_save.setStyleSheet(_BTN_PRIMARY)
        btn_save.setMinimumHeight(36)
        btn_save.setMinimumWidth(100)
        btn_save.clicked.connect(self._save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    def _load_values(self):
        saved = fetch_instance_values(self.conn, self.instance_id)
        for fid, spin in self._spins.items():
            val = saved.get(fid, {}).get("value_num")
            if val is not None:
                spin.setValue(float(val))

    def _calc_one(self, field_id, spin):
        if not self.instance_id:
            self._save_temp()
        val = calc_instance_cross_auto(self.conn, field_id, self.instance_id)
        if val is not None:
            spin.setValue(val)
        else:
            QMessageBox.information(self, "تنبيه",
                "لا توجد قيمة للحقل المصدر بعد.\n"
                "أدخل قيمة المصدر في مجموعتها أولاً.")

    def _calc_all_auto(self):
        if not self.instance_id:
            self._save_temp()
        fields = fetch_fields_for_set(self.conn, self.set_id)
        for f in fields:
            if f["field_type"] != "number" or not _row_val(f, "source_field_id"):
                continue
            fid = f["id"]
            if fid not in self._spins:
                continue
            val = calc_instance_cross_auto(self.conn, fid, self.instance_id)
            if val is not None:
                self._spins[fid].setValue(val)

    def _save_temp(self):
        """يحفظ مؤقتاً بدون إغلاق النافذة — للحساب التلقائي."""
        if not self.instance_id:
            name = self.inp_name.text().strip()
            self.instance_id = insert_instance(self.conn, self.set_id, name)
        values = {fid: sp.value() for fid, sp in self._spins.items()}
        save_instance_values(self.conn, self.instance_id, self.set_id, values)

    def _save(self):
        name = self.inp_name.text().strip()

        if self.instance_id:
            update_instance(self.conn, self.instance_id, name)
        else:
            self.instance_id = insert_instance(self.conn, self.set_id, name)

        values = {fid: sp.value() for fid, sp in self._spins.items()}
        save_instance_values(self.conn, self.instance_id, self.set_id, values)
        self.saved.emit(self.instance_id)
        self.accept()


# ══════════════════════════════════════════════════════════
# بطاقة مجموعة مقاسات (في القايمة اليسار)
# ══════════════════════════════════════════════════════════

class _SetCard(QFrame):
    clicked = pyqtSignal(int)   # set_id

    def __init__(self, set_id: int, name: str,
                 category: str, unit: str, fields_cnt: int,
                 instances_cnt: int, parent=None):
        super().__init__(parent)
        self.set_id   = set_id
        self._selected = False
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(_CARD_NORMAL)
        self.setMinimumHeight(72)
        self._build(name, category, unit, fields_cnt, instances_cnt)

    def _build(self, name, category, unit, fields_cnt, instances_cnt):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(10)

        # أيقونة
        icon_lbl = QLabel("📐")
        icon_lbl.setStyleSheet(f"font-size: 22px; background: transparent; border: none;")
        icon_lbl.setFixedWidth(34)
        icon_lbl.setAlignment(Qt.AlignCenter)

        # النصوص
        text_col = QVBoxLayout()
        text_col.setSpacing(2)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"""
            font-weight: bold;
            font-size: 13px;
            color: {_TEXT};
            background: transparent;
            border: none;
        """)

        meta_lbl = QLabel(
            f"{category or '—'}  ·  {unit}  ·  {fields_cnt} حقل"
        )
        meta_lbl.setStyleSheet(f"""
            font-size: 10px;
            color: {_TEXT_MUTED};
            background: transparent;
            border: none;
        """)

        text_col.addWidget(name_lbl)
        text_col.addWidget(meta_lbl)

        # badge عدد instances
        badge = QLabel(f"{instances_cnt} قيمة")
        badge.setAlignment(Qt.AlignCenter)
        badge.setFixedSize(58, 22)
        badge.setStyleSheet(f"""
            background: {_BLUE_LIGHT};
            color: {_BLUE};
            border-radius: 11px;
            font-size: 10px;
            font-weight: bold;
            border: none;
        """)

        lay.addWidget(icon_lbl)
        lay.addLayout(text_col, stretch=1)
        lay.addWidget(badge)

    def set_selected(self, sel: bool):
        self._selected = sel
        self.setStyleSheet(_CARD_SELECTED if sel else _CARD_NORMAL)

    def mousePressEvent(self, event):
        self.clicked.emit(self.set_id)
        super().mousePressEvent(event)


# ══════════════════════════════════════════════════════════
# قايمة مجموعات المقاسات (يسار)
# ══════════════════════════════════════════════════════════

class _SetsListPanel(QWidget):
    set_selected = pyqtSignal(int)   # set_id

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._cards     = {}   # set_id → _SetCard
        self._active_id = None
        self._all_rows  = []
        self._build()
        self._load()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── رأس ──
        hdr = QLabel("📐  مجموعات المقاسات")
        hdr.setStyleSheet(f"""
            font-weight: bold;
            font-size: 13px;
            color: {_BLUE};
            background: {_BLUE_LIGHT};
            padding: 10px 16px;
            border-bottom: 1px solid {_BORDER};
        """)
        root.addWidget(hdr)

        # ── فلتر بحث ──
        search_frame = QFrame()
        search_frame.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        s_lay = QHBoxLayout(search_frame)
        s_lay.setContentsMargins(10, 8, 10, 8)
        s_lay.setSpacing(6)

        self.inp_search = QLineEdit()
        self.inp_search.setPlaceholderText("🔍  بحث...")
        self.inp_search.setMinimumHeight(32)
        self.inp_search.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {_BORDER};
                border-radius: 8px;
                padding: 3px 10px;
                font-size: 12px;
                background: {_GRAY_BG};
            }}
            QLineEdit:focus {{ border-color: {_BLUE}; background: white; }}
        """)
        self.inp_search.textChanged.connect(self._apply_filter)

        # فلتر تصنيف
        from PyQt5.QtWidgets import QComboBox
        self.cmb_cat = QComboBox()
        self.cmb_cat.setMinimumHeight(32)
        self.cmb_cat.setMaximumWidth(130)
        self.cmb_cat.setStyleSheet(f"""
            QComboBox {{
                border: 1.5px solid {_BORDER};
                border-radius: 8px;
                padding: 3px 8px;
                font-size: 11px;
                background: {_GRAY_BG};
            }}
            QComboBox:focus {{ border-color: {_BLUE}; }}
            QComboBox::drop-down {{ border: none; }}
        """)
        self.cmb_cat.currentIndexChanged.connect(self._apply_filter)

        s_lay.addWidget(self.inp_search, stretch=1)
        s_lay.addWidget(self.cmb_cat)
        root.addWidget(search_frame)

        # ── منطقة البطاقات ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
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

        self._cards_widget = QWidget()
        self._cards_widget.setStyleSheet(f"background: {_GRAY_BG};")
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setSpacing(8)
        self._cards_layout.setContentsMargins(10, 10, 10, 10)
        self._cards_layout.addStretch()

        scroll.setWidget(self._cards_widget)
        root.addWidget(scroll, stretch=1)

        # ── عداد ──
        self.lbl_count = QLabel("")
        self.lbl_count.setAlignment(Qt.AlignCenter)
        self.lbl_count.setStyleSheet(f"""
            color: {_TEXT_MUTED};
            font-size: 10px;
            padding: 6px;
            background: white;
            border-top: 1px solid {_BORDER};
        """)
        root.addWidget(self.lbl_count)

    def _reload_cat_filter(self):
        from PyQt5.QtWidgets import QComboBox
        prev = self.cmb_cat.currentData()
        self.cmb_cat.blockSignals(True)
        self.cmb_cat.clear()
        self.cmb_cat.addItem("كل التصنيفات", None)
        rows = fetch_all_design_categories(self.conn)
        tree = build_category_tree(rows)
        self._add_cat_nodes(tree, 0)
        for i in range(self.cmb_cat.count()):
            if self.cmb_cat.itemData(i) == prev:
                self.cmb_cat.setCurrentIndex(i)
                break
        self.cmb_cat.blockSignals(False)

    def _add_cat_nodes(self, nodes, depth):
        indent = "  " * depth
        arrow  = "↳ " if depth > 0 else ""
        for node in nodes:
            self.cmb_cat.addItem(f"{indent}{arrow}{node['name']}", node["id"])
            if node["children"]:
                self._add_cat_nodes(node["children"], depth + 1)

    def _load(self):
        self._all_rows = list(fetch_all_dimension_sets(self.conn))
        self._reload_cat_filter()
        self._apply_filter()

    def _apply_filter(self):
        q      = self.inp_search.text().strip().lower()
        cat_id = self.cmb_cat.currentData()

        # امسح البطاقات الحالية
        for card in self._cards.values():
            self._cards_layout.removeWidget(card)
            card.deleteLater()
        self._cards = {}

        shown = 0
        for ds in self._all_rows:
            if q and q not in ds["name"].lower():
                continue
            if cat_id is not None and ds["category_id"] != cat_id:
                continue

            fields_cnt = self.conn.execute(
                "SELECT COUNT(*) as c FROM dimension_fields WHERE set_id=?",
                (ds["id"],)
            ).fetchone()["c"]

            instances_cnt = self.conn.execute(
                "SELECT COUNT(*) as c FROM dimension_set_instances WHERE set_id=?",
                (ds["id"],)
            ).fetchone()["c"]

            card = _SetCard(
                ds["id"], ds["name"],
                ds["category_name"] or "",
                ds["default_unit"] or "cm",
                fields_cnt, instances_cnt
            )
            card.clicked.connect(self._on_card_click)
            if ds["id"] == self._active_id:
                card.set_selected(True)

            self._cards_layout.insertWidget(
                self._cards_layout.count() - 1, card
            )
            self._cards[ds["id"]] = card
            shown += 1

        total = len(self._all_rows)
        self.lbl_count.setText(
            f"{shown} مجموعة" if shown == total
            else f"{shown} من {total} مجموعة"
        )

    def _on_card_click(self, set_id: int):
        # رفع تحديد القديم
        if self._active_id and self._active_id in self._cards:
            self._cards[self._active_id].set_selected(False)
        self._active_id = set_id
        if set_id in self._cards:
            self._cards[set_id].set_selected(True)
        self.set_selected.emit(set_id)

    def refresh(self):
        self._load()
        # لو كانت في مجموعة مختارة ابعت السيجنال تاني
        if self._active_id:
            self.set_selected.emit(self._active_id)

    def refresh_card(self, set_id: int):
        """يحدّث badge عدد الـ instances لبطاقة واحدة."""
        self._load()


# ══════════════════════════════════════════════════════════
# جدول الـ Instances (يمين)
# ══════════════════════════════════════════════════════════

class _InstancesTable(QWidget):
    """
    يعرض instances المجموعة المختارة في جدول واضح.
    الأعمدة: الاسم + قيمة كل حقل.
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._set_id = None
        self._fields = []
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── شريط الأدوات ──
        toolbar = QFrame()
        toolbar.setStyleSheet(f"""
            QFrame {{
                background: white;
                border-bottom: 1px solid {_BORDER};
            }}
        """)
        t_lay = QHBoxLayout(toolbar)
        t_lay.setContentsMargins(14, 10, 14, 10)
        t_lay.setSpacing(10)

        self.lbl_set_name = QLabel("اختر مجموعة مقاسات من القايمة")
        self.lbl_set_name.setStyleSheet(f"""
            font-weight: bold;
            font-size: 13px;
            color: {_TEXT};
            background: transparent;
        """)

        t_lay.addWidget(self.lbl_set_name, stretch=1)

        self.btn_add = QPushButton("➕  إضافة قيمة")
        self.btn_add.setStyleSheet(_BTN_PRIMARY)
        self.btn_add.setMinimumHeight(34)
        self.btn_add.setEnabled(False)
        self.btn_add.clicked.connect(self._add_instance)

        self.btn_edit = QPushButton("✏️  تعديل")
        self.btn_edit.setStyleSheet(_BTN_GHOST)
        self.btn_edit.setMinimumHeight(34)
        self.btn_edit.setEnabled(False)
        self.btn_edit.clicked.connect(self._edit_instance)

        self.btn_copy = QPushButton("📋  نسخ")
        self.btn_copy.setStyleSheet(_BTN_GHOST)
        self.btn_copy.setMinimumHeight(34)
        self.btn_copy.setEnabled(False)
        self.btn_copy.clicked.connect(self._copy_instance)

        self.btn_del = QPushButton("🗑️  حذف")
        self.btn_del.setStyleSheet(_BTN_DANGER)
        self.btn_del.setMinimumHeight(34)
        self.btn_del.setEnabled(False)
        self.btn_del.clicked.connect(self._delete_instance)

        t_lay.addWidget(self.btn_add)
        t_lay.addWidget(self.btn_edit)
        t_lay.addWidget(self.btn_copy)
        t_lay.addWidget(self.btn_del)

        root.addWidget(toolbar)

        # ── الجدول ──
        self.table = QTableWidget()
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setWordWrap(False)
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(True)
        self.table.setGridStyle(Qt.SolidLine)
        self.table.setStyleSheet(f"""
            QTableWidget {{
                border: none;
                background: white;
                alternate-background-color: #fafbff;
                gridline-color: {_BORDER};
                font-size: 12px;
                color: {_TEXT};
                outline: none;
            }}
            QTableWidget::item {{
                padding: 8px 12px;
            }}
            QTableWidget::item:selected {{
                background: {_BLUE_LIGHT};
                color: {_BLUE};
            }}
            QHeaderView::section {{
                background: {_GRAY_BG};
                color: {_TEXT_MUTED};
                font-weight: bold;
                font-size: 11px;
                padding: 8px 12px;
                border: none;
                border-bottom: 2px solid {_BORDER};
                border-right: 1px solid {_BORDER};
            }}
        """)
        self.table.horizontalHeader().setDefaultAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.table.horizontalHeader().setMinimumSectionSize(60)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.itemSelectionChanged.connect(self._on_select)
        self.table.doubleClicked.connect(lambda: self._edit_instance())
        root.addWidget(self.table, stretch=1)

        # ── شريط الحالة ──
        self._status_bar = QLabel("")
        self._status_bar.setAlignment(Qt.AlignCenter)
        self._status_bar.setStyleSheet(f"""
            background: {_GRAY_BG};
            color: {_TEXT_MUTED};
            font-size: 10px;
            padding: 6px;
            border-top: 1px solid {_BORDER};
        """)
        root.addWidget(self._status_bar)

        # ── حالة الفراغ ──
        self._empty_state = QFrame()
        self._empty_state.setStyleSheet("background: white; border: none;")
        e_lay = QVBoxLayout(self._empty_state)
        e_lay.setAlignment(Qt.AlignCenter)
        e_lbl = QLabel("📋")
        e_lbl.setAlignment(Qt.AlignCenter)
        e_lbl.setStyleSheet("font-size: 40px; background: transparent;")
        e_msg = QLabel("اختر مجموعة مقاسات لعرض قيمها")
        e_msg.setAlignment(Qt.AlignCenter)
        e_msg.setStyleSheet(f"color: {_TEXT_MUTED}; font-size: 13px; background: transparent;")
        e_hint = QLabel("اضغط على أي مجموعة من القايمة على اليسار")
        e_hint.setAlignment(Qt.AlignCenter)
        e_hint.setStyleSheet(f"color: #b0bec5; font-size: 11px; background: transparent;")
        e_lay.addWidget(e_lbl)
        e_lay.addSpacing(8)
        e_lay.addWidget(e_msg)
        e_lay.addWidget(e_hint)

        root.addWidget(self._empty_state)
        self.table.setVisible(False)
        self._status_bar.setVisible(False)

    # ── تحميل بيانات ──

    def load_set(self, set_id: int):
        self._set_id = set_id
        self.btn_add.setEnabled(True)

        # اسم المجموعة
        try:
            ds = self.conn.execute(
                "SELECT name FROM dimension_sets WHERE id=?", (set_id,)
            ).fetchone()
            set_name = ds["name"] if ds else f"مجموعة #{set_id}"
        except Exception:
            set_name = f"مجموعة #{set_id}"
        self.lbl_set_name.setText(f"📐  {set_name}")

        self._fields = [
            f for f in fetch_fields_for_set(self.conn, set_id)
            if f["field_type"] == "number"
        ]
        self._empty_state.setVisible(False)
        self.table.setVisible(True)
        self._status_bar.setVisible(True)
        self._refresh_table()

    def _refresh_table(self):
        if not self._set_id:
            return

        prev_row = self.table.currentRow()
        self.table.blockSignals(True)
        self.table.clear()
        self.table.setRowCount(0)

        # أعمدة: الاسم + كل حقل
        col_labels = ["الاسم"] + [f["label"] for f in self._fields]
        self.table.setColumnCount(len(col_labels))
        self.table.setHorizontalHeaderLabels(col_labels)

        hh = self.table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.Interactive)
        self.table.setColumnWidth(0, 160)
        for i in range(1, len(col_labels)):
            hh.setSectionResizeMode(i, QHeaderView.Interactive)
            self.table.setColumnWidth(i, 110)
        if len(col_labels) > 1:
            hh.setSectionResizeMode(len(col_labels) - 1, QHeaderView.Stretch)

        instances = fetch_instances_for_set(self.conn, self._set_id)
        for inst in instances:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setRowHeight(r, 42)

            # اسم الـ instance
            name = inst["name"].strip() if inst["name"].strip() else f"مجموعة #{inst['id']}"
            name_item = QTableWidgetItem(name)
            name_item.setData(Qt.UserRole, inst["id"])
            name_item.setFont(QFont("", -1, QFont.Bold))
            name_item.setForeground(QColor(_BLUE))
            self.table.setItem(r, 0, name_item)

            # قيم الحقول
            values = fetch_instance_values(self.conn, inst["id"])
            for ci, f in enumerate(self._fields, start=1):
                val_info = values.get(f["id"], {})
                val = val_info.get("value_num")
                unit = f["unit"] or ""
                if val is not None:
                    txt = f"{val:g}  {unit}".strip()
                else:
                    txt = "—"
                item = QTableWidgetItem(txt)
                item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                if val is None:
                    item.setForeground(QColor(_TEXT_MUTED))
                self.table.setItem(r, ci, item)

        self.table.blockSignals(False)

        cnt = self.table.rowCount()
        self._status_bar.setText(f"{cnt} مجموعة قيم  ·  انقر مرتين للتعديل")

        if prev_row >= 0 and prev_row < cnt:
            self.table.selectRow(prev_row)

        self._update_action_btns()

    def _selected_instance_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _on_select(self):
        self._update_action_btns()

    def _update_action_btns(self):
        has_sel = self._selected_instance_id() is not None
        self.btn_edit.setEnabled(has_sel)
        self.btn_copy.setEnabled(has_sel)
        self.btn_del.setEnabled(has_sel)

    # ── CRUD ──

    def _add_instance(self):
        if not self._set_id:
            return
        popup = _InstancePopup(self.conn, self._set_id, parent=self)
        popup.saved.connect(self._on_saved)
        popup.exec_()

    def _edit_instance(self):
        iid = self._selected_instance_id()
        if not iid:
            return
        popup = _InstancePopup(self.conn, self._set_id,
                                instance_id=iid, parent=self)
        popup.saved.connect(self._on_saved)
        popup.exec_()

    def _copy_instance(self):
        iid = self._selected_instance_id()
        if not iid:
            return
        inst = fetch_instance(self.conn, iid)
        src_name = inst["name"] if inst else ""
        name, ok = QInputDialog.getText(
            self, "نسخ مجموعة القيم",
            "اسم النسخة الجديدة:",
            text=f"{src_name} (نسخة)" if src_name else "نسخة جديدة"
        )
        if ok:
            duplicate_instance(self.conn, iid, name.strip())
            self._refresh_table()

    def _delete_instance(self):
        iid = self._selected_instance_id()
        if not iid:
            return
        inst = fetch_instance(self.conn, iid)
        name = inst["name"] if inst and inst["name"] else f"مجموعة #{iid}"
        if QMessageBox.question(
            self, "تأكيد الحذف",
            f"حذف «{name}» وكل قيمها؟",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            delete_instance(self.conn, iid)
            self._refresh_table()

    def _on_saved(self, instance_id: int):
        self._refresh_table()
        # حدد الصف المحفوظ
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 0)
            if item and item.data(Qt.UserRole) == instance_id:
                self.table.selectRow(r)
                break

    def clear(self):
        self._set_id = None
        self._fields = []
        self.table.setRowCount(0)
        self.table.setColumnCount(0)
        self.table.setVisible(False)
        self._status_bar.setVisible(False)
        self._empty_state.setVisible(True)
        self.lbl_set_name.setText("اختر مجموعة مقاسات من القايمة")
        self.btn_add.setEnabled(False)
        self.btn_edit.setEnabled(False)
        self.btn_copy.setEnabled(False)
        self.btn_del.setEnabled(False)


# ══════════════════════════════════════════════════════════
# اللوحة الرئيسية
# ══════════════════════════════════════════════════════════

class _ValuesPanel(QWidget):
    """
    اللوحة الرئيسية — Splitter:
      يسار: قايمة بطاقات المجموعات
      يمين: جدول instances + toolbar
    """

    def __init__(self, conn, parent=None):
        super().__init__(parent)
        self.conn    = conn
        self._set_id = None
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(4)
        splitter.setStyleSheet(f"""
            QSplitter::handle {{
                background: {_BORDER};
            }}
            QSplitter::handle:hover {{
                background: {_BLUE_MID};
            }}
        """)

        # يسار — قايمة المجموعات
        self._sets_list = _SetsListPanel(self.conn)
        self._sets_list.setMinimumWidth(240)
        self._sets_list.setMaximumWidth(360)
        self._sets_list.setStyleSheet(f"""
            background: {_GRAY_BG};
            border-right: 1px solid {_BORDER};
        """)

        # يمين — جدول القيم
        self._table = _InstancesTable(self.conn)
        self._table.setStyleSheet("background: white;")

        self._sets_list.set_selected.connect(self._on_set_selected)

        splitter.addWidget(self._sets_list)
        splitter.addWidget(self._table)
        splitter.setSizes([280, 720])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        root.addWidget(splitter)

    def load_set(self, set_id: int):
        """يُستدعى من _SetsPanel الخارجي لما يختار مجموعة."""
        self._set_id = set_id
        # نختار البطاقة في القايمة
        self._sets_list._on_card_click(set_id)

    def _on_set_selected(self, set_id: int):
        self._set_id = set_id
        self._table.load_set(set_id)

    def clear(self):
        self._set_id = None
        self._table.clear()