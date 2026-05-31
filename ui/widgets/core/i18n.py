"""
ui/widgets/core/i18n.py
========================
نظام الترجمة للتطبيق — عربي وإنجليزي.

الاستخدام:
    from ui.widgets.core.i18n import tr, i18n_manager

    text = tr("save")
    text = tr("delete_confirm_msg", name="X")

    i18n_manager.set_language("en")
    i18n_manager.language_changed.connect(my_fn)

مصدر الترجمات:
    ui/i18n/ar.py  →  AR_STRINGS  (العربية)
    ui/i18n/en.py  →  EN_STRINGS  (الإنجليزية)
    هما المصدر الوحيد — لا يوجد قاموس داخلي مكرر هنا.

[تغيير] الـ imports أصبحت absolute بدل relative لوضوح أكبر وتجنب
هشاشة الـ relative imports عند إعادة هيكلة المجلدات.
"""

from __future__ import annotations

from typing import Dict
from PyQt5.QtCore import QObject, pyqtSignal, Qt


# ══════════════════════════════════════════════════════════
# قواميس اللغات — تُملأ من الملفات الخارجية فقط
# ══════════════════════════════════════════════════════════

_TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ar": {},
    "en": {},
}

_LANGUAGE_DIRECTION: Dict[str, str] = {
    "ar": "rtl",
    "en": "ltr",
}

_LANGUAGE_DISPLAY_NAMES: Dict[str, str] = {
    "ar": "العربية",
    "en": "English",
}


def _load_translations():
    """
    يحمّل الترجمات من ui/i18n/ar.py و ui/i18n/en.py.

    [تغيير] استخدام absolute imports بدل relative imports:
      قبل: from ...i18n.ar import AR_STRINGS
      بعد: from ui.i18n.ar import AR_STRINGS

    هذا أوضح وأكثر صموداً عند إعادة هيكلة المجلدات.
    يُستدعى تلقائياً عند استيراد هذا الملف.
    """
    try:
        from ui.i18n.ar import AR_STRINGS
        _TRANSLATIONS["ar"].update(AR_STRINGS)
    except Exception:
        pass

    try:
        from ui.i18n.en import EN_STRINGS
        _TRANSLATIONS["en"].update(EN_STRINGS)
    except Exception:
        pass


_load_translations()


# ══════════════════════════════════════════════════════════
# I18nManager
# ══════════════════════════════════════════════════════════

class I18nManager(QObject):
    """
    Singleton يدير لغة التطبيق.

    الاستخدام:
        from ui.widgets.core.i18n import i18n_manager, tr

        i18n_manager.set_language("en")
        text = tr("save")   # "Save"
    """

    language_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._language: str = "ar"

    @property
    def language(self) -> str:
        return self._language

    @property
    def is_rtl(self) -> bool:
        return _LANGUAGE_DIRECTION.get(self._language, "rtl") == "rtl"

    @property
    def qt_direction(self) -> Qt.LayoutDirection:
        return Qt.RightToLeft if self.is_rtl else Qt.LeftToRight

    def set_language(self, lang: str, save: bool = True):
        if lang not in _TRANSLATIONS:
            lang = "ar"
        if lang == self._language:
            return
        self._language = lang
        self._apply_direction()
        if save:
            self._save_to_db()
        self.language_changed.emit(lang)

    def translate(self, key: str, lang: str = None, **kwargs) -> str:
        target = lang or self._language
        text = _TRANSLATIONS.get(target, {}).get(key)
        if text is None:
            # fallback للعربية
            text = _TRANSLATIONS["ar"].get(key, key)
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass
        return text

    def load_from_db(self):
        try:
            from db.shared.connection import get_connection
            from db.shared.settings_repo import get_setting
            conn = get_connection()
            lang = get_setting(conn, "ui_language", "ar")
            if lang in _TRANSLATIONS:
                self._language = lang
            self._apply_direction()
        except Exception:
            pass

    def get_available_languages(self) -> list:
        return [
            {
                "code":   code,
                "name":   _LANGUAGE_DISPLAY_NAMES.get(code, code),
                "active": code == self._language,
                "is_rtl": _LANGUAGE_DIRECTION.get(code, "ltr") == "rtl",
            }
            for code in _TRANSLATIONS
        ]

    def add_translations(self, lang_code: str, translations: Dict[str, str]):
        """إضافة ترجمات جديدة أو تحديث موجودة برمجياً."""
        if lang_code not in _TRANSLATIONS:
            _TRANSLATIONS[lang_code] = {}
        _TRANSLATIONS[lang_code].update(translations)

    # ── Internal ──────────────────────────────────────────

    def _apply_direction(self):
        try:
            from PyQt5.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.setLayoutDirection(self.qt_direction)
        except Exception:
            pass

    def _save_to_db(self):
        try:
            from db.shared.connection import get_connection
            from db.shared.settings_repo import set_setting
            conn = get_connection()
            set_setting(conn, "ui_language", self._language)
        except Exception:
            pass


# ── Singletons ────────────────────────────────────────────
i18n_manager = I18nManager()


def tr(key: str, lang: str = None, **kwargs) -> str:
    """
    دالة الترجمة الرئيسية.

    مثال:
        from ui.widgets.core.i18n import tr

        btn.setText(tr("save"))
        lbl.setText(tr("delete_confirm_msg", name="المنتج"))
    """
    return i18n_manager.translate(key, lang, **kwargs)