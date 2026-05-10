"""
main.py
=======
نقطة الدخول الوحيدة — شغّل هذا الملف.
"""

import sys
from PyQt5.QtWidgets import QApplication
from db.schema               import init_db
from ui.app_settings         import apply_font
from ui.main_window          import MainWindow
from ui.widgets.no_wheel     import install_no_wheel_filter   # ← جديد


def main():
    init_db()
    qt_app = QApplication(sys.argv)
    apply_font(qt_app)

    # ✅ منع عجلة الماوس من تغيير قيم الـ inputs في كل التطبيق
    install_no_wheel_filter(qt_app)

    window = MainWindow(qt_app)
    window.show()
    sys.exit(qt_app.exec_())


if __name__ == "__main__":
    main()
