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

from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_XS, FS_SM, FS_BASE, FS_MD, FS_LG
from services.design.dimension_set_service import DimensionSetService
from ui.tabs.design.dimension_sets._source_picker_dialog import _SourcePickerDialog


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
        self._svc        = DimensionSetService(conn)
        self.set_id      = set_id
        self.instance_id = instance_id
        self._spins      = {}   # field_id → QDoubleSpinBox

        title = tr("dim_inst_dlg_edit_title") if instance_id else tr("dim_inst_dlg_new_title")
        self.setWindowTitle(title)
        self.setMinimumWidth(520)
        self.setMinimumHeight(400)
        self.setModal(True)
        self.setStyleSheet(f"""
            QDialog {{
                background: {_C['bg_surface']};
            }}
            QLabel {{
                color: {_C['text_primary']};
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
            tr("dim_inst_hdr_edit") if self.instance_id
            else tr("dim_inst_hdr_new")
        )
        hdr.setStyleSheet(f"""
            font-size: {FS_MD}px;
            font-weight: bold;
            color: {_C['accent']};
            background: {_C['accent_light']};
            border-radius: 8px;
            padding: 8px 14px;
        """)
        root.addWidget(hdr)

        # ── اسم المجموعة ──
        name_row = QHBoxLayout()
        lbl_name = QLabel(tr("dim_inst_name_label") + ":")
        lbl_name.setFixedWidth(90)
        lbl_name.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl_name.setStyleSheet("font-weight: bold;")

        self.inp_name = QLineEdit()
        self.inp_name.setPlaceholderText(tr("dim_inst_name_placeholder"))
        self.inp_name.setMinimumHeight(36)
        self.inp_name.setStyleSheet(f"""
            QLineEdit {{
                border: 1.5px solid {_C['border']};
                border-radius: 8px;
                padding: 4px 12px;
                font-size: {FS_BASE}px;
                background: {_C['bg_input']};
            }}
            QLineEdit:focus {{ border-color: {_C['accent']}; }}
        """)

        if self.instance_id:
            inst = self._svc.get_instance(self.instance_id)
            if inst:
                self.inp_name.setText(inst["name"])

        name_row.addWidget(lbl_name)
        name_row.addWidget(self.inp_name)
        root.addLayout(name_row)

        # ── فاصل ──
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet(f"color: {_C['border']};")
        root.addWidget(sep)

        # ── حقول الإدخال ──
        fields_lbl = QLabel(tr("dim_inst_values_label") + ":")
        fields_lbl.setStyleSheet(f"font-weight: bold; color: {_C['text_muted']}; font-size: {FS_SM}px;")
        root.addWidget(fields_lbl)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{
                background: {_C['bg_surface']}; width: 6px; border-radius: 3px;
            }}
            QScrollBar::handle:vertical {{
                background: {_C['border']}; border-radius: 3px; min-height: 24px;
            }}
            QScrollBar::add-line:vertical,
            QScrollBar::sub-line:vertical {{ height: 0; }}
        """)

        fields_w = QWidget()
        fields_w.setStyleSheet("background: transparent;")
        grid = QGridLayout(fields_w)
        grid.setSpacing(10)
        grid.setContentsMargins(0, 4, 0, 4)

        fields = self._svc.list_fields(self.set_id)
        num_fields = [f for f in fields if f["field_type"] == "number"]

        for i, f in enumerate(num_fields):
            lbl = QLabel(f["label"])
            lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            lbl.setStyleSheet(f"font-weight: 500; color: {_C['text_primary']};")
            lbl.setFixedWidth(130)

            spin = QDoubleSpinBox()
            spin.setRange(-99999, 99999)
            spin.setDecimals(4)
            spin.setMinimumHeight(36)
            spin.setStyleSheet(f"""
                QDoubleSpinBox {{
                    border: 1.5px solid {_C['border']};
                    border-radius: 8px;
                    padding: 4px 10px;
                    font-size: {FS_BASE}px;
                    background: {_C['bg_input']};
                }}
                QDoubleSpinBox:focus {{ border-color: {_C['accent']}; }}
            """)

            unit_lbl = QLabel(f["unit"] or "")
            unit_lbl.setFixedWidth(38)
            unit_lbl.setStyleSheet(f"color: {_C['text_muted']}; font-size: {FS_SM}px;")
            unit_lbl.setAlignment(Qt.AlignVCenter)

            # زر الحساب التلقائي لو في اعتمادية
            has_dep = bool(_row_val(f, "source_field_id"))
            if has_dep:
                btn_auto = QToolButton()
                btn_auto.setText("⟳")
                btn_auto.setFixedSize(32, 32)
                btn_auto.setStyleSheet(f"""
                    QToolButton {{
                        background: transparent;
                        border: none;
                        color: {_C['text_muted']};
                        font-size: {FS_MD}px;
                        border-radius: 5px;
                        padding: 3px 6px;
                    }}
                    QToolButton:hover {{ background: {_C['accent_light']}; color: {_C['accent']}; }}
                """)
                btn_auto.setToolTip(tr("dim_inst_auto_tooltip"))
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
            empty = QLabel(tr("dim_inst_no_numeric_fields"))
            empty.setStyleSheet(f"color: {_C['text_muted']}; padding: 12px;")
            empty.setAlignment(Qt.AlignCenter)
            grid.addWidget(empty, 0, 0, 1, 3)

        scroll.setWidget(fields_w)
        root.addWidget(scroll, stretch=1)

        # ── أزرار الحفظ ──
        btn_row = QHBoxLayout()

        has_auto = any(bool(_row_val(f, "source_field_id"))
                       for f in num_fields)
        if has_auto:
            btn_calc_all = QPushButton(tr("dim_inst_calc_all_btn"))
            btn_calc_all.setStyleSheet(f"""
                QPushButton {{
                    background: {_C['bg_input']};
                    color: {_C['accent']};
                    border: 1.5px solid {_C['accent_mid']};
                    border-radius: 7px;
                    padding: 5px 14px;
                    font-size: {FS_BASE}px;
                }}
                QPushButton:hover {{ background: {_C['accent_light']}; }}
            """)
            btn_calc_all.setMinimumHeight(36)
            btn_calc_all.clicked.connect(self._calc_all_auto)
            btn_row.addWidget(btn_calc_all)

        btn_row.addStretch()

        btn_cancel = QPushButton(tr("cancel"))
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_input']};
                color: {_C['accent']};
                border: 1.5px solid {_C['accent_mid']};
                border-radius: 7px;
                padding: 5px 14px;
                font-size: {FS_BASE}px;
            }}
            QPushButton:hover {{ background: {_C['accent_light']}; }}
        """)
        btn_cancel.setMinimumHeight(36)
        btn_cancel.clicked.connect(self.reject)

        btn_save = QPushButton("💾  " + tr("save"))
        btn_save.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']};
                color: {_C['btn_primary_text']};
                border: none;
                border-radius: 7px;
                padding: 6px 18px;
                font-weight: bold;
                font-size: {FS_BASE}px;
            }}
            QPushButton:hover  {{ background: {_C['accent_hover']}; }}
            QPushButton:disabled {{ background: {_C['text_muted']}; }}
        """)
        btn_save.setMinimumHeight(36)
        btn_save.setMinimumWidth(100)
        btn_save.clicked.connect(self._save)

        btn_row.addWidget(btn_cancel)
        btn_row.addWidget(btn_save)
        root.addLayout(btn_row)

    def _load_values(self):
        saved = self._svc.get_instance_values(self.instance_id)
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
        dep = self._svc.get_field_dependency(field_id)
        if not dep:
            return None

        source_set_id   = dep["source_set_id"]   # None = نفس المجموعة
        source_field_id = dep["source_field_id"]
        offset          = float(dep["offset"])

        # نفس المجموعة: المصدر = self.instance_id دايماً
        if source_set_id is None:
            return self.instance_id

        # مجموعة مختلفة: اسأل المستخدم دايماً حتى لو instance واحد
        target_field = self._svc.get_field(field_id)
        target_label = target_field["label"] if target_field else ""

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

        dep = self._svc.get_field_dependency(field_id)
        if not dep:
            return

        source_set_id   = dep["source_set_id"]
        source_field_id = dep["source_field_id"]
        offset          = float(dep["offset"])

        # نفس المجموعة: احسب مباشرة بدون dialog
        if source_set_id is None:
            val = self._svc.calc_same_set_auto(field_id, self.instance_id)
            if val is not None:
                spin.setValue(val)
            else:
                QMessageBox.information(
                    self, tr("info"),
                    tr("dim_inst_no_source_value")
                )
            return

        # مجموعة مختلفة: اسأل المستخدم (دايماً حتى لو instance واحد)
        source_instance_id = self._pick_source_instance(field_id)
        if source_instance_id is None:
            return   # ألغى المستخدم

        val = self._svc.get_field_value(source_instance_id, source_field_id)

        if val is not None:
            result = float(val) + offset
            spin.setValue(result)
        else:
            QMessageBox.information(
                self, tr("info"),
                tr("dim_inst_no_cross_value")
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

        fields = self._svc.list_fields(self.set_id)

        # مجموعة مصدر → instance_id المختار (None = ألغى)
        # تُملأ تدريجياً لتجنب سؤال المستخدم مرتين عن نفس المجموعة
        source_instance_map: dict = {}

        for f in fields:
            if f["field_type"] != "number":
                continue
            fid = f["id"]
            if fid not in self._spins:
                continue

            dep = self._svc.get_field_dependency(fid)
            if not dep:
                continue

            source_set_id   = dep["source_set_id"]
            source_field_id = dep["source_field_id"]
            offset          = float(dep["offset"])
            spin            = self._spins[fid]

            # نفس المجموعة: احسب مباشرة
            if source_set_id is None:
                val = self._svc.calc_same_set_auto(fid, self.instance_id)
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

            val = self._svc.get_field_value(src_iid, source_field_id)

            if val is not None:
                spin.setValue(float(val) + offset)

    def _save_temp(self):
        """يحفظ مؤقتاً بدون إغلاق النافذة — للحساب التلقائي."""
        if not self.instance_id:
            name = self.inp_name.text().strip()
            self.instance_id = self._svc.create_instance(self.set_id, name)
        values = {fid: sp.value() for fid, sp in self._spins.items()}
        self._svc.save_instance_values(self.instance_id, self.set_id, values)

    def _save(self):
        name = self.inp_name.text().strip()

        if self.instance_id:
            self._svc.update_instance(self.instance_id, name)
        else:
            self.instance_id = self._svc.create_instance(self.set_id, name)

        values = {fid: sp.value() for fid, sp in self._spins.items()}
        self._svc.save_instance_values(self.instance_id, self.set_id, values)
        self.saved.emit(self.instance_id)
        self.accept()

