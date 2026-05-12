"""
ui/tabs/accounting/journal/journal_lines.py
============================================
Facade للتوافق مع الكود القديم — يُعيد تصدير من lines/

التقسيم الداخلي:
  lines/_smart_line.py  → _SmartLine
  lines/_lines_panel.py → _LinesPanel
"""

from .lines._smart_line  import _SmartLine   # noqa: F401
from .lines._lines_panel import _LinesPanel  # noqa: F401

__all__ = ["_SmartLine", "_LinesPanel"]