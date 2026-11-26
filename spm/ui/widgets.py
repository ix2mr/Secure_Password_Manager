# -*- coding: utf-8 -*-
"""
widgets.py — مكونات واجهة مشتركة (بطاقات، أشرطة قوة، تنبيهات Toast)
"""
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QWidget, QLabel, QProgressBar, QVBoxLayout, QHBoxLayout, QFrame,
    QPushButton, QSizePolicy,
)

from . import theme


def hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"color: {theme.BORDER}; background: {theme.BORDER};"
                       "max-height: 1px; border: none;")
    return line


class TitleLabel(QLabel):
    def __init__(self, text, size=16, color=None, parent=None):
        super().__init__(text, parent)
        f = theme.app_font(size, bold=True)
        self.setFont(f)
        self.setStyleSheet(f"color: {color or theme.PRIMARY}; background: transparent;")


class StatCard(QWidget):
    """بطاقة إحصائية: أيقونة/رقم كبير + عنوان + وصف، بلون مميز."""
    clicked = Signal()

    def __init__(self, title, value="--", subtitle="", color=None, parent=None):
        super().__init__(parent)
        self.setObjectName("StatCard")
        color = color or theme.PRIMARY_LIGHT
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(4)
        self.value_label = QLabel(str(value))
        self.value_label.setFont(theme.app_font(24, bold=True))
        self.value_label.setStyleSheet(f"color: {color}; background: transparent;")
        self.title_label = QLabel(title)
        self.title_label.setFont(theme.app_font(10.5, bold=True))
        self.title_label.setStyleSheet(f"color: {theme.TEXT}; background: transparent;")
        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(
            f"color: {theme.MUTED}; background: transparent; font-size: 8.5pt;")
        self.subtitle_label.setWordWrap(True)
        lay.addWidget(self.title_label)
        lay.addWidget(self.value_label)
        lay.addWidget(self.subtitle_label)

    def set_value(self, value, color=None):
        self.value_label.setText(str(value))
        if color:
            self.value_label.setStyleSheet(
                f"color: {color}; background: transparent;")


class StrengthBar(QWidget):
    """شريط قوة كلمة المرور مع نص المستوى."""
    def __init__(self, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)
        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(12)
        self.level_label = QLabel("—")
        self.level_label.setStyleSheet(
            f"color: {theme.MUTED}; background: transparent; font-size: 9pt;")
        lay.addWidget(self.bar)
        lay.addWidget(self.level_label)

    def set_result(self, analysis: dict):
        score = analysis["score"]
        level = analysis["level"]
        color = theme.STRENGTH_COLORS.get(level, theme.WARNING)
        self.bar.setValue(score)
        self.bar.setStyleSheet(
            f"QProgressBar {{ background: #E4EAF1; border-radius: 6px; }}"
            f"QProgressBar::chunk {{ background: {color}; border-radius: 6px; }}")
        self.level_label.setText(
            f"{level} — {score}/100  (إنتروبيا ≈ {analysis['entropy_bits']} بت)")
        self.level_label.setStyleSheet(
            f"color: {color}; background: transparent; font-weight: bold; font-size: 9.5pt;")


class Toast(QLabel):
    """تنبيه عائم يظهر أسفل النافذة ثم يختفي تلقائيًا."""
    def __init__(self, parent):
        super().__init__(parent)
        self.setStyleSheet(
            f"background: {theme.PRIMARY}; color: white; "
            "border-radius: 10px; padding: 10px 18px; font-weight: bold;")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.hide()
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.hide)

    def show_message(self, text: str, seconds: int = 3000):
        self.setText(text)
        self.adjustSize()
        pw = self.parentWidget().width()
        ph = self.parentWidget().height()
        self.move((pw - self.width()) // 2, ph - self.height() - 28)
        self.show()
        self.raise_()
        self._timer.start(seconds)


class IconButton(QPushButton):
    """زر صغير للجدول (إظهار/نسخ/تعديل/حذف)."""
    def __init__(self, text, kind="ghost", tooltip="", parent=None):
        super().__init__(text, parent)
        self.setToolTip(tooltip)
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        if kind == "danger":
            self.setStyleSheet(
                f"background: {theme.DANGER}; color: white; border: none;"
                "border-radius: 6px; padding: 4px 10px; font-weight: bold;")
        elif kind == "primary":
            self.setStyleSheet(
                f"background: {theme.PRIMARY_LIGHT}; color: white; border: none;"
                "border-radius: 6px; padding: 4px 10px; font-weight: bold;")
        elif kind == "warn":
            self.setStyleSheet(
                f"background: {theme.WARNING}; color: white; border: none;"
                "border-radius: 6px; padding: 4px 10px; font-weight: bold;")
        else:
            self.setStyleSheet(
                f"background: white; color: {theme.PRIMARY_LIGHT};"
                f"border: 1px solid {theme.BORDER}; border-radius: 6px;"
                "padding: 4px 10px; font-weight: bold;")
