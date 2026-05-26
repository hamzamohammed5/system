"""
ui/widgets/panels/notify.py
============================
مكونات الإشعارات والتحذيرات:

  NotificationBar — شريط إشعارات مؤقت (success/info/warning/danger)
  BaseWarningBar  — شريط تحذير ثابت مع أزرار إصلاح وتعديل
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore    import QTimer, pyqtSignal

from ui.app_settings import fs, get_font_size

_STATUS_COLORS = {
    "success": {"fg": "#065f46", "bg": "#ecfdf5", "border": "#6ee7b7"},
    "warning": {"fg": "#92400e", "bg": "#fffbeb", "border": "#fcd34d"},
    "danger":  {"fg": "#991b1b", "bg": "#fef2f2", "border": "#fca5a5"},
    "info":    {"fg": "#1e40af", "bg": "#eff6ff", "border": "#93c5fd"},
    "neutral": {"fg": "#374151", "bg": "#f9fafb", "border": "#d1d5db"},
}

_NOTIF_ICONS = {
    "success": "✅", "info": "ℹ️", "warning": "⚠️", "danger": "❌",
}


def _make_btn(text: str, style: str = "normal") -> QPushButton:
    from ..panels._btn import make_btn
    return make_btn(text, style)


def _base() -> int:
    return get_font_size()


# ══════════════════════════════════════════════════════════
# NotificationBar
# ══════════════════════════════════════════════════════════

class NotificationBar(QFrame):
    """شريط إشعارات مؤقت مع دعم الإغلاق والإخفاء التلقائي."""

    dismissed = pyqtSignal()

    def __init__(self, show_dismiss: bool = True, parent=None):
        super().__init__(parent)
        self._show_dismiss = show_dismiss
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide_bar)
        self._build()
        self.setVisible(False)

    def _build(self):
        self.setObjectName("notifBar")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(8)

        self._lbl_icon = QLabel()
        self._lbl_icon.setStyleSheet(
            "background:transparent; border:none; font-size:14px;"
        )
        lay.addWidget(self._lbl_icon)

        self._lbl_msg = QLabel()
        self._lbl_msg.setWordWrap(True)
        self._lbl_msg.setStyleSheet("background:transparent; border:none;")
        lay.addWidget(self._lbl_msg, stretch=1)

        if self._show_dismiss:
            btn = QPushButton("✖")
            btn.setFixedSize(22, 22)
            btn.setStyleSheet(
                "QPushButton{background:transparent;border:none;color:#aaa;}"
                "QPushButton:hover{color:#666;}"
            )
            btn.clicked.connect(self._on_dismiss)
            lay.addWidget(btn)

    def show(self, message: str, level: str = "info", auto_hide: int = 0):
        """
        يعرض الإشعار.
        level: "success" | "info" | "warning" | "danger"
        auto_hide: إخفاء بعد N ms (0 = لا إخفاء تلقائي)
        """
        cfg  = _STATUS_COLORS.get(level, _STATUS_COLORS["info"])
        icon = _NOTIF_ICONS.get(level, "ℹ️")
        base = _base()

        self.setStyleSheet(f"""
            #notifBar {{
                background:{cfg['bg']}; border:1px solid {cfg['border']};
                border-radius:6px;
            }}
        """)
        self._lbl_icon.setText(icon)
        self._lbl_msg.setText(message)
        self._lbl_msg.setStyleSheet(
            f"font-size:{fs(base,0)}pt; font-weight:600;"
            f"color:{cfg['fg']}; background:transparent; border:none;"
        )
        self.setVisible(True)

        if auto_hide > 0:
            self._timer.start(auto_hide)

    def hide_bar(self):
        self._timer.stop()
        self.setVisible(False)

    def _on_dismiss(self):
        self.hide_bar()
        self.dismissed.emit()


# ══════════════════════════════════════════════════════════
# BaseWarningBar
# ══════════════════════════════════════════════════════════

class BaseWarningBar(QFrame):
    """
    شريط تحذير أفقي موحد مع أزرار إصلاح وتعديل.

    Signals:
        fix_clicked  — زر الإصلاح
        edit_clicked — زر التعديل
        dismissed    — زر الإغلاق
    """

    fix_clicked  = pyqtSignal()
    edit_clicked = pyqtSignal()
    dismissed    = pyqtSignal()

    def __init__(self, on_fix=None, on_edit=None,
                 fix_text: str = "🗑️ حذف الناقص",
                 edit_text: str = "✏️ تعديل",
                 show_dismiss: bool = True, parent=None):
        super().__init__(parent)
        self._fix_text  = fix_text
        self._edit_text = edit_text
        self._build(show_dismiss)
        self.setVisible(False)

        if on_fix:
            self.fix_clicked.connect(on_fix)
        if on_edit:
            self.edit_clicked.connect(on_edit)

    def _build(self, show_dismiss: bool):
        s = _STATUS_COLORS["warning"]
        self.setObjectName("warningBar")
        self.setStyleSheet(f"""
            #warningBar {{
                background:{s['bg']}; border:1px solid {s['border']}; border-radius:6px;
            }}
        """)

        lay = QHBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        lay.setSpacing(10)

        lbl_icon = QLabel("⚠️")
        lbl_icon.setStyleSheet("font-size:16px; background:transparent; border:none;")
        lay.addWidget(lbl_icon)

        self._lbl = QLabel()
        self._lbl.setWordWrap(True)
        self._lbl.setStyleSheet(
            f"color:{s['fg']}; font-weight:bold; background:transparent; border:none;"
        )
        lay.addWidget(self._lbl, stretch=1)

        self._btn_fix  = _make_btn(self._fix_text, "danger")
        self._btn_edit = _make_btn(self._edit_text, "primary")
        self._btn_fix.clicked.connect(self.fix_clicked.emit)
        self._btn_edit.clicked.connect(self.edit_clicked.emit)
        lay.addWidget(self._btn_fix)
        lay.addWidget(self._btn_edit)

        if show_dismiss:
            btn_x = _make_btn("✖", "ghost")
            btn_x.clicked.connect(self._on_dismiss)
            lay.addWidget(btn_x)

    def show_message(self, message: str, fix_text: str = None, edit_text: str = None):
        self._lbl.setText(message)
        if fix_text:
            self._btn_fix.setText(fix_text)
        if edit_text:
            self._btn_edit.setText(edit_text)
        self.setVisible(True)

    def show_orphans(self, orphans: list, product_name: str,
                     type_labels: dict = None):
        if not orphans:
            self.setVisible(False)
            return
        _labels = type_labels or {
            "raw": "خامة", "semi": "نصف مصنع",
            "labor_op": "عملية عمالة", "machine_op": "عملية تشغيل",
        }
        lines = [
            f"• {_labels.get(o['child_type'], o['child_type'])}: «{o.get('child_name') or f'ID:{o[\"child_id\"]}'}»"
            for o in orphans
        ]
        msg = f"«{product_name}» — {len(orphans)} مكوّن محذوف:\n" + "  ".join(lines)
        self.show_message(msg)

    def hide_warning(self):
        self.setVisible(False)

    def set_fix_visible(self, v: bool):
        self._btn_fix.setVisible(v)

    def set_edit_visible(self, v: bool):
        self._btn_edit.setVisible(v)

    def _on_dismiss(self):
        self.setVisible(False)
        self.dismissed.emit()