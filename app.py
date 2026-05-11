"""
app.py
======
النافذة الرئيسية — تجمع التبويبات + قايمة الإعدادات.
"""

from PyQt5.QtWidgets import QMainWindow, QTabWidget
from PyQt5.QtCore    import Qt

from ui.tabs.costing_section.raw_tab        import RawTab
from ui.tabs.costing_section.product_tab    import ProductTab
from ui.tabs.costing_section.labor_tab      import LaborTab
from ui.tabs.costing_section.machine_tab    import MachineTab
from ui.settings_dialog     import SettingsDialog


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self._app = app

        self.setWindowTitle("ERP — نظام قوائم المواد")
        self.resize(1150, 800)
        self.setLayoutDirection(Qt.RightToLeft)

        # ── التبويبات ──
        tabs = QTabWidget()
        tabs.addTab(RawTab(),            "📦 الخامات")
        tabs.addTab(ProductTab("semi"),  "🔧 نصف مصنع")
        tabs.addTab(ProductTab("final"), "🏭 منتج نهائي")
        tabs.addTab(LaborTab(),          "👷 العمالة")
        tabs.addTab(MachineTab(),        "⚙️ التشغيل")
        self.setCentralWidget(tabs)

        # ── قايمة الإعدادات ──
        menu = self.menuBar().addMenu("⚙️  إعدادات")
        menu.addAction("🔤  حجم الخط", self._open_settings)

    def _open_settings(self):
        SettingsDialog(self._app, parent=self).exec_()