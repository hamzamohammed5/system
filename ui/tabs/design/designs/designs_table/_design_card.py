
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
    QLabel, QFrame
)
from PyQt5.QtCore  import Qt, pyqtSignal, QThread, pyqtSignal as Signal, QTimer
from PyQt5.QtGui   import QPixmap, QFont

from db.designs.design_item_categories_repo import (
    fetch_item_category_descendants,
)
from .._xcf_thumbnail import get_xcf_thumbnail
from ui.theme import _C
from ui.widgets.core.i18n import tr
from ui.font import get_font_size, fs, FS_XS

import os

# ── Layout Constants ──────────────────────────────────────────────
_CARD_W      = 172
_CARD_THUMB  = 128
_RADIUS      = "10px"
_RADIUS_SM   = "6px"


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
# دالة مساعدة: أول xcf حسب المجموعة
# ════════════════════════════════════════════════════════

def _get_xcf_for_set(conn, design_id: int, set_id=None) -> "str | None":
    """
    يجيب مسار الـ xcf المناسب للتصميم:
      - لو set_id محدد → أول ملف ينتمي لهذه المجموعة
      - fallback      → أول ملف موجود عموماً بغض النظر عن المجموعة
    يرجع None لو مفيش ملف.
    """
    if set_id is not None:
        row = conn.execute(
            """
            SELECT xcf_path FROM design_sizes
            WHERE  design_id = ?
              AND  set_id    = ?
              AND  xcf_path IS NOT NULL
              AND  xcf_path != ''
            ORDER  BY sort_order, id
            LIMIT  1
            """,
            (design_id, set_id),
        ).fetchone()
        if row and row["xcf_path"]:
            return row["xcf_path"]

    # fallback: أول ملف موجود بغض النظر عن المجموعة
    row = conn.execute(
        """
        SELECT xcf_path FROM design_sizes
        WHERE  design_id = ?
          AND  xcf_path IS NOT NULL
          AND  xcf_path != ''
        ORDER  BY sort_order, id
        LIMIT  1
        """,
        (design_id,),
    ).fetchone()
    return row["xcf_path"] if row and row["xcf_path"] else None


# ════════════════════════════════════════════════════════
# جلب التصميمات مع فلترة
# ════════════════════════════════════════════════════════

def _fetch_designs_filtered(conn, name_q="", category_id=None, set_id=None):
    """
    جلب التصميمات مع فلترة بالاسم والتصنيف والمجموعة.

    first_xcf: يأخذ أولوية المجموعة المفلترة لو محددة (مع fallback لأول ملف عموماً).
    set_id يُدمج في الـ SQL بشكل آمن بعد int() cast.
    """
    if set_id is not None:
        set_id_int = int(set_id)
        first_xcf_sql = f"""
            COALESCE(
                (SELECT ds2.xcf_path
                 FROM   design_sizes ds2
                 WHERE  ds2.design_id = d.id
                   AND  ds2.set_id    = {set_id_int}
                   AND  ds2.xcf_path IS NOT NULL
                   AND  ds2.xcf_path != ''
                 ORDER  BY ds2.sort_order, ds2.id
                 LIMIT  1),
                (SELECT ds3.xcf_path
                 FROM   design_sizes ds3
                 WHERE  ds3.design_id = d.id
                   AND  ds3.xcf_path IS NOT NULL
                   AND  ds3.xcf_path != ''
                 ORDER  BY ds3.sort_order, ds3.id
                 LIMIT  1)
            )
        """
    else:
        first_xcf_sql = """
            (SELECT ds2.xcf_path
             FROM   design_sizes ds2
             WHERE  ds2.design_id = d.id
               AND  ds2.xcf_path IS NOT NULL
               AND  ds2.xcf_path != ''
             ORDER  BY ds2.sort_order, ds2.id
             LIMIT  1)
        """

    sql = f"""
        SELECT d.id, d.name, d.item_category_id, d.notes,
               d.created_at, d.updated_at,
               ic.name                              AS category_name,
               ic.color                             AS category_color,
               COUNT(DISTINCT ds.id)                AS sizes_count,
               SUM(CASE WHEN ds.xcf_path IS NOT NULL
                             AND ds.xcf_path != ''
                        THEN 1 ELSE 0 END)          AS files_count,
               {first_xcf_sql}                      AS first_xcf
        FROM   designs d
        LEFT JOIN design_item_categories ic ON ic.id = d.item_category_id
        LEFT JOIN design_sizes ds           ON ds.design_id = d.id
    """
    conditions, params = [], []

    if name_q:
        conditions.append("d.name LIKE ?")
        params.append(f"%{name_q}%")

    if category_id is not None:
        try:
            desc = fetch_item_category_descendants(conn, category_id)
            ph   = ",".join("?" * len(desc))
            conditions.append(f"d.item_category_id IN ({ph})")
            params.extend(desc)
        except Exception:
            conditions.append("d.item_category_id = ?")
            params.append(category_id)

    if set_id is not None:
        conditions.append(
            "EXISTS (SELECT 1 FROM design_sizes ds2 "
            "WHERE ds2.design_id = d.id AND ds2.set_id = ?)"
        )
        params.append(set_id)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " GROUP BY d.id ORDER BY d.updated_at DESC, d.name"
    return conn.execute(sql, params).fetchall()


# ════════════════════════════════════════════════════════
# بطاقة تصميم واحد
# ════════════════════════════════════════════════════════

class _DesignCard(QFrame):
    selected = pyqtSignal(int)
    deleted  = pyqtSignal(int)

    def __init__(self, conn, design_data, set_id=None, parent=None):
        super().__init__(parent)
        self.conn      = conn
        self._data     = dict(design_data)
        self._did      = self._data["id"]
        self._set_id   = set_id
        self._selected = False
        self._worker   = None
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedWidth(_CARD_W)
        self._build()

    def _build(self):
        self._update_style()
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── منطقة الـ Thumbnail ──
        thumb_frame = QFrame()
        thumb_frame.setFixedSize(_CARD_W, _CARD_THUMB)
        thumb_frame.setStyleSheet(f"""
            QFrame {{
                background: {_C['design_thumb_bg']};
                border-radius: {_RADIUS} {_RADIUS} 0 0;
            }}
        """)

        self._thumb_lbl = QLabel(thumb_frame)
        self._thumb_lbl.setFixedSize(_CARD_W, _CARD_THUMB)
        self._thumb_lbl.setAlignment(Qt.AlignCenter)
        self._thumb_lbl.setStyleSheet(
            f"background:transparent; font-size:{fs(FS_XS,+18)}px; color:{_C['design_thumb_icon']};"
        )
        self._thumb_lbl.setText("🎨")

        # badge عدد المقاسات
        sz_cnt = self._data.get("sizes_count") or 0
        if sz_cnt:
            badge = QLabel(f"{sz_cnt}", thumb_frame)
            badge.setGeometry(_CARD_W - 30, 8, 22, 18)
            badge.setAlignment(Qt.AlignCenter)
            badge.setStyleSheet(
                f"background:rgba(0,0,0,0.55); color:{_C['card_badge_text']};"
                f"border-radius:9px; font-size:{fs(FS_XS,-1)}px; font-weight:700;"
                "border:1px solid rgba(255,255,255,0.2);"
            )

        root.addWidget(thumb_frame)

        # ── معلومات التصميم ──
        info = QFrame()
        info.setStyleSheet("QFrame{background:transparent; border:none;}")
        info_lay = QVBoxLayout(info)
        info_lay.setContentsMargins(10, 8, 10, 10)
        info_lay.setSpacing(3)

        name = self._data.get("name", "")
        lbl_name = QLabel(name)
        lbl_name.setWordWrap(True)
        font_n = QFont()
        font_n.setPointSize(fs(get_font_size(), -2))
        font_n.setWeight(QFont.Medium)
        lbl_name.setFont(font_n)
        lbl_name.setStyleSheet(
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )
        info_lay.addWidget(lbl_name)

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
            self._thumb_lbl.setText("🎨")

    def load_thumbnail(self, xcf_path: str = None):
        """
        يحمّل الـ thumbnail في الخلفية.
        لو xcf_path مش ممرر → يحسبه من DB حسب _set_id.
        """
        if xcf_path is None:
            xcf_path = _get_xcf_for_set(self.conn, self._did, self._set_id)

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

