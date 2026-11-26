# -*- coding: utf-8 -*-
"""
vault.py — إدارة الخزنة المشفّرة والتخزين المحلي
================================================
بنية ملف الخزنة (JSON) على القرص:
  {
    "format": "SecurePasswordManager-Vault",
    "format_version": 1,
    "kdf":  { خوارزمية Argon2id + الملح + المعاملات },
    "cipher": { AES-256-GCM + nonce },
    "aad": {...},          # بيانات مُوثَّقة تُربط سلامتها بالتشفير
    "ciphertext": {...}    # نص مشفّر Base64 (يشمل وسم السلامة)
  }
النص الصريح (الحسابات والإعدادات) لا يُكتب أبدًا على القرص؛
يوجد فقط داخل النص المشفّر، ولا يُفك إلا بكلمة المرور الرئيسية.
"""

import os
import json
import uuid
import pathlib
import datetime

from .crypto import (
    KDF_ALGORITHM, KDF_TIME_COST, KDF_MEMORY_COST, KDF_PARALLELISM,
    CIPHER_ALGORITHM, SALT_LEN,
    generate_salt, generate_nonce, derive_key, encrypt_bytes, decrypt_bytes,
    b64_encode, b64_decode, wipe_buffer, IntegrityError, CryptoError,
)

FORMAT_NAME = "SecurePasswordManager-Vault"
FORMAT_VERSION = 1
INNER_MAGIC = "SPM-INNER-OK"   # ثابت داخلي للتحقق من فك التشفير الناجح


class VaultError(Exception):
    """خطأ عام في الخزنة."""


class VaultAlreadyExistsError(VaultError):
    """محاولة إنشاء خزنة فوق خزنة موجودة."""


class VaultFileNotFoundError(VaultError):
    """محاولة فتح خزنة غير موجودة."""


class WrongPasswordError(VaultError):
    """كلمة المرور الرئيسية خاطئة."""


DEFAULT_SETTINGS = {
    "auto_lock_minutes": 5,
    "clipboard_clear_seconds": 30,
    "generator_defaults": {
        "length": 16,
        "upper": True, "lower": True, "digits": True, "symbols": True,
        "exclude_ambiguous": False,
    },
}


def default_vault_path() -> pathlib.Path:
    """
    المسار الافتراضي لملف الخزنة:
      Windows: %APPDATA%\\SecurePasswordManager\\vault.spm
               (مثل: C:\\Users\\<user>\\AppData\\Roaming\\SecurePasswordManager\\vault.spm)
               وهو المكان القياسي لبيانات التطبيقات، ولا يُحذف عند إزالة
               البرنامج إلا بطلب صريح من المستخدم.
      Linux/macOS: ~/SecurePasswordManager/vault.spm
    يمكن تجاوزه بمتغير البيئة SPM_VAULT_PATH لأغراض الاختبار.
    """
    env = os.environ.get("SPM_VAULT_PATH")
    if env:
        return pathlib.Path(env)
    if os.name == "nt":
        appdata = os.environ.get("APPDATA") or str(pathlib.Path.home() / "AppData" / "Roaming")
        return pathlib.Path(appdata) / "SecurePasswordManager" / "vault.spm"
    return pathlib.Path.home() / "SecurePasswordManager" / "vault.spm"


def _now_iso() -> str:
    # دقة الميكروثانية لضمان تميّز ختم كل عملية حفظ/تعديل
    return datetime.datetime.now().isoformat(timespec="microseconds")


class VaultManager:
    """
    مدير الخزنة: الإنشاء، الفتح بالكلمة الرئيسية، القراءة/الكتابة المشفّرة،
    إدارة الحسابات، تغيير الكلمة الرئيسية، والقفل الآمن.
    """

    def __init__(self, path):
        self.path = pathlib.Path(path)
        self._key = None          # مفتاح 256-بت في الذاكرة فقط
        self._data = None         # البيانات الداخلية (حسابات/إعدادات)
        self.unlocked = False
        self.created_at = None
        self._salt = None
        self._kdf_params = dict(
            time_cost=KDF_TIME_COST,
            memory_cost=KDF_MEMORY_COST,
            parallelism=KDF_PARALLELISM,
        )

    # ------------------------------------------------------------------
    # بناء رأس الملف (Header) — يُستخدم كـ AAD لربط سلامته بالنص المشفّر
    # ------------------------------------------------------------------
    def _header(self, nonce_b64: str) -> dict:
        return {
            "format": FORMAT_NAME,
            "format_version": FORMAT_VERSION,
            "kdf": {
                "algorithm": KDF_ALGORITHM,
                "salt": b64_encode(self._salt),
                "time_cost": self._kdf_params["time_cost"],
                "memory_cost_kib": self._kdf_params["memory_cost"],
                "parallelism": self._kdf_params["parallelism"],
                "derived_key_len_bits": 256,
            },
            "cipher": {"algorithm": CIPHER_ALGORITHM, "nonce": nonce_b64},
        }

    @staticmethod
    def _aad_from_header(header: dict) -> bytes:
        """AAD: تمثيل ثابت للرأس بحيث أي تعديل على الملح/المعاملات يُكتشف."""
        canonical = json.dumps(header, sort_keys=True,
                               separators=(",", ":"), ensure_ascii=False)
        return canonical.encode("utf-8")

    # ------------------------------------------------------------------
    # إنشاء خزنة جديدة
    # ------------------------------------------------------------------
    def create(self, master_password: str) -> None:
        if self.path.exists():
            raise VaultAlreadyExistsError(
                f"يوجد ملف خزنة مسبقًا في: {self.path}")
        if not master_password or len(master_password) < 8:
            raise VaultError(
                "كلمة المرور الرئيسية يجب أن تكون 8 أحرف على الأقل")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._salt = generate_salt()
        self.created_at = _now_iso()
        self._data = {
            "magic": INNER_MAGIC,
            "accounts": [],
            "settings": json.loads(json.dumps(DEFAULT_SETTINGS)),
            "created_at": self.created_at,
            "updated_at": self.created_at,
        }
        self._key = derive_key(master_password, self._salt,
                               **self._kdf_params)
        self._write_file()
        self.unlocked = True

    # ------------------------------------------------------------------
    # فتح خزنة موجودة
    # ------------------------------------------------------------------
    def unlock(self, master_password: str) -> None:
        if not self.path.exists():
            raise VaultFileNotFoundError(
                f"لا يوجد ملف خزنة في: {self.path}")
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        kdf = raw["kdf"]
        self._salt = b64_decode(kdf["salt"])
        self._kdf_params = dict(
            time_cost=int(kdf["time_cost"]),
            memory_cost=int(kdf["memory_cost_kib"]),
            parallelism=int(kdf["parallelism"]),
        )
        self.created_at = raw.get("created_at")
        # الرأس الكامل (الملح + المعاملات + nonce) يُستخدم كـ AAD
        header = {k: raw[k] for k in ("format", "format_version",
                                      "kdf", "cipher")}
        self._key = derive_key(master_password, self._salt,
                               **self._kdf_params)
        try:
            plaintext = decrypt_bytes(
                b64_decode(raw["cipher"]["nonce"]),
                b64_decode(raw["payload"]["ciphertext"]),
                self._key,
                self._aad_from_header(header),
            )
            data = json.loads(plaintext.decode("utf-8"))
            if data.get("magic") != INNER_MAGIC:
                raise IntegrityError("بنية الخزنة غير متوقعة")
            self._data = data
            self.unlocked = True
        except IntegrityError:
            self.lock()
            raise
        except (KeyError, ValueError, json.JSONDecodeError):
            self.lock()
            raise IntegrityError("ملف الخزنة تالف أو غير صالح")

    # ------------------------------------------------------------------
    # الكتابة المشفّرة على القرص
    # ------------------------------------------------------------------
    def _write_file(self) -> None:
        if self._key is None or self._data is None:
            raise VaultError("الخزنة غير مفتوحة")
        self._data["updated_at"] = _now_iso()
        plaintext = json.dumps(self._data, ensure_ascii=False,
                               indent=2).encode("utf-8")
        # nonce جديد فريد في كل حفظ — لا يُعاد استخدامه مع نفس المفتاح
        nonce = generate_nonce()
        header = self._header(b64_encode(nonce))
        # ربط الرأس (الملح + معاملات KDF + nonce) بوسم السلامة:
        # أي تعديل خارجي على أي جزء منه يفشل فك التشفير فورًا
        aad = self._aad_from_header(header)
        nonce, ciphertext = encrypt_bytes(plaintext, self._key, aad,
                                          nonce=nonce)
        payload = dict(header)
        payload["created_at"] = self.created_at or _now_iso()
        payload["aad_note"] = "header-bound-authentication"
        payload["payload"] = {"ciphertext": b64_encode(ciphertext)}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                       encoding="utf-8")
        os.replace(tmp, self.path)   # كتابة ذرّية آمنة

    def save(self) -> None:
        if not self.unlocked:
            raise VaultError("الخزنة مقفلة")
        self._write_file()

    # ------------------------------------------------------------------
    # إدارة الحسابات (CRUD)
    # ------------------------------------------------------------------
    def add_account(self, site_name: str, username: str, password: str,
                    url: str = "", notes: str = "") -> dict:
        record = {
            "id": uuid.uuid4().hex,
            "site_name": site_name.strip(),
            "username": username.strip(),
            "url": (url or "").strip(),
            "password": password,
            "notes": (notes or "").strip(),
            "created_at": _now_iso(),
            "modified_at": _now_iso(),
        }
        self._data["accounts"].append(record)
        self.save()
        return record

    def edit_account(self, account_id: str, **fields) -> dict:
        for rec in self._data["accounts"]:
            if rec["id"] == account_id:
                for k in ("site_name", "username", "url",
                          "password", "notes"):
                    if k in fields and fields[k] is not None:
                        rec[k] = fields[k]
                rec["modified_at"] = _now_iso()
                self.save()
                return rec
        raise VaultError("الحساب غير موجود")

    def delete_account(self, account_id: str) -> bool:
        before = len(self._data["accounts"])
        self._data["accounts"] = [
            r for r in self._data["accounts"] if r["id"] != account_id
        ]
        if len(self._data["accounts"]) < before:
            self.save()
            return True
        return False

    def get_account(self, account_id: str):
        for rec in self._data["accounts"]:
            if rec["id"] == account_id:
                return dict(rec)
        return None

    def search_accounts(self, query: str):
        """بحث حي في اسم الموقع/المستخدم/الرابط/الملاحظات."""
        q = (query or "").strip().lower()
        if not q:
            return [dict(r) for r in self._data["accounts"]]
        return [dict(r) for r in self._data["accounts"]
                if any(q in str(r.get(k, "")).lower()
                       for k in ("site_name", "username", "url", "notes"))]

    @property
    def accounts(self):
        return [dict(r) for r in self._data["accounts"]]

    @property
    def settings(self) -> dict:
        return self._data["settings"]

    def update_settings(self, **kwargs) -> None:
        self._data["settings"].update(kwargs)
        self.save()

    # ------------------------------------------------------------------
    # تغيير كلمة المرور الرئيسية
    # ------------------------------------------------------------------
    def change_master_password(self, old_password: str,
                               new_password: str) -> None:
        if len(new_password) < 8:
            raise VaultError("الكلمة الجديدة يجب أن تكون 8 أحرف على الأقل")
        if old_password == new_password:
            raise VaultError("الكلمة الجديدة مطابقة للقديمة")
        # التحقق من الكلمة القديمة بمحاولة فك تشفير مستقلة
        probe = VaultManager(self.path)
        probe.unlock(old_password)          # يرفع خطأ إن كانت خاطئة
        self._salt = generate_salt()        # ملح جديد فريد
        old_key = self._key
        self._key = derive_key(new_password, self._salt, **self._kdf_params)
        wipe_buffer(old_key)                # مسح المفتاح القديم فعليًا
        self._write_file()

    # ------------------------------------------------------------------
    # القفل الآمن
    # ------------------------------------------------------------------
    def lock(self) -> None:
        """قفل الخزنة ومسح المفتاح والبيانات الحساسة من الذاكرة."""
        if self._key is not None:
            wipe_buffer(self._key)   # مسح المفتاح الفعلي من الذاكرة
        self._key = None
        self._data = None
        self.unlocked = False
