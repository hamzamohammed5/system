"""
ui/settings_dialog.py
=====================
نافذة الإعدادات — حجم الخط + مسار GIMP.
"""

import os
from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QDialogButtonBox,
    QLineEdit, QFileDialog, QGroupBox,
)

from ui.app_settings import get_font_size, set_font_size, apply_font
from db.shared.connection import get_connection
from db.settings_repo import get_setting, set_setting


class SettingsDialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app           = app
        self._original_size = get_font_size()
        self._conn          = get_connection()

        self.setWindowTitle("⚙️  إعدادات")
        self.setFixedWidth(480)
        self.setModal(True)
        self._build()
        self._slider.setValue(self._original_size)
        self._load_settings()

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(16)
        root.setContentsMargins(20, 20, 20, 20)

        # ══ قسم الخط ══════════════════════════════════════
        font_group = QGroupBox("حجم الخط")
        font_lay   = QVBoxLayout(font_group)

        row = QHBoxLayout()
        row.setSpacing(8)

        lbl_small = QLabel("أ")
        lbl_small.setStyleSheet("font-size: 9pt;")

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(8, 20)
        self._slider.setTickInterval(1)
        self._slider.setTickPosition(QSlider.TicksBelow)
        self._slider.valueChanged.connect(self._on_font_change)

        lbl_big = QLabel("أ")
        lbl_big.setStyleSheet("font-size: 15pt; font-weight: bold;")

        self._lbl_val = QLabel("11 pt")
        self._lbl_val.setMinimumWidth(44)
        self._lbl_val.setAlignment(Qt.AlignCenter)

        row.addWidget(lbl_small)
        row.addWidget(self._slider, stretch=1)
        row.addWidget(lbl_big)
        row.addSpacing(8)
        row.addWidget(self._lbl_val)
        font_lay.addLayout(row)

        self._preview = QLabel("معاينة النص — Preview 123")
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setStyleSheet(
            "border: 1px solid #ccc; border-radius: 6px; padding: 12px;"
        )
        font_lay.addWidget(self._preview)
        root.addWidget(font_group)

        # ══ قسم GIMP ══════════════════════════════════════
        gimp_group = QGroupBox("مسار برنامج GIMP")
        gimp_lay   = QVBoxLayout(gimp_group)
        gimp_lay.setSpacing(6)

        gimp_row = QHBoxLayout()
        gimp_row.setSpacing(6)

        self._inp_gimp = QLineEdit()
        self._inp_gimp.setPlaceholderText(
            r"مثال: C:\Program Files\GIMP 2\bin\gimp-2.10.exe"
        )
        self._inp_gimp.setMinimumHeight(34)

        btn_browse = QPushButton("📂  تصفح")
        btn_browse.setMinimumHeight(34)
        btn_browse.setStyleSheet("""
            QPushButton {
                background: #1565c0; color: white;
                border: none; border-radius: 6px;
                padding: 4px 14px; font-weight: bold;
            }
            QPushButton:hover { background: #0d47a1; }
        """)
        btn_browse.clicked.connect(self._browse_gimp)

        btn_clear = QPushButton("✖")
        btn_clear.setFixedSize(34, 34)
        btn_clear.setToolTip("مسح المسار")
        btn_clear.setStyleSheet("""
            QPushButton {
                background: #fdecea; color: #c62828;
                border: 1px solid #ef9a9a; border-radius: 6px;
            }
            QPushButton:hover { background: #ffcdd2; }
        """)
        btn_clear.clicked.connect(lambda: self._inp_gimp.clear())

        gimp_row.addWidget(self._inp_gimp, stretch=1)
        gimp_row.addWidget(btn_browse)
        gimp_row.addWidget(btn_clear)
        gimp_lay.addLayout(gimp_row)

        lbl_hint = QLabel("💡  اتركه فارغاً للبحث التلقائي في المسارات الشائعة")
        lbl_hint.setStyleSheet(
            "color: #888; font-size: 10px; background: transparent;"
        )
        gimp_lay.addWidget(lbl_hint)
        root.addWidget(gimp_group)

        # ══ أزرار ══════════════════════════════════════════
        btns       = QDialogButtonBox()
        btn_ok     = btns.addButton("✅  حفظ",   QDialogButtonBox.AcceptRole)
        btn_cancel = btns.addButton("✖  إلغاء", QDialogButtonBox.RejectRole)
        btn_ok.setMinimumHeight(34)
        btn_cancel.setMinimumHeight(34)
        btn_ok.clicked.connect(self._save)
        btn_cancel.clicked.connect(self._cancel)
        root.addWidget(btns)

    def _load_settings(self):
        try:
            path = get_setting(self._conn, "gimp_path", "")
            self._inp_gimp.setText(path)
        except Exception:
            pass

    def _browse_gimp(self):
        start = self._inp_gimp.text().strip()
        if start and os.path.exists(os.path.dirname(start)):
            start_dir = os.path.dirname(start)
        else:
            start_dir = r"C:\Program Files"

        path, _ = QFileDialog.getOpenFileName(
            self,
            "اختر ملف GIMP التنفيذي",
            start_dir,
            "GIMP (gimp*.exe);;Executable Files (*.exe);;All Files (*)"
        )
        if path:
            self._inp_gimp.setText(path)

    def _on_font_change(self, val: int):
        self._lbl_val.setText(f"{val} pt")
        apply_font(self._app, val)
        self._preview.setStyleSheet(
            f"font-size: {val}pt; border: 1px solid #ccc; "
            "border-radius: 6px; padding: 12px;"
        )

    def _save(self):
        size = self._slider.value()
        set_font_size(size)
        apply_font(self._app, size)

        try:
            set_setting(self._conn, "gimp_path", self._inp_gimp.text().strip())
        except Exception:
            pass

        self.accept()

    def _cancel(self):
        apply_font(self._app, self._original_size)
        self.reject()

    def closeEvent(self, event):
        try:
            self._conn.close()
        except Exception:
            pass
        super().closeEvent(event)