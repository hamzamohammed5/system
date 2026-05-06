"""
main.py
=======
نقطة الدخول الوحيدة — شغّل هذا الملف.
"""

import sys
from PyQt5.QtWidgets import QApplication
from db.schema       import init_db
from ui.app_settings import apply_font
from ui.main_window  import MainWindow


def main():
    init_db()
    qt_app = QApplication(sys.argv)
    apply_font(qt_app)
    window = MainWindow(qt_app)
    window.show()
    sys.exit(qt_app.exec_())


if __name__ == "__main__":
    main()