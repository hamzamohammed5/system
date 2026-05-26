"""
ui/widgets/dialogs/shell.py
============================
DialogShell — هيكل نافذة حوار موحد بدون منطق.
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QFrame, QWidget,
)
from PyQt5.QtCore import Qt

from ui.app_settings import _C, fs, get_font_size


class DialogShell(QDialog):
    """
    هيكل نافذة موحد:
      - هيدر ملون مع أيقونة وعنوان
      - منطقة محتوى (body_layout)
      - شريط أزرار (btn_layout)
      - RTL + modal تلقائي
    """

    def __init__(self, parent=None, title: str = "", icon: str = "📋",
                 subtitle: str = "", accent: str = None,
                 min_width: int = 380, min_height: int = 0):
        super().__init__(
            parent,
            Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint,
        )
        self.setWindowTitle(title)
        self.setModal(True)
        self.setMinimumWidth(min_width)
        if min_height:
            self.setMinimumHeight(min_height)
        self.setLayoutDirection(Qt.RightToLeft)
        self._accent = accent or _C['accent']
        self._build(icon, title, subtitle)

    def _build(self, icon: str, title: str, subtitle: str):
        self.setStyleSheet(
            f"QDialog {{ background:{_C['bg_page']}; }}"
        )
        root = QVBoxLayout(self)
        root.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        root.addWidget(self._make_header(icon, title, subtitle))

        body = QWidget()
        body.setStyleSheet(f"background:{_C['bg_page']};")
        self._body_layout = QVBoxLayout(body)
        self._body_layout.setContentsMargins(20, 16, 20, 12)
        self._body_layout.setSpacing(10)
        root.addWidget(body, stretch=1)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{_C['border']}; border:none;")
        root.addWidget(sep)

        bar = QWidget()
        bar.setStyleSheet(f"background:{_C['bg_surface']};")
        bar.setFixedHeight(54)
        self._btn_layout = QHBoxLayout(bar)
        self._btn_layout.setContentsMargins(16, 0, 16, 0)
        self._btn_layout.setSpacing(8)
        self._btn_layout.addStretch()
        root.addWidget(bar)

    def _make_header(self, icon: str, title: str, subtitle: str) -> QFrame:
        a   = self._accent
        hdr = QFrame()
        hdr.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 {a}, stop:1 {a}dd);
                border-bottom:2px solid {a}99;
            }}
        """)
        hdr.setFixedHeight(64 if subtitle else 52)

        lay = QHBoxLayout(hdr)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(10)

        base = get_font_size()

        lbl_ico = QLabel(icon)
        lbl_ico.setStyleSheet(
            f"font-size:{fs(base,+2)}pt; background:transparent; border:none;"
        )
        lbl_ico.setAlignment(Qt.AlignVCenter)
        lay.addWidget(lbl_ico)

        col = QVBoxLayout()
        col.setSpacing(2)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(
            f"font-size:{fs(base,+1)}pt; font-weight:bold; color:white;"
            "background:transparent; border:none;"
        )
        col.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setStyleSheet(
                f"font-size:{fs(base,-1)}pt; color:rgba(255,255,255,0.8);"
                "background:transparent; border:none;"
            )
            col.addWidget(lbl_sub)

        lay.addLayout(col)
        lay.addStretch()
        return hdr

    @property
    def body_layout(self) -> QVBoxLayout:
        return self._body_layout

    @property
    def btn_layout(self) -> QHBoxLayout:
        return self._btn_layout
