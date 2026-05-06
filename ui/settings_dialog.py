"""
ui/settings_dialog.py
=====================
نافذة إعداد حجم الخط — تُفتح من قايمة Settings.
"""

from PyQt5.QtCore    import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSlider, QDialogButtonBox,
)

from ui.app_settings import get_font_size, set_font_size, apply_font


class SettingsDialog(QDialog):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app          = app
        self._original_size = get_font_size()   # عشان نرجعه لو ضغط إلغاء

        self.setWindowTitle("⚙️  إعدادات الخط")
        self.setFixedWidth(360)
        self.setModal(True)
        self._build()
        self._slider.setValue(self._original_size)

    # ══════════════════════════════════════════════════════
    # بناء الواجهة
    # ══════════════════════════════════════════════════════

    def _build(self):
        root = QVBoxLayout(self)
        root.setSpacing(18)
        root.setContentsMargins(20, 20, 20, 20)

        # ── عنوان ──
        title = QLabel("حجم الخط")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-weight: bold; font-size: 13pt;")
        root.addWidget(title)

        # ── Slider ──
        row = QHBoxLayout()

        lbl_small = QLabel("أ")
        lbl_small.setStyleSheet("font-size: 9pt;")

        self._slider = QSlider(Qt.Horizontal)
        self._slider.setRange(8, 20)
        self._slider.setTickInterval(1)
        self._slider.setTickPosition(QSlider.TicksBelow)
        self._slider.valueChanged.connect(self._on_change)

        lbl_big = QLabel("أ")
        lbl_big.setStyleSheet("font-size: 16pt; font-weight: bold;")

        self._lbl_val = QLabel("11 pt")
        self._lbl_val.setFixedWidth(40)
        self._lbl_val.setAlignment(Qt.AlignCenter)

        row.addWidget(lbl_small)
        row.addWidget(self._slider, stretch=1)
        row.addWidget(lbl_big)
        row.addSpacing(8)
        row.addWidget(self._lbl_val)
        root.addLayout(row)

        # ── معاينة ──
        self._preview = QLabel("معاينة النص — Preview 123")
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setStyleSheet(
            "border: 1px solid #ccc; border-radius: 6px; padding: 12px;"
        )
        root.addWidget(self._preview)

        # ── أزرار ──
        btns = QDialogButtonBox()
        btn_ok     = btns.addButton("✅  حفظ",   QDialogButtonBox.AcceptRole)
        btn_cancel = btns.addButton("✖  إلغاء", QDialogButtonBox.RejectRole)
        btn_ok.clicked.connect(self._save)
        btn_cancel.clicked.connect(self._cancel)
        root.addWidget(btns)

    # ══════════════════════════════════════════════════════
    # منطق
    # ══════════════════════════════════════════════════════

    def _on_change(self, val: int):
        self._lbl_val.setText(f"{val} pt")
        self._preview.setStyleSheet(
            f"font-size: {val}pt; border: 1px solid #ccc; "
            "border-radius: 6px; padding: 12px;"
        )
        # live preview على التطبيق كله
        apply_font(self._app, val)

    def _save(self):
        size = self._slider.value()
        set_font_size(size)
        apply_font(self._app, size)
        self.accept()

    def _cancel(self):
        # ارجع لحجم الخط الأصلي
        apply_font(self._app, self._original_size)
        self.reject()