# -*- coding: utf-8 -*-
"""unlock.py — شاشة إدخال كلمة المرور الرئيسية لفتح الخزنة"""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QMessageBox,
)

from . import theme


MAX_ATTEMPTS = 5          # عدد المحاولات قبل التجميد
COOLDOWN_SECONDS = 30     # مدة التجميد بعد تجاوز المحاولات


class UnlockScreen(QWidget):
    """فتح الخزنة: إدخال الكلمة الرئيسية + معالجة آمنة للمحاولات الخاطئة."""
    vault_unlocked = Signal(object)   # يرسل VaultManager المفتوحة

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self.attempts = 0
        self._cooldown_timer = QTimer(self)
        self._cooldown_timer.setSingleShot(True)
        self._cooldown_timer.timeout.connect(self._end_cooldown)
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.addStretch(1)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(520)
        card.setStyleSheet(
            f"#Card {{ background: {theme.CARD}; border-radius: 16px;"
            f" border: 1px solid {theme.BORDER}; }}")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(30, 28, 30, 28)
        lay.setSpacing(10)

        logo = QLabel()
        logo.setPixmap(theme.app_logo_pixmap(72))
        logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(logo)

        title = QLabel("قفل الخزنة — أدخل كلمة المرور الرئيسية")
        title.setFont(theme.app_font(16, bold=True))
        title.setStyleSheet(f"color: {theme.PRIMARY};")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        self.message = QLabel("الخزنة مشفّرة ولا تفتح إلا بكلمة المرور الرئيسية.")
        self.message.setWordWrap(True)
        self.message.setStyleSheet(f"color: {theme.MUTED}; font-size: 9.5pt;")
        self.message.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.message)

        row = QHBoxLayout()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("كلمة المرور الرئيسية")
        self.password.returnPressed.connect(self._try_unlock)
        btn_show = QPushButton("إظهار")
        btn_show.setCheckable(True)
        btn_show.setFixedWidth(74)
        btn_show.toggled.connect(
            lambda on: self.password.setEchoMode(
                QLineEdit.Normal if on else QLineEdit.Password))
        btn_show.toggled.connect(
            lambda on: btn_show.setText("إخفاء" if on else "إظهار"))
        row.addWidget(self.password, 1)
        row.addWidget(btn_show)
        lay.addLayout(row)

        self.attempts_label = QLabel("")
        self.attempts_label.setStyleSheet(f"color: {theme.DANGER}; font-size: 9pt;")
        lay.addWidget(self.attempts_label)

        self.btn_unlock = QPushButton("فتح الخزنة")
        self.btn_unlock.setObjectName("primary")
        self.btn_unlock.setFixedHeight(44)
        self.btn_unlock.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_unlock.clicked.connect(self._try_unlock)
        lay.addWidget(self.btn_unlock)

        note = QLabel("بعد 5 محاولات خاطئة تُجمَّد الشاشة مؤقتًا لحماية "
                      "الخزنة من هجمات التخمين (Brute Force).")
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {theme.MUTED}; font-size: 8.5pt;")
        lay.addWidget(note)

        root.addWidget(card)
        root.addStretch(1)

    # ------------------------------------------------------------------
    def show_message(self, text: str, is_warning: bool = False):
        """رسالة علوية (مثل: تم القفل تلقائيًا بسبب الخمول)."""
        self.message.setText(text)
        color = theme.DANGER if is_warning else theme.MUTED
        self.message.setStyleSheet(f"color: {color}; font-size: 9.5pt;"
                                   "font-weight: bold;")

    def reset_screen(self):
        self.password.clear()
        self.attempts = 0
        self.attempts_label.setText("")
        self.btn_unlock.setEnabled(True)
        self.password.setFocus()

    def _try_unlock(self):
        if self._cooldown_timer.isActive():
            return
        if not self.mw or self.mw.vault is None:
            QMessageBox.critical(self, "خطأ", "لا يوجد ملف خزنة.")
            return
        pwd = self.password.text()
        if not pwd:
            self.attempts_label.setText("أدخل كلمة المرور الرئيسية أولًا")
            return
        try:
            self.mw.vault.unlock(pwd)
        except Exception:
            self.attempts += 1
            self.password.clear()
            remaining = MAX_ATTEMPTS - self.attempts
            if remaining <= 0:
                self.btn_unlock.setEnabled(False)
                self.attempts_label.setText(
                    f"تجاوزت عدد المحاولات المسموح. التجميد {COOLDOWN_SECONDS} ثانية…")
                self._cooldown_timer.start(COOLDOWN_SECONDS * 1000)
            else:
                self.attempts_label.setText(
                    f"كلمة المرور خاطئة — المحاولات المتبقية: {remaining}")
            return
        self.password.clear()
        self.attempts = 0
        self.attempts_label.setText("")
        self.vault_unlocked.emit(self.mw.vault)

    def _end_cooldown(self):
        self.attempts = 0
        self.btn_unlock.setEnabled(True)
        self.attempts_label.setText(
            "يمكنك المحاولة مجددًا الآن — تأكد من الكلمة الصحيحة")
