# -*- coding: utf-8 -*-
"""
crypto.py — وحدة التشفير المركزية في التطبيق
============================================
المسؤوليات:
  1) اشتقاق مفتاح 256-بت من كلمة المرور الرئيسية باستخدام Argon2id
     مع ملح (Salt) عشوائي فريد لكل خزنة.
  2) تشفير البيانات وفك تشفيرها باستخدام AES-256-GCM
     (تشفير متحقق من السلامة Authenticated Encryption).
  3) توليد ملح و nonce عشوائيين آمنين (os.urandom).
  4) مسح المفاتيح الحساسة من الذاكرة عند الانتهاء منها.

ملاحظات أمنية:
  - Argon2id مُوصى به من OWASP لاشتقاق المفاتيح من كلمات المرور.
  - AES-GCM يوفر السرية + سلامة البيانات (Auth Tag)، وأي تعديل
    على الملف المشفّر—even بايت واحد—يفشل فك تشفيره.
  - يُستخدم nonce فريد عشوائي (12 بايت) لكل عملية تشفير؛ ولا يُعاد
    استخدامه أبدًا مع نفس المفتاح.
"""

import os
import base64
import ctypes

from argon2.low_level import hash_secret_raw, Type
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

# ---------------------------------------------------------------------------
# إعدادات اشتقاق المفتاح (KDF) — Argon2id
# المعاملات ضمن نطاق توصيات OWASP Password Storage Cheat Sheet
# ---------------------------------------------------------------------------
KDF_ALGORITHM = "Argon2id"
KDF_TIME_COST = 3          # عدد المرورات (iterations)
KDF_MEMORY_COST = 65536    # الذاكرة بالـ KiB = 64 MiB
KDF_PARALLELISM = 4        # عدد الخيوط المتوازية
KDF_HASH_LEN = 32          # طول المفتاح المُشتق = 256 بت

# ---------------------------------------------------------------------------
# إعدادات التشفير — AES-256-GCM
# ---------------------------------------------------------------------------
CIPHER_ALGORITHM = "AES-256-GCM"
SALT_LEN = 16    # 128 بت ملح عشوائي
NONCE_LEN = 12   # 96 بت nonce (الطول المعياري لـ GCM)

B64 = base64.b64encode
UB64 = base64.b64decode


class CryptoError(Exception):
    """خطأ عام في عمليات التشفير."""


class IntegrityError(CryptoError):
    """فشل التحقق من السلامة: كلمة مرور خاطئة أو ملف مُعدَّل/تالف."""


# ---------------------------------------------------------------------------
# توليد القيم العشوائية الآمنة
# ---------------------------------------------------------------------------
def generate_salt() -> bytes:
    """توليد ملح عشوائي فريد (16 بايت) لكل خزنة جديدة."""
    return os.urandom(SALT_LEN)


def generate_nonce() -> bytes:
    """توليد nonce عشوائي فريد (12 بايت) لكل عملية تشفير."""
    return os.urandom(NONCE_LEN)


def encrypt_bytes(plaintext: bytes, key: bytes, aad: bytes = b"",
                  nonce: bytes = None):
    """
    تشفير بيانات باستخدام AES-256-GCM مع nonce فريد لكل عملية.

    يمكن تمرير nonce جاهز (يُستخدم لبناء الرأس المُوثَّق قبل التشفير)،
    وإلا يُولَّد nonce عشوائي جديد تلقائيًا.

    يعيد (nonce, ciphertext) حيث يتضمن النص المشفّر وسم سلامة (Auth Tag)
    بطول 16 بايت تتحقق من عدم تعديل البيانات وعدم تعديل الـ aad.
    """
    if len(key) != KDF_HASH_LEN:
        raise CryptoError("طول المفتاح غير صالح")
    if nonce is None:
        nonce = generate_nonce()
    if len(nonce) != NONCE_LEN:
        raise CryptoError("طول nonce غير صالح")
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad or None)
    return nonce, ciphertext


# ---------------------------------------------------------------------------
# اشتقاق المفتاح — Argon2id
# ---------------------------------------------------------------------------
def derive_key(password: str, salt: bytes,
               time_cost: int = KDF_TIME_COST,
               memory_cost: int = KDF_MEMORY_COST,
               parallelism: int = KDF_PARALLELISM) -> bytearray:
    """
    اشتقاق مفتاح 256-بت من كلمة المرور الرئيسية عبر Argon2id.

    يعيد المفتاح في bytearray قابل للمسح الصريح من الذاكرة عند القفل.
    المفتاح المُشتق لا يُخزَّن أبدًا على القرص.
    """
    if not password:
        raise CryptoError("كلمة المرور فارغة")
    if not isinstance(salt, bytes) or len(salt) != SALT_LEN:
        raise CryptoError("الملح غير صالح")

    pwd_buffer = bytearray(password.encode("utf-8"))
    try:
        key = hash_secret_raw(
            secret=bytes(pwd_buffer),
            salt=salt,
            time_cost=time_cost,
            memory_cost=memory_cost,
            parallelism=parallelism,
            hash_len=KDF_HASH_LEN,
            type=Type.ID,          # Argon2id
        )
        return bytearray(key)
    finally:
        # مسح نسخة كلمة المرور المؤقتة من الذاكرة
        wipe_buffer(pwd_buffer)


# ---------------------------------------------------------------------------
# التشفير وفك التشفير — AES-256-GCM
# ---------------------------------------------------------------------------
def decrypt_bytes(nonce: bytes, ciphertext: bytes, key: bytes,
                  aad: bytes = b"") -> bytes:
    """
    فك تشفير بيانات AES-256-GCM مع التحقق من السلامة قبل الاستخدام.
    يرفع IntegrityError إذا فشل التحقق (كلمة مرور خاطئة أو تعديل خارجي).
    """
    try:
        return AESGCM(key).decrypt(nonce, ciphertext, aad or None)
    except InvalidTag:
        raise IntegrityError(
            "فشل التحقق من سلامة البيانات: كلمة المرور الرئيسية خاطئة "
            "أو تم تعديل ملف الخزنة خارج التطبيق"
        )


# ---------------------------------------------------------------------------
# أدوات الترميز Base64 للتخزين النصي الآمن
# ---------------------------------------------------------------------------
def b64_encode(data: bytes) -> str:
    return B64(data).decode("ascii")


def b64_decode(text: str) -> bytes:
    return UB64(text.encode("ascii"))


# ---------------------------------------------------------------------------
# مسح الذاكرة من البيانات الحساسة
# ---------------------------------------------------------------------------
def wipe_buffer(buffer: bytearray) -> None:
    """
    مسح محتوى bytearray من الذاكرة بشكل صريح (تقريب لأفضل ممارسة
    في لغة بايثون حيث لا يضمن مُشغّل الذاكرة حذف كل النسخ).
    """
    if buffer is None:
        return
    try:
        ctypes.memset(
            (ctypes.c_char * len(buffer)).from_buffer(buffer),
            0, len(buffer)
        )
    except (ValueError, TypeError):
        # الذاكرة محرَّرة مسبقًا أو كائن غير قابل للوصول
        pass
