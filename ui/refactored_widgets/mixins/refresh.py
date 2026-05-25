"""
ui/widgets/shared/mixins/refresh.py
=====================================
RefreshableMixin — نمط التحميل والعرض المنفصلين.
"""


class RefreshableMixin:
    """
    Mixin لأي widget يحتاج تحديث دوري.

    Override:
        _load_data() → يجلب البيانات
        _fill_ui(data) → يملأ الـ UI
    """

    def refresh(self):
        try:
            data = self._load_data()
            self._fill_ui(data)
        except Exception as e:
            self._on_refresh_error(e)

    def _load_data(self):
        return []

    def _fill_ui(self, data):
        pass

    def _on_refresh_error(self, error: Exception):
        print(f"[{self.__class__.__name__}] refresh error: {error}")