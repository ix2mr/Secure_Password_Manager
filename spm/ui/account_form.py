# -*- coding: utf-8 -*-
"""account_form.py — نموذج إضافة/تعديل حساب مع توليد كلمة وقياس قوة حي"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QTextEdit, QMessageBox, QScrollArea,
)

from . import theme
from .widgets import TitleLabel, StrengthBar
from ..passwords import analyze_password, generate_password
from ..vault import VaultError


class AccountFormScreen(QWidget):
    saved = Signal()          # بعد الحفظ الناجح
    cancelled = Signal()

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self.editing_id = None
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 20, 28, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(
            f"#Card {{ background: {theme.CARD}; border-radius: 14px;"
            f" border: 1px solid {theme.BORDER}; }}")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(26, 22, 26, 22)
        lay.setSpacing(9)

        self.title = TitleLabel("إضافة حساب جديد", 16)
        lay.addWidget(self.title)

        def field_label(text):
            l = QLabel(text)
            l.setStyleSheet(f"color: {theme.PRIMARY}; font-weight: bold;")
            return l

        lay.addWidget(field_label("اسم الموقع / الخدمة *"))
        self.site = QLineEdit()
        self.site.setPlaceholderText("مثال: Google، بنك الراجحي، Twitter")
        lay.addWidget(self.site)

        lay.addWidget(field_label("اسم المستخدم / البريد الإلكتروني *"))
        self.username = QLineEdit()
        self.username.setPlaceholderText("مثال: user@example.com")
        lay.addWidget(self.username)

        lay.addWidget(field_label("كلمة المرور *"))
        row = QHBoxLayout()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("اكتبها أو ولّد كلمة قوية آليًا")
        self.password.textChanged.connect(
            lambda: self.strength.set_result(
                analyze_password(self.password.text())))
        btn_show = QPushButton("إظهار")
        btn_show.setCheckable(True)
        btn_show.setFixedWidth(74)
        btn_show.toggled.connect(
            lambda on: self.password.setEchoMode(
                QLineEdit.Normal if on else QLineEdit.Password))
        btn_show.toggled.connect(
            lambda on: btn_show.setText("إخفاء" if on else "إظهار"))
        self.btn_generate = QPushButton("توليد كلمة قوية")
        self.btn_generate.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate.clicked.connect(self._generate)
        row.addWidget(self.password, 1)
        row.addWidget(btn_show)
        row.addWidget(self.btn_generate)
        lay.addLayout(row)

        self.strength = StrengthBar()
        lay.addWidget(self.strength)

        self.weak_warning = QLabel("")
        self.weak_warning.setStyleSheet(
            f"color: {theme.DANGER}; font-size: 9pt; font-weight: bold;")
        self.weak_warning.setWordWrap(True)
        self.weak_warning.hide()
        lay.addWidget(self.weak_warning)

        lay.addWidget(field_label("الموقع الإلكتروني (اختياري)"))
        self.url = QLineEdit()
        self.url.setPlaceholderText("https://example.com")
        lay.addWidget(self.url)

        lay.addWidget(field_label("ملاحظات (اختياري)"))
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("أي تفاصيل إضافية: رقم السؤال السري، "
                                      "تاريخ آخر تحديث، إلخ")
        self.notes.setFixedHeight(80)
        lay.addWidget(self.notes)

        buttons = QHBoxLayout()
        self.btn_save = QPushButton("حفظ الحساب (يُشفَّر فورًا)")
        self.btn_save.setObjectName("primary")
        self.btn_save.setFixedHeight(42)
        self.btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("إلغاء")
        btn_cancel.setFixedHeight(42)
        btn_cancel.clicked.connect(self._cancel)
        buttons.addWidget(self.btn_save, 2)
        buttons.addWidget(btn_cancel, 1)
        lay.addLayout(buttons)

        scroll.setWidget(card)
        outer.addWidget(scroll)

    # ------------------------------------------------------------------
    def open_add(self):
        self.editing_id = None
        self.title.setText("إضافة حساب جديد")
        self.btn_save.setText("حفظ الحساب (يُشفَّر فورًا)")
        self._clear()
        self.strength.set_result(analyze_password(""))

    def open_edit(self, account_id: str):
        acc = self.mw.vault.get_account(account_id)
        if not acc:
            return
        self.editing_id = account_id
        self.title.setText(f"تعديل الحساب: {acc['site_name']}")
        self.btn_save.setText("حفظ التعديلات (إعادة تشفير)")
        self.site.setText(acc["site_name"])
        self.username.setText(acc["username"])
        self.url.setText(acc["url"])
        self.notes.setPlainText(acc["notes"])
        self.password.setText(acc["password"])
        self.strength.set_result(analyze_password(acc["password"]))

    def _clear(self):
        self.site.clear()
        self.username.clear()
        self.url.clear()
        self.notes.clear()
        self.password.clear()

    def _generate(self):
        settings = self.mw.vault.settings.get("generator_defaults",
                                              {}) if self.mw.vault else {}
        pwd = generate_password(
            length=settings.get("length", 16),
            upper=settings.get("upper", True),
            lower=settings.get("lower", True),
            digits=settings.get("digits", True),
            symbols=settings.get("symbols", True),
            exclude_ambiguous=settings.get("exclude_ambiguous", False),
        )
        self.password.setEchoMode(QLineEdit.Normal)
        self.password.setText(pwd)

    def _save(self):
        site = self.site.text().strip()
        username = self.username.text().strip()
        pwd = self.password.text()
        if not site or not username or not pwd:
            QMessageBox.warning(
                self, "بيانات ناقصة",
                "الحقول المطلوبة: اسم الموقع، اسم المستخدم، كلمة المرور")
            return
        a = analyze_password(pwd)
        if a["is_weak"]:
            self.weak_warning.setText(
                "تنبيه: هذه الكلمة ضعيفة/شائعة. يمكنك المتابعة لكن "
                "يُنصح باستخدام زر «توليد كلمة قوية».")
            self.weak_warning.show()
        else:
            self.weak_warning.hide()
        try:
            if self.editing_id:
                self.mw.vault.edit_account(
                    self.editing_id,
                    site_name=site, username=username, password=pwd,
                    url=self.url.text().strip(),
                    notes=self.notes.toPlainText().strip())
            else:
                self.mw.vault.add_account(
                    site_name=site, username=username, password=pwd,
                    url=self.url.text().strip(),
                    notes=self.notes.toPlainText().strip())
        except VaultError as e:
            QMessageBox.critical(self, "خطأ", str(e))
            return
        self.saved.emit()
        self._clear()
        self.weak_warning.hide()

    def _cancel(self):
        self._clear()
        self.cancelled.emit()
