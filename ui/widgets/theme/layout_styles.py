"""
ui/widgets/theme/layout_styles.py
====================================
Stylesheet generators للـ layout widgets (tabs, scroll, tree, list, etc).

[Refactor V3 — المرحلة 10] مستخرج من theme/styles.py.
"""
from PyQt5.QtCore import Qt
from ui.theme import _C
from ui.font  import fs, get_font_size
from ui.constants import (
    SCROLL_BAR_WIDTH, SCROLL_HANDLE_MIN_LEN,
    TAB_PAD_V_SMALL, TAB_PAD_H_SMALL, TAB_PAD_V_NORMAL, TAB_PAD_H_NORMAL,
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

    # [Fix] شيل min-width الثابتة — كانت بتفرض نفس العرض على كل
    # التبويبات بغض النظر عن طول نصها الفعلي (زي "العمالة" مقابل
    # "منتج نهائي" بنفس العرض بالظبط)، عكس فلسفة الأزرار (make_btn)
    # اللي بتتحسب من القياس الفعلي للنص. من غيرها، Qt بيحسب عرض كل
    # تبويب تلقائيًا من (عرض النص + padding) — زي الأزرار بالظبط.
    return f"""
        QTabWidget::pane {{ border:none; background:{_C['bg_page']}; }}
        QTabBar::tab {{
            background:{_C['bg_surface_2']}; border:1px solid {_C['border']};
            border-bottom:none; padding:{padding}; margin-left:2px;
            font-size:{font_sz}pt; color:{_C['text_muted']};
        }}
        QTabBar::tab:selected {{
            background:{_C['bg_input']}; color:{c};
            font-weight:bold; border-top:2px solid {c};
        }}
        QTabBar::tab:hover:!selected {{
            background:{_C['bg_hover']}; color:{_C['text_primary']};
        }}
    """


def _tab_bar_natural_width(tab_bar, padding_h: int, font_pt: int) -> int:
    """
    يحسب مجموع عرض كل تبويبات الـ tab_bar فعليًا بـ padding/font
    معيّنين — بنفس منطق _calc_btn_width_for_text في button.py، بس
    لمجموع كل التبويبات مع بعض بدل تبويب واحد.
    """
    from PyQt5.QtGui import QFont, QFontMetrics
    f = QFont(tab_bar.font())
    f.setPointSize(font_pt)
    fm = QFontMetrics(f)
    total = 0
    for i in range(tab_bar.count()):
        text = tab_bar.tabText(i)
        w = fm.boundingRect(text).width() + (padding_h * 2) + 8  # +8: border+margin تقريبي
        total += w
    return total


def _shrink_tabs_to_fit(tabs, size: str) -> None:
    """
    [الحل الجذري] بدل الاعتماد على setUsesScrollButtons — اللي عندها
    مشكلة رسم معروفة مع RTL + custom QSS (الأزرار بتتظهر فعليًا لكن
    التبويبات مش بتتقص عند حدودها، فبترسم برّه المساحة المرئية وتبان
    "مقطوعة" بدل ما تتحول لسكرول سلس) — بنحسب هنا هل مجموع عرض
    التبويبات بعرضها الطبيعي أكبر من العرض المتاح فعليًا للـ tab bar.
    لو أه: مرحلة 1) نقلل الـ padding الأفقي تدريجيًا لحد أدنى معقول.
    لو لسه مش كافي (مساحة ضيقة جدًا زي شاشات صغيرة): مرحلة 2) نقلل
    حجم الخط تدريجيًا كمان لحد أدنى معقول. الاتنين مع بعض يضمنوا إن
    كل التبويبات تفضل ظاهرة كاملة بدون قص، بغض النظر عن ضيق المساحة.
    """
    from ui.constants import TAB_PAD_H_SMALL, TAB_PAD_H_NORMAL
    base = get_font_size()
    is_small  = size in ("inner", "small")
    max_pad_h = TAB_PAD_H_SMALL if is_small else TAB_PAD_H_NORMAL
    max_font  = fs(base, -1) if is_small else fs(base, 0)

    tab_bar = tabs.tabBar()
    if tab_bar.count() == 0:
        return

    available = tabs.width()
    if available <= 0:
        return

    min_pad_h  = 4
    min_font   = 7  # أصغر حجم خط مقروء معقول — حاجز أخير يمنع النص من الانمحاء

    pad_h    = max_pad_h
    font_pt  = max_font

    # مرحلة 1: تقليل الـ padding مع الإبقاء على حجم الخط الأصلي
    while pad_h > min_pad_h and _tab_bar_natural_width(tab_bar, pad_h, font_pt) > available:
        pad_h -= 1

    # مرحلة 2: لو لسه مش كافي حتى بعد أقل padding، نقلل حجم الخط تدريجيًا
    while font_pt > min_font and _tab_bar_natural_width(tab_bar, pad_h, font_pt) > available:
        font_pt -= 1

    pad_v = 6 if is_small else 8
    tabs.setStyleSheet(_tab_style_with_padding(pad_v, pad_h, font_pt, tabs.property("_tab_accent")))
    # [Fix] setStyleSheet وحدها مش كفاية لإجبار QTabBar يعيد حساب
    # tabSizeHint فورًا — من غيرها القياسات القديمة (بالـ padding/font
    # السابقين) بتفضل متسجلة داخليًا لحد ما يحصل حدث resize حقيقي من
    # نظام النوافذ. unpolish+polish بيجبروا Qt يعيد تطبيق الـ style
    # بالكامل فورًا، فالتبويبات تاخد حجمها الجديد الفعلي في نفس اللحظة.
    tab_bar.style().unpolish(tab_bar)
    tab_bar.style().polish(tab_bar)
    tab_bar.updateGeometry()
    tabs.updateGeometry()


def _tab_style_with_padding(pad_v: int, pad_h: int, font_pt: int, accent: str = None) -> str:
    c = accent or _C["accent"]
    return f"""
        QTabWidget::pane {{ border:none; background:{_C['bg_page']}; }}
        QTabBar::tab {{
            background:{_C['bg_surface_2']}; border:1px solid {_C['border']};
            border-bottom:none; padding:{pad_v}px {pad_h}px; margin-left:2px;
            font-size:{font_pt}pt; color:{_C['text_muted']};
        }}
        QTabBar::tab:selected {{
            background:{_C['bg_input']}; color:{c};
            font-weight:bold; border-top:2px solid {c};
        }}
        QTabBar::tab:hover:!selected {{
            background:{_C['bg_hover']}; color:{_C['text_primary']};
        }}
    """


def apply_tab_style(tabs, accent: str = None, size: str = "normal") -> None:
    """
    [نقطة التطبيق المركزية] تُطبّق كل إعدادات التبويب المطلوبة على
    QTabWidget واحد دفعة واحدة، وتضمن إن كل التبويبات تفضل ظاهرة
    بالكامل بدون قص أو تراكب مهما كان عرض الحاوية المتاح:

      1. tab_style() كـ stylesheet أساسي (الألوان/الحجم/الخط).
      2. setElideMode(Qt.ElideNone) — منع القص بـ "...".
      3. auto-shrink تلقائي: مربوط على resizeEvent الخاص بـ tabs،
         بيقلل الـ padding الأفقي تدريجيًا لو مجموع عرض التبويبات
         الطبيعي أكبر من العرض المتاح، لحد ما تتلائم كلها من غير
         قص. ده بديل عن setUsesScrollButtons — اللي جُرِّبت وتبيّن
         إنها بتظهر الأزرار فعليًا لكن مش بتقص رسم التبويبات عند
         حدودها (باج معروف مع RTL + QSS مخصص على QTabBar::tab)،
         فالتبويبات الزيادة كانت بترسم برّه المساحة المرئية بدل ما
         تختفي ورا سكرول سلس.

    كل الأقسام (costing/pricing/design/orders/inventory/accounting)
    لازم تنادي الدالة دي بدل استدعاء setStyleSheet(tab_style()) لوحدها
    — عشان كل التبويبات في المشروع تاخد نفس السلوك من نقطة واحدة.
    """
    tabs.setProperty("_tab_accent", accent)
    tabs.setProperty("_tab_size", size)
    tabs.setStyleSheet(tab_style(accent=accent, size=size))
    tabs.setElideMode(Qt.ElideNone)
    tabs.tabBar().setExpanding(False)

    # [auto-shrink] نربط resizeEvent مرة واحدة بس لكل tabs instance —
    # علّمنا الويدجت بـ property عشان منربطش نفس الحدث مرتين لو
    # apply_tab_style اتنادت أكتر من مرة على نفس الـ tabs (زي عند
    # تغيير الثيم في _refresh_style).
    if not tabs.property("_auto_shrink_installed"):
        tabs.setProperty("_auto_shrink_installed", True)
        original_resize = tabs.resizeEvent

        def _wrapped_resize(event, _orig=original_resize, _tabs=tabs):
            _orig(event)
            _shrink_tabs_to_fit(_tabs, _tabs.property("_tab_size") or "normal")

        tabs.resizeEvent = _wrapped_resize

    # تطبيق فوري أول مرة (لو الحجم النهائي معروف بالفعل)
    _shrink_tabs_to_fit(tabs, size)


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
