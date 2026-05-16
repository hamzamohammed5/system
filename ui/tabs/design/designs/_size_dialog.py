"""
ui/tabs/design/designs/_size_dialog.py
==============================
"""

import os


from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit,
    QComboBox, QMessageBox, QDialog, QDialogButtonBox,
    QFileDialog, QFormLayout,
)
from PyQt5.QtCore import Qt

from db.designs.dimension_sets_repo import (
    fetch_all_dimension_sets,
    fetch_fields_for_set,
)

from db.designs.designs_sizes_repo import (
    insert_design_size, update_design_size,
    fetch_instances_for_set_with_values,
    instance_already_used,
)

# ── ألوان ──
_BLUE       = "#1565c0"
_BLUE_LIGHT = "#e8f0fe"
_BLUE_MID   = "#bbdefb"
_GREEN      = "#2e7d32"
_GREEN_LT   = "#e8f5e9"
_GRAY_BG    = "#f8f9fc"


# ══════════════════════════════════════════════════════════
# Dialog — إضافة / تعديل مقاس للتصميم
# ══════════════════════════════════════════════════════════

class _SizeDialog(QDialog):
    """
    Dialog لإضافة أو تعديل مقاس واحد للتصميم.
    يختار: مجموعة مقاسات → instance → حقل العرض → حقل الطول → مسار الملف
    """

    def __init__(self, conn, design_id: int,
                 size_data=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self.design_id = design_id
        self.size_id   = size_data["id"] if size_data else None
        self._size_data = size_data

        self.setWindowTitle("تعديل مقاس" if size_data else "إضافة مقاس جديد")
        self.setMinimumWidth(520)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background: {_GRAY_BG}; }}")
        self._build()
        if size_data:
            self._load(size_data)

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(20, 18, 20, 18)
        root.setSpacing(14)

        # ── رأس ──
        hdr = QLabel("📐  " + ("تعديل مقاس" if self.size_id else "إضافة مقاس جديد"))
        hdr.setStyleSheet(f"""
            font-size: 13px; font-weight: bold; color: {_BLUE};
            background: {_BLUE_LIGHT}; border-radius: 8px; padding: 8px 14px;
        """)
        root.addWidget(hdr)

        form = QFormLayout()
        form.setSpacing(12)
        form.setLabelAlignment(Qt.AlignRight)

        # ── مجموعة المقاسات ──
        self.cmb_set = QComboBox()
        self.cmb_set.setMinimumHeight(34)
        self.cmb_set.currentIndexChanged.connect(self._on_set_changed)
        self._load_sets_combo()
        form.addRow("مجموعة المقاسات :", self.cmb_set)

        # ── المقاس (instance) ──
        self.cmb_instance = QComboBox()
        self.cmb_instance.setMinimumHeight(34)
        self.cmb_instance.currentIndexChanged.connect(self._on_instance_changed)
        form.addRow("المقاس :", self.cmb_instance)

        # ── حقل العرض ──
        self.cmb_width = QComboBox()
        self.cmb_width.setMinimumHeight(34)
        self.cmb_width.currentIndexChanged.connect(self._update_canvas_preview)
        form.addRow("حقل العرض :", self.cmb_width)

        # ── حقل الطول ──
        self.cmb_height = QComboBox()
        self.cmb_height.setMinimumHeight(34)
        self.cmb_height.currentIndexChanged.connect(self._update_canvas_preview)
        form.addRow("حقل الطول :", self.cmb_height)

        # ── معاينة الكانفاس ──
        self.lbl_canvas = QLabel("─")
        self.lbl_canvas.setStyleSheet(f"""
            color: {_GREEN}; font-weight: bold; font-size: 12px;
            background: {_GREEN_LT}; border: 1px solid #a5d6a7;
            border-radius: 6px; padding: 6px 12px;
        """)
        form.addRow("مقاس الكانفاس :", self.lbl_canvas)

        # ── مسار ملف GIMP ──
        path_row = QHBoxLayout()
        self.inp_path = QLineEdit()
        self.inp_path.setPlaceholderText("مسار ملف .xcf — اتركه فارغاً لإنشاء ملف جديد")
        self.inp_path.setMinimumHeight(34)
        btn_browse = QPushButton("📂")
        btn_browse.setFixedSize(34, 34)
        btn_browse.setToolTip("اختر ملف .xcf موجود")
        btn_browse.clicked.connect(self._browse_xcf)
        btn_browse.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE_LIGHT}; border: 1.5px solid {_BLUE_MID};
                border-radius: 6px; font-size: 14px;
            }}
            QPushButton:hover {{ background: {_BLUE_MID}; }}
        """)
        path_row.addWidget(self.inp_path)
        path_row.addWidget(btn_browse)
        form.addRow("مسار ملف GIMP :", path_row)

        # ── ملاحظات ──
        self.inp_notes = QLineEdit()
        self.inp_notes.setPlaceholderText("ملاحظات اختيارية...")
        self.inp_notes.setMinimumHeight(34)
        form.addRow("ملاحظات :", self.inp_notes)

        root.addLayout(form)

        # ── أزرار ──
        btns = QDialogButtonBox()
        btn_ok     = btns.addButton("💾  حفظ",   QDialogButtonBox.AcceptRole)
        btn_cancel = btns.addButton("✖  إلغاء", QDialogButtonBox.RejectRole)
        btn_ok.setMinimumHeight(36)
        btn_cancel.setMinimumHeight(36)
        btn_ok.setStyleSheet(f"""
            QPushButton {{
                background: {_BLUE}; color: white; border: none;
                border-radius: 7px; padding: 6px 20px; font-weight: bold;
            }}
            QPushButton:hover {{ background: #0d47a1; }}
        """)
        btn_cancel.setStyleSheet(f"""
            QPushButton {{
                background: white; color: {_BLUE};
                border: 1.5px solid {_BLUE_MID}; border-radius: 7px; padding: 5px 16px;
            }}
            QPushButton:hover {{ background: {_BLUE_LIGHT}; }}
        """)
        btns.accepted.connect(self._save)
        btns.rejected.connect(self.reject)
        root.addWidget(btns)

    # ── تحميل combos ──

    def _load_sets_combo(self):
        self.cmb_set.blockSignals(True)
        self.cmb_set.clear()
        self.cmb_set.addItem("─ اختر مجموعة مقاسات ─", None)
        for ds in fetch_all_dimension_sets(self.conn):
            self.cmb_set.addItem(ds["name"], ds["id"])
        self.cmb_set.blockSignals(False)

    def _on_set_changed(self):
        set_id = self.cmb_set.currentData()
        self.cmb_instance.clear()
        self.cmb_width.clear()
        self.cmb_height.clear()
        self.lbl_canvas.setText("─")

        if not set_id:
            return

        # instances
        self.cmb_instance.addItem("─ اختر مقاساً ─", None)
        for inst in fetch_instances_for_set_with_values(self.conn, set_id):
            name = inst["name"].strip() or f"مقاس #{inst['id']}"
            self.cmb_instance.addItem(name, inst["id"])

        # حقول رقمية للعرض والطول
        self.cmb_width.addItem("─ اختر حقل العرض ─", None)
        self.cmb_height.addItem("─ اختر حقل الطول ─", None)
        for f in fetch_fields_for_set(self.conn, set_id):
            if f["field_type"] == "number":
                label = f"{f['label']} ({f['unit'] or 'cm'})"
                self.cmb_width.addItem(label, f["id"])
                self.cmb_height.addItem(label, f["id"])

    def _on_instance_changed(self):
        self._update_canvas_preview()

    def _update_canvas_preview(self):
        """يحسب ويعرض مقاس الكانفاس بناءً على الاختيارات الحالية."""
        inst_id  = self.cmb_instance.currentData()
        w_fid    = self.cmb_width.currentData()
        h_fid    = self.cmb_height.currentData()

        if not inst_id or not w_fid or not h_fid:
            self.lbl_canvas.setText("─")
            return

        w_val = h_val = None
        if w_fid:
            r = self.conn.execute(
                "SELECT value_num FROM dimension_set_values WHERE instance_id=? AND field_id=?",
                (inst_id, w_fid)
            ).fetchone()
            w_val = r["value_num"] if r else None

        if h_fid:
            r = self.conn.execute(
                "SELECT value_num FROM dimension_set_values WHERE instance_id=? AND field_id=?",
                (inst_id, h_fid)
            ).fetchone()
            h_val = r["value_num"] if r else None

        if w_val is not None and h_val is not None:
            self.lbl_canvas.setText(f"{w_val:g}  ×  {h_val:g}  px")
        else:
            self.lbl_canvas.setText("⚠️  القيم غير مكتملة في هذا المقاس")

    def _browse_xcf(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "اختر ملف GIMP",
            os.path.expanduser("~"),
            "GIMP Files (*.xcf);;All Files (*)"
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

        # حقول العرض والطول
        for i in range(self.cmb_width.count()):
            if self.cmb_width.itemData(i) == d["width_field_id"]:
                self.cmb_width.setCurrentIndex(i)
                break
        for i in range(self.cmb_height.count()):
            if self.cmb_height.itemData(i) == d["height_field_id"]:
                self.cmb_height.setCurrentIndex(i)
                break

        self.inp_path.setText(d["xcf_path"] or "")
        self.inp_notes.setText(d["notes"] or "")
        self._update_canvas_preview()

    def _save(self):
        set_id    = self.cmb_set.currentData()
        inst_id   = self.cmb_instance.currentData()
        w_fid     = self.cmb_width.currentData()
        h_fid     = self.cmb_height.currentData()
        path      = self.inp_path.text().strip()
        notes     = self.inp_notes.text().strip()

        if not set_id:
            QMessageBox.warning(self, "تنبيه", "اختر مجموعة مقاسات")
            return
        if not inst_id:
            QMessageBox.warning(self, "تنبيه", "اختر المقاس")
            return

        # تحقق من التكرار
        if instance_already_used(self.conn, self.design_id, inst_id,
                                  exclude_size_id=self.size_id):
            QMessageBox.warning(self, "تنبيه", "هذا المقاس مضاف بالفعل لهذا التصميم")
            return

        if self.size_id:
            update_design_size(self.conn, self.size_id, w_fid, h_fid, path, notes)
        else:
            self.size_id = insert_design_size(
                self.conn, self.design_id, set_id, inst_id,
                w_fid, h_fid, path, notes
            )
        self.accept()

