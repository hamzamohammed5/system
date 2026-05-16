"""
ui/tabs/design/dimension_sets/_source_picker_dialog.py
=======================================================
_SourcePickerDialog — dialog لاختيار الـ instance المصدر قبل الحساب التلقائي.

يُستدعى من _InstancePopup عند الضغط على ⟳ لأي حقل تلقائي cross-set.

يعرض:
  - اسم المجموعة المصدر
  - اسم الحقل المصدر
  - قايمة instances المجموعة المصدر مع قيمة الحقل لكل منها
  - معاينة النتيجة (قيمة المصدر + offset = النتيجة)

يرجع: instance_id المختار أو None لو ألغى
"""

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QWidget,
    QButtonGroup, QRadioButton,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor

from db.designs.dimension_sets_repo import (
    fetch_instances_for_set,
    fetch_instance_values,
    fetch_field,
)

# ── ألوان ──
_BLUE       = "#1565c0"
_BLUE_LIGHT = "#e8f0fe"
_BLUE_MID   = "#bbdefb"
_GREEN      = "#2e7d32"
_GREEN_LT   = "#e8f5e9"
_BORDER     = "#e0e7f3"
_TEXT       = "#1a2340"
_TEXT_MUTED = "#7a869a"
_GRAY_BG    = "#f8f9fc"

_BTN_PRIMARY = f"""
    QPushButton {{
        background: {_BLUE};
        color: white;
        border: none;
        border-radius: 7px;
        padding: 6px 20px;
        font-weight: bold;
        font-size: 12px;
    }}
    QPushButton:hover  {{ background: #0d47a1; }}
    QPushButton:disabled {{ background: #b0bec5; color: #fff; }}
"""
_BTN_GHOST = f"""
    QPushButton {{
        background: white;
        color: {_BLUE};
        border: 1.5px solid {_BLUE_MID};
        border-radius: 7px;
        padding: 5px 16px;
        font-size: 12px;
    }}
    QPushButton:hover {{ background: {_BLUE_LIGHT}; }}
"""


class _SourcePickerDialog(QDialog):
    """
    Dialog اختيار الـ instance المصدر للحساب التلقائي.

    المعاملات:
        conn             : اتصال قاعدة البيانات
        source_set_id    : ID مجموعة المقاسات المصدر
        source_field_id  : ID الحقل المصدر
        offset           : قيمة الإضافة/الخصم
        target_field_label: اسم الحقل المستهدف (للعرض فقط)

    ملاحظة: يظهر الـ dialog دايماً حتى لو instance واحد فقط —
            المستخدم يجب أن يؤكد اختياره صراحةً.
    """

    def __init__(self, conn,
                 source_set_id: int,
                 source_field_id: int,
                 offset: float = 0.0,
                 target_field_label: str = "",
                 parent=None):
        super().__init__(parent)
        self.conn             = conn
        self.source_set_id    = source_set_id
        self.source_field_id  = source_field_id
        self.offset           = offset
        self.target_label     = target_field_label
        self.selected_instance_id = None

        # نخزن اسم كل instance هنا لاستخدامه في _on_instance_selected
        self._instance_names: dict[int, str] = {}

        self.setWindowTitle("اختيار مصدر الحساب التلقائي")
        self.setMinimumWidth(480)
        self.setMinimumHeight(360)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {_GRAY_BG}; }}")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        # ── رأس ──
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet(f"""
            QFrame {{
                background: {_BLUE_LIGHT};
                border-radius: 10px;
                border: 1px solid {_BLUE_MID};
            }}
        """)
        hdr_lay = QVBoxLayout(hdr_frame)
        hdr_lay.setContentsMargins(14, 12, 14, 12)
        hdr_lay.setSpacing(4)

        title = QLabel("⟳  اختر مجموعة القيم المصدر")
        title.setStyleSheet(f"""
            font-weight: bold;
            font-size: 13px;
            color: {_BLUE};
            background: transparent;
            border: none;
        """)

        # جلب بيانات المجموعة والحقل المصدر
        src_set = self.conn.execute(
            "SELECT name FROM dimension_sets WHERE id=?",
            (self.source_set_id,)
        ).fetchone()
        src_set_name = src_set["name"] if src_set else f"مجموعة #{self.source_set_id}"

        src_field = fetch_field(self.conn, self.source_field_id)
        src_field_label = src_field["label"] if src_field else f"حقل #{self.source_field_id}"
        src_field_unit  = src_field["unit"]  if src_field else ""

        self._src_field_label = src_field_label
        self._src_field_unit  = src_field_unit

        sign = f"+{self.offset:g}" if self.offset >= 0 else f"{self.offset:g}"
        formula = (
            f"{src_field_label}  {sign}  →  {self.target_label}"
            if self.offset != 0
            else f"{src_field_label}  →  {self.target_label}"
        )

        subtitle = QLabel(
            f"من مجموعة:  <b>{src_set_name}</b>   ·   "
            f"الحقل:  <b>{src_field_label}</b>"
        )
        subtitle.setStyleSheet(f"""
            font-size: 11px;
            color: {_TEXT};
            background: transparent;
            border: none;
        """)

        formula_lbl = QLabel(f"📐  {formula}")
        formula_lbl.setStyleSheet(f"""
            font-size: 11px;
            color: {_TEXT_MUTED};
            background: transparent;
            border: none;
        """)

        hdr_lay.addWidget(title)
        hdr_lay.addWidget(subtitle)
        hdr_lay.addWidget(formula_lbl)
        root.addWidget(hdr_frame)

        # ── تعليمات ──
        hint = QLabel("اختر مجموعة القيم اللي هيتحسب منها الحقل:")
        hint.setStyleSheet(f"""
            font-size: 11px;
            font-weight: bold;
            color: {_TEXT_MUTED};
            background: transparent;
        """)
        root.addWidget(hint)

        # ── قايمة الـ instances ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1.5px solid {_BORDER};
                border-radius: 8px;
                background: white;
            }}
            QScrollBar:vertical {{
                background: #f0f0f0; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: #c5cae9; border-radius: 3px; min-height: 24px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        container = QWidget()
        container.setStyleSheet("background: white;")
        self._list_lay = QVBoxLayout(container)
        self._list_lay.setSpacing(4)
        self._list_lay.setContentsMargins(10, 10, 10, 10)

        self._btn_group = QButtonGroup(self)
        self._btn_group.buttonClicked.connect(self._on_instance_selected)

        instances = fetch_instances_for_set(self.conn, self.source_set_id)

        if not instances:
            empty = QLabel("لا توجد قيم محفوظة في هذه المجموعة.")
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {_TEXT_MUTED}; padding: 20px;")
            self._list_lay.addWidget(empty)
        else:
            for inst in instances:
                self._add_instance_row(inst)
            # لو instance واحد فقط → اختره تلقائياً لتسهيل التجربة
            # لكن الـ dialog يظل مفتوح حتى يضغط المستخدم "تطبيق"
            if len(instances) == 1:
                first_btn = self._btn_group.button(instances[0]["id"])
                if first_btn and first_btn.isEnabled():
                    first_btn.setChecked(True)
                    self._on_instance_selected(first_btn)

        self._list_lay.addStretch()
        scroll.setWidget(container)
        root.addWidget(scroll, stretch=1)

        # ── معاينة النتيجة ──
        self._preview_frame = QFrame()
        self._preview_frame.setStyleSheet(f"""
            QFrame {{
                background: {_GREEN_LT};
                border: 1.5px solid #a5d6a7;
                border-radius: 8px;
            }}
        """)
        self._preview_frame.setVisible(False)
        p_lay = QHBoxLayout(self._preview_frame)
        p_lay.setContentsMargins(14, 10, 14, 10)

        self._preview_lbl = QLabel("")
        self._preview_lbl.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: {_GREEN};
            background: transparent;
            border: none;
        """)
        p_lay.addWidget(self._preview_lbl)
        root.addWidget(self._preview_frame)

        # ── أزرار ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton("إلغاء")
        self.btn_cancel.setStyleSheet(_BTN_GHOST)
        self.btn_cancel.setMinimumHeight(36)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_ok = QPushButton("✓  تطبيق الحساب")
        self.btn_ok.setStyleSheet(_BTN_PRIMARY)
        self.btn_ok.setMinimumHeight(36)
        self.btn_ok.setMinimumWidth(140)
        self.btn_ok.setEnabled(False)
        self.btn_ok.clicked.connect(self.accept)

        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_ok)
        root.addLayout(btn_row)

    def _add_instance_row(self, inst):
        """يبني row لكل instance مع قيمة الحقل المصدر."""
        iid   = inst["id"]
        name  = inst["name"].strip() if inst["name"].strip() else f"مجموعة #{iid}"

        # خزّن الاسم للاستخدام لاحقاً بدون الاعتماد على widget hierarchy
        self._instance_names[iid] = name

        # جلب قيمة الحقل المصدر لهذا الـ instance
        values   = fetch_instance_values(self.conn, iid)
        val_info = values.get(self.source_field_id, {})
        src_val  = val_info.get("value_num")

        # بناء الـ row
        row_frame = QFrame()
        row_frame.setStyleSheet(f"""
            QFrame {{
                background: white;
                border: 1.5px solid {_BORDER};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: {_BLUE_MID};
                background: #f5f8ff;
            }}
        """)
        row_lay = QHBoxLayout(row_frame)
        row_lay.setContentsMargins(12, 8, 12, 8)
        row_lay.setSpacing(12)

        # Radio button
        radio = QRadioButton()
        radio.setStyleSheet(f"""
            QRadioButton {{
                spacing: 0px;
                background: transparent;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {_BLUE_MID};
                background: white;
            }}
            QRadioButton::indicator:checked {{
                background: {_BLUE};
                border-color: {_BLUE};
            }}
        """)
        # نخزن البيانات كـ properties على الـ radio مباشرة
        radio.setProperty("instance_id", iid)
        radio.setProperty("src_val", src_val)

        # لو مفيش قيمة → عطّل الـ radio
        has_value = src_val is not None
        radio.setEnabled(has_value)

        self._btn_group.addButton(radio, iid)

        # اسم الـ instance
        name_lbl = QLabel(name)
        name_lbl.setStyleSheet(f"""
            font-weight: bold;
            font-size: 12px;
            color: {_TEXT if has_value else _TEXT_MUTED};
            background: transparent;
            border: none;
        """)

        # قيمة الحقل المصدر + النتيجة
        if has_value:
            val_txt = f"{src_val:g}  {self._src_field_unit}".strip()
            result  = src_val + self.offset
            sign    = f"+{self.offset:g}" if self.offset >= 0 else f"{self.offset:g}"
            res_txt = (
                f"= {result:g}" if self.offset == 0
                else f"{sign} = {result:g}"
            )
            val_lbl = QLabel(val_txt)
            val_lbl.setStyleSheet(f"""
                font-size: 12px;
                color: {_TEXT};
                background: transparent;
                border: none;
            """)
            res_lbl = QLabel(res_txt)
            res_lbl.setStyleSheet(f"""
                font-size: 12px;
                font-weight: bold;
                color: {_GREEN};
                background: {_GREEN_LT};
                border: 1px solid #a5d6a7;
                border-radius: 5px;
                padding: 1px 8px;
            """)
        else:
            val_lbl = QLabel("لا توجد قيمة")
            val_lbl.setStyleSheet(f"""
                font-size: 11px;
                color: #ef9a9a;
                background: transparent;
                border: none;
            """)
            res_lbl = QLabel("—")
            res_lbl.setStyleSheet(
                f"color: {_TEXT_MUTED}; background: transparent; border: none;"
            )

        row_lay.addWidget(radio)
        row_lay.addWidget(name_lbl, stretch=1)
        row_lay.addWidget(val_lbl)
        row_lay.addWidget(res_lbl)

        # ضغط على الـ frame = تحديد الـ radio (لو مفعّل)
        def _frame_click(event, r=radio):
            if r.isEnabled():
                r.setChecked(True)
                self._on_instance_selected(r)

        row_frame.mousePressEvent = _frame_click

        self._list_lay.addWidget(row_frame)

    def _on_instance_selected(self, btn):
        iid     = btn.property("instance_id")
        src_val = btn.property("src_val")

        if iid is None or src_val is None:
            return

        self.selected_instance_id = iid
        self.btn_ok.setEnabled(True)

        # استرجاع الاسم من الـ dict بدلاً من widget hierarchy
        inst_name = self._instance_names.get(iid, "")

        result = src_val + self.offset
        sign   = f"+{self.offset:g}" if self.offset >= 0 else f"{self.offset:g}"

        if self.offset != 0:
            txt = f"✓  {inst_name}:  {src_val:g}  {sign}  =  {result:g}  {self._src_field_unit}".strip()
        else:
            txt = f"✓  {inst_name}:  {result:g}  {self._src_field_unit}".strip()

        self._preview_lbl.setText(txt)
        self._preview_frame.setVisible(True)

    def get_selected(self) -> int | None:
        """يرجع instance_id المختار أو None."""
        return self.selected_instance_id