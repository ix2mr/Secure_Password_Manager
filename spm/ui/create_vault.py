# -*- coding: utf-8 -*-
"""create_vault.py — شاشة إنشاء خزنة جديدة (أول تشغيل)"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QMessageBox,
)

from . import theme
from .widgets import TitleLabel, StrengthBar
from ..vault import VaultManager, VaultError, VaultAlreadyExistsError
from ..passwords import analyze_password


class CreateVaultScreen(QWidget):
    """إنشاء الخزنة: كلمة مرور رئيسية + تأكيدها + قياس القوة الحي."""
    vault_created = Signal(object)   # يرسل VaultManager الجاهزة

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(40, 24, 40, 24)
        root.addStretch(1)

        card = QFrame()
        card.setObjectName("Card")
        card.setFixedWidth(560)
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

        title = TitleLabel("إنشاء خزنة جديدة", 17)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(title)

        desc = QLabel(
            "الخزنة ملف محلي مشفّر يُحفظ على جهازك فقط. "
            "ستكون كلمة المرور الرئيسية هي المفتاح الوحيد لفتحها — "
            "احفظها جيدًا، فلا يمكن استرجاعها إذا نسيتها.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {theme.MUTED}; font-size: 9.5pt;")
        lay.addWidget(desc)

        lbl1 = QLabel("كلمة المرور الرئيسية")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("12 حرفًا أو أكثر — حروف وأرقام ورموز")
        self.password.textChanged.connect(self._on_changed)
        btn_show1 = QPushButton("إظهار")
        btn_show1.setCheckable(True)
        btn_show1.setFixedWidth(74)
        btn_show1.toggled.connect(
            lambda on: self.password.setEchoMode(
                QLineEdit.Normal if on else QLineEdit.Password))
        btn_show1.toggled.connect(
            lambda on: btn_show1.setText("إخفاء" if on else "إظهار"))

        row1 = QHBoxLayout()
        row1.addWidget(self.password, 1)
        row1.addWidget(btn_show1)
        lay.addWidget(lbl1)
        lay.addLayout(row1)

        self.strength = StrengthBar()
        lay.addWidget(self.strength)

        lbl2 = QLabel("تأكيد كلمة المرور الرئيسية")
        self.confirm = QLineEdit()
        self.confirm.setEchoMode(QLineEdit.Password)
        self.confirm.setPlaceholderText("أعد كتابة الكلمة نفسها")
        self.confirm.textChanged.connect(self._on_changed)
        lay.addWidget(lbl2)
        lay.addWidget(self.confirm)

        self.hint = QLabel("")
        self.hint.setWordWrap(True)
        self.hint.setStyleSheet(f"font-size: 9pt; color: {theme.DANGER};")
        lay.addWidget(self.hint)

        self.btn_create = QPushButton("إنشاء الخزنة المشفّرة")
        self.btn_create.setObjectName("primary")
        self.btn_create.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_create.setFixedHeight(44)
        self.btn_create.clicked.connect(self._create)
        lay.addWidget(self.btn_create)

        note = QLabel("يُشتق مفتاح التشفير من كلمتك عبر Argon2id، وتُشفَّر "
                      "البيانات بـ AES-256-GCM ولا تُغادر جهازك أبدًا.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {theme.MUTED}; font-size: 8.5pt;")
        lay.addWidget(note)

        root.addWidget(card)
        root.addStretch(1)

    def _on_changed(self):
        pwd = self.password.text()
        self.strength.set_result(analyze_password(pwd))
        c = self.confirm.text()
        if c and pwd and c != pwd:
            self.hint.setText("الكلمتان غير متطابقتين")
        elif pwd and len(pwd) < 8:
            self.hint.setText("كلمة المرور الرئيسية يجب أن تكون 8 أحرف على الأقل")
        else:
            self.hint.setText("")

    def _create(self):
        pwd = self.password.text()
        confirm = self.confirm.text()
        if not pwd:
            QMessageBox.warning(self, "تنبيه", "أدخل كلمة المرور الرئيسية")
            return
        if pwd != confirm:
            QMessageBox.warning(self, "تنبيه",
                                "كلمة المرور وتأكيدها غير متطابقتين")
            return
        a = analyze_password(pwd)
        if a["is_weak"]:
            ok = QMessageBox.question(
                self, "كلمة مرور ضعيفة",
                "كلمة المرور الرئيسية ضعيفة وستكون أول هدف للمهاجمين.\n"
                "هل تريد المتابعة رغم ذلك؟",
                QMessageBox.Yes | QMessageBox.No)
            if ok != QMessageBox.Yes:
                return
        try:
            vault = VaultManager(self.mw.vault_path())
            vault.create(pwd)
            self.mw.vault = vault   # اجعل هذه الخزنة هي خزنة التطبيق النشطة
        except VaultAlreadyExistsError:
            QMessageBox.critical(self, "خطأ",
                                 "توجد خزنة مسبقًا. أعد تشغيل التطبيق لفتحها.")
            return
        except VaultError as e:
            QMessageBox.critical(self, "خطأ", str(e))
            return
        self.password.clear()
        self.confirm.clear()
        self.strength.set_result(analyze_password(""))
        self.vault_created.emit(vault)
