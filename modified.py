from ui.widgets.core.widget_mixin import ThemeRefreshMixin


# قبل
class MyLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(f"color:{_C['text_sec']};")  # يتجمد!

# بعد
from ui.widgets.core.widget_mixin import ThemeRefreshMixin

class MyLabel(QLabel, ThemeRefreshMixin):
    def __init__(self):
        super().__init__()
        self._init_theme_refresh()      # ← سطر واحد
        self._refresh_style()

    def _refresh_style(self, *_):
        self.setStyleSheet(f"color:{_C['text_sec']};")  # يتحدث تلقائياً
        
# القاعدة العامة لأي widget جديد:

# 1. وارث ThemeRefreshMixin
# 2. استدعي self._init_theme_refresh() في __init__
# 3. حط كل الـ stylesheet في _refresh_style(self, *_)
# 4. لا تستدعي setStyleSheet في أي مكان تاني