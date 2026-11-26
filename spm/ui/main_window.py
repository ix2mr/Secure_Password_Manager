# -*- coding: utf-8 -*-
"""
main_window.py — النافذة الرئيسية: التنقل، القفل التلقائي، النسخ الآمن
"""
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QStackedWidget, QFrame, QButtonGroup, QMessageBox,
)

from . import theme
from .widgets import Toast
from .splash import SplashScreen
from .create_vault import CreateVaultScreen
from .unlock import UnlockScreen
from .dashboard import DashboardScreen, vault_security_score
from .accounts import AccountsScreen
from .account_form import AccountFormScreen
from .generator import GeneratorScreen
from .strength import StrengthScreen
from .settings import SettingsScreen
from .security_info import SecurityInfoScreen
from ..vault import VaultManager, default_vault_path
from ..passwords import analyze_password


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.vault = None
        self.setWindowTitle("مدير كلمات المرور الآمن — Secure Password Manager")
        self.setMinimumSize(1120, 720)
        self.resize(1180, 760)

        self._clipboard_clear_timer = QTimer(self)
        self._clipboard_clear_timer.setSingleShot(True)
        self._clipboard_clear_timer.timeout.connect(self._clear_clipboard)
        self._last_copied = ""

        self.autolock_timer = QTimer(self)
        self.autolock_timer.setSingleShot(True)
        self.autolock_timer.timeout.connect(self._auto_lock)

        # ---------- البنية ----------
        central = QWidget()
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.sidebar = QFrame()
        self.sidebar.setObjectName("Sidebar")
        self.sidebar.setFixedWidth(230)
        sb = QVBoxLayout(self.sidebar)
        sb.setContentsMargins(14, 18, 14, 18)
        sb.setSpacing(4)

        brand = QLabel("مدير كلمات المرور الآمن")
        brand.setFont(theme.app_font(12, bold=True))
        brand.setStyleSheet(f"color: white; padding: 6px 2px;")
        brand.setWordWrap(True)
        sb.addWidget(brand)
        self.user_label = QLabel("")
        self.user_label.setStyleSheet(
            "color: #A9BACD; font-size: 8.5pt; padding-bottom: 8px;")
        sb.addWidget(self.user_label)

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "لوحة التحكم"),
            ("accounts", "الحسابات"),
            ("add", "إضافة حساب"),
            ("generator", "المولّد"),
            ("strength", "تحليل القوة"),
            ("settings", "الإعدادات"),
            ("security_info", "معلومات الأمان"),
        ]
        for key, text in nav_items:
            b = QPushButton(text)
            b.setCheckable(True)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            self.nav_group.addButton(b)
            self.nav_buttons[key] = b
            sb.addWidget(b)
        sb.addStretch(1)

        btn_lock = QPushButton("قفل الخزنة الآن")
        btn_lock.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_lock.setStyleSheet(
            f"background: {theme.ACCENT}; color: white; border: none;"
            "border-radius: 8px; padding: 9px; font-weight: bold;")
        btn_lock.clicked.connect(self.lock_vault)
        sb.addWidget(btn_lock)

        btn_exit = QPushButton("خروج آمن")
        btn_exit.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_exit.setStyleSheet(
            f"background: rgba(198,40,40,0.85); color: white; border: none;"
            "border-radius: 8px; padding: 9px; font-weight: bold;")
        btn_exit.clicked.connect(self.secure_exit)
        sb.addWidget(btn_exit)

        root.addWidget(self.sidebar)

        # ---------- الشاشات ----------
        self.stack = QStackedWidget()
        root.addWidget(self.stack, 1)

        self.create_vault_screen = CreateVaultScreen(self)
        self.unlock_screen = UnlockScreen(self)
        self.dashboard_screen = DashboardScreen(self)
        self.accounts_screen = AccountsScreen(self)
        self.account_form_screen = AccountFormScreen(self)
        self.generator_screen = GeneratorScreen(self)
        self.strength_screen = StrengthScreen(self)
        self.settings_screen = SettingsScreen(self)
        self.security_info_screen = SecurityInfoScreen(self)

        for w in (self.create_vault_screen, self.unlock_screen,
                  self.dashboard_screen, self.accounts_screen,
                  self.account_form_screen, self.generator_screen,
                  self.strength_screen, self.settings_screen,
                  self.security_info_screen):
            self.stack.addWidget(w)

        self.toast = Toast(self)

        # ---------- الإشارات ----------
        self.create_vault_screen.vault_created.connect(self.on_vault_ready)
        self.unlock_screen.vault_unlocked.connect(self.on_vault_unlocked)
        self.dashboard_screen.go_add_account.connect(self.go_add_account)
        self.dashboard_screen.go_generator.connect(
            lambda: self.navigate("generator"))
        self.dashboard_screen.go_strength.connect(
            lambda: self.navigate("strength"))
        self.dashboard_screen.go_accounts.connect(
            lambda: self.navigate("accounts"))
        self.accounts_screen.request_add.connect(self.go_add_account)
        self.accounts_screen.request_edit.connect(self.go_edit_account)
        self.account_form_screen.saved.connect(self._on_form_saved)
        self.account_form_screen.cancelled.connect(
            lambda: self.navigate("accounts"))
        self.settings_screen.master_changed.connect(self._on_master_changed)
        self.nav_group.buttonClicked.connect(
            lambda btn: self._on_nav_clicked(btn))

        # تتبع النشاط لآلية القفل التلقائي
        QGuiApplication.instance().installEventFilter(self)

        self.setCentralWidget(central)

        # ---------- البداية ----------
        self._show_splash_then_route()

    # ==================================================================
    # المسار الأولي
    # ==================================================================
    def _show_splash_then_route(self):
        splash = SplashScreen(self)
        splash.exec()
        if default_vault_path().exists():
            self.vault = VaultManager(default_vault_path())
            self._show_unlock_screen("مرحبًا بعودتك — أدخل كلمة المرور "
                                     "الرئيسية لفتح الخزنة.")
        else:
            self.vault = VaultManager(default_vault_path())
            self._go_create_vault()

    def vault_path(self):
        return default_vault_path()

    def _go_create_vault(self):
        self.sidebar.hide()
        self.stack.setCurrentWidget(self.create_vault_screen)

    def _show_unlock_screen(self, message="", is_warning=False):
        self.sidebar.hide()
        self.stack.setCurrentWidget(self.unlock_screen)
        if message:
            self.unlock_screen.show_message(message, is_warning)
        self.unlock_screen.reset_screen()
        self.autolock_timer.stop()

    # ==================================================================
    # فتح/إنشاء الخزنة
    # ==================================================================
    def on_vault_ready(self, vault):
        """بعد إنشاء خزنة جديدة."""
        self.on_vault_unlocked(vault, first_time=True)

    def on_vault_unlocked(self, vault, first_time=False):
        self.sidebar.show()
        self.user_label.setText(
            f"خزنة مشفّرة: {vault.path.name}")
        self.stack.setCurrentWidget(self.dashboard_screen)
        self.dashboard_screen.master_score = None
        self.refresh_all()
        self.apply_autolock_settings()

    def refresh_all(self):
        self.dashboard_screen.refresh()
        self.accounts_screen.refresh()
        self.generator_screen.on_unlocked()
        self.settings_screen.refresh()

    def refresh_dashboard_if_visible(self):
        if self.stack.currentWidget() is self.dashboard_screen:
            self.dashboard_screen.refresh()

    # ==================================================================
    # التنقل
    # ==================================================================
    def navigate(self, key):
        screens = {
            "dashboard": self.dashboard_screen,
            "accounts": self.accounts_screen,
            "add": self.account_form_screen,
            "generator": self.generator_screen,
            "strength": self.strength_screen,
            "settings": self.settings_screen,
            "security_info": self.security_info_screen,
        }
        if not self.vault or not self.vault.unlocked:
            return
        if key in ("dashboard", "accounts", "settings"):
            self.refresh_all()
        if key == "accounts":
            self.accounts_screen.revealed.clear()
        if key == "add":
            self.account_form_screen.open_add()
        self.stack.setCurrentWidget(screens[key])
        btn = self.nav_buttons.get(key)
        if btn:
            btn.setChecked(True)

    def _on_nav_clicked(self, btn):
        key = next((k for k, b in self.nav_buttons.items() if b is btn), None)
        if key:
            self.navigate(key)

    def go_add_account(self):
        self.navigate("add")

    def go_edit_account(self, account_id):
        self.account_form_screen.open_edit(account_id)
        self.stack.setCurrentWidget(self.account_form_screen)

    def _on_form_saved(self):
        self.navigate("accounts")
        self.toast.show_message("تم الحفظ — أُعيد تشفير الخزنة وكتابتها آمنة")

    def _on_master_changed(self):
        self.toast.show_message("تم تغيير كلمة المرور الرئيسية وملح التشفير")
        self.dashboard_screen.master_score = None

    # ==================================================================
    # الحافظة الآمنة
    # ==================================================================
    def copy_to_clipboard(self, text: str, clear_after_seconds: int):
        clip = QGuiApplication.clipboard()
        clip.setText(text)
        self._last_copied = text
        self._clipboard_clear_timer.start(clear_after_seconds * 1000)

    def _clear_clipboard(self):
        clip = QGuiApplication.clipboard()
        if clip.text() == self._last_copied:
            clip.clear()
        self._last_copied = ""

    # ==================================================================
    # القفل التلقائي والقفل اليدوي والخروج
    # ==================================================================
    def eventFilter(self, watched, event):
        if event.type() in (QEvent.MouseMove, QEvent.MouseButtonPress,
                            QEvent.KeyPress, QEvent.Wheel):
            if self.vault and self.vault.unlocked and \
                    self.stack.currentWidget() not in (
                        self.create_vault_screen, self.unlock_screen):
                minutes = self.vault.settings.get("auto_lock_minutes", 5)
                self.autolock_timer.start(int(minutes * 60_000))
        return super().eventFilter(watched, event)

    def apply_autolock_settings(self):
        if self.vault and self.vault.unlocked:
            minutes = self.vault.settings.get("auto_lock_minutes", 5)
            self.autolock_timer.start(int(minutes * 60_000))
        else:
            self.autolock_timer.stop()

    def _auto_lock(self):
        if not (self.vault and self.vault.unlocked):
            return
        self._clear_clipboard_now()
        self.vault.lock()
        self.accounts_screen.revealed.clear()
        self._show_unlock_screen(
            "أُقفلت الخزنة تلقائيًا بسبب عدم النشاط لحمايتك — "
            "أدخل كلمة المرور الرئيسية لاستئناف العمل.", True)

    def lock_vault(self):
        if not (self.vault and self.vault.unlocked):
            return
        self._clear_clipboard_now()
        self.vault.lock()
        self.accounts_screen.revealed.clear()
        self._show_unlock_screen("تم قفل الخزنة يدويًا. حتى نراك آمنًا!")

    def _clear_clipboard_now(self):
        self._clipboard_clear_timer.stop()
        self._clear_clipboard()

    def secure_exit(self):
        answer = QMessageBox.question(
            self, "خروج آمن",
            "سيتم إغلاق التطبيق ومسح المفتاح والبيانات الحساسة من الذاكرة "
            "ومسح الحافظة.\nهل تريد المتابعة؟",
            QMessageBox.Yes | QMessageBox.No)
        if answer == QMessageBox.Yes:
            self._clear_clipboard_now()
            if self.vault:
                self.vault.lock()
            QGuiApplication.instance().quit()

    def closeEvent(self, event):
        # إغلاق النافذة = خروج آمن أيضًا
        self._clear_clipboard_now()
        if self.vault:
            self.vault.lock()
        super().closeEvent(event)
