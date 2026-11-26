# -*- coding: utf-8 -*-
"""accounts.py — قائمة الحسابات: بحث، جدول، إظهار/نسخ كلمة المرور، تعديل/حذف"""
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QAbstractItemView, QHeaderView,
    QMessageBox, QFrame,
)

from . import theme
from .widgets import TitleLabel, IconButton, Toast
from ..passwords import analyze_password

COLUMNS = ["الموقع / الخدمة", "اسم المستخدم", "كلمة المرور",
           "الموقع الإلكتروني", "القوة", "إجراءات"]


class AccountsScreen(QWidget):
    request_edit = Signal(str)          # account_id
    request_add = Signal()

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self.revealed = set()             # معرّفات الحسابات المكشوفة حاليًا
        self._build()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(12)

        top = QHBoxLayout()
        title = TitleLabel("الحسابات المحفوظة", 16)
        top.addWidget(title)
        top.addStretch(1)
        self.btn_add = QPushButton("إضافة حساب")
        self.btn_add.setObjectName("primary")
        self.btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_add.clicked.connect(self.request_add.emit)
        top.addWidget(self.btn_add)
        root.addLayout(top)

        search_row = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setPlaceholderText(
            "بحث فوري في: اسم الموقع، اسم المستخدم، الرابط، الملاحظات…")
        self.search.setFixedHeight(40)
        self.search.textChanged.connect(self.refresh)
        self.count_label = QLabel("")
        self.count_label.setStyleSheet(f"color: {theme.MUTED};")
        search_row.addWidget(self.search, 1)
        search_row.addWidget(self.count_label)
        root.addLayout(search_row)

        self.table = QTableWidget(0, len(COLUMNS))
        self.table.setHorizontalHeaderLabels(COLUMNS)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setDefaultSectionSize(46)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Fixed)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.setColumnWidth(2, 170)
        root.addWidget(self.table, 1)

        self.toast = Toast(self)

    # ------------------------------------------------------------------
    def refresh(self):
        if not (self.mw and self.mw.vault and self.mw.vault.unlocked):
            return
        query = self.search.text()
        rows = self.mw.vault.search_accounts(query)
        self.table.setRowCount(0)
        self.table.setRowCount(len(rows))
        for i, acc in enumerate(rows):
            a = analyze_password(acc["password"])
            level_color = theme.STRENGTH_COLORS.get(a["level"], theme.WARNING)

            self.table.setItem(i, 0, self._item(acc["site_name"], bold=True))
            self.table.setItem(i, 1, self._item(acc["username"]))

            # خلية كلمة المرور: إخفاء/إظهار + نسخ
            pwd_widget = QWidget()
            pl = QHBoxLayout(pwd_widget)
            pl.setContentsMargins(6, 2, 6, 2)
            pl.setSpacing(4)
            if acc["id"] in self.revealed:
                mask = QLabel(acc["password"])
                mask.setStyleSheet(
                    "color: #1A2733; background: transparent;"
                    "font-weight: bold;")
            else:
                mask = QLabel("••••••••••")
                mask.setStyleSheet("color: #1A2733; background: transparent;")
            pl.addWidget(mask, 1)
            if acc["id"] in self.revealed:
                show_btn = IconButton("إخفاء", "ghost", "إخفاء كلمة المرور")
            else:
                show_btn = IconButton("إظهار", "ghost", "إظهار كلمة المرور")
            show_btn.clicked.connect(
                lambda _=False, aid=acc["id"]: self._toggle_reveal(aid))
            copy_btn = IconButton("نسخ", "ghost",
                                  "نسخ إلى الحافظة مع مسح تلقائي")
            copy_btn.clicked.connect(
                lambda _=False, aid=acc["id"]: self._copy_password(aid))
            pl.addWidget(show_btn)
            pl.addWidget(copy_btn)
            self.table.setCellWidget(i, 2, pwd_widget)

            url_item = self._item(acc["url"])
            self.table.setItem(i, 3, url_item)

            strength_item = QTableWidgetItem(f"{a['level']}")
            strength_item.setForeground(QColor(level_color))
            strength_item.setTextAlignment(
                Qt.AlignmentFlag.AlignCenter)
            if a["is_weak"]:
                strength_item.setToolTip(
                    "كلمة مرور ضعيفة/شائعة — يُنصح بتغييرها من زر التعديل")
            self.table.setItem(i, 4, strength_item)

            # إجراءات: تعديل + حذف
            act = QWidget()
            al = QHBoxLayout(act)
            al.setContentsMargins(4, 2, 4, 2)
            al.setSpacing(6)
            edit_btn = IconButton("تعديل", "primary", "تعديل بيانات الحساب")
            edit_btn.clicked.connect(
                lambda _=False, aid=acc["id"]: self.request_edit.emit(aid))
            del_btn = IconButton("حذف", "danger", "حذف الحساب نهائيًا")
            del_btn.clicked.connect(
                lambda _=False, aid=acc["id"]: self._delete(aid))
            al.addWidget(edit_btn)
            al.addWidget(del_btn)
            self.table.setCellWidget(i, 5, act)

        total = len(self.mw.vault.accounts)
        shown = len(rows)
        self.count_label.setText(
            f"عرض {shown} من أصل {total} حساب" if query else
            f"{total} حساب محفوظ")
        # تحديث لوحة التحكم إن كانت الشاشة نفسها تُظهر تغيّرًا
        if self.mw:
            self.mw.refresh_dashboard_if_visible()

    @staticmethod
    def _item(text, bold=False):
        it = QTableWidgetItem(text)
        if bold:
            f = it.font()
            f.setBold(True)
            it.setFont(f)
        it.setForeground(QColor("#1A2733"))
        return it

    # ------------------------------------------------------------------
    def _toggle_reveal(self, account_id):
        if account_id in self.revealed:
            self.revealed.discard(account_id)
        else:
            self.revealed.add(account_id)
        self.refresh()

    def _copy_password(self, account_id):
        acc = self.mw.vault.get_account(account_id)
        if not acc:
            return
        seconds = self.mw.vault.settings["clipboard_clear_seconds"]
        self.mw.copy_to_clipboard(acc["password"], seconds)
        self.toast.show_message(
            f"تم نسخ كلمة مرور «{acc['site_name']}» — "
            f"ستُمسح من الحافظة تلقائيًا بعد {seconds} ثانية", 3500)

    def _delete(self, account_id):
        acc = self.mw.vault.get_account(account_id)
        if not acc:
            return
        answer = QMessageBox.question(
            self, "تأكيد الحذف",
            f"سيُحذف الحساب «{acc['site_name']} — {acc['username']}» "
            "نهائيًا من الخزنة.\nهل أنت متأكد؟",
            QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            self.mw.vault.delete_account(account_id)
            self.revealed.discard(account_id)
            self.toast.show_message("تم حذف الحساب وإعادة تشفير الخزنة")
            self.refresh()
