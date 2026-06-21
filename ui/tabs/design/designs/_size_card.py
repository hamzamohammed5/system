"""
ui/tabs/design/designs/_size_card.py  — v3
==========================================
بطاقة مقاس واحد — تصميم محسّن.

التحسينات:
  - Layout أوضح وأكثر تنظيماً
  - أزرار أصغر وأنظف
  - Status bar أجمل
  - Thumbnail مع rounded corners
  - ألوان Palette موحدة
"""

import os

from PyQt5.QtWidgets import (
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox,
    QFrame, QFileDialog,
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, pyqtSignal as Signal
from PyQt5.QtGui  import QPixmap, QFont

from db.designs.designs_sizes_repo import (
    update_design_size_path,
    fetch_canvas_size,
    fetch_canvas_dpi,
)
from ._xcf_thumbnail import get_watcher
from .size_card.helper import _ThumbnailWidget, _to_px, _unit_for_set, _btn_ss, _open_gimp
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import get_font_size, fs, FS_SM
from ui.widgets.core.events import bus

# ── Layout Constants ──────────────────────────
_RADIUS      = "10px"
_RADIUS_XS   = "4px"

_DEFAULT_DPI = 300.0
_THUMB_SIZE  = 72

# ── Palette من _C ──────────────────────────────────────
_BG          = _C["bg_input"]
_BG_SURFACE  = _C["bg_surface"]
_BORDER      = _C["border"]
_BORDER_MED  = _C["border_med"]
_TEXT_SEC    = _C["text_sec"]
_TEXT_MUT    = _C["text_muted"]
_ACCENT      = _C["accent"]
_ACCENT_DARK = _C["accent_hover"]
_SUCCESS     = _C["success"]
_SUCCESS_LT  = _C["success_bg"]
_SUCCESS_BDR = _C["success_border"]
_DANGER      = _C["danger"]
_DANGER_LT   = _C["danger_bg"]
_DANGER_BDR  = _C["danger_border"]
_WARNING     = _C["warning"]
_WARNING_LT  = _C["warning_bg"]
_WARNING_BDR = _C["warning_border"]



# ════════════════════════════════════════════════════════
# بطاقة مقاس — v3
# ════════════════════════════════════════════════════════

class _SizeCard(QFrame):
    edit_requested   = pyqtSignal(int)
    delete_requested = pyqtSignal(int)
    path_changed     = pyqtSignal()

    def __init__(self, conn, size_data, parent=None):
        super().__init__(parent)
        self.conn     = conn
        self._data    = dict(size_data)
        self._size_id = self._data["id"]
        self._build()

        xcf = self._data.get("xcf_path") or ""
        if xcf and os.path.exists(xcf):
            get_watcher().watch(xcf)
            get_watcher().file_changed.connect(self._on_xcf_changed)

        bus.font_changed.connect(self._apply_name_font)

    def _apply_name_font(self, size: int = None):
        """يحدّث خط اسم المقاس ديناميكياً عند تغيير حجم الخط من الإعدادات."""
        size = size or get_font_size()
        font_n = QFont()
        font_n.setPointSize(fs(size, -1))
        font_n.setWeight(QFont.Medium)
        self._lbl_name.setFont(font_n)

    def _on_xcf_changed(self, path: str):
        xcf = os.path.normpath(self._data.get("xcf_path") or "")
        if os.path.normpath(path) == xcf:
            self._thumb.refresh(path)

    def closeEvent(self, event):
        self._stop_watching()
        super().closeEvent(event)

    def hideEvent(self, event):
        self._stop_watching()
        super().hideEvent(event)

    def _stop_watching(self):
        xcf = self._data.get("xcf_path") or ""
        if xcf:
            try:
                get_watcher().file_changed.disconnect(self._on_xcf_changed)
            except Exception:
                pass

    def _build(self):
        xcf_path    = self._data.get("xcf_path") or ""
        has_file    = bool(xcf_path)
        file_exists = has_file and os.path.exists(xcf_path)

        self.setStyleSheet(f"""
            QFrame {{
                background: {_BG};
                border: 1px solid {_BORDER};
                border-radius: {_RADIUS};
            }}
        """)
        self.setMinimumHeight(90)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── الجزء الرئيسي ──────────────────────────
        main = QFrame()
        main.setStyleSheet("QFrame{background:transparent;border:none;}")
        m_lay = QHBoxLayout(main)
        m_lay.setContentsMargins(12, 12, 12, 12)
        m_lay.setSpacing(12)

        # Thumbnail
        self._thumb = _ThumbnailWidget(xcf_path, size=_THUMB_SIZE)
        m_lay.addWidget(self._thumb)

        # معلومات
        info = QVBoxLayout()
        info.setSpacing(3)
        info.setContentsMargins(0, 0, 0, 0)

        # اسم المقاس + مجموعته
        inst_name = (self._data.get("instance_name") or
                     tr("design_size_card_fallback_name").format(
                         id=self._data.get('instance_id', '')))
        set_name  = self._data.get("set_name", "")

        self._lbl_name = QLabel(inst_name)
        self._apply_name_font()
        self._lbl_name.setStyleSheet(f"color:{_C['text_primary']}; background:transparent;")

        lbl_set = QLabel(set_name)
        lbl_set.setStyleSheet(f"color:{_C['text_muted']}; font-size:{FS_SM}px; background:transparent;")

        # الأبعاد
        w, h = fetch_canvas_size(self.conn, self._size_id)
        unit = _unit_for_set(self.conn, self._data.get("set_id", 0))
        dpi  = fetch_canvas_dpi(self.conn, self._size_id)

        if w is not None and h is not None:
            if dpi:
                w_px = _to_px(w, unit, dpi)
                h_px = _to_px(h, unit, dpi)
                dims = tr("design_size_card_dims_with_dpi").format(
                    w=f"{w:g}", h=f"{h:g}", unit=unit,
                    w_px=f"{w_px:,}", h_px=f"{h_px:,}"
                )
            else:
                dims = tr("design_size_card_dims_no_dpi").format(
                    w=f"{w:g}", h=f"{h:g}", unit=unit
                )
        else:
            dims = tr("design_size_card_dims_unknown")

        lbl_dims = QLabel(dims)
        lbl_dims.setStyleSheet(f"color:{_C['text_sec']}; font-size:{FS_SM}px; background:transparent;")

        info.addWidget(self._lbl_name)
        info.addWidget(lbl_set)
        info.addWidget(lbl_dims)
        info.addStretch()

        m_lay.addLayout(info, stretch=1)

        # أزرار
        btns = QVBoxLayout()
        btns.setSpacing(5)
        btns.setContentsMargins(0, 0, 0, 0)

        # الزر الرئيسي (GIMP)
        if file_exists:
            btn_main = QPushButton(tr("design_size_card_open_gimp_btn"))
            btn_main.setStyleSheet(
                _btn_ss(_ACCENT, _C["accent_text"], _ACCENT, _ACCENT_DARK, height=30)
            )
            btn_main.clicked.connect(self._open_in_gimp)
        else:
            btn_main = QPushButton(tr("design_size_card_create_gimp_btn"))
            btn_main.setStyleSheet(
                _btn_ss(_SUCCESS_LT, _SUCCESS, _SUCCESS_BDR, _SUCCESS_LT, height=30)
            )
            btn_main.clicked.connect(self._create_in_gimp)

        btn_main.setMinimumWidth(120)
        btns.addWidget(btn_main)

        # صف أزرار الإجراءات
        act = QHBoxLayout()
        act.setSpacing(4)

        if not file_exists:
            btn_link = QPushButton(tr("design_size_card_link_file_btn"))
            btn_link.setStyleSheet(
                _btn_ss(_BG_SURFACE, _TEXT_SEC, _BORDER, _BG, height=26)
            )
            btn_link.clicked.connect(self._set_path)
            act.addWidget(btn_link)

        btn_edit = QPushButton("✏")
        btn_edit.setFixedSize(28, 26)
        btn_edit.setToolTip(tr("edit"))
        btn_edit.setStyleSheet(
            _btn_ss(_BG_SURFACE, _TEXT_SEC, _BORDER, _BG, height=26, radius=_RADIUS_XS)
        )
        btn_edit.clicked.connect(lambda: self.edit_requested.emit(self._size_id))

        btn_del = QPushButton("🗑")
        btn_del.setFixedSize(28, 26)
        btn_del.setToolTip(tr("delete"))
        btn_del.setStyleSheet(
            _btn_ss(_DANGER_LT, _DANGER, _DANGER_BDR, _DANGER_LT, height=26, radius=_RADIUS_XS)
        )
        btn_del.clicked.connect(lambda: self.delete_requested.emit(self._size_id))

        act.addStretch()
        act.addWidget(btn_edit)
        act.addWidget(btn_del)

        btns.addLayout(act)
        btns.addStretch()

        m_lay.addLayout(btns)
        root.addWidget(main)

        # ── شريط الحالة ────────────────────────────
        self._build_status_bar(root, file_exists, has_file, unit, dpi)

    def _build_status_bar(self, root, file_exists, has_file, unit, dpi):
        bar = QFrame()

        if file_exists:
            bg     = _SUCCESS_LT
            border = _SUCCESS_BDR
            txt    = tr("design_size_card_file_exists")
            col    = _SUCCESS
        elif has_file:
            bg     = _WARNING_LT
            border = _WARNING_BDR
            txt    = tr("design_size_card_file_missing")
            col    = _WARNING
        else:
            bg     = _BG_SURFACE
            border = _BORDER
            txt    = tr("design_size_card_file_none")
            col    = _TEXT_MUT

        bar.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-top: 1px solid {border};
                border-bottom-left-radius: {_RADIUS};
                border-bottom-right-radius: {_RADIUS};
            }}
        """)

        bl = QHBoxLayout(bar)
        bl.setContentsMargins(12, 5, 12, 5)
        bl.setSpacing(8)

        lbl_s = QLabel(txt)
        lbl_s.setStyleSheet(
            f"color:{col}; font-size:{FS_SM}px; font-weight:600; background:transparent;"
        )

        chips = QHBoxLayout()
        chips.setSpacing(4)
        for chip_txt in [unit, (f"{int(dpi)} DPI" if dpi else "—")]:
            chip = QLabel(chip_txt)
            chip.setStyleSheet(f"""
                QLabel {{
                    background: {_BG};
                    color: {_TEXT_SEC};
                    border: 1px solid {_BORDER_MED};
                    border-radius: 3px;
                    padding: 1px 6px;
                    font-size: {fs(FS_SM, -2)}px;
                }}
            """)
            chips.addWidget(chip)

        bl.addWidget(lbl_s)
        bl.addStretch()
        bl.addLayout(chips)

        root.addWidget(bar)

    # ── GIMP Actions ───────────────────────────────────────

    def _open_in_gimp(self):
        xcf = self._data["xcf_path"]
        if xcf and os.path.exists(xcf):
            get_watcher().watch(xcf)
            _open_gimp(xcf_path=xcf)
        else:
            QMessageBox.warning(
                self, tr("file_not_found"),
                tr("design_size_card_file_not_found_msg").format(path=xcf)
            )

    def _create_in_gimp(self):
        w, h  = fetch_canvas_size(self.conn, self._size_id)
        unit  = _unit_for_set(self.conn, self._data["set_id"])
        dpi   = fetch_canvas_dpi(self.conn, self._size_id) or _DEFAULT_DPI

        inst_name    = (self._data.get("instance_name") or "design").replace(" ", "_")
        default_name = f"{inst_name}.xcf"
        start_dir    = os.path.expanduser("~")

        if self._data.get("xcf_path"):
            parent = os.path.dirname(self._data["xcf_path"])
            if os.path.isdir(parent):
                start_dir = parent

        save_path, _ = QFileDialog.getSaveFileName(
            self, tr("design_size_card_save_gimp_title"),
            os.path.join(start_dir, default_name),
            tr("design_size_card_gimp_filter")
        )
        if not save_path:
            return
        if not save_path.lower().endswith(".xcf"):
            save_path += ".xcf"

        update_design_size_path(self.conn, self._size_id, save_path)
        self._data["xcf_path"] = save_path
        get_watcher().watch(save_path)

        if w and h:
            u = unit.strip().lower()
            actual_dpi = 96.0 if u == "px" else float(dpi)
            w_px = _to_px(w, unit, actual_dpi)
            h_px = _to_px(h, unit, actual_dpi)
            QMessageBox.information(
                self, tr("design_size_card_create_canvas_title"),
                tr("design_size_card_create_canvas_msg").format(
                    w=f"{w:g}", h=f"{h:g}", unit=unit,
                    w_px=f"{w_px:,}", h_px=f"{h_px:,}", dpi=int(actual_dpi), path=save_path
                )
            )
            _open_gimp(xcf_path=save_path, width_val=w, height_val=h,
                       unit=unit, dpi=actual_dpi)
        else:
            _open_gimp()

        self._thumb.refresh(save_path)
        self.path_changed.emit()

    def _set_path(self):
        start_dir = os.path.expanduser("~")
        if self._data.get("xcf_path"):
            parent = os.path.dirname(self._data["xcf_path"])
            if os.path.isdir(parent):
                start_dir = parent

        path, _ = QFileDialog.getOpenFileName(
            self, tr("design_size_card_link_file_title"),
            start_dir, tr("design_size_card_gimp_filter")
        )
        if path:
            old = self._data.get("xcf_path") or ""
            if old:
                get_watcher().unwatch(old)
            update_design_size_path(self.conn, self._size_id, path)
            self._data["xcf_path"] = path
            get_watcher().watch(path)
            self._thumb.refresh(path)
            self.path_changed.emit()