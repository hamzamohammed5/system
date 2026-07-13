
"""
ui/tabs/design/designs/designs_table/_design_card.py  — v3
===============================================
قائمة التصميمات — Grid Cards محسّن.

التغييرات عن v2:
  - _fetch_designs_filtered: الـ first_xcf بيتحدد حسب set_id المفلتر
    (أول ملف من المجموعة المطلوبة، وإلا fallback لأول ملف عموماً)
  - _DesignCard: يستقبل set_id ويدعم update_set_filter لتحديث الـ thumbnail
  - _DesignsTable._on_set_changed: يعمل apply_filter كامل عند تغيير المجموعة
"""

from PyQt5.QtWidgets import (
    QVBoxLayout,
    QLabel
)
from PyQt5.QtCore  import Qt, pyqtSignal, QThread, pyqtSignal as Signal, QTimer
from PyQt5.QtGui   import QPixmap, QFont

from ui.widgets.panels.themed_inputs import ThemedFrame

from services.design import get_design_service
from .._xcf_thumbnail import get_xcf_thumbnail
from ui.widgets.core.widget_mixin import WidgetMixin
from ui.widgets.core.i18n import tr
from ui.font import fs, FS_XS
from ui.theme import _C
from ui.constants import (
    DESIGN_CARD_W, DESIGN_CARD_THUMB,
    DESIGN_CARD_RADIUS, DESIGN_CARD_RADIUS_SM,
    DESIGN_CARD_BADGE_X_OFFSET, DESIGN_CARD_BADGE_Y,
    DESIGN_CARD_BADGE_W, DESIGN_CARD_BADGE_H, DESIGN_CARD_BADGE_RADIUS,
    DESIGN_CARD_INFO_MARGIN_H, DESIGN_CARD_INFO_MARGIN_T,
    DESIGN_CARD_INFO_MARGIN_B, DESIGN_CARD_INFO_SPACING,
)

import os

# ── Layout Constants ──────────────────────────────────────────────
_CARD_W      = DESIGN_CARD_W
_CARD_THUMB  = DESIGN_CARD_THUMB
_RADIUS      = DESIGN_CARD_RADIUS
_RADIUS_SM   = DESIGN_CARD_RADIUS_SM


# ════════════════════════════════════════════════════════
# Worker — تحميل الـ thumbnail في الخلفية
# ════════════════════════════════════════════════════════

class _ThumbWorker(QThread):
    done = Signal(str, object)  # xcf_path, QPixmap|None

    def __init__(self, xcf_path: str, size: int = _CARD_THUMB):
        super().__init__()
        self._path = xcf_path
        self._size = size

    def run(self):
        try:
            px = get_xcf_thumbnail(self._path, self._size)
        except Exception:
            px = None
        self.done.emit(self._path, px)


# ════════════════════════════════════════════════════════
# بطاقة تصميم واحد
# ════════════════════════════════════════════════════════

class _DesignCard(ThemedFrame, WidgetMixin):
    selected = pyqtSignal(int)
    deleted  = pyqtSignal(int)

    def __init__(self, conn, design_data, set_id=None, parent=None):
        super().__init__(parent)
        self._init_widget_mixin(lang=False, data=False)
        self.conn      = conn
        self._svc      = get_design_service(conn)
        self._data     = dict(design_data)
        self._did      = self._data["id"]
        self._set_id   = set_id
        self._selected = False
        self._worker   = None
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedWidth(_CARD_W)
        self._build()

    def _refresh_style(self, *_):
        """يُعيد بناء الـ stylesheet عند تغيير الثيم أو الخط."""
        self._update_style()
        if hasattr(self, '_lbl_name'):
            self._apply_name_font()
        if hasattr(self, '_thumb_frame'):
            self._apply_thumb_style()
        if hasattr(self, '_thumb_lbl'):
            self._apply_thumb_lbl_style()

    def _apply_name_font(self, size: int = None):
        """يحدّث خط اسم التصميم ديناميكياً عند تغيير حجم الخط من الإعدادات."""
        from ui.font import get_font_size
        size = size or get_font_size()
        font_n = QFont()
        font_n.setPointSize(fs(size, -2))
        font_n.setWeight(QFont.Medium)
        self._lbl_name.setFont(font_n)

    def _apply_thumb_style(self):
        """يُنسّق إطار الـ thumbnail (الخلفية + الحواف العلوية المدوّرة)."""
        self._thumb_frame.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: none;
                border-top-left-radius: {_RADIUS};
                border-top-right-radius: {_RADIUS};
            }}
        """)

    def _apply_thumb_lbl_style(self):
        """يُنسّق الـ label اللي بيعرض الصورة أو الأيقونة البديلة."""
        self._thumb_lbl.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border: none;
                color: {_C['text_muted']};
                font-size: {fs(FS_XS, 6)}px;
            }}
        """)

    def _apply_badge_style(self, badge: QLabel):
        """يُنسّق شارة عدد المقاسات فوق الـ thumbnail."""
        badge.setStyleSheet(f"""
            QLabel {{
                background: {_C['accent']};
                color: {_C['bg_input']};
                border: none;
                border-radius: {DESIGN_CARD_BADGE_RADIUS}px;
                font-weight: bold;
                font-size: {FS_XS}px;
            }}
        """)

    def _build(self):
        self._update_style()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── منطقة الـ Thumbnail ──
        thumb_frame = ThemedFrame()
        thumb_frame.setFixedSize(_CARD_W, _CARD_THUMB)
        self._thumb_frame = thumb_frame
        self._apply_thumb_style()

        self._thumb_lbl = QLabel(thumb_frame)
        self._thumb_lbl.setFixedSize(_CARD_W, _CARD_THUMB)
        self._thumb_lbl.setAlignment(Qt.AlignCenter)
        self._apply_thumb_lbl_style()
        self._thumb_lbl.setText(tr("design_card_thumb_placeholder_icon"))

        # badge عدد المقاسات
        sz_cnt = self._data.get("sizes_count") or 0
        if sz_cnt:
            badge = QLabel(f"{sz_cnt}", thumb_frame)
            badge.setGeometry(
                _CARD_W - DESIGN_CARD_BADGE_X_OFFSET,
                DESIGN_CARD_BADGE_Y,
                DESIGN_CARD_BADGE_W,
                DESIGN_CARD_BADGE_H,
            )
            badge.setAlignment(Qt.AlignCenter)
            self._apply_badge_style(badge)

        root.addWidget(thumb_frame)

        # ── معلومات التصميم ──
        info = ThemedFrame()
        info.setStyleSheet("QFrame{background:transparent; border:none;}")
        info_lay = QVBoxLayout(info)
        info_lay.setContentsMargins(
            DESIGN_CARD_INFO_MARGIN_H,
            DESIGN_CARD_INFO_MARGIN_T,
            DESIGN_CARD_INFO_MARGIN_H,
            DESIGN_CARD_INFO_MARGIN_B,
        )
        info_lay.setSpacing(DESIGN_CARD_INFO_SPACING)

        name = self._data.get("name", "")
        self._lbl_name = QLabel(name)
        self._lbl_name.setWordWrap(True)
        self._lbl_name.setStyleSheet(
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )
        self._apply_name_font()
        info_lay.addWidget(self._lbl_name)

        cat = self._data.get("category_name") or ""
        if cat:
            lbl_cat = QLabel(cat)
            font_c = QFont()
            font_c.setPointSize(fs(FS_XS, -2))
            lbl_cat.setFont(font_c)
            lbl_cat.setStyleSheet(
                f"color:{_C['text_muted']}; background:transparent; border:none;"
            )
            info_lay.addWidget(lbl_cat)

        fl_cnt = self._data.get("files_count") or 0
        if sz_cnt:
            if fl_cnt == sz_cnt:
                status_col  = _C['success']
                status_text = tr("design_card_status_all_files").format(count=fl_cnt, total=sz_cnt)
            elif fl_cnt > 0:
                status_col  = _C['warning']
                status_text = tr("design_card_status_partial_files").format(count=fl_cnt, total=sz_cnt)
            else:
                status_col  = _C['text_muted']
                status_text = tr("design_card_status_no_files").format(count=sz_cnt)

            lbl_status = QLabel(status_text)
            font_s = QFont()
            font_s.setPointSize(fs(FS_XS, -2))
            lbl_status.setFont(font_s)
            lbl_status.setStyleSheet(
                f"color:{status_col}; background:transparent; border:none;"
            )
            info_lay.addWidget(lbl_status)

        root.addWidget(info)

    # ── Thumbnail API ──────────────────────────────────────

    def set_thumbnail(self, pixmap):
        """يعرض الـ pixmap في الـ thumbnail."""
        if pixmap and not pixmap.isNull():
            scaled = pixmap.scaled(
                _CARD_W, _CARD_THUMB,
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            self._thumb_lbl.setPixmap(scaled)
            self._thumb_lbl.setText("")
        else:
            self._thumb_lbl.setPixmap(QPixmap())
            self._thumb_lbl.setText(tr("design_card_thumb_placeholder_icon"))

    def load_thumbnail(self, xcf_path: str = None):
        """
        يحمّل الـ thumbnail في الخلفية.
        لو xcf_path مش ممرر → يحسبه من DB حسب _set_id.
        """
        if xcf_path is None:
            xcf_path = self._svc.get_first_xcf_for_design(self._did, self._set_id)

        if not xcf_path or not os.path.exists(xcf_path):
            self.set_thumbnail(None)
            return

        if self._worker and self._worker.isRunning():
            self._worker.quit()
            self._worker.wait()

        self._worker = _ThumbWorker(xcf_path, _CARD_THUMB)
        self._worker.done.connect(lambda _p, px: self.set_thumbnail(px))
        self._worker.start()

    def update_set_filter(self, set_id):
        """يُستدعى لما يتغير فلتر المجموعة — يعيد تحميل الـ thumbnail."""
        self._set_id = set_id
        self.load_thumbnail()

    # ── Style ──────────────────────────────────────────────

    def set_selected(self, sel: bool):
        self._selected = sel
        self._update_style()

    def _update_style(self):
        if self._selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {_C['accent_light']};
                    border: 2px solid {_C['accent']};
                    border-radius: {_RADIUS};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame {{
                    background: {_C['bg_input']};
                    border: 1px solid {_C['border']};
                    border-radius: {_RADIUS};
                }}
                QFrame:hover {{
                    border-color: {_C['accent_mid']};
                    background: {_C['accent_light']};
                }}
            """)

    def mousePressEvent(self, event):
        self.selected.emit(self._did)
        super().mousePressEvent(event)

