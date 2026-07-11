"""
main.py
=======
نقطة الدخول الوحيدة — شغّل هذا الملف.
"""

import sys


def main():
    # 1. تهيئة companies.db المركزية فقط
    from services.companies.company_service import CompanyService
    conn = CompanyService.get_central_conn_and_init()
    conn.close()

    # 2. تشغيل Qt
    from PyQt5.QtWidgets import QApplication
    qt_app = QApplication(sys.argv)

    # 3. تحميل الثيم واللغة من DB قبل أي شيء
    from ui.theme_manager import theme_manager
    from ui.widgets.core.i18n import i18n_manager
    theme_manager.load_from_db()
    i18n_manager.load_from_db()

    # 4. تطبيق الخط بالحجم المحفوظ
    from ui.font import get_font_size, apply_font
    apply_font(qt_app, get_font_size())

    # 5. تطبيق اتجاه اللغة
    qt_app.setLayoutDirection(i18n_manager.qt_direction)

    # 6. منع عجلة الماوس من تغيير قيم الـ inputs
    from ui.widgets.utils.no_wheel import (
        install_no_wheel_filter,
        install_shift_wheel_filter,
    )
    install_no_wheel_filter(qt_app)
    install_shift_wheel_filter(qt_app)

    # 6.5. [إصلاح tooltip أبيض على Windows] استبدال الـ QToolTip الافتراضي
    # (اللي بيتجاهل QSS/Palette مع بعض أنماط Windows native) بـ tooltip
    # مخصص مرسوم بالكامل بمحرك Qt نفسه.
    from ui.widgets.utils.tooltip import install_custom_tooltip_filter
    install_custom_tooltip_filter(qt_app)

    # 7. النافذة الرئيسية
    from ui.main_window import MainWindow
    window = MainWindow(qt_app)
    window.show()

    sys.exit(qt_app.exec_())


if __name__ == "__main__":
    main()