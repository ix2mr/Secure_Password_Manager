# -*- coding: utf-8 -*-
"""
theme.py — الهوية البصرية للتطبيق (الألوان، الخطوط، التنسيقات QSS)
===================================================================
"""

import pathlib

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase, QPixmap, QIcon

APP_DIR = pathlib.Path(__file__).resolve().parents[2]   # جذر مجلد التطبيق
ASSETS_DIR = APP_DIR / "assets"
FONTS_DIR = APP_DIR / "fonts"

# ---------------------------------------------------------------------------
# لوحة الألوان
# ---------------------------------------------------------------------------
PRIMARY = "#16324F"       # كحلي داكن (الشريط الجانبي والعناوين)
PRIMARY_LIGHT = "#1D5B8C" # أزرق أساسي (الأزرار الرئيسية)
ACCENT = "#0E9594"        # تركواز (تمييز)
BG = "#F2F5F9"            # خلفية عامة
CARD = "#FFFFFF"          # خلفية البطاقات
BORDER = "#C9D3DF"
TEXT = "#1A2733"
MUTED = "#5B6B7C"
SUCCESS = "#2E7D32"
WARNING = "#E6A817"
DANGER = "#C62828"
SIDEBAR_TEXT = "#E8EEF5"

STRENGTH_COLORS = {
    "ضعيفة جدًا": DANGER,
    "ضعيفة": "#E0532F",
    "متوسطة": WARNING,
    "قوية": "#7BA428",
    "قوية جدًا": SUCCESS,
}

_font_family = None


def load_app_fonts() -> str:
    """
    تحميل خطوط Noto Sans Arabic المرفقة مع التطبيق.
    إن تعذر التحميل (مثلًا ملفات مفقودة) نرجع لخط النظام Segoe UI
    الذي يدعم العربية على Windows.
    يعيد اسم عائلة الخط المستخدم.
    """
    global _font_family
    if _font_family:
        return _font_family
    loaded_ok = False
    for name in ("NotoSansArabic-Regular.ttf", "NotoSansArabic-Bold.ttf"):
        p = FONTS_DIR / name
        if p.exists():
            fid = QFontDatabase.addApplicationFont(str(p))
            if fid >= 0:
                families = QFontDatabase.applicationFontFamilies(fid)
                if families:
                    loaded_ok = True
    _font_family = "Noto Sans Arabic" if loaded_ok else "Segoe UI"
    return _font_family


def app_font(size: int = 10, bold: bool = False) -> QFont:
    f = QFont(load_app_fonts(), size)
    f.setBold(bold)
    return f


def app_logo_pixmap(size: int = 96) -> QPixmap:
    pm = QPixmap(str(ASSETS_DIR / "app_logo.png"))
    if pm.isNull():
        return QPixmap()
    return pm.scaled(size, size, Qt.KeepAspectRatio,
                     Qt.SmoothTransformation)


def app_icon() -> QIcon:
    return QIcon(str(ASSETS_DIR / "app_logo.png"))


# ---------------------------------------------------------------------------
# ورقة التنسيق العامة (QSS)
# ---------------------------------------------------------------------------
load_app_fonts()   # تحميل الخطوط المرفقة قبل بناء ورقة التنسيق
FONT_FAMILY = _font_family if _font_family else "Segoe UI"

QSS = f"""
QWidget {{
    font-family: "{FONT_FAMILY}";
    color: {TEXT};
    font-size: 10pt;
}}
QMainWindow, QDialog {{
    background: {BG};
}}
/* ---- الحقول ---- */
QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 12px;
    selection-background-color: {PRIMARY_LIGHT};
}}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {{
    border: 2px solid {PRIMARY_LIGHT};
}}
QLineEdit:disabled {{
    background: #EEF1F5;
    color: {MUTED};
}}
/* ---- الأزرار ---- */
QPushButton {{
    background: {CARD};
    border: 1px solid {BORDER};
    border-radius: 8px;
    padding: 8px 16px;
}}
QPushButton:hover {{
    border-color: {PRIMARY_LIGHT};
    background: #F5F8FC;
}}
QPushButton#primary {{
    background: {PRIMARY_LIGHT};
    color: white;
    border: none;
    font-weight: bold;
    padding: 10px 22px;
}}
QPushButton#primary:hover {{
    background: #17497A;
}}
QPushButton#primary:pressed {{
    background: {PRIMARY};
}}
QPushButton#danger {{
    background: {DANGER};
    color: white;
    border: none;
    font-weight: bold;
    padding: 8px 16px;
}}
QPushButton#danger:hover {{
    background: #A61E23;
}}
QPushButton#ghost {{
    background: transparent;
    border: 1px solid {BORDER};
    color: {PRIMARY};
    font-weight: bold;
}}
QPushButton:disabled {{
    color: #9AA7B4;
    background: #EDF0F4;
    border-color: #DDE3EA;
}}
/* ---- الشريط الجانبي ---- */
#Sidebar {{
    background: {PRIMARY};
}}
#Sidebar QLabel {{
    color: {SIDEBAR_TEXT};
}}
#Sidebar QPushButton {{
    background: transparent;
    color: {SIDEBAR_TEXT};
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    text-align: right;
    font-size: 10.5pt;
}}
#Sidebar QPushButton:hover {{
    background: rgba(255,255,255,0.10);
}}
#Sidebar QPushButton:checked {{
    background: {PRIMARY_LIGHT};
    color: white;
    font-weight: bold;
}}
/* ---- البطاقات ---- */
#Card {{
    background: {CARD};
    border: 1px solid #E1E7EE;
    border-radius: 12px;
}}
#StatCard {{
    background: {CARD};
    border: 1px solid #E1E7EE;
    border-radius: 12px;
}}
/* ---- الجداول ---- */
QTableWidget {{
    background: {CARD};
    border: 1px solid #E1E7EE;
    border-radius: 10px;
    gridline-color: #EDF1F6;
    alternate-background-color: #F7FAFD;
}}
QTableWidget::item {{
    padding: 6px;
}}
QTableWidget::item:selected {{
    background: #DCE9F7;
    color: {TEXT};
}}
QHeaderView::section {{
    background: #E8EEF5;
    color: {PRIMARY};
    font-weight: bold;
    border: none;
    padding: 8px;
}}
/* ---- شريط التقدم ---- */
QProgressBar {{
    background: #E4EAF1;
    border: none;
    border-radius: 7px;
    min-height: 14px;
    text-align: center;
    color: white;
    font-size: 8.5pt;
}}
/* ---- عناصر أخرى ---- */
QCheckBox, QRadioButton {{
    spacing: 8px;
    padding: 3px;
}}
QCheckBox::indicator, QRadioButton::indicator {{
    width: 17px; height: 17px;
}}
QGroupBox {{
    background: {CARD};
    border: 1px solid #E1E7EE;
    border-radius: 12px;
    margin-top: 12px;
    padding-top: 16px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    right: 14px;
    padding: 0 6px;
    color: {PRIMARY};
}}
QScrollBar:vertical {{
    background: transparent; width: 10px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #B9C6D4; border-radius: 5px; min-height: 30px;
}}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QToolTip {{
    background: {PRIMARY}; color: white; border: none; padding: 6px;
}}
"""
