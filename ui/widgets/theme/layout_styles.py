"""
ui/widgets/theme/layout_styles.py
====================================
Stylesheet generators للـ layout widgets (tabs, scroll, tree, list, etc).

[Refactor V3 — المرحلة 10] مستخرج من theme/styles.py.
"""
from PyQt5.QtGui import QFont, QFontMetrics

from ui.theme import _C
from ui.font  import fs, get_font_size
from ui.constants import (
    SCROLL_BAR_WIDTH, SCROLL_HANDLE_MIN_LEN,
    TAB_MIN_W_SMALL, TAB_MIN_W_NORMAL,
    TAB_PAD_V_SMALL, TAB_PAD_H_SMALL, TAB_PAD_V_NORMAL, TAB_PAD_H_NORMAL,
    TAB_INDICATOR_BORDER_W,
    FILTER_TOOLBAR_BORDER_RADIUS, FILTER_BAR_BORDER_RADIUS,
    TREE_BORDER_RADIUS, LIST_BORDER_RADIUS,
    TREE_ITEM_PAD_V, TREE_ITEM_PAD_H,
    LIST_ITEM_PAD_V, LIST_ITEM_PAD_H, LIST_ITEM_BORDER_W,
)


def tab_style(accent: str = None, size: str = "normal") -> str:
    """
    Stylesheet للتبويبات.
    size: "normal" | "inner" | "small"
    """
    base     = get_font_size()
    c        = accent or _C["accent"]
    is_small = size in ("inner", "small")
    padding  = f"{TAB_PAD_V_SMALL}px {TAB_PAD_H_SMALL}px" if is_small else f"{TAB_PAD_V_NORMAL}px {TAB_PAD_H_NORMAL}px"
    font_sz  = fs(base, -1) if is_small else fs(base, 0)
    min_w    = f"{TAB_MIN_W_SMALL}px" if is_small else f"{TAB_MIN_W_NORMAL}px"

    return f"""
        QTabWidget::pane {{ border:none; background:{_C['bg_page']}; }}
        QTabBar::tab {{
            background:{_C['bg_surface_2']}; border:1px solid {_C['border']};
            border-bottom:none; padding:{padding}; margin-left:2px;
            font-size:{font_sz}pt; color:{_C['text_muted']}; min-width:{min_w};
        }}
        QTabBar::tab:selected {{
            background:{_C['bg_input']}; color:{c};
            font-weight:bold; border-top:2px solid {c};
        }}
        QTabBar::tab:hover:!selected {{
            background:{_C['bg_hover']}; color:{_C['text_primary']};
        }}
    """


# [إضافة] حساب عرض تلقائي للتبويبات حسب النص الفعلي — نفس فلسفة
# _calc_btn_width_for_text في components/button.py: القياس الحقيقي
# للنص (QFontMetrics) + الـ "chrome" الفعلي (padding + border) اللي
# tab_style() بترسمه، بدل رقم min-width ثابت في constants.py ممكن
# يبقى أصغر من نصوص عربية/طويلة فيتقص العرض بصريًا (زي ما ظهر في
# تبويبات "منتج نهائي"/"التشغيل" في CostingSection).
# دالة واحدة مركزية هنا — أي قسم عنده QTabWidget يستخدمها بدل ما كل
# قسم يحسب بمنطقه الخاص.
def calc_tab_width(text: str, size: str = "normal", extra_pad: int = 0) -> int:
    """
    يحسب العرض اللازم لتبويب نصه `text` بحيث يبان كامل بدون قص.
    size: "normal" | "inner" | "small" — لازم يطابق نفس size المستخدم
          في tab_style() لنفس الـ QTabWidget.
    """
    base     = get_font_size()
    is_small = size in ("inner", "small")
    pad_h    = TAB_PAD_H_SMALL if is_small else TAB_PAD_H_NORMAL
    font_sz  = fs(base, -1) if is_small else fs(base, 0)

    f = QFont()
    f.setPointSize(font_sz)
    text_w = QFontMetrics(f).horizontalAdvance(text)
    # 2×padding أفقي + حدود يمين/يسار (1px من كل جهة كما في tab_style)
    # + سمك مؤشر التاب النشط (border-top) عشان أي تاب يتحول selected
    # ما يتغيرش حجمه فجأة (القاعدة selected بتضيف border-top إضافي).
    chrome = 2 * pad_h + 2 * 1 + TAB_INDICATOR_BORDER_W
    return int(text_w + chrome + extra_pad)


def apply_tab_widths(tab_widget, size: str = "normal", extra_pad: int = 6) -> None:
    """
    يضبط min-width الفعلي لتبويبات QTabWidget حسب أطول نص موجود فعليًا
    بين كل التبويبات — بيحل مشكلة القص لما min-width الثابت في
    tab_style() (من TAB_MIN_W_NORMAL/SMALL) يبقى أصغر من نص التاب.

    [قيد Qt] QTabBar مالهاش API لعرض مختلف لكل تاب لوحده عبر QSS
    (::tab بينطبق بنفس القاعدة على كل التابس) — فالحل المضمون هو رفع
    min-width العام لأكبر عرض نص فعلي بين كل التبويبات، بدل رقم
    تقريبي ثابت في constants.py.

    الاستخدام (بعد إضافة كل التبويبات بـ addTab):
        self._tabs.setStyleSheet(tab_style())
        apply_tab_widths(self._tabs)

    يُستدعى مرة كل ما تتغير عناوين التبويبات (بناء أولي، تغيير لغة،
    تغيير حجم خط) عشان يعاد الحساب.
    """
    bar = tab_widget.tabBar()
    widths = [calc_tab_width(tab_widget.tabText(i), size=size, extra_pad=extra_pad)
              for i in range(tab_widget.count())]
    if not widths:
        return
    bar.setStyleSheet(bar.styleSheet() + f"\nQTabBar::tab {{ min-width:{max(widths)}px; }}")


# [حل مركزي لتناسق شكل التبويبات] لوحظ إن بعض الأقسام (CostingSection)
# كانت بتضبط خصائص إضافية على مستوى الـ QTabWidget/QTabBar نفسه (مش
# stylesheet) زي setTabPosition/setElideMode/setUsesScrollButtons/
# setDrawBase، بينما أقسام تانية (InventoryTab) كانت من غيرها —
# فرغم استخدام نفس tab_style()، شكل التبويبات كان مختلف بصريًا
# (مثلاً القاعدة السفلية للـ tab bar غير متصلة بصريًا بالمحتوى).
# بدل تكرار نفس الأسطر يدويًا في كل قسم، دالة واحدة هنا تضمن نفس
# السلوك البصري لأي QTabWidget في المشروع.
def normalize_tab_widget(tab_widget) -> None:
    """
    يوحّد إعدادات العرض الأساسية لأي QTabWidget بحيث يتصرف ويظهر بنفس
    الشكل في كل الأقسام — مكمّل لـ tab_style() (الألوان/الحدود) لكنه
    يضبط خصائص مش ممكن التحكم فيها عبر QSS.
    يُستدعى مرة واحدة بعد إنشاء الـ QTabWidget مباشرة (قبل أو بعد
    إضافة التبويبات، لا فرق).
    """
    from PyQt5.QtWidgets import QTabWidget
    from PyQt5.QtCore import Qt

    tab_widget.setTabPosition(QTabWidget.North)
    tab_widget.setUsesScrollButtons(True)
    tab_widget.setElideMode(Qt.ElideNone)

    bar = tab_widget.tabBar()
    bar.setExpanding(False)
    bar.setDrawBase(True)




def scroll_style(width: int = SCROLL_BAR_WIDTH) -> str:
    """Stylesheet موحد لـ QScrollArea / QScrollBar — المصدر الوحيد."""
    r = width // 2
    return f"""
        QScrollArea {{ border:none; background:transparent; }}
        QScrollBar:vertical {{
            background:transparent; width:{width}px; border-radius:{r}px;
        }}
        QScrollBar::handle:vertical {{
            background:{_C['border_med']}; border-radius:{r}px; min-height:{SCROLL_HANDLE_MIN_LEN}px;
        }}
        QScrollBar::handle:vertical:hover {{ background:{_C['border_strong']}; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0px; }}
        QScrollBar:horizontal {{
            background:transparent; height:{width}px; border-radius:{r}px;
        }}
        QScrollBar::handle:horizontal {{
            background:{_C['border_med']}; border-radius:{r}px; min-width:{SCROLL_HANDLE_MIN_LEN}px;
        }}
        QScrollBar::handle:horizontal:hover {{ background:{_C['border_strong']}; }}
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0px; }}
    """


def filter_bar_style() -> str:
    return f"""
        QFrame {{
            background:{_C['bg_surface_2']}; border:1px solid {_C['border']};
            border-radius:{FILTER_BAR_BORDER_RADIUS}px;
        }}
    """


def toolbar_style() -> str:
    return f"""
        QFrame {{
            background:{_C['bg_input']};
            border-bottom:1px solid {_C['border']};
        }}
    """


def tree_style() -> str:
    return f"""
        QTreeWidget {{
            border:1px solid {_C['border']}; border-radius:{TREE_BORDER_RADIUS}px;
            background:{_C['bg_surface']}; outline:none;
            alternate-background-color:{_C['bg_surface_2']};
            color:{_C['text_primary']};
        }}
        QTreeWidget::item {{ padding:{TREE_ITEM_PAD_V}px {TREE_ITEM_PAD_H}px; }}
        QTreeWidget::item:selected {{
            background:{_C['accent_light']}; color:{_C['accent_text']};
        }}
        QTreeWidget::item:hover:!selected {{ background:{_C['bg_hover']}; }}
    """


def list_style() -> str:
    return f"""
        QListWidget {{
            border:1px solid {_C['border']}; border-radius:{LIST_BORDER_RADIUS}px;
            background:{_C['bg_surface']}; outline:none;
        }}
        QListWidget::item {{
            padding:{LIST_ITEM_PAD_V}px {LIST_ITEM_PAD_H}px; border-bottom:{LIST_ITEM_BORDER_W}px solid {_C['border']};
        }}
        QListWidget::item:selected {{
            background:{_C['accent_light']}; color:{_C['accent_text']};
        }}
        QListWidget::item:hover:!selected {{ background:{_C['bg_hover']}; }}
    """
