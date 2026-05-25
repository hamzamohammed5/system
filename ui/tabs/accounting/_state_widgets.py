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

from ui.widgets.shared.empty_state_helpers import EmptyPanelState


# ══════════════════════════════════════════════════════════
# دوال بناء الـ state widgets
# ══════════════════════════════════════════════════════════

def make_no_company_widget() -> QLabel:
    """Widget 'اختر شركة أولاً'."""
    lbl = QLabel("⚠️  اختر شركة أولاً لعرض الحسابات")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet("font-size:14px; color:#888; padding:40px;")
    return lbl


def make_error_widget(message: str,
                      bg: str = "#fdecea",
                      color: str = "#c62828") -> QLabel:
    """
    Widget خطأ عام — يستبدل make_conn_error_widget + make_init_failed_widget.

    الاستخدام:
        w = make_error_widget(f"خطأ في الاتصال:\n{e}")
        w = make_error_widget("تعذّر تهيئة قاعدة البيانات")
    """
    lbl = QLabel(message)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        f"font-size:13px; color:{color}; padding:40px;"
        f"background:{bg}; border-radius:8px; margin:20px;"
    )
    return lbl


# للتوافق مع الكود القديم
def make_conn_error_widget(error: Exception) -> QLabel:
    return make_error_widget(f"❌  خطأ في الاتصال بقاعدة البيانات:\n{error}")


def make_init_failed_widget() -> QLabel:
    return make_error_widget(
        "❌  تعذّر تهيئة قاعدة بيانات المحاسبة\n"
        "جرّب إعادة تشغيل البرنامج أو تحديد الشركة مجدداً"
    )


def make_loading_widget(attempt: int, max_attempts: int = 5,
                        text: str = None) -> QLabel:
    """Widget التحميل مع عداد المحاولات."""
    msg = text or f"⏳  جاري تهيئة قاعدة البيانات... ({attempt}/{max_attempts})"
    lbl = QLabel(msg)
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet("font-size:13px; color:#888; padding:40px;")
    return lbl


def make_empty_state(icon: str = "📋",
                     title: str = "لا توجد بيانات",
                     subtitle: str = "",
                     action_text: str = "") -> EmptyPanelState:
    """
    يبني EmptyPanelState موحد من panels.

    الاستخدام:
        empty = make_empty_state("🏦", "لا توجد حسابات", "أضف حساباً جديداً")
        layout.addWidget(empty)
    """
    return EmptyPanelState(
        icon=icon,
        title=title,
        subtitle=subtitle,
        action_text=action_text,
    )