# -*- coding: utf-8 -*-
"""generator.py — مولّد كلمات المرور العشوائية القوية"""
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QCheckBox, QSlider, QMessageBox,
)

from . import theme
from .widgets import TitleLabel, StrengthBar, IconButton, hline
from ..passwords import generate_password, analyze_password


class GeneratorScreen(QWidget):
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self._build()
        self._regenerate()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)

        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(
            f"#Card {{ background: {theme.CARD}; border-radius: 14px;"
            f" border: 1px solid {theme.BORDER}; }}")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(26, 22, 26, 22)
        lay.setSpacing(10)

        title = TitleLabel("مولّد كلمات المرور العشوائية", 16)
        lay.addWidget(title)
        desc = QLabel(
            "يستخدم المولّد مولّد الأرقام العشوائية المُشفَّر الآمن "
            "(secrets / CSPRNG) لضمان أن كل كلمة عشوائية فعلًا "
            "وليست قابلة للتنبؤ.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {theme.MUTED}; font-size: 9.5pt;")
        lay.addWidget(desc)
        lay.addWidget(hline())

        # الطول
        row_len = QHBoxLayout()
        lbl = QLabel("طول كلمة المرور:")
        lbl.setFont(theme.app_font(10.5, bold=True))
        self.len_value = QLabel("16")
        self.len_value.setFont(theme.app_font(11, bold=True))
        self.len_value.setStyleSheet(f"color: {theme.PRIMARY_LIGHT};")
        row_len.addWidget(lbl)
        row_len.addWidget(self.len_value)
        row_len.addStretch(1)
        lay.addLayout(row_len)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(8, 64)
        self.slider.setValue(16)
        self.slider.valueChanged.connect(
            lambda v: self.len_value.setText(str(v)))
        self.slider.valueChanged.connect(self._regenerate)
        lay.addWidget(self.slider)

        # خيارات الفئات
        self.cb_upper = QCheckBox("حروف كبيرة (A-Z)")
        self.cb_lower = QCheckBox("حروف صغيرة (a-z)")
        self.cb_digits = QCheckBox("أرقام (0-9)")
        self.cb_symbols = QCheckBox("رموز (!@#$%…)")
        self.cb_ambiguous = QCheckBox(
            "استبعاد الحروف الملتبسة (I l 1 O 0 o)")
        self.cb_ambiguous.setToolTip(
            "مفيد عند نسخ كلمة المرور يدويًا لتجنب الخلط بين الحروف المتشابهة")
        # القيم الافتراضية قبل ربط الإشارات (يحدّثها showEvent من إعدادات الخزنة)
        self.cb_upper.setChecked(True)
        self.cb_lower.setChecked(True)
        self.cb_digits.setChecked(True)
        self.cb_symbols.setChecked(True)
        for cb in (self.cb_upper, self.cb_lower, self.cb_digits,
                   self.cb_symbols, self.cb_ambiguous):
            cb.setCursor(Qt.CursorShape.PointingHandCursor)
            cb.toggled.connect(self._regenerate)
        opts = QHBoxLayout()
        opts.addWidget(self.cb_upper)
        opts.addWidget(self.cb_lower)
        opts.addWidget(self.cb_digits)
        opts.addWidget(self.cb_symbols)
        lay.addLayout(opts)
        lay.addWidget(self.cb_ambiguous)

        # الناتج
        out_lbl = QLabel("كلمة المرور المولَّدة:")
        out_lbl.setFont(theme.app_font(10.5, bold=True))
        lay.addWidget(out_lbl)
        out_row = QHBoxLayout()
        self.output = QLineEdit()
        self.output.setReadOnly(False)
        self.output.setFixedHeight(46)
        self.output.setFont(theme.app_font(12, bold=True))
        out_row.addWidget(self.output, 1)
        self.btn_regen = IconButton("توليد جديدة", "primary", "توليد كلمة أخرى")
        self.btn_regen.setFixedHeight(44)
        self.btn_regen.clicked.connect(self._regenerate)
        self.btn_copy = IconButton("نسخ", "ghost", "نسخ مع مسح تلقائي للحافظة")
        self.btn_copy.setFixedHeight(44)
        self.btn_copy.clicked.connect(self._copy)
        out_row.addWidget(self.btn_regen)
        out_row.addWidget(self.btn_copy)
        lay.addLayout(out_row)

        self.strength = StrengthBar()
        lay.addWidget(self.strength)

        self.output.textChanged.connect(
            lambda: self.strength.set_result(
                analyze_password(self.output.text())))

        note = QLabel(
            "قاعدة ذهبية: كلمة المرور العشوائية الطويلة (16+) والفريدة لكل "
            "حساب هي أقوى دفاع يديره المستخدم بنفسه.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {theme.MUTED}; font-size: 9pt;")
        lay.addWidget(note)

        root.addWidget(card)
        root.addStretch(1)

    def _load_defaults(self):
        d = (self.mw.vault.settings.get("generator_defaults", {})
             if (self.mw and self.mw.vault) else {})
        self.slider.setValue(int(d.get("length", 16)))
        self.cb_upper.setChecked(bool(d.get("upper", True)))
        self.cb_lower.setChecked(bool(d.get("lower", True)))
        self.cb_digits.setChecked(bool(d.get("digits", True)))
        self.cb_symbols.setChecked(bool(d.get("symbols", True)))
        self.cb_ambiguous.setChecked(bool(d.get("exclude_ambiguous", False)))

    def showEvent(self, event):
        self._load_defaults()
        self._regenerate()
        super().showEvent(event)

    def _regenerate(self):
        try:
            pwd = generate_password(
                length=self.slider.value(),
                upper=self.cb_upper.isChecked(),
                lower=self.cb_lower.isChecked(),
                digits=self.cb_digits.isChecked(),
                symbols=self.cb_symbols.isChecked(),
                exclude_ambiguous=self.cb_ambiguous.isChecked(),
            )
            self.output.setText(pwd)
        except ValueError as e:
            QMessageBox.warning(self, "خيارات غير صالحة", str(e))

    def _copy(self):
        pwd = self.output.text()
        if not pwd:
            return
        seconds = (self.mw.vault.settings["clipboard_clear_seconds"]
                   if (self.mw and self.mw.vault) else 30)
        self.mw.copy_to_clipboard(pwd, seconds)
        self.btn_copy.setText("تم النسخ ✓")
        QTimer.singleShot(2000, lambda: self.btn_copy.setText("نسخ"))

    def on_unlocked(self):
        """إعادة تهيئة بعد فتح الخزنة."""
        self._load_defaults()
        self._regenerate()
