# -*- coding: utf-8 -*-
"""dashboard.py — لوحة التحكم الرئيسية: إحصاءات الأمان والوصول السريع"""
import datetime

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QListWidget, QListWidgetItem,
)

from . import theme
from .widgets import TitleLabel, StatCard, hline
from ..passwords import find_weak_accounts, find_duplicate_accounts, \
    improvement_suggestions, analyze_password

SECURITY_LEVELS = [
    (85, "ممتاز", theme.SUCCESS),
    (65, "جيد", "#7BA428"),
    (45, "متوسط", theme.WARNING),
    (0, "ضعيف", theme.DANGER),
]


def vault_security_score(accounts, master_score=None) -> int:
    """حساب درجة أمان الخزنة (0-100) من حالة كلمات مرور الحسابات."""
    weak = len(find_weak_accounts(accounts))
    dups = len(find_duplicate_accounts(accounts))
    score = 100 - weak * 12 - dups * 10
    if master_score is not None:
        score -= max(0, (60 - master_score) // 3)
    return max(0, min(100, score))


class DashboardScreen(QWidget):
    go_add_account = Signal()
    go_generator = Signal()
    go_strength = Signal()
    go_accounts = Signal()

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self.master_score = None
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 20, 28, 20)
        outer.setSpacing(14)

        header = TitleLabel("لوحة التحكم الرئيسية", 17)
        outer.addWidget(header)

        self.welcome = QLabel("")
        self.welcome.setStyleSheet(f"color: {theme.MUTED}; font-size: 9.5pt;")
        self.welcome.setWordWrap(True)
        outer.addWidget(self.welcome)

        # ----- بطاقات الإحصاءات -----
        grid = QGridLayout()
        grid.setSpacing(12)
        self.card_total = StatCard("إجمالي الحسابات", "--",
                                   "عدد الحسابات المحفوظة في الخزنة",
                                   theme.PRIMARY_LIGHT)
        self.card_weak = StatCard("كلمات مرور ضعيفة", "--",
                                  "ضعيفة أو قصيرة أو شائعة مسرّبة",
                                  theme.DANGER)
        self.card_dup = StatCard("كلمات مكررة", "--",
                                 "حسابات تشارك الكلمة نفسها",
                                 theme.WARNING)
        self.card_level = StatCard("مستوى أمان الخزنة", "--",
                                   "محسوب من كلمات المرور المحفوظة",
                                   theme.SUCCESS)
        grid.addWidget(self.card_total, 0, 0)
        grid.addWidget(self.card_weak, 0, 1)
        grid.addWidget(self.card_dup, 0, 2)
        grid.addWidget(self.card_level, 0, 3)
        outer.addLayout(grid)

        # ----- إجراءات سريعة -----
        actions = QFrame()
        actions.setObjectName("Card")
        actions.setStyleSheet(
            f"#Card {{ background: {theme.CARD}; border-radius: 12px;"
            f" border: 1px solid {theme.BORDER}; }}")
        al = QHBoxLayout(actions)
        al.setContentsMargins(16, 12, 16, 12)
        al.setSpacing(10)
        lbl = QLabel("إجراءات سريعة:")
        lbl.setFont(theme.app_font(10.5, bold=True))
        lbl.setStyleSheet(f"color: {theme.PRIMARY};")
        al.addWidget(lbl)
        b1 = QPushButton("إضافة حساب جديد")
        b1.setObjectName("primary")
        b1.clicked.connect(self.go_add_account.emit)
        b2 = QPushButton("مولّد كلمات المرور")
        b2.clicked.connect(self.go_generator.emit)
        b3 = QPushButton("تحليل قوة كلمة")
        b3.clicked.connect(self.go_strength.emit)
        b4 = QPushButton("عرض كل الحسابات")
        b4.clicked.connect(self.go_accounts.emit)
        for b in (b1, b2, b3, b4):
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            al.addWidget(b)
        al.addStretch(1)
        outer.addWidget(actions)

        # ----- توصيات ومعلومات -----
        bottom = QHBoxLayout()
        bottom.setSpacing(12)

        rec_frame = QFrame()
        rec_frame.setObjectName("Card")
        rec_frame.setStyleSheet(
            f"#Card {{ background: {theme.CARD}; border-radius: 12px;"
            f" border: 1px solid {theme.BORDER}; }}")
        rl = QVBoxLayout(rec_frame)
        rl.setContentsMargins(16, 12, 16, 12)
        t1 = TitleLabel("توصيات أمنية لخزنتك", 12)
        rl.addWidget(t1)
        self.recommendations = QListWidget()
        self.recommendations.setStyleSheet(
            "QListWidget { background: white; border: none; }"
            "QListWidget::item { padding: 5px; border-bottom: 1px solid #F0F3F7; }")
        rl.addWidget(self.recommendations)

        info_frame = QFrame()
        info_frame.setObjectName("Card")
        info_frame.setStyleSheet(
            f"#Card {{ background: {theme.CARD}; border-radius: 12px;"
            f" border: 1px solid {theme.BORDER}; }}")
        il = QVBoxLayout(info_frame)
        il.setContentsMargins(16, 12, 16, 12)
        t2 = TitleLabel("معلومات الخزنة", 12)
        il.addWidget(t2)
        self.info_labels = QLabel("")
        self.info_labels.setStyleSheet("color: #1A2733; font-size: 9.5pt;"
                                       " background: transparent;")
        self.info_labels.setWordWrap(True)
        il.addWidget(self.info_labels)
        il.addStretch(1)

        bottom.addWidget(rec_frame, 3)
        bottom.addWidget(info_frame, 2)
        outer.addLayout(bottom, 1)

    # ------------------------------------------------------------------
    def refresh(self):
        if not (self.mw and self.mw.vault and self.mw.vault.unlocked):
            return
        accounts = self.mw.vault.accounts
        weak = find_weak_accounts(accounts)
        dups = find_duplicate_accounts(accounts)
        score = vault_security_score(accounts, self.master_score)

        self.card_total.set_value(len(accounts))
        self.card_weak.set_value(len(weak),
                                 theme.DANGER if weak else theme.SUCCESS)
        self.card_dup.set_value(sum(d["count"] for d in dups),
                                theme.WARNING if dups else theme.SUCCESS)
        level_text, level_color = next(
            (t, c) for th, t, c in SECURITY_LEVELS if score >= th)
        self.card_level.set_value(f"{score}%", level_color)
        self.card_level.title_label.setText(f"أمان الخزنة: {level_text}")

        self.welcome.setText(
            "أهلًا بك في خزنتك المشفّرة. جميع البيانات محفوظة محليًا على "
            "جهازك بتشفير AES-256-GCM ولا تُرسل إلى أي جهة خارجية.")

        # توصيات
        self.recommendations.clear()
        for s in improvement_suggestions(accounts):
            self.recommendations.addItem("• " + s)
        if self.master_score is not None:
            self.recommendations.addItem(
                f"• قوة كلمة المرور الرئيسية نفسها: "
                f"{self.master_score}/100 — قوّتها أساس حماية كل ما داخل الخزنة")

        v = self.mw.vault
        import pathlib
        size_kb = v.path.stat().st_size / 1024
        updated = v._data.get("updated_at", "—") if v.unlocked else "—"
        # تنسيق قراءة واضح مع علامة اتجاه LTR للتاريخ
        lrm = "\u200e"

        def fmt_ts(s):
            if not s or s == "—":
                return "—"
            try:
                d = datetime.datetime.fromisoformat(s)
                return lrm + d.strftime("%Y-%m-%d | %H:%M")
            except Exception:
                return lrm + s

        self.info_labels.setText(
            f"ملف الخزنة: {v.path.name}\n"
            f"المجلد: {v.path.parent.name}\n\n"
            f"الحجم المشفّر: {size_kb:.1f} KB\n"
            f"تاريخ الإنشاء: {fmt_ts(v.created_at)}\n"
            f"آخر تحديث مشفّر: {fmt_ts(updated)}\n"
            f"القفل التلقائي: {v.settings['auto_lock_minutes']} دقيقة\n"
            f"مسح الحافظة بعد: {v.settings['clipboard_clear_seconds']} ثانية")
