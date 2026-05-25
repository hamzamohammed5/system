"""
ui/widgets/shared/detail_panel_mixins.py
=========================================
_DetailNotifMixin  — منطق الإشعارات لـ BaseDetailPanel
_DetailStateMixin  — منطق الـ show/hide state

مستخرجة من base_detail_panel.py لتقليل الحجم.
تُستخدم فقط من base_detail_panel.py.
"""


class _DetailNotifMixin:
    """
    Mixin يضيف دوال الإشعارات لـ BaseDetailPanel.

    يفترض وجود:
      - self._notif : NotificationBar
    """

    def show_success(self, msg: str, auto_hide: int = 3000):
        self._notif.show(msg, "success", auto_hide)

    def show_error(self, msg: str):
        self._notif.show(msg, "danger")

    def show_warning(self, msg: str, auto_hide: int = 0):
        self._notif.show(msg, "warning", auto_hide)

    def show_info(self, msg: str, auto_hide: int = 0):
        self._notif.show(msg, "info", auto_hide)


class _DetailStateMixin:
    """
    Mixin يضيف دوال الـ show/hide state لـ BaseDetailPanel.

    يفترض وجود:
      - self._scroll  : QScrollArea
      - self._hdr     : DetailHeader
      - self._empty   : EmptyState
    """

    def _set_mode(self, has_data: bool):
        self._scroll.setVisible(has_data)
        self._hdr.setVisible(has_data)
        self._empty.setVisible(not has_data)

    # أُبقي عليهما للتوافق مع الكود الموروث
    def _show_empty(self):
        self._set_mode(has_data=False)

    def _show_detail(self):
        self._set_mode(has_data=True)