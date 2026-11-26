# ملاحظة تسليم حزمة التثبيت — اقرأها قبل البناء

## ما الذي سُلّم بالضبط؟

سُلّم داخل هذا المجلد **مجموعة البناء الكاملة** التي تُنتج الملفين المطلوبين على أي جهاز Windows:

| الملف المطلوب | كيف يُنتَج | الأمر |
|---|---|---|
| `SecurePasswordManager.exe` | PyInstaller من `SecurePasswordManager.spec` | `build_exe.bat` |
| `SecurePasswordManager_Setup.exe` | Inno Setup 6 من `installer/SecurePasswordManager.iss` | `build_installer.bat` |
| الاثنان معًا بالترتيب الصحيح | — | `build_all.bat` (أمر واحد) |

## لماذا لم نسلّم ملفي EXE جاهزين مباشرة؟

بيئة تجهيز المشروع كانت Linux، و **PyInstaller لا ينتج ملفات Windows إلا من داخل Windows نفسه**
(لا يدعم البناء المتقاطع Cross-Compilation رسميًا). ولانطلاقًا لقاعدة المشروع «لا تُدّعي ما لم
تُنفّذه فعلًا»، لم نُنشئ ملفات EXE/Setup هنا ولم نزوّرها، بل سلّمنا **كل ملفات البناء الجاهزة**
التي تُنتجهما بتنفيذ أمر واحد (`build_all.bat`) على جهاز Windows، مع شرح كامل خطوة بخطوة أدناه.

## خطوات الإنتاج على Windows 10/11 (خمس دقائق تقريبًا)

1. **ثبّت Python 3.10 أو أحدث** من [python.org/downloads](https://www.python.org/downloads/)
   مع تفعيل خيار **Add python.exe to PATH**.
2. **ثبّت Inno Setup 6** (مجاني) من [jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php).
3. انسخ مجلد `Application` كاملًا إلى جهاز Windows.
4. شغّل **`build_all.bat`** بالنقر المزدوج. سيقوم السكربت تلقائيًا بـ:
   - إنشاء بيئة بناء معزولة `.venv-build` وتثبيت المكتبات من `requirements.txt` + PyInstaller.
   - تنفيذ `SecurePasswordManager.spec` لإنتاج **`dist\SecurePasswordManager.exe`**
     (ملف واحد يحوي كل المكتبات والخطوط والأصول — يعمل دون تثبيت Python على جهاز المستخدم).
   - تنفيذ `installer\SecurePasswordManager.iss` عبر ISCC لإنتاج
     **`installer\Output\SecurePasswordManager_Setup.exe`**.
5. جرّب `Setup.exe`: تثبيت → اختصار سطح المكتب + قائمة ابدأ → تشغيل → إزالة تثبيت.

## ما يفعله المثبّت بالضبط؟

- يثبّت التطبيق في `C:\Program Files\SecurePasswordManager` (يطلب صلاحيات المدير).
- ينشئ **اختصارًا على سطح المكتب** و **عنصرًا في قائمة ابدأ** + مدخل إزالة التثبيت.
- **بيانات المستخدم تُحفظ في `%APPDATA%\SecurePasswordManager`** (ملف الخزنة المشفرة
  `vault.spm`)، وهي منفصلة تمامًا عن مجلد التثبيت، وتُستبدل نسخة البرنامج دون أن تُمسّ.
- عند **إزالة التثبيت**: تُحذف ملفات البرنامج فقط، وتبقى بيانات المستخدم، ثم تظهر رسالة
  تسأل صراحة: هل تريد حذف بيانات المستخدم؟ (نعم = حذف نهائي، لا = الاحتفاظ بها).

## التحقق بعد البناء (قائمة تحقق سريعة)

- [ ] `dist\SecurePasswordManager.exe` يعمل بالنقر المزدوج على جهاز **بدون Python**.
- [ ] `Setup.exe` يُكمل التثبيت وينشئ الاختصارين.
- [ ] التطبيق المثبت ينشئ الخزنة في `%APPDATA%\SecurePasswordManager\vault.spm`.
- [ ] إزالة التثبيت تحذف ملفات البرنامج وتبقي الخزنة، وتسأل عن حذفها صراحة.
