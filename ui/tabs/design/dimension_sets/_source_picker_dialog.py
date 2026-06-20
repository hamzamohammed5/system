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

from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_SM, FS_BASE, FS_MD
from services.design.dimension_set_service import DimensionSetService


def _btn_primary_ss():
    return f"""
        QPushButton {{
            background: {_C['accent']};
            color: {_C['accent_text']};
            border: none;
            border-radius: 7px;
            padding: 6px 20px;
            font-weight: bold;
            font-size: {FS_BASE}px;
        }}
        QPushButton:hover  {{ background: {_C['accent_hover']}; }}
        QPushButton:disabled {{ background: {_C['border_med']}; color: {_C['text_disabled']}; }}
    """


def _btn_ghost_ss():
    return f"""
        QPushButton {{
            background: {_C['bg_input']};
            color: {_C['accent']};
            border: 1.5px solid {_C['accent_mid']};
            border-radius: 7px;
            padding: 5px 16px;
            font-size: {FS_BASE}px;
        }}
        QPushButton:hover {{ background: {_C['accent_light']}; }}
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
        self._svc             = DimensionSetService(conn)
        self.source_set_id    = source_set_id
        self.source_field_id  = source_field_id
        self.offset           = offset
        self.target_label     = target_field_label
        self.selected_instance_id = None

        # نخزن اسم كل instance هنا لاستخدامه في _on_instance_selected
        self._instance_names: dict[int, str] = {}

        self.setWindowTitle(tr("dim_src_picker_title"))
        self.setMinimumWidth(480)
        self.setMinimumHeight(360)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {_C['bg_surface']}; }}")
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        # ── رأس ──
        hdr_frame = QFrame()
        hdr_frame.setStyleSheet(f"""
            QFrame {{
                background: {_C['accent_light']};
                border-radius: 10px;
                border: 1px solid {_C['accent_mid']};
            }}
        """)
        hdr_lay = QVBoxLayout(hdr_frame)
        hdr_lay.setContentsMargins(14, 12, 14, 12)
        hdr_lay.setSpacing(4)

        title = QLabel(f"⟳  {tr('dim_src_picker_header')}")
        title.setStyleSheet(f"""
            font-weight: bold;
            font-size: {FS_MD}px;
            color: {_C['accent']};
            background: transparent;
            border: none;
        """)

        # جلب بيانات المجموعة والحقل المصدر
        src_set_name = self._svc.get_set_name(self.source_set_id)

        src_field = self._svc.get_field(self.source_field_id)
        src_field_label = src_field["label"] if src_field else f"#{self.source_field_id}"
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
            f"{tr('dim_src_picker_from_group')}:  <b>{src_set_name}</b>   ·   "
            f"{tr('dim_src_picker_field')}:  <b>{src_field_label}</b>"
        )
        subtitle.setStyleSheet(f"""
            font-size: {FS_SM}px;
            color: {_C['text_primary']};
            background: transparent;
            border: none;
        """)

        formula_lbl = QLabel(f"📐  {formula}")
        formula_lbl.setStyleSheet(f"""
            font-size: {FS_SM}px;
            color: {_C['text_muted']};
            background: transparent;
            border: none;
        """)

        hdr_lay.addWidget(title)
        hdr_lay.addWidget(subtitle)
        hdr_lay.addWidget(formula_lbl)
        root.addWidget(hdr_frame)

        # ── تعليمات ──
        hint = QLabel(tr("dim_src_picker_hint") + ":")
        hint.setStyleSheet(f"""
            font-size: {FS_SM}px;
            font-weight: bold;
            color: {_C['text_muted']};
            background: transparent;
        """)
        root.addWidget(hint)

        # ── قايمة الـ instances ──
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                border: 1.5px solid {_C['border']};
                border-radius: 8px;
                background: {_C['bg_input']};
            }}
            QScrollBar:vertical {{
                background: {_C['bg_surface']}; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {_C['border_med']}; border-radius: 3px; min-height: 24px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        container = QWidget()
        container.setStyleSheet(f"background: {_C['bg_input']};")
        self._list_lay = QVBoxLayout(container)
        self._list_lay.setSpacing(4)
        self._list_lay.setContentsMargins(10, 10, 10, 10)

        self._btn_group = QButtonGroup(self)
        self._btn_group.buttonClicked.connect(self._on_instance_selected)

        instances = self._svc.list_instances(self.source_set_id)

        if not instances:
            empty = QLabel(tr("dim_src_picker_no_values"))
            empty.setAlignment(Qt.AlignCenter)
            empty.setStyleSheet(f"color: {_C['text_muted']}; padding: 20px;")
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
                background: {_C['success_bg']};
                border: 1.5px solid {_C['success_border']};
                border-radius: 8px;
            }}
        """)
        self._preview_frame.setVisible(False)
        p_lay = QHBoxLayout(self._preview_frame)
        p_lay.setContentsMargins(14, 10, 14, 10)

        self._preview_lbl = QLabel("")
        self._preview_lbl.setStyleSheet(f"""
            font-size: {FS_BASE}px;
            font-weight: bold;
            color: {_C['success']};
            background: transparent;
            border: none;
        """)
        p_lay.addWidget(self._preview_lbl)
        root.addWidget(self._preview_frame)

        # ── أزرار ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self.btn_cancel = QPushButton(tr("cancel"))
        self.btn_cancel.setStyleSheet(_btn_ghost_ss())
        self.btn_cancel.setMinimumHeight(36)
        self.btn_cancel.clicked.connect(self.reject)

        self.btn_ok = QPushButton(tr("dim_src_picker_apply"))
        self.btn_ok.setStyleSheet(_btn_primary_ss())
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
        name  = inst["name"].strip() if inst["name"].strip() else f"#{iid}"

        # خزّن الاسم للاستخدام لاحقاً بدون الاعتماد على widget hierarchy
        self._instance_names[iid] = name

        # جلب قيمة الحقل المصدر لهذا الـ instance
        values   = self._svc.get_instance_values(iid)
        val_info = values.get(self.source_field_id, {})
        src_val  = val_info.get("value_num")

        # بناء الـ row
        row_frame = QFrame()
        row_frame.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_input']};
                border: 1.5px solid {_C['border']};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: {_C['accent_mid']};
                background: {_C['bg_hover']};
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
                border: 2px solid {_C['accent_mid']};
                background: {_C['bg_input']};
            }}
            QRadioButton::indicator:checked {{
                background: {_C['accent']};
                border-color: {_C['accent']};
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
            font-size: {FS_BASE}px;
            color: {_C['text_primary'] if has_value else _C['text_muted']};
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
                font-size: {FS_BASE}px;
                color: {_C['text_primary']};
                background: transparent;
                border: none;
            """)
            res_lbl = QLabel(res_txt)
            res_lbl.setStyleSheet(f"""
                font-size: {FS_BASE}px;
                font-weight: bold;
                color: {_C['success']};
                background: {_C['success_bg']};
                border: 1px solid {_C['success_border']};
                border-radius: 5px;
                padding: 1px 8px;
            """)
        else:
            val_lbl = QLabel(tr("dim_src_picker_no_value_short"))
            val_lbl.setStyleSheet(f"""
                font-size: {FS_SM}px;
                color: {_C['danger_border']};
                background: transparent;
                border: none;
            """)
            res_lbl = QLabel(tr("dash"))
            res_lbl.setStyleSheet(
                f"color: {_C['text_muted']}; background: transparent; border: none;"
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