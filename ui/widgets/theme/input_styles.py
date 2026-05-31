"""
ui/widgets/theme/input_styles.py
=================================
Stylesheet generators للـ inputs.

[Refactor V3 — المرحلة 10] مستخرج من theme/styles.py.

[إصلاح ألوان] استبدال ألوان error و positive الـ hardcoded بمفاتيح _C:
  - input_error_bg / input_error_border  ← من theme_manager
  - input_positive_bg / input_positive_border / input_positive_color ← من theme_manager
  هذا يضمن تغيير الألوان تلقائياً عند التبديل بين light و dark.
"""
from ui.theme import _C
from ui.font  import fs, get_font_size


def input_style(height: int = 32, error: bool = False) -> str:
    """
    Stylesheet موحد لـ QLineEdit / QComboBox / QDateEdit.

    [إصلاح] error colors من _C بدل hardcoded:
      القديم: "#fef2f2", "#f87171"
      الجديد: _C["input_error_bg"], _C["input_error_border"]
    """
    base   = get_font_size()
    bg     = _C["input_error_bg"]     if error else _C["bg_input"]
    border = _C["input_error_border"] if error else _C["border_med"]
    return (
        f"background:{bg}; border:1.5px solid {border};"
        f"border-radius:6px; padding:0 8px;"
        f"font-size:{fs(base,0)}pt; color:{_C['text_primary']};"
        f"min-height:{height}px;"
    )


def spinbox_style(height: int = 32, positive: bool = False,
                  widget: str = "QDoubleSpinBox") -> str:
    """
    Stylesheet موحد لـ QDoubleSpinBox / QSpinBox.

    [إصلاح] positive colors من _C بدل hardcoded:
      القديم: "#f0fdf4", "#86efac", "#15803d"
      الجديد: _C["input_positive_bg"], _C["input_positive_border"], _C["input_positive_color"]
    """
    base = get_font_size()
    if positive:
        bg     = _C["input_positive_bg"]
        border = _C["input_positive_border"]
        color  = _C["input_positive_color"]
        weight = "bold"
    else:
        bg     = _C["bg_input"]
        border = _C["border_med"]
        color  = _C["text_primary"]
        weight = "normal"
    return f"""
        {widget} {{
            background:{bg}; border:1.5px solid {border};
            border-radius:6px; padding:0 8px;
            font-size:{fs(base,0)}pt; color:{color};
            font-weight:{weight}; min-height:{height}px;
        }}
        {widget}:focus {{ border-color:{_C['accent']}; background:{_C['bg_input']}; }}
        {widget}:disabled {{
            background:{_C['bg_surface_2']}; color:{_C['text_disabled']};
        }}
    """


def search_input_style(height: int = 34) -> str:
    """Stylesheet لحقول البحث."""
    base = get_font_size()
    return f"""
        QLineEdit {{
            background:{_C['bg_input']};
            border:1.5px solid {_C['border_med']};
            border-radius:6px; padding:0 10px;
            font-size:{fs(base,0)}pt; color:{_C['text_primary']};
        }}
        QLineEdit:focus {{ border-color:{_C['accent']}; background:{_C['bg_input']}; }}
    """