# -*- coding: utf-8 -*-
"""settings.py — الإعدادات: القفل التلقائي، الحافظة، تغيير الكلمة الرئيسية"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QFrame, QSpinBox, QGroupBox, QMessageBox, QFormLayout, QScrollArea,
)

from . import theme
from .widgets import TitleLabel, hline
from ..vault import VaultError, WrongPasswordError, IntegrityError


class SettingsScreen(QWidget):
    saved = Signal()
    master_changed = Signal()

    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.mw = main_window
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 20, 28, 20)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        content = QWidget()
        lay = QVBoxLayout(content)
        lay.setSpacing(12)

        title = TitleLabel("الإعدادات", 16)
        lay.addWidget(title)

        # ----- إعدادات الأمان -----
        g1 = QGroupBox("إعدادات الأمان")
        f1 = QFormLayout(g1)
        f1.setSpacing(10)
        self.auto_lock = QSpinBox()
        self.auto_lock.setRange(1, 60)
        self.auto_lock.setSuffix(" دقيقة")
        self.auto_lock.setToolTip(
            "يُقفل التطبيق تلقائيًا ويمسح المفتاح من الذاكرة بعد هذه المدة "
            "من عدم النشاط")
        self.clipboard = QSpinBox()
        self.clipboard.setRange(10, 300)
        self.clipboard.setSuffix(" ثانية")
        self.clipboard.setToolTip(
            "تُمسح كلمة المرور من حافظة النظام تلقائيًا بعد هذه المدة")
        f1.addRow("القفل التلقائي عند الخمول:", self.auto_lock)
        f1.addRow("مسح كلمة المرور من الحافظة بعد:", self.clipboard)
        btn_save = QPushButton("حفظ الإعدادات")
        btn_save.setObjectName("primary")
        btn_save.setFixedWidth(180)
        btn_save.clicked.connect(self._save_settings)
        f1.addRow("", btn_save)
        lay.addWidget(g1)

        # ----- تغيير كلمة المرور الرئيسية -----
        g2 = QGroupBox("تغيير كلمة المرور الرئيسية")
        f2 = QFormLayout(g2)
        f2.setSpacing(10)
        self.old_pwd = QLineEdit()
        self.old_pwd.setEchoMode(QLineEdit.Password)
        self.new_pwd = QLineEdit()
        self.new_pwd.setEchoMode(QLineEdit.Password)
        self.confirm_pwd = QLineEdit()
        self.confirm_pwd.setEchoMode(QLineEdit.Password)
        f2.addRow("الكلمة الحالية:", self.old_pwd)
        f2.addRow("الكلمة الجديدة:", self.new_pwd)
        f2.addRow("تأكيد الكلمة الجديدة:", self.confirm_pwd)
        note = QLabel("يُنشأ ملح (Salt) جديد فريد عند التغيير وتُعاد تشفير "
                      "الخزنة بالكامل بالمفتاح المُشتق من الكلمة الجديدة.")
        note.setWordWrap(True)
        note.setStyleSheet(f"color: {theme.MUTED}; font-size: 8.5pt;")
        f2.addRow("", note)
        btn_change = QPushButton("تغيير كلمة المرور الرئيسية")
        btn_change.setObjectName("primary")
        btn_change.setFixedWidth(240)
        btn_change.clicked.connect(self._change_master)
        f2.addRow("", btn_change)
        lay.addWidget(g2)

        # ----- معلومات ملف الخزنة -----
        g3 = QGroupBox("ملف الخزنة")
        f3 = QFormLayout(g3)
        self.path_label = QLabel("—")
        self.path_label.setWordWrap(True)
        self.path_label.setTextInteractionFlags(
            Qt.TextSelectableByMouse)
        f3.addRow("المسار:", self.path_label)
        self.meta_label = QLabel("—")
        self.meta_label.setWordWrap(True)
        f3.addRow("معلومات:", self.meta_label)
        lay.addWidget(g3)

        lay.addStretch(1)
        scroll.setWidget(content)
        outer.addWidget(scroll)

    def refresh(self):
        if not (self.mw and self.mw.vault):
            return
        v = self.mw.vault
        self.auto_lock.setValue(int(v.settings["auto_lock_minutes"]))
        self.clipboard.setValue(int(v.settings["clipboard_clear_seconds"]))
        import pathlib
        size_kb = v.path.stat().st_size / 1024
        lrm = "\u200e"
        updated = (v._data.get("updated_at", "—") if v.unlocked else "—")
        try:
            import datetime as _dt
            if updated and updated != "—":
                updated = lrm + _dt.datetime.fromisoformat(updated).strftime(
                    "%Y-%m-%d | %H:%M")
        except Exception:
            updated = lrm + str(updated)
        self.path_label.setText(str(v.path))
        self.meta_label.setText(
            f"الحجم: {size_kb:.1f} KB — آخر تحديث مشفّر: {updated}")

    def _save_settings(self):
        self.mw.vault.update_settings(
            auto_lock_minutes=self.auto_lock.value(),
            clipboard_clear_seconds=self.clipboard.value())
        self.mw.apply_autolock_settings()
        QMessageBox.information(self, "تم", "حُفظت الإعدادات المشفّرة في الخزنة")
        self.saved.emit()

    def _change_master(self):
        old = self.old_pwd.text()
        new = self.new_pwd.text()
        confirm = self.confirm_pwd.text()
        if not old or not new:
            QMessageBox.warning(self, "تنبيه",
                                "أكمل الحقول المطلوبة أولًا")
            return
        if new != confirm:
            QMessageBox.warning(self, "تنبيه",
                                "الكلمة الجديدة وتأكيدها غير متطابقتين")
            return
        if len(new) < 8:
            QMessageBox.warning(self, "تنبيه",
                                "الكلمة الجديدة يجب أن تكون 8 أحرف على الأقل")
            return
        try:
            self.mw.vault.change_master_password(old, new)
        except (WrongPasswordError, IntegrityError):
            QMessageBox.critical(
                self, "كلمة خاطئة",
                "الكلمة المرور الحالية غير صحيحة — لم يتم أي تغيير")
            self.old_pwd.clear()
            return
        except VaultError as e:
            QMessageBox.critical(self, "خطأ", str(e))
            return
        self.old_pwd.clear()
        self.new_pwd.clear()
        self.confirm_pwd.clear()
        QMessageBox.information(
            self, "تم التغيير",
            "غُيّرت كلمة المرور الرئيسية بنجاح:\n"
            "• ملح جديد فريد\n• مفتاح جديد مشتق بـ Argon2id\n"
            "• أُعيد تشفير كل البيانات")
        self.master_changed.emit()
        self.refresh()
