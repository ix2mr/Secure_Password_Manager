; ============================================================
; SecurePasswordManager.iss — سكربت Inno Setup 6
; ينتج: SecurePasswordManager_Setup.exe
; الوظيفة: تثبيت التطبيق كملف تنفيذي واحد، اختصار سطح المكتب
;          وقائمة ابدأ، إزالة تثبيت قياسية، والاحتفاظ ببيانات
;          المستخدم (%APPDATA%\SecurePasswordManager) بعد الإزالة
;          إلا إذا طلب المستخدم حذفها صراحةً.
; ============================================================

#define MyAppName "Secure Password Manager"
#define MyAppNameAr "مدير كلمات المرور الآمن"
#define MyAppVersion "1.0.0"
#define MyAppExe "SecurePasswordManager.exe"
#define MyAppGUID "{{B7F9C4A2-6E1D-4A8B-9C3E-2D5F8A10E7C4}"

[Setup]
AppId={#MyAppGUID}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
DefaultDirName={autopf}\SecurePasswordManager
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExe}
OutputDir=Output
OutputBaseFilename=SecurePasswordManager_Setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\assets\app_icon.ico
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; \
    GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
Source: "..\dist\{#MyAppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; Comment: "{#MyAppNameAr}"
Name: "{group}\Uninstall {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExe}"; \
    Tasks: desktopicon; Comment: "{#MyAppNameAr}"

[Run]
Filename: "{app}\{#MyAppExe}"; \
    Description: "{cm:LaunchProgram,{#MyAppName}}"; \
    Flags: nowait postinstall skipifsilent

[Code]
; ------------------------------------------------------------------
; بيانات المستخدم (ملف الخزنة المشفرة vault.spm) تُحفظ في:
;   %APPDATA%\SecurePasswordManager
; وهي منفصلة تمامًا عن مجلد التثبيت، ولا تُحذف عند إزالة البرنامج
; إلا إذا اختار المستخدم ذلك صراحة في الرسالة أدناه.
; ------------------------------------------------------------------
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserDataDir: string;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    UserDataDir := ExpandConstant('{userappdata}\SecurePasswordManager');
    if DirExists(UserDataDir) then
    begin
      if MsgBox('هل تريد حذف بيانات المستخدم المحفوظة؟' #13#10 +
                '(الخزنة المشفرة vault.spm داخل %APPDATA%\SecurePasswordManager)' #13#10 #13#10 +
                'نعم = حذف نهائي للبيانات.' #13#10 +
                'لا = الاحتفاظ بالبيانات (الخيار الافتراضي الآمن).',
                mbConfirmation, MB_YESNO) = IDYES then
        DelTree(UserDataDir, True, True, True);
    end;
  end;
end;
