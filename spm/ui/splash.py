# -*- coding: utf-8 -*-
"""splash.py — شاشة البداية (التحميل)"""
from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QProgressBar, QFrame,
)

from . import theme
from .. import APP_NAME, APP_NAME_EN, __version__


class SplashScreen(QDialog):
    """شاشة بداية أنيقة تعرض شعار التطبيق وشريط تحميل قصير."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(560, 420)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setStyleSheet(f"QDialog {{ background: {theme.BG}; }}")

        root = QVBoxLayout(self)
        root.setContentsMargins(30, 36, 30, 28)
        root.setSpacing(10)

        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(
            f"#Card {{ background: {theme.CARD}; border-radius: 18px; "
            f"border: 1px solid {theme.BORDER}; }}")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(24, 30, 24, 26)
        lay.setSpacing(12)

        logo = QLabel()
        logo.setPixmap(theme.app_logo_pixmap(120))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo)

        t1 = QLabel(APP_NAME)
        t1.setFont(theme.app_font(20, bold=True))
        t1.setStyleSheet(f"color: {theme.PRIMARY}; background: transparent;")
        t1.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t1)

        t2 = QLabel(APP_NAME_EN)
        t2.setFont(theme.app_font(12))
        t2.setStyleSheet(f"color: {theme.ACCENT}; background: transparent;"
                         "font-weight: bold;")
        t2.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t2)

        t3 = QLabel("حماية كلمات مرورك بتشفير AES-256-GCM واشتقاق مفاتيح Argon2id")
        t3.setStyleSheet(f"color: {theme.MUTED}; background: transparent;")
        t3.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(t3)

        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(10)
        self.progress.setStyleSheet(
            f"QProgressBar {{ background: {theme.BG}; border-radius: 5px; }}"
            f"QProgressBar::chunk {{ background: {theme.PRIMARY_LIGHT};"
            " border-radius: 5px; }}")
        lay.addSpacing(6)
        lay.addWidget(self.progress)

        status = QLabel("جارٍ تحميل مكونات الأمان…")
        status.setStyleSheet(f"color: {theme.MUTED};"
                             " background: transparent; font-size: 9pt;")
        status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(status)

        root.addWidget(card)

        ver = QLabel(f"الإصدار {__version__} — مشروع تخرج / الأمن السيبراني 2026")
        ver.setStyleSheet(f"color: {theme.MUTED}; font-size: 8.5pt;")
        ver.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(ver)

        self._step = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._advance)
        self._timer.start(28)

    def _advance(self):
        self._step += 1
        self.progress.setValue(min(100, self._step * 2))
        if self.progress.value() >= 100:
            self._timer.stop()
            self.accept()
