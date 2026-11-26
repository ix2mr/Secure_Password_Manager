# -*- coding: utf-8 -*-
"""
main.py — نقطة انطلاق تطبيق «مدير كلمات المرور الآمن»
تشغيل: python main.py
"""
import sys
import os

# تشغيل بصيغة عالية الدقة على Windows
if hasattr(os, "addDllDirectory"):
    pass

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from spm import APP_NAME
from spm.ui import theme
from spm.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationDisplayName(APP_NAME)
    app.setLayoutDirection(Qt.RightToLeft)     # واجهة عربية RTL
    app.setStyle("Fusion")

    font_family = theme.load_app_fonts()
    app.setFont(QFont(font_family, 10))
    app.setStyleSheet(theme.QSS)
    app.setWindowIcon(theme.app_icon())

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
