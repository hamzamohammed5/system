"""
ui/tabs/accounting/_state_widgets.py
======================================
_StateWidgets — widgets حالة الانتظار والخطأ لـ AccountingTab.

[تحديث v3]:
  - make_empty_state يستخدم EmptyPanelState من panels (توحيد).
  - make_loading_widget يقبل نص مخصص.
  - make_error_widget دالة واحدة بدل make_conn_error_widget + make_init_failed_widget.
"""

from PyQt5.QtWidgets import QLabel, QFrame, QVBoxLayout
from PyQt5.QtCore import Qt

from ui.widgets.panels.state import EmptyState
from ui.widgets.core.i18n import tr
from ui.theme import _C
from ui.font import FS_BASE, FS_LG


# ══════════════════════════════════════════════════════════
# دوال بناء الـ state widgets
# ══════════════════════════════════════════════════════════

def make_no_company_widget() -> QLabel:
    """Widget 'اختر شركة أولاً'."""
    lbl = QLabel(tr("accounting_no_company_msg"))
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(f"font-size:{FS_LG}px; color:{_C['text_state_neutral']}; padding:40px;")
    return lbl


def make_error_widget(message: str,
                      bg: str = None,
                      color: str = None) -> QLabel:
    """
    Widget خطأ عام — يستبدل make_conn_error_widget + make_init_failed_widget.

    الاستخدام:
        w = make_error_widget(f"خطأ في الاتصال:\n{e}")
        w = make_error_widget("تعذّر تهيئة قاعدة البيانات")
    """
    bg    = bg or _C["badge_cr_bg"]
    color = color or _C["badge_cr_text"]
    lbl = QLabel(message)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"font-size:{FS_BASE}px; color:{color}; padding:40px;"
        f"background:{bg}; border-radius:8px; margin:20px;"
    )
    return lbl


# للتوافق مع الكود القديم
def make_conn_error_widget(error: Exception) -> QLabel:
    return make_error_widget(tr("conn_error_msg", error=error))


def make_init_failed_widget() -> QLabel:
    return make_error_widget(tr("init_failed_msg"))


def make_loading_widget(attempt: int, max_attempts: int = 5,
                        text: str = None) -> QLabel:
    """Widget التحميل مع عداد المحاولات."""
    msg = text or tr("loading_db_msg", attempt=attempt, max=max_attempts)
    lbl = QLabel(msg)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet(f"font-size:{FS_BASE}px; color:{_C['text_state_neutral']}; padding:40px;")
    return lbl


def make_empty_state(icon: str = "📋",
                     title: str = None,
                     subtitle: str = "",
                     action_text: str = "") -> EmptyState:
    """
    يبني EmptyState موحد من panels.
    """
    return EmptyState(
        icon=icon,
        title=title or tr("no_data"),
        subtitle=subtitle,
        action_text=action_text,
        expandable=True,
    )