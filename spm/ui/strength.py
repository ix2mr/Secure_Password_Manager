# -*- coding: utf-8 -*-
"""strength.py — شاشة تحليل قوة كلمة المرور مع الفحوص والاقتراحات"""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView, QListWidget,
    QScrollArea,
)

from . import theme
from .widgets import TitleLabel, StrengthBar, IconButton
from ..passwords import analyze_password, generate_password


class StrengthScreen(QWidget):
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 20, 28, 20)

        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(
            f"#Card {{ background: {theme.CARD}; border-radius: 14px;"
            f" border: 1px solid {theme.BORDER}; }}")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(26, 22, 26, 22)
        lay.setSpacing(10)

        title = TitleLabel("تحليل قوة كلمة المرور", 16)
        lay.addWidget(title)
        desc = QLabel(
            "أدخل أي كلمة مرور لتحليلها محليًا (لا تُحفظ ولا تُرسل لأي مكان). "
            "يفحص المحلل: الطول، الفئات، الكلمات الشائعة المسرّبة، التكرار "
            "والتسلسلات، ثم يحسب الإنتروبيا ويزنّرها.")
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color: {theme.MUTED}; font-size: 9.5pt;")
        lay.addWidget(desc)

        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setEchoMode(QLineEdit.Password)
        self.input.setPlaceholderText("اكتب كلمة المرور المراد تحليلها…")
        self.input.setFixedHeight(44)
        self.input.textChanged.connect(self._analyze)
        btn_show = QPushButton("إظهار")
        btn_show.setCheckable(True)
        btn_show.setFixedWidth(74)
        btn_show.toggled.connect(
            lambda on: self.input.setEchoMode(
                QLineEdit.Normal if on else QLineEdit.Password))
        btn_show.toggled.connect(
            lambda on: btn_show.setText("إخفاء" if on else "إظهار"))
        btn_gen = QPushButton("جرّب كلمة مولَّدة")
        btn_gen.clicked.connect(
            lambda: self.input.setText(generate_password(16)))
        row.addWidget(self.input, 1)
        row.addWidget(btn_show)
        row.addWidget(btn_gen)
        lay.addLayout(row)

        self.strength = StrengthBar()
        lay.addWidget(self.strength)

        self.crack_label = QLabel("زمن التخمين المتوقع عند مهاجم Offline: —")
        self.crack_label.setStyleSheet(
            f"color: {theme.PRIMARY}; font-weight: bold; font-size: 10pt;")
        lay.addWidget(self.crack_label)

        checks_title = QLabel("نتيجة الفحوص التفصيلية:")
        checks_title.setFont(theme.app_font(10.5, bold=True))
        lay.addWidget(checks_title)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["البند", "الحالة", "التفاصيل"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setFixedHeight(210)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        lay.addWidget(self.table)

        sugg_title = QLabel("اقتراحات التحسين:")
        sugg_title.setFont(theme.app_font(10.5, bold=True))
        lay.addWidget(sugg_title)
        self.suggestions = QListWidget()
        self.suggestions.setFixedHeight(120)
        self.suggestions.setStyleSheet(
            "QListWidget { background: #FFFDF6; border: 1px solid #F2E7C6;"
            " border-radius: 8px; }"
            "QListWidget::item { padding: 4px; }")
        lay.addWidget(self.suggestions)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(card)
        outer.addWidget(scroll)

    def _analyze(self):
        pwd = self.input.text()
        a = analyze_password(pwd)
        self.strength.set_result(a)
        self.crack_label.setText(
            f"زمن التخمين المتوقع عند مهاجم Offline (10 مليار محاولة/ثانية): "
            f"{a['crack_time']}")
        self.table.setRowCount(len(a["checks"]))
        for i, (name, ok, note) in enumerate(a["checks"]):
            it_name = QTableWidgetItem(name)
            it_name.setForeground(QColor("#1A2733"))
            it_status = QTableWidgetItem("✓ سليم" if ok else "✗ مشكلة")
            it_status.setForeground(QColor(theme.SUCCESS if ok else theme.DANGER))
            it_note = QTableWidgetItem(note)
            it_note.setForeground(QColor("#1A2733"))
            self.table.setItem(i, 0, it_name)
            self.table.setItem(i, 1, it_status)
            self.table.setItem(i, 2, it_note)
        self.suggestions.clear()
        if a["suggestions"]:
            for s in a["suggestions"]:
                self.suggestions.addItem("• " + s)
        else:
            self.suggestions.addItem(
                "• ممتاز — هذه كلمة مرور قوية، ولا تُعاد استخدامها لأكثر من حساب")
