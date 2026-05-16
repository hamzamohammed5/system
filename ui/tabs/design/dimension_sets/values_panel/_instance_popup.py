"""
ui/tabs/design/dimension_sets/values_panel/_instance_popup.py
=====================================

"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QDoubleSpinBox,
    QMessageBox, QScrollArea, QFrame, QDialog,
    QToolButton, QGridLayout,
)
from PyQt5.QtCore import Qt, pyqtSignal

from db.designs.dimension_sets_repo import (
    fetch_fields_for_set,
    fetch_instance,
    insert_instance, update_instance,
    fetch_instance_values, save_instance_values, calc_instance_cross_auto,
    fetch_field_dep,
)
from ui.tabs.design.dimension_sets._source_picker_dialog import _SourcePickerDialog

_BLUE       = "#1565c0"
_BLUE_LIGHT = "#e8f0fe"
_BLUE_MID   = "#bbdefb"
_GRAY_BG    = "#f8f9fc"
_BORDER     = "#e0e7f3"
_TEXT       = "#1a2340"
_TEXT_MUTED = "#7a869a"


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

    # ──────────────────────────────────────────────────────
    # دالة مساعدة: تحدد الـ source_instance_id مع سؤال المستخدم
    # ──────────────────────────────────────────────────────

    def _pick_source_instance(self, field_id: int):
        """
        لو الحقل عنده cross-set dependency → يفتح _SourcePickerDialog.
        لو same-set dependency → يرجع self.instance_id مباشرة.
        يرجع source_instance_id أو None لو ألغى المستخدم.
        """
        dep = fetch_field_dep(self.conn, field_id)
        if not dep:
            return None

        source_set_id   = dep["source_set_id"]   # None = نفس المجموعة
        source_field_id = dep["source_field_id"]
        offset          = float(dep["offset"])

        # نفس المجموعة: المصدر = self.instance_id دايماً
        if source_set_id is None:
            return self.instance_id

        # مجموعة مختلفة: اسأل المستخدم دايماً حتى لو instance واحد
        try:
            target_field = self.conn.execute(
                "SELECT label FROM dimension_fields WHERE id=?",
                (field_id,)
            ).fetchone()
            target_label = target_field["label"] if target_field else ""
        except Exception:
            target_label = ""

        dlg = _SourcePickerDialog(
            conn               = self.conn,
            source_set_id      = source_set_id,
            source_field_id    = source_field_id,
            offset             = offset,
            target_field_label = target_label,
            parent             = self,
        )

        if dlg.exec_() != QDialog.Accepted:
            return None   # ألغى

        return dlg.get_selected()

    # ──────────────────────────────────────────────────────
    # حساب حقل واحد
    # ──────────────────────────────────────────────────────

    def _calc_one(self, field_id: int, spin):
        """حساب قيمة حقل واحد — مع اختيار الـ instance المصدر لو cross-set."""

        # تأكد إن الـ instance موجود في الـ DB قبل الحساب
        if not self.instance_id:
            self._save_temp()

        dep = fetch_field_dep(self.conn, field_id)
        if not dep:
            return

        source_set_id   = dep["source_set_id"]
        source_field_id = dep["source_field_id"]
        offset          = float(dep["offset"])

        # نفس المجموعة: احسب مباشرة بدون dialog
        if source_set_id is None:
            val = calc_instance_cross_auto(self.conn, field_id, self.instance_id)
            if val is not None:
                spin.setValue(val)
            else:
                QMessageBox.information(
                    self, "تنبيه",
                    "لا توجد قيمة للحقل المصدر بعد.\n"
                    "أدخل قيمة المصدر في هذه المجموعة أولاً."
                )
            return

        # مجموعة مختلفة: اسأل المستخدم (دايماً حتى لو instance واحد)
        source_instance_id = self._pick_source_instance(field_id)
        if source_instance_id is None:
            return   # ألغى المستخدم

        val_row = self.conn.execute(
            "SELECT value_num FROM dimension_set_values "
            "WHERE instance_id=? AND field_id=?",
            (source_instance_id, source_field_id)
        ).fetchone()

        if val_row and val_row["value_num"] is not None:
            result = float(val_row["value_num"]) + offset
            spin.setValue(result)
        else:
            QMessageBox.information(
                self, "تنبيه",
                "لا توجد قيمة للحقل المصدر في المجموعة المختارة.\n"
                "أدخل القيمة في مجموعة القيم المصدر أولاً."
            )

    # ──────────────────────────────────────────────────────
    # حساب كل الحقول التلقائية
    # ──────────────────────────────────────────────────────

    def _calc_all_auto(self):
        """
        حساب كل الحقول التلقائية.
        للـ cross-set: يسأل مرة واحدة لكل مجموعة مصدر فريدة.
        """
        if not self.instance_id:
            self._save_temp()

        fields = fetch_fields_for_set(self.conn, self.set_id)

        # مجموعة مصدر → instance_id المختار (None = ألغى)
        # تُملأ تدريجياً لتجنب سؤال المستخدم مرتين عن نفس المجموعة
        source_instance_map: dict = {}

        for f in fields:
            if f["field_type"] != "number":
                continue
            fid = f["id"]
            if fid not in self._spins:
                continue

            dep = fetch_field_dep(self.conn, fid)
            if not dep:
                continue

            source_set_id   = dep["source_set_id"]
            source_field_id = dep["source_field_id"]
            offset          = float(dep["offset"])
            spin            = self._spins[fid]

            # نفس المجموعة: احسب مباشرة
            if source_set_id is None:
                val = calc_instance_cross_auto(self.conn, fid, self.instance_id)
                if val is not None:
                    spin.setValue(val)
                continue

            # مجموعة مختلفة: اسأل مرة واحدة لكل مجموعة مصدر
            if source_set_id not in source_instance_map:
                src_iid = self._pick_source_instance(fid)
                source_instance_map[source_set_id] = src_iid

            src_iid = source_instance_map[source_set_id]
            if src_iid is None:
                continue   # المستخدم ألغى لهذه المجموعة → تخطى

            val_row = self.conn.execute(
                "SELECT value_num FROM dimension_set_values "
                "WHERE instance_id=? AND field_id=?",
                (src_iid, source_field_id)
            ).fetchone()

            if val_row and val_row["value_num"] is not None:
                spin.setValue(float(val_row["value_num"]) + offset)

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

