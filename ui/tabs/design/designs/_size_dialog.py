"""
ui/tabs/design/designs/_size_dialog.py
==============================
"""

import os

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QComboBox, QMessageBox, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout,
)
from PyQt5.QtCore import Qt

from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import FS_XS, FS_SM, FS_BASE, FS_MD, FS_LG
from ui.widgets.core.widget_mixin import WidgetMixin
from services.design.dimension_set_service import DimensionSetService
from ui.constants import (
    SIZE_DLG_MIN_W, SIZE_DLG_MARGIN_H, SIZE_DLG_MARGIN_V, SIZE_DLG_ROOT_SPACING,
    SIZE_DLG_HDR_RADIUS, SIZE_DLG_HDR_PAD_V, SIZE_DLG_HDR_PAD_H, SIZE_DLG_FORM_SPACING,
    SIZE_DLG_FIELD_H, SIZE_DLG_CANVAS_RADIUS, SIZE_DLG_CANVAS_PAD_V, SIZE_DLG_CANVAS_PAD_H,
    SIZE_DLG_CANVAS_BORDER_W, SIZE_DLG_BROWSE_BTN_SIZE, SIZE_DLG_BROWSE_RADIUS,
    SIZE_DLG_BROWSE_BORDER_W, SIZE_DLG_BTN_H, SIZE_DLG_BTN_OK_RADIUS, SIZE_DLG_BTN_OK_PAD_V,
    SIZE_DLG_BTN_OK_PAD_H, SIZE_DLG_BTN_CANCEL_PAD_V, SIZE_DLG_BTN_CANCEL_PAD_H,
)


# ══════════════════════════════════════════════════════════
# Dialog — إضافة / تعديل مقاس للتصميم
# ══════════════════════════════════════════════════════════

class _SizeDialog(QDialog, WidgetMixin):
    """
    Dialog لإضافة أو تعديل مقاس واحد للتصميم.
    يختار: مجموعة مقاسات → instance → حقل العرض → حقل الطول → حقل الـ DPI → مسار الملف
    """

    def __init__(self, conn, design_id: int,
                 size_data=None, parent=None):
        super().__init__(parent)
        self.conn       = conn
        self._svc       = DimensionSetService(conn)
        self.design_id  = design_id
        self.size_id    = size_data["id"] if size_data else None
        self._size_data = size_data

        self.setWindowTitle(tr("design_size_dlg_edit_title") if size_data else tr("design_size_dlg_new_title"))
        self.setMinimumWidth(SIZE_DLG_MIN_W)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {_C['bg_surface']}; }}")
        self._init_widget_mixin(theme=False, font=False, lang=False, data=False)
        self._build()
        if size_data:
            self._load(size_data)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(SIZE_DLG_MARGIN_H, SIZE_DLG_MARGIN_V, SIZE_DLG_MARGIN_H, SIZE_DLG_MARGIN_V)
        root.setSpacing(SIZE_DLG_ROOT_SPACING)

        # ── رأس ──
        hdr = QLabel(tr("design_size_dlg_header_icon") + (tr("design_size_dlg_edit_title") if self.size_id else tr("design_size_dlg_new_title")))
        hdr.setStyleSheet(f"""
            font-size: {FS_MD}px; font-weight: bold; color: {_C['accent']};
            background: {_C['accent_light']}; border-radius: {SIZE_DLG_HDR_RADIUS}px;
            padding: {SIZE_DLG_HDR_PAD_V}px {SIZE_DLG_HDR_PAD_H}px;
        """)
        root.addWidget(hdr)

        form = QFormLayout()
        form.setSpacing(SIZE_DLG_FORM_SPACING)
        form.setLabelAlignment(Qt.AlignRight)

        # ── مجموعة المقاسات ──
        self.cmb_set = QComboBox()
        self.cmb_set.setMinimumHeight(SIZE_DLG_FIELD_H)
        self.cmb_set.currentIndexChanged.connect(self._on_set_changed)
        self._load_sets_combo()
        form.addRow(tr("design_size_set_label") + tr("field_colon"), self.cmb_set)

        # ── المقاس (instance) ──
        self.cmb_instance = QComboBox()
        self.cmb_instance.setMinimumHeight(SIZE_DLG_FIELD_H)
        self.cmb_instance.currentIndexChanged.connect(self._on_instance_changed)
        form.addRow(tr("design_size_instance_label") + tr("field_colon"), self.cmb_instance)

        # ── حقل العرض ──
        self.cmb_width = QComboBox()
        self.cmb_width.setMinimumHeight(SIZE_DLG_FIELD_H)
        self.cmb_width.currentIndexChanged.connect(self._update_canvas_preview)
        form.addRow(tr("design_size_width_label") + tr("field_colon"), self.cmb_width)

        # ── حقل الطول ──
        self.cmb_height = QComboBox()
        self.cmb_height.setMinimumHeight(SIZE_DLG_FIELD_H)
        self.cmb_height.currentIndexChanged.connect(self._update_canvas_preview)
        form.addRow(tr("design_size_height_label") + tr("field_colon"), self.cmb_height)

        # ── حقل الـ DPI ──
        self.cmb_dpi = QComboBox()
        self.cmb_dpi.setMinimumHeight(SIZE_DLG_FIELD_H)
        self.cmb_dpi.currentIndexChanged.connect(self._update_canvas_preview)
        form.addRow(tr("design_size_dpi_label") + tr("field_colon"), self.cmb_dpi)

        # ── معاينة الكانفاس ──
        self.lbl_canvas = QLabel(tr("design_size_canvas_dash"))
        self.lbl_canvas.setStyleSheet(f"""
            color: {_C['success']}; font-weight: bold; font-size: {FS_BASE}px;
            background: {_C['success_bg']}; border: {SIZE_DLG_CANVAS_BORDER_W}px solid {_C['success_border']};
            border-radius: {SIZE_DLG_CANVAS_RADIUS}px; padding: {SIZE_DLG_CANVAS_PAD_V}px {SIZE_DLG_CANVAS_PAD_H}px;
        """)
        form.addRow(tr("design_size_canvas_label") + tr("field_colon"), self.lbl_canvas)

        # ── مسار ملف GIMP ──
        path_row = QHBoxLayout()
        self.inp_path = QLineEdit()
        self.inp_path.setPlaceholderText(tr("design_size_gimp_placeholder"))
        self.inp_path.setMinimumHeight(SIZE_DLG_FIELD_H)
        btn_browse = QPushButton(tr("design_size_gimp_browse_icon"))
        btn_browse.setFixedSize(SIZE_DLG_BROWSE_BTN_SIZE, SIZE_DLG_BROWSE_BTN_SIZE)
        btn_browse.setToolTip(tr("design_size_gimp_browse_tooltip"))
        btn_browse.clicked.connect(self._browse_xcf)
        btn_browse.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent_light']}; border: {SIZE_DLG_BROWSE_BORDER_W}px solid {_C['accent_mid']};
                border-radius: {SIZE_DLG_BROWSE_RADIUS}px; font-size: {FS_MD}px;
            }}
            QPushButton:hover {{ background: {_C['accent_mid']}; }}
        """)
        path_row.addWidget(self.inp_path)
        path_row.addWidget(btn_browse)
        form.addRow(tr("design_size_gimp_path_label") + tr("field_colon"), path_row)

        # ── ملاحظات ──
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText(tr("notes"))
        self.inp_notes.setMinimumHeight(SIZE_DLG_FIELD_H)
        form.addRow(tr("notes") + tr("field_colon"), self.inp_notes)

        root.addLayout(form)

        # ── أزرار ──
        btns = QDialogButtonBox()
        btn_ok     = btns.addButton(tr("design_size_dlg_save_btn"),   QDialogButtonBox.AcceptRole)
        btn_cancel = btns.addButton(tr("design_size_dlg_cancel_btn"), QDialogButtonBox.RejectRole)
        btn_ok.setMinimumHeight(SIZE_DLG_BTN_H)
        btn_cancel.setMinimumHeight(SIZE_DLG_BTN_H)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background: {_C['accent']}; color: {_C['btn_primary_text']}; border: none;
                border-radius: {SIZE_DLG_BTN_OK_RADIUS}px; padding: {SIZE_DLG_BTN_OK_PAD_V}px {SIZE_DLG_BTN_OK_PAD_H}px; font-weight: bold;
            }}
            QPushButton:hover {{ background: {_C['accent_hover']}; }}
        """)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_input']}; color: {_C['accent']};
                border: {SIZE_DLG_BROWSE_BORDER_W}px solid {_C['accent_mid']}; border-radius: {SIZE_DLG_BTN_OK_RADIUS}px;
                padding: {SIZE_DLG_BTN_CANCEL_PAD_V}px {SIZE_DLG_BTN_CANCEL_PAD_H}px;
            }}
            QPushButton:hover {{ background: {_C['accent_light']}; }}
        """)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    # ── تحميل combos ──

    def _load_sets_combo(self):
        self.cmb_set.blockSignals(True)
        self.cmb_set.clear()
        self.cmb_set.addItem(tr("design_size_select_set"), None)
        for ds in self._svc.list_sets():
            self.cmb_set.addItem(ds["name"], ds["id"])
        self.cmb_set.blockSignals(False)

    def _on_set_changed(self):
        set_id = self.cmb_set.currentData()
        self.cmb_instance.clear()
        self.cmb_width.clear()
        self.cmb_height.clear()
        self.lbl_canvas.setText(tr("design_size_canvas_dash"))

        if not set_id:
            return

        # instances
        self.cmb_instance.addItem(tr("design_size_select_instance"), None)
        for inst in self._svc.list_instances(set_id):
            name = inst["name"].strip() or f"#{inst['id']}"
            self.cmb_instance.addItem(name, inst["id"])

        # حقول رقمية للعرض والطول والـ DPI
        self.cmb_width.addItem(tr("design_size_select_width"), None)
        self.cmb_height.addItem(tr("design_size_select_height"), None)
        self.cmb_dpi.addItem(tr("design_size_select_dpi"), None)

        for f in self._svc.list_fields(set_id):
            if f["field_type"] == "number":
                label = f"{f['label']} ({f['unit'] or 'cm'})"
                self.cmb_width.addItem(label, f["id"])
                self.cmb_height.addItem(label, f["id"])
                self.cmb_dpi.addItem(label, f["id"])

    def _on_instance_changed(self):
        self._update_canvas_preview()

    def _update_canvas_preview(self):
        """يحسب ويعرض مقاس الكانفاس بناءً على الاختيارات الحالية."""
        inst_id = self.cmb_instance.currentData()
        w_fid   = self.cmb_width.currentData()
        h_fid   = self.cmb_height.currentData()
        dpi_fid = self.cmb_dpi.currentData()

        if not inst_id or not w_fid or not h_fid:
            self.lbl_canvas.setText(tr("design_size_canvas_dash"))
            return

        w_val = h_val = dpi_val = None

        # جلب القيم من service
        w_val = self._svc.get_field_value(inst_id, w_fid)
        h_val = self._svc.get_field_value(inst_id, h_fid)

        # جلب قيمة الـ DPI لو محدد
        if dpi_fid:
            dpi_val = self._svc.get_field_value(inst_id, dpi_fid)

        if w_val is not None and h_val is not None:
            # جلب الوحدة الافتراضية للمجموعة
            set_id = self.cmb_set.currentData()
            unit = self._svc.get_set_default_unit(set_id) if set_id else "cm"

            if dpi_val:
                w_px = _to_px_preview(w_val, unit, dpi_val)
                h_px = _to_px_preview(h_val, unit, dpi_val)
                self.lbl_canvas.setText(
                    tr("design_size_canvas_with_dpi").format(
                        w=f"{w_val:g}", h=f"{h_val:g}", unit=unit,
                        w_px=w_px, h_px=h_px, dpi=f"{dpi_val:g}"
                    )
                )
                self.lbl_canvas.setStyleSheet(f"""
                    color: {_C['success']}; font-weight: bold; font-size: {FS_BASE}px;
                    background: {_C['success_bg']}; border: {SIZE_DLG_CANVAS_BORDER_W}px solid {_C['success_border']};
                    border-radius: {SIZE_DLG_CANVAS_RADIUS}px; padding: {SIZE_DLG_CANVAS_PAD_V}px {SIZE_DLG_CANVAS_PAD_H}px;
                """)
            else:
                self.lbl_canvas.setText(
                    tr("design_size_canvas_no_dpi").format(
                        w=f"{w_val:g}", h=f"{h_val:g}", unit=unit
                    )
                )
                self.lbl_canvas.setStyleSheet(f"""
                    color: {_C['warning']}; font-weight: bold; font-size: {FS_BASE}px;
                    background: {_C['warning_bg']}; border: {SIZE_DLG_CANVAS_BORDER_W}px solid {_C['warning_border']};
                    border-radius: {SIZE_DLG_CANVAS_RADIUS}px; padding: {SIZE_DLG_CANVAS_PAD_V}px {SIZE_DLG_CANVAS_PAD_H}px;
                """)
        else:
            self.lbl_canvas.setText(tr("design_size_canvas_incomplete"))
            self.lbl_canvas.setStyleSheet(f"""
                color: {_C['warning']}; font-weight: bold; font-size: {FS_BASE}px;
                background: {_C['warning_bg']}; border: {SIZE_DLG_CANVAS_BORDER_W}px solid {_C['warning_border']};
                border-radius: {SIZE_DLG_CANVAS_RADIUS}px; padding: {SIZE_DLG_CANVAS_PAD_V}px {SIZE_DLG_CANVAS_PAD_H}px;
            """)

    def _browse_xcf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, tr("design_size_card_link_file_title"),
            os.path.expanduser("~"),
            tr("design_size_card_gimp_filter")
        )
        if path:
            self.inp_path.setText(path)

    def _load(self, d):
        """تحميل بيانات مقاس موجود."""
        # مجموعة المقاسات
        for i in range(self.cmb_set.count()):
            if self.cmb_set.itemData(i) == d["set_id"]:
                self.cmb_set.setCurrentIndex(i)
                break
        self._on_set_changed()

        # instance
        for i in range(self.cmb_instance.count()):
            if self.cmb_instance.itemData(i) == d["instance_id"]:
                self.cmb_instance.setCurrentIndex(i)
                break

        # حقول العرض والطول والـ DPI
        for i in range(self.cmb_width.count()):
            if self.cmb_width.itemData(i) == d["width_field_id"]:
                self.cmb_width.setCurrentIndex(i)
                break
        for i in range(self.cmb_height.count()):
            if self.cmb_height.itemData(i) == d["height_field_id"]:
                self.cmb_height.setCurrentIndex(i)
                break

        # حقل الـ DPI — اختياري
        dpi_fid = d["dpi_field_id"] if d["dpi_field_id"] else None
        if dpi_fid:
            for i in range(self.cmb_dpi.count()):
                if self.cmb_dpi.itemData(i) == dpi_fid:
                    self.cmb_dpi.setCurrentIndex(i)
                    break

        self.inp_path.setText(d["xcf_path"] or "")
        self.inp_notes.setText(d["notes"] or "")
        self._update_canvas_preview()

    def _save(self):
        set_id    = self.cmb_set.currentData()
        inst_id   = self.cmb_instance.currentData()
        w_fid     = self.cmb_width.currentData()
        h_fid     = self.cmb_height.currentData()
        dpi_fid   = self.cmb_dpi.currentData()          # اختياري — ممكن يكون None
        path      = self.inp_path.text().strip()
        notes     = self.inp_notes.text().strip()

        if not set_id:
            QMessageBox.warning(self, tr("warning"), tr("design_size_choose_set"))
            return
        if not inst_id:
            QMessageBox.warning(self, tr("warning"), tr("design_size_choose_instance"))
            return

        # تحقق من التكرار
        if self._svc.is_instance_used(self.design_id, inst_id, exclude_size_id=self.size_id):
            QMessageBox.warning(self, tr("warning"), tr("design_size_already_used"))
            return

        if self.size_id:
            self._svc.update_size(self.size_id, w_fid, h_fid, path, notes, dpi_field_id=dpi_fid)
        else:
            self.size_id = self._svc.create_size(
                self.design_id, set_id, inst_id,
                w_fid, h_fid, path, notes,
                dpi_field_id=dpi_fid
            )
        self.accept()


# ══════════════════════════════════════════════════════════
# دالة مساعدة للمعاينة
# ══════════════════════════════════════════════════════════

def _to_px_preview(value: float, unit: str, dpi: float) -> int:
    """تحويل القيمة لـ px للعرض في المعاينة."""
    u = unit.strip().lower()
    if u == "px":
        return max(1, int(round(value)))
    elif u == "mm":
        return max(1, int(round(value / 25.4 * dpi)))
    elif u == "cm":
        return max(1, int(round(value / 2.54 * dpi)))
    elif u == "m":
        return max(1, int(round(value / 0.0254 * dpi)))
    elif u in ("inch", "in"):
        return max(1, int(round(value * dpi)))
    return max(1, int(round(value)))