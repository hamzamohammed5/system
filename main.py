"""
main.py
=======
نقطة الدخول الوحيدة — شغّل هذا الملف.
"""

import sys


def main():
    # 1. تهيئة companies.db المركزية فقط — بدون أي connection للشركات
    from db.costing.schema import init_db
    init_db()

    # 2. تشغيل Qt
    from PyQt5.QtWidgets import QApplication
    qt_app = QApplication(sys.argv)

    # 3. تطبيق الخط بالحجم الافتراضي (بدون قراءة من DB)
    from ui.app_settings import DEFAULT_FONT_SIZE, _build_stylesheet
    qt_app.setStyleSheet(_build_stylesheet(DEFAULT_FONT_SIZE))

    # 4. منع عجلة الماوس من تغيير قيم الـ inputs
    from ui.widgets.shared.no_wheel import (
        install_no_wheel_filter,
        install_shift_wheel_filter,
    )
    install_no_wheel_filter(qt_app)
    install_shift_wheel_filter(qt_app)

    # 5. النافذة الرئيسية
    from ui.main_window import MainWindow
    window = MainWindow(qt_app)
    window.show()

    sys.exit(qt_app.exec_())


if __name__ == "__main__":
    main()