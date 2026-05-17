"""
ui/widgets/shared/panels.py
============================
مكونات UI مشتركة قابلة لإعادة الاستخدام في كل الأقسام.

المكونات:
  StatCard        — بطاقة إحصائية (أيقونة + عنوان + قيمة + تلوين ديناميكي)
  SectionHeader   — رأس قسم أفقي مع عنوان وأزرار
  EmptyState      — رسالة "لا توجد بيانات" مع أيقونة وزر اختياري
  BadgeLabel      — شارة ملونة (حالة، أولوية، نوع)
  ActionToolbar   — شريط أزرار إجراءات موحد
  InfoRow         — صف معلومات أفقي (label: value)
  CollapsibleCard — بطاقة قابلة للطي

الاستخدام:
    from ui.widgets.shared.panels import StatCard, SectionHeader, EmptyState

    card = StatCard("💰", "الإجمالي", color="#1565c0")
    card.set_value("1,200 ج")

    header = SectionHeader("📦 بنود الطلب")
    header.add_button("➕ إضافة", callback=self._add)

    empty = EmptyState("📋", "لا توجد بنود", "اضغط إضافة لبدء")
"""

from PyQt5.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QSizePolicy,
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui  import QFont, QColor

from ui.app_settings import _C, get_font_size, fs


# ══════════════════════════════════════════════════════════
# ثوابت داخلية
# ══════════════════════════════════════════════════════════

def _base() -> int:
    return get_font_size()


# ══════════════════════════════════════════════════════════
# StatCard — بطاقة إحصائية
# ══════════════════════════════════════════════════════════

class StatCard(QFrame):
    """
    بطاقة إحصائية قابلة للتخصيص.

    المعاملات:
        icon    : أيقونة (emoji أو نص)
        title   : عنوان البطاقة
        value   : القيمة الأولية (تُحدَّث بـ set_value)
        color   : لون القيمة والأيقونة
        bg      : لون الخلفية (None = يُحسب تلقائياً)
        border  : لون الحدود (None = يُحسب تلقائياً)
        compact : حجم أصغر للمساحات الضيقة

    المثال:
        card = StatCard("💰", "الإجمالي", color="#1565c0")
        card.set_value("1,200 ج")
        card.set_color("#e53935")   # تغيير اللون ديناميكياً
    """

    def __init__(self, icon: str = "", title: str = "",
                 value: str = "─", color: str = "#1565c0",
                 bg: str = None, border: str = None,
                 compact: bool = False, parent=None):
        super().__init__(parent)
        self._color   = color
        self._compact = compact
        self._build(icon, title, value, color, bg, border)

    def _build(self, icon, title, value, color, bg, border):
        # خلفية وحدود تلقائية لو مش محددة
        _bg     = bg     or self._lighten(color)
        _border = border or self._midtone(color)

        self.setStyleSheet(f"""
            QFrame {{
                background: {_bg};
                border: 1px solid {_border};
                border-radius: 8px;
            }}
        """)

        lay = QVBoxLayout(self)
        p = (8, 6, 8, 6) if self._compact else (12, 10, 12, 10)
        lay.setContentsMargins(*p)
        lay.setSpacing(2 if self._compact else 4)

        # صف الأيقونة والقيمة
        top_row = QHBoxLayout()
        top_row.setSpacing(6)

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setStyleSheet("background:transparent; border:none;")
            top_row.addWidget(lbl_icon)

        top_row.addStretch()

        base = _base()
        self._lbl_value = QLabel(value)
        f = QFont()
        f.setPointSize(fs(base, +3) if not self._compact else fs(base, +1))
        f.setBold(True)
        self._lbl_value.setFont(f)
        self._lbl_value.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )
        self._lbl_value.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        top_row.addWidget(self._lbl_value)
        lay.addLayout(top_row)

        # العنوان
        self._lbl_title = QLabel(title)
        self._lbl_title.setStyleSheet(
            f"color:{color}; font-weight:600;"
            "background:transparent; border:none;"
        )
        lay.addWidget(self._lbl_title)

    def set_value(self, text: str):
        """تحديث القيمة المعروضة."""
        self._lbl_value.setText(text)

    def set_color(self, color: str):
        """تغيير لون القيمة والعنوان ديناميكياً."""
        self._color = color
        self._lbl_value.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )
        self._lbl_title.setStyleSheet(
            f"color:{color}; font-weight:600;"
            "background:transparent; border:none;"
        )

    def value_label(self) -> QLabel:
        """إرجاع الـ QLabel الخاص بالقيمة للتعديل المباشر."""
        return self._lbl_value

    @staticmethod
    def _lighten(hex_color: str) -> str:
        """يحول اللون لخلفية فاتحة جداً."""
        _map = {
            "#1565c0": "#e8f0fe", "#0d47a1": "#e3f2fd",
            "#10b981": "#ecfdf5", "#2e7d32": "#e8f5e9",
            "#ef4444": "#fef2f2", "#dc2626": "#fef2f2",
            "#c62828": "#ffebee", "#f59e0b": "#fffbeb",
            "#e65100": "#fff3e0", "#6b7280": "#f9fafb",
            "#8b5cf6": "#f5f3ff", "#6a1b9a": "#f3e5f5",
        }
        return _map.get(hex_color, "#f5f5f5")

    @staticmethod
    def _midtone(hex_color: str) -> str:
        """يحول اللون لحد متوسط."""
        _map = {
            "#1565c0": "#90caf9", "#0d47a1": "#64b5f6",
            "#10b981": "#a7f3d0", "#2e7d32": "#a5d6a7",
            "#ef4444": "#fecaca", "#dc2626": "#fca5a5",
            "#c62828": "#ef9a9a", "#f59e0b": "#fde68a",
            "#e65100": "#ffcc80", "#6b7280": "#e5e7eb",
            "#8b5cf6": "#ddd6fe", "#6a1b9a": "#ce93d8",
        }
        return _map.get(hex_color, "#e0e0e0")


# ══════════════════════════════════════════════════════════
# SectionHeader — رأس قسم
# ══════════════════════════════════════════════════════════

class SectionHeader(QWidget):
    """
    رأس قسم أفقي مع عنوان وأزرار.

    المثال:
        hdr = SectionHeader("📦 بنود الطلب")
        hdr.add_button("➕ إضافة", callback=self._add, style="success")
        hdr.add_button("🗑️ حذف",  callback=self._del, style="danger")
        layout.addWidget(hdr)
    """

    def __init__(self, title: str = "", parent=None):
        super().__init__(parent)
        self._build(title)

    def _build(self, title):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(8)

        self._lbl = QLabel(title)
        base = _base()
        self._lbl.setStyleSheet(
            f"font-weight:bold; font-size:{fs(base,+1)}pt;"
            f"color:{_C['text_sec']}; background:transparent;"
        )
        lay.addWidget(self._lbl)
        lay.addStretch()

        self._btn_container = lay   # نضيف الأزرار عليه

    def set_title(self, title: str):
        self._lbl.setText(title)

    def add_button(self, text: str, callback=None,
                   style: str = "normal") -> QPushButton:
        """
        يضيف زر للـ header.
        style: "normal" | "primary" | "success" | "danger" | "ghost"
        """
        btn = _make_btn(text, style)
        if callback:
            btn.clicked.connect(callback)
        self._btn_container.addWidget(btn)
        return btn


# ══════════════════════════════════════════════════════════
# EmptyState — رسالة "لا توجد بيانات"
# ══════════════════════════════════════════════════════════

class EmptyState(QFrame):
    """
    رسالة "لا توجد بيانات" مع أيقونة ونص وزر اختياري.

    المثال:
        empty = EmptyState(
            icon="📦",
            title="لا توجد بنود",
            subtitle="اضغط ＋ إضافة بند لبدء",
            style="dashed",   # "dashed" | "solid" | "plain"
            color="#10b981",
        )
        layout.addWidget(empty)
    """

    action_clicked = pyqtSignal()

    def __init__(self, icon: str = "📋",
                 title: str = "لا توجد بيانات",
                 subtitle: str = "",
                 action_text: str = "",
                 style: str = "dashed",
                 color: str = "#10b981",
                 min_height: int = 80,
                 parent=None):
        super().__init__(parent)
        self._build(icon, title, subtitle, action_text, style, color, min_height)

    def _build(self, icon, title, subtitle, action_text, style, color, min_h):
        _light = StatCard._lighten(color)
        _mid   = StatCard._midtone(color)

        if style == "dashed":
            border_style = "dashed"
        elif style == "solid":
            border_style = "solid"
        else:
            border_style = "none"

        self.setStyleSheet(f"""
            QFrame {{
                background: {_light};
                border: 2px {border_style} {_mid};
                border-radius: 8px;
            }}
        """)
        self.setMinimumHeight(min_h)

        lay = QVBoxLayout(self)
        lay.setAlignment(Qt.AlignCenter)
        lay.setSpacing(4)

        if icon:
            lbl_icon = QLabel(icon)
            lbl_icon.setAlignment(Qt.AlignCenter)
            lbl_icon.setStyleSheet(
                "background:transparent; border:none; font-size:22px;"
            )
            lay.addWidget(lbl_icon)

        lbl_title = QLabel(title)
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_title.setStyleSheet(
            f"color:{color}; font-weight:600; background:transparent; border:none;"
        )
        lay.addWidget(lbl_title)

        if subtitle:
            lbl_sub = QLabel(subtitle)
            lbl_sub.setAlignment(Qt.AlignCenter)
            lbl_sub.setStyleSheet(
                f"color:{StatCard._midtone(color)}; background:transparent; border:none;"
            )
            lay.addWidget(lbl_sub)

        if action_text:
            btn = _make_btn(action_text, "success")
            btn.clicked.connect(self.action_clicked.emit)
            lay.addWidget(btn, alignment=Qt.AlignCenter)


# ══════════════════════════════════════════════════════════
# BadgeLabel — شارة ملونة
# ══════════════════════════════════════════════════════════

class BadgeLabel(QLabel):
    """
    شارة ملونة للحالات والأولويات والأنواع.

    المثال:
        badge = BadgeLabel()
        badge.set_badge("✅ مؤكد", text_color="#1d4ed8",
                        bg="#eff6ff", border="#bfdbfe")

        # أو بالاختصار:
        badge.set_status("confirmed")  # لو استخدمت STATUS_CONFIG
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignCenter)
        self._apply_base_style()

    def _apply_base_style(self, text_color="#555", bg="#f5f5f5", border="#e0e0e0"):
        self.setStyleSheet(
            f"font-weight:bold; padding:3px 12px;"
            f"border-radius:10px; color:{text_color};"
            f"background:{bg}; border:1px solid {border};"
        )

    def set_badge(self, text: str, text_color: str = "#555",
                  bg: str = "#f5f5f5", border: str = "#e0e0e0"):
        """تعيين نص وألوان الشارة."""
        self.setText(text)
        self._apply_base_style(text_color, bg, border)

    def clear_badge(self):
        self.setText("")
        self._apply_base_style()


# ══════════════════════════════════════════════════════════
# InfoRow — صف معلومات
# ══════════════════════════════════════════════════════════

class InfoRow(QWidget):
    """
    صف أفقي لعرض بيانات: أيقونة + نص.
    يُستخدم في هيدرات التفاصيل.

    المثال:
        row = InfoRow()
        row.set_parts(["👤 محمد أحمد (C-001)", "📞 01234567890", "📍 القاهرة"])
        layout.addWidget(row)
    """

    def __init__(self, separator: str = "   |   ", parent=None):
        super().__init__(parent)
        self._separator = separator
        self._lbl = QLabel()
        self._lbl.setStyleSheet(
            f"color:{_C['text_muted']}; background:transparent;"
        )
        self._lbl.setWordWrap(True)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._lbl)

    def set_parts(self, parts: list[str]):
        """تعيين أجزاء الصف."""
        filtered = [p for p in parts if p]
        self._lbl.setText(self._separator.join(filtered) if filtered else "")

    def set_text(self, text: str):
        self._lbl.setText(text)

    def label(self) -> QLabel:
        return self._lbl


# ══════════════════════════════════════════════════════════
# ActionToolbar — شريط أزرار موحد
# ══════════════════════════════════════════════════════════

class ActionToolbar(QWidget):
    """
    شريط أزرار أفقي مع فصل بين الأزرار الأساسية والخطرة.

    المثال:
        toolbar = ActionToolbar()

        # أزرار أساسية (يسار RTL)
        btn_edit   = toolbar.add_action("✏️ تعديل", "primary", self._edit)
        btn_status = toolbar.add_action("🔄 الحالة", "ghost",   self._status)

        # أزرار خطرة (يمين RTL)
        btn_del = toolbar.add_danger("🗑️ حذف", self._delete)

        layout.addWidget(toolbar)
    """

    def __init__(self, spacing: int = 6, parent=None):
        super().__init__(parent)
        self._spacing = spacing
        self._build()

    def _build(self):
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        lay.setSpacing(self._spacing)

        self._left_lay  = QHBoxLayout()
        self._left_lay.setSpacing(self._spacing)

        self._right_lay = QHBoxLayout()
        self._right_lay.setSpacing(self._spacing)

        lay.addLayout(self._left_lay)
        lay.addStretch()

        # فاصل عمودي
        self._sep = QFrame()
        self._sep.setFrameShape(QFrame.VLine)
        self._sep.setStyleSheet(f"color:{_C['border']}; background:{_C['border']};")
        self._sep.setFixedWidth(1)
        self._sep.setVisible(False)
        lay.addWidget(self._sep)

        lay.addLayout(self._right_lay)

    def add_action(self, text: str, style: str = "normal",
                   callback=None, enabled: bool = True) -> QPushButton:
        """يضيف زر في المنطقة الأساسية (يسار)."""
        btn = _make_btn(text, style)
        btn.setEnabled(enabled)
        if callback:
            btn.clicked.connect(callback)
        self._left_lay.addWidget(btn)
        return btn

    def add_danger(self, text: str, callback=None,
                   enabled: bool = True) -> QPushButton:
        """يضيف زر خطر في المنطقة اليمنى مع ظهور الفاصل."""
        btn = _make_btn(text, "danger")
        btn.setEnabled(enabled)
        if callback:
            btn.clicked.connect(callback)
        self._right_lay.addWidget(btn)
        self._sep.setVisible(True)
        return btn

    def add_separator(self):
        """يضيف فاصل بين الأزرار الأساسية."""
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet(f"color:{_C['border']};")
        self._left_lay.addWidget(sep)


# ══════════════════════════════════════════════════════════
# CollapsibleCard — بطاقة قابلة للطي
# ══════════════════════════════════════════════════════════

class CollapsibleCard(QFrame):
    """
    بطاقة مع رأس قابل للنقر لطي/فرد المحتوى.

    المثال:
        card = CollapsibleCard("📜 سجل الحالة")
        card.content_layout.addWidget(my_table)
        layout.addWidget(card)
    """

    toggled = pyqtSignal(bool)   # True = مفتوح

    def __init__(self, title: str = "", expanded: bool = True,
                 accent: str = "#1565c0", parent=None):
        super().__init__(parent)
        self._expanded = expanded
        self._accent   = accent
        self._build(title)

    def _build(self, title):
        self.setStyleSheet(f"""
            QFrame {{
                background: {_C['bg_surface']};
                border: 1px solid {_C['border']};
                border-radius: 8px;
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── رأس قابل للنقر ──
        self._header_btn = QPushButton()
        self._header_btn.setCursor(Qt.PointingHandCursor)
        self._header_btn.clicked.connect(self._toggle)
        self._header_btn.setStyleSheet(f"""
            QPushButton {{
                background: {_C['bg_surface_2']};
                border: none;
                border-radius: 8px 8px 0 0;
                padding: 8px 14px;
                text-align: right;
                font-weight: bold;
                color: {_C['text_sec']};
            }}
            QPushButton:hover {{
                background: {_C['bg_hover']};
            }}
        """)
        self._update_header(title)
        root.addWidget(self._header_btn)

        # ── المحتوى ──
        self._content_widget = QWidget()
        self._content_widget.setStyleSheet("background:transparent;")
        self.content_layout = QVBoxLayout(self._content_widget)
        self.content_layout.setContentsMargins(10, 8, 10, 10)
        self.content_layout.setSpacing(6)
        self._content_widget.setVisible(self._expanded)
        root.addWidget(self._content_widget)

    def _update_header(self, title: str):
        arrow = "▼" if self._expanded else "▶"
        self._header_btn.setText(f"{arrow}  {title}")
        self._title = title

    def _toggle(self):
        self._expanded = not self._expanded
        self._content_widget.setVisible(self._expanded)
        self._update_header(self._title)
        self.toggled.emit(self._expanded)

    def set_expanded(self, expanded: bool):
        if self._expanded != expanded:
            self._toggle()


# ══════════════════════════════════════════════════════════
# دالة مساعدة لبناء الأزرار
# ══════════════════════════════════════════════════════════

def _make_btn(text: str, style: str = "normal") -> QPushButton:
    """يبني زر بستايل موحد."""
    btn = QPushButton(text)
    btn.setMinimumHeight(30)
    btn.setCursor(Qt.PointingHandCursor)

    base = _base()

    styles = {
        "primary": f"""
            QPushButton {{
                background: {_C['accent_light']}; color: {_C['accent_text']};
                border: 1px solid {_C['accent_mid']}; border-radius: 6px;
                padding: 0 14px; font-weight: bold; font-size:{fs(base,0)}pt;
            }}
            QPushButton:hover {{ background: #bbdefb; }}
            QPushButton:disabled {{ background: {_C['bg_surface_2']}; color: {_C['text_disabled']}; border-color: {_C['border']}; }}
        """,
        "success": f"""
            QPushButton {{
                background: #ecfdf5; color: #065f46;
                border: 1px solid #a7f3d0; border-radius: 6px;
                padding: 0 14px; font-weight: bold; font-size:{fs(base,0)}pt;
            }}
            QPushButton:hover {{ background: #d1fae5; }}
            QPushButton:disabled {{ background: {_C['bg_surface_2']}; color: {_C['text_disabled']}; border-color: {_C['border']}; }}
        """,
        "danger": f"""
            QPushButton {{
                background: #fef2f2; color: #dc2626;
                border: 1px solid #fecaca; border-radius: 6px;
                padding: 0 14px; font-size:{fs(base,0)}pt;
            }}
            QPushButton:hover {{ background: #fee2e2; }}
            QPushButton:disabled {{ background: {_C['bg_surface_2']}; color: {_C['text_disabled']}; border-color: {_C['border']}; }}
        """,
        "ghost": f"""
            QPushButton {{
                background: {_C['bg_surface']}; color: {_C['text_sec']};
                border: 1px solid {_C['border_med']}; border-radius: 6px;
                padding: 0 14px; font-size:{fs(base,0)}pt;
            }}
            QPushButton:hover {{ background: {_C['accent_light']}; color: {_C['accent_text']}; border-color: {_C['accent_mid']}; }}
            QPushButton:disabled {{ background: {_C['bg_surface_2']}; color: {_C['text_disabled']}; border-color: {_C['border']}; }}
        """,
        "normal": f"""
            QPushButton {{
                background: {_C['bg_surface_2']}; color: {_C['text_sec']};
                border: 1px solid {_C['border']}; border-radius: 6px;
                padding: 0 14px; font-size:{fs(base,0)}pt;
            }}
            QPushButton:hover {{ background: {_C['bg_hover']}; }}
            QPushButton:disabled {{ background: {_C['bg_surface_2']}; color: {_C['text_disabled']}; border-color: {_C['border']}; }}
        """,
    }
    btn.setStyleSheet(styles.get(style, styles["normal"]))
    return btn


# ══════════════════════════════════════════════════════════
# DetailHeader — هيدر صفحة التفاصيل الكاملة
# ══════════════════════════════════════════════════════════

class DetailHeader(QFrame):
    """
    هيدر موحد لصفحات التفاصيل (طلب، عميل، منتج، ...).

    الهيكل:
      [رقم/عنوان]  [شارة النوع]    [شارة الأولوية] [شارة الحالة]
      [معلومات ثانوية (هاتف، مدينة، ...)]
      [بطاقات إحصائية]
      [شريط أزرار]

    المثال:
        hdr = DetailHeader()
        hdr.set_title("ORD-2026-0001")
        hdr.set_type_badge("📋 جديد")
        hdr.set_status_badge("✅ مؤكد", "#1d4ed8", "#eff6ff", "#bfdbfe")
        hdr.set_info(["👤 محمد", "📞 01234567"])

        # بطاقات الإحصائيات
        hdr.add_stat_card("💰", "الإجمالي",  color="#1565c0")
        hdr.add_stat_card("✅", "المدفوع",  color="#10b981")

        # أزرار
        hdr.toolbar.add_action("✏️ تعديل", "primary", self._edit)
        hdr.toolbar.add_danger("🗑️ حذف", self._delete)
    """

    def __init__(self, bg: str = "#ffffff", border_color: str = None,
                 parent=None):
        super().__init__(parent)
        self._stat_cards: list[StatCard] = []
        self._build(bg, border_color or _C['border'])

    def _build(self, bg, border_color):
        self.setStyleSheet(f"""
            QFrame {{
                background: {bg};
                border-bottom: 2px solid {border_color};
            }}
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(8)

        # ── صف 1: العنوان + الشارات ──
        title_row = QHBoxLayout()
        title_row.setSpacing(8)

        self._lbl_title = QLabel("─")
        f = QFont()
        f.setPointSize(fs(_base(), +2))
        f.setBold(True)
        self._lbl_title.setFont(f)
        self._lbl_title.setStyleSheet(
            f"color:{_C['text_primary']}; background:transparent; border:none;"
        )

        self._lbl_type = QLabel("")
        self._lbl_type.setStyleSheet(
            f"color:{_C['text_muted']}; background:transparent; border:none;"
        )

        self._badge_status   = BadgeLabel()
        self._badge_priority = QLabel("")
        self._badge_priority.setStyleSheet(
            "background:transparent; border:none;"
        )

        title_row.addWidget(self._lbl_title)
        title_row.addWidget(self._lbl_type)
        title_row.addStretch()
        title_row.addWidget(self._badge_priority)
        title_row.addWidget(self._badge_status)
        root.addLayout(title_row)

        # ── صف 2: معلومات ثانوية ──
        self._info_row = InfoRow()
        root.addWidget(self._info_row)

        # ── صف 3: بطاقات الإحصائيات ──
        self._cards_row = QHBoxLayout()
        self._cards_row.setSpacing(8)
        root.addLayout(self._cards_row)

        # ── صف 4: شريط الأزرار ──
        self.toolbar = ActionToolbar()
        root.addWidget(self.toolbar)

    # ── API ──

    def set_title(self, text: str):
        self._lbl_title.setText(text)

    def set_type_badge(self, text: str, color: str = None):
        self._lbl_type.setText(text)
        if color:
            self._lbl_type.setStyleSheet(f"color:{color}; background:transparent; border:none;")

    def set_status_badge(self, text: str, text_color: str = "#555",
                         bg: str = "#f5f5f5", border: str = "#e0e0e0"):
        self._badge_status.set_badge(text, text_color, bg, border)

    def set_priority_badge(self, text: str, color: str = "#6b7280"):
        self._badge_priority.setText(text)
        self._badge_priority.setStyleSheet(
            f"color:{color}; background:transparent; border:none;"
        )

    def set_info(self, parts: list[str]):
        self._info_row.set_parts(parts)

    def add_stat_card(self, icon: str, title: str, value: str = "─",
                      color: str = "#1565c0", compact: bool = True) -> StatCard:
        """يضيف بطاقة إحصائية ويرجعها للتحديث لاحقاً."""
        card = StatCard(icon, title, value, color, compact=compact)
        self._cards_row.addWidget(card, stretch=1)
        self._stat_cards.append(card)
        return card

    def clear_stat_cards(self):
        """يمسح كل البطاقات الإحصائية."""
        for card in self._stat_cards:
            self._cards_row.removeWidget(card)
            card.deleteLater()
        self._stat_cards.clear()