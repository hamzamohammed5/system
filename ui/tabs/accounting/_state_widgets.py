"""
ui/tabs/accounting/_state_widgets.py
======================================
_StateWidgets — widgets حالة الانتظار والخطأ لـ AccountingTab.

مُستخرج من accounting_section.py لتقليل حجمه.
"""

from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt


def make_no_company_widget() -> QLabel:
    """Widget 'اختر شركة أولاً'."""
    lbl = QLabel("⚠️  اختر شركة أولاً لعرض الحسابات")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet("font-size:14px; color:#888; padding:40px;")
    return lbl


def make_conn_error_widget(error: Exception) -> QLabel:
    """Widget خطأ الاتصال."""
    lbl = QLabel(f"❌  خطأ في الاتصال بقاعدة البيانات:\n{error}")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        "font-size:13px; color:#c62828; padding:40px;"
        "background:#fdecea; border-radius:8px; margin:20px;"
    )
    return lbl


def make_loading_widget(attempt: int, max_attempts: int = 5) -> QLabel:
    """Widget التحميل مع عداد المحاولات."""
    lbl = QLabel(f"⏳  جاري تهيئة قاعدة البيانات... ({attempt}/{max_attempts})")
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setStyleSheet("font-size:13px; color:#888; padding:40px;")
    return lbl


def make_init_failed_widget() -> QLabel:
    """Widget فشل التهيئة النهائي."""
    lbl = QLabel(
        "❌  تعذّر تهيئة قاعدة بيانات المحاسبة\n"
        "جرّب إعادة تشغيل البرنامج أو تحديد الشركة مجدداً"
    )
    lbl.setAlignment(Qt.AlignCenter)
    lbl.setWordWrap(True)
    lbl.setStyleSheet(
        "font-size:13px; color:#c62828; padding:40px;"
        "background:#fdecea; border-radius:8px; margin:20px;"
    )
    return lbl