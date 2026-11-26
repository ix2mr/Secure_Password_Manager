# -*- coding: utf-8 -*-
"""security_info.py — صفحة معلومات الأمان (شرح تعليمي داخل التطبيق)"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTextBrowser, QFrame,
)

from . import theme
from .widgets import TitleLabel

CONTENT = f"""
<div dir='rtl' style='line-height: 1.9;'>
<h2 style='color: {theme.PRIMARY};'>كيف يحمي «مدير كلمات المرور الآمن» بياناتك؟</h2>

<h3 style='color: {theme.PRIMARY_LIGHT};'>1) الفرق بين التشفير (Encryption) والتجزئة (Hashing)</h3>
<p><b>التشفير Encryption:</b> تحويل البيانات إلى صيغة غير مقروءة عبر مفتاح،
ويمكن <u>فكها واستعادة الأصل</u> بامتلاك المفتاح الصحيح. هذا ما يستخدمه
التطبيق لحساباتك: يجب أن نستطيع استرجاع كلمة مرورك لعرضها ونسخها، لذا
تُشفَّر بـ AES-256-GCM.</p>
<p><b>التجزئة Hashing:</b> تمرير البيانات عبر دالة رياضية باتجاه واحد
لا يمكن عكسه، ولا تُستخدم للاسترجاع، بل للتحقق من المساواة أو السلامة.
في مشروعنا لا نخزّن تجزئة لكلمات المرور العادية لأننا نحتاج النص الأصلي،
أما وسم السلامة (Auth Tag) في AES-GCM فيؤدي دور التحقق من عدم العبث.</p>

<h3 style='color: {theme.PRIMARY_LIGHT};'>2) اشتقاق المفتاح — Argon2id</h3>
<p>كلمة المرور الرئيسية نفسها لا تُستخدم مباشرة كمفتاح؛ بل تمر عبر
<b>Argon2id</b> (الفائز بمسابقة Password Hashing Competition) مع
<b>ملح عشوائي فريد 128-بت</b> لكل خزنة، وبمعاملات صعبة حسابيًا
(3 مرورات، 64 ميجابايت ذاكرة، 4 خيوط) لجعل هجمات التخمين بالحاسبات
الحديثة مكلفة جدًا وبطيئة. المفتاح الناتج 256-بت يعيش في الذاكرة فقط
ويُمسح عند القفل أو الخروج، ولا يُكتب على القرص أبدًا.</p>

<h3 style='color: {theme.PRIMARY_LIGHT};'>3) التشفير المتحقق من سلامته — AES-256-GCM</h3>
<p>كل بيانات الخزنة (الحسابات والإعدادات) تُشفَّر دفعة واحدة بـ
<b>AES-256-GCM</b> مع <b>nonce فريد عشوائي 96-بت</b> في كل عملية حفظ،
ووسم سلامة (Auth Tag) يتحقق من عدم تعديل أي بايت. إضافةً إلى ذلك يُربط
رأس الملف (الملح + معاملات الاشتقاق + nonce) كبيانات مُوثَّقة (AAD)
بوسم السلامة، فأي تبديل أو تعديل خارجي في الرأس أو النص المشفّر يفشل
فك التشفير فورًا بمحاولة واحدة.</p>

<h3 style='color: {theme.PRIMARY_LIGHT};'>4) حماية أثناء الاستخدام</h3>
<ul>
<li>كلمات المرور مخفية افتراضيًا (••••) وتظهر فقط بطلب صريح منك.</li>
<li>النسخ إلى الحافظة يُمسح تلقائيًا بعد المدة المحددة في الإعدادات.</li>
<li>القفل التلقائي عند الخمول يمسح المفتاح من الذاكرة ويعيد فتح الخزنة
بالكلمة الرئيسية.</li>
<li>الملف يُكتب بعملية ذرّية (كتابة لملف مؤقت ثم استبدال) لتجنب التلف.</li>
<li>رسائل الخطأ عامة ولا تكشف أي معلومة حساسة في السجلات أو الشاشة.</li>
</ul>

<h3 style='color: {theme.PRIMARY_LIGHT};'>5) حدود الحماية — بشفافية</h3>
<p style='background-color:#FFF6E5; padding:10px; border-radius:8px;'>
<b>لا يوجد أي نظام آمن بنسبة 100%.</b> أقوى نقطة في هذا النظام هي كلمة
المرور الرئيسية؛ إذا سُرقت أو كانت ضعيفة فقد يتجاوز المهاجم كل التشفير.
كما أن أي برنامج يعمل بصلاحيات مدير على جهازك قد يقرأ الذاكرة أو يلتقط
الشاشة. الحماية الحقيقية طبقات: كلمة رئيسية قوية + تحديث النظام + عدم
تشغيل برامج مشبوهة + تفعيل التحقق بخطوتين في المواقع المهمة.</p>

<h3 style='color: {theme.PRIMARY_LIGHT};'>6) خوارزميات مرفوضة عمدًا</h3>
<p>لا يستخدم التطبيق أي خوارزمية قديمة أو مجزوءة مثل DES أو 3DES أو RC4
أو MD5 أو SHA-1، ولا يخزن أي كلمة مرور كنص صريح على القرص أو في سجل.</p>
</div>
"""


class SecurityInfoScreen(QWidget):
    def __init__(self, main_window=None, parent=None):
        super().__init__(parent)
        self.mw = main_window
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)

        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(
            f"#Card {{ background: {theme.CARD}; border-radius: 14px;"
            f" border: 1px solid {theme.BORDER}; }}")
        lay = QVBoxLayout(card)
        lay.setContentsMargins(20, 14, 20, 14)

        browser = QTextBrowser()
        browser.setHtml(CONTENT)
        browser.setOpenExternalLinks(False)
        browser.setStyleSheet(
            f"QTextBrowser {{ background: {theme.CARD}; border: none; }}")
        lay.addWidget(browser)
        root.addWidget(card)
