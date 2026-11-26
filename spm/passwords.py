# -*- coding: utf-8 -*-
"""
passwords.py — أدوات توليد وتحليل كلمات المرور
===============================================
  1) توليد كلمات مرور عشوائية قوية عبر وحدة secrets (أمنية تشفيريًا).
  2) تحليل قوة كلمة المرور (طول، فئات، إنتروبيا، أنماط ضعيفة).
  3) قائمة كلمات مرور شائعة (من أكثر الكلمات تسريبًا عالميًا) للكشف عنها.
  4) اكتشاف الحسابات الضعيفة والمكررة داخل الخزنة.
  5) تقدير زمن التخمين للمهاجم بخصم Offline.
  6) تقديم اقتراحات تحسين بالعربية.
"""

import secrets
import string
import math
import re

# ---------------------------------------------------------------------------
# قائمة كلمات مرور شائعة (أكثر الكلمات ظهورًا في تسريبات معروفة عالميًا)
# ---------------------------------------------------------------------------
COMMON_PASSWORDS = frozenset({
    "123456", "password", "123456789", "12345678", "12345", "qwerty",
    "1234567890", "1234567", "111111", "123123", "abc123", "1234",
    "password1", "iloveyou", "000000", "qwerty123", "1q2w3e", "aa123456",
    "654321", "555555", "dragon", "sunshine", "princess", "letmein",
    "welcome", "monkey", "football", "baseball", "master", "hello",
    "freedom", "whatever", "qazwsx", "trustno1", "batman", "admin",
    "admin123", "root", "toor", "pass", "pass123", "passw0rd", "p@ssword",
    "p@ssw0rd", "abcd1234", "asdfgh", "zxcvbn", "qwe123", "1qaz2wsx",
    "qwertyuiop", "azerty", "salesforce", "starwars", "superman",
    "shadow", "michael", "jennifer", "hunter", "buster", "thomas",
    "tigger", "robert", "soccer", "hockey", "killer", "george",
    "sexy", "andrew", "charlie", "jordan", "joshua", "harley",
    "ranger", "buster1", "summer", "ashley", "bailey", "passwird",
    "loveme", "test", "test123", "guest", "user", "user123",
    "abcd", "abcde", "a1b2c3", "121212", "112233", "121314",
    "654321a", "aaaaaa", "999999", "888888", "159753", "13579",
    "135791", "147258", "159357", "789456", "987654", "102030",
    "112358", "2000", "2020", "2023", "2024", "2025", "2026",
    "saudi", "saudi123", "riyadh", "nemo", "numo", "tvetc",
    "secure", "secure123", "google", "google123", "facebook",
    "facebook1", "gmail", "gmail123", "twitter", "instagram",
    "tiktok123", "snapchat", "youtube", "whatsapp", "keyboard",
    "changethis", "default", "changeme", "temp", "temp123",
    "q1w2e3r4", "1q2w3e4r", "1q2w3e4r5t", "zaq12wsx", "123qwe",
    "qweasd", "asd123", "zxc123", "hello123", "helloworld",
    "mypassword", "ourpassword", "password12", "password123",
    "password1234", "password12345", "newpassword", "oldpassword",
    "student", "student123", "college", "college123", "university",
    "graduation", "project", "project2026", "cyber", "cyber123",
})

# حروف/رموز ملتبسة بصريًا يمكن استبعادها من المولّد
AMBIGUOUS_CHARS = "Il1O0o|`'\";:,."

CHAR_CLASSES = {
    "lower": string.ascii_lowercase,
    "upper": string.ascii_uppercase,
    "digits": string.digits,
    "symbols": "!@#$%^&*()-_=+[]{};:,.?/",
}


# ---------------------------------------------------------------------------
# 1) مولّد كلمات المرور العشوائية
# ---------------------------------------------------------------------------
def generate_password(length: int = 16, upper: bool = True,
                      lower: bool = True, digits: bool = True,
                      symbols: bool = True,
                      exclude_ambiguous: bool = False) -> str:
    """
    توليد كلمة مرور عشوائية آمنة (مصدر العشوائية: secrets = CSPRNG).
    يضمن وجود حرف واحد على الأقل من كل فئة مُحدَّدة، ثم يخلط البقية.
    """
    if length < 4:
        raise ValueError("طول كلمة المرور يجب أن يكون 4 على الأقل")
    if not (upper or lower or digits or symbols):
        raise ValueError("يجب اختيار فئة واحدة على الأقل")

    def pool_of(name):
        chars = CHAR_CLASSES[name]
        if exclude_ambiguous:
            chars = "".join(c for c in chars if c not in AMBIGUOUS_CHARS)
        return chars

    pools = {n: pool_of(n) for n in
             ("upper", "lower", "digits", "symbols")
             if {"upper": upper, "lower": lower,
                 "digits": digits, "symbols": symbols}[n]}
    for n, p in pools.items():
        if not p:
            raise ValueError(f"الفئة {n} فارغة بعد استبعاد الحروف الملتبسة")

    required = [secrets.choice(p) for p in pools.values()]
    all_pool = "".join(pools.values())
    remaining = length - len(required)
    body = [secrets.choice(all_pool) for _ in range(remaining)]
    result = required + body
    # خلط Fisher-Yates بـ secrets لمنع التموضع المتوقع
    for i in range(len(result) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        result[i], result[j] = result[j], result[i]
    return "".join(result)


# ---------------------------------------------------------------------------
# 2) حساب الإنتروبيا وتقدير زمن التخمين
# ---------------------------------------------------------------------------
def charset_size(password: str) -> int:
    size = 0
    if re.search(r"[a-z]", password):
        size += 26
    if re.search(r"[A-Z]", password):
        size += 26
    if re.search(r"[0-9]", password):
        size += 10
    if re.search(r"[^a-zA-Z0-9]", password):
        size += 33
    return size or 1


def raw_entropy_bits(password: str) -> float:
    n = charset_size(password)
    return len(password) * math.log2(n) if len(password) else 0.0


def estimate_crack_time(password: str, guesses_per_second=10_000_000_000):
    """
    تقدير زمن كسر كلمة المرور بافتراض مهاجم Offline
    سرعته 10 مليار محاولة/ثانية (GPU حديث متعدد الكروت).
    يعيد نصًا عربيًا وصفيًا.
    """
    bits = max(raw_entropy_bits(password), 1.0)
    seconds = (2 ** bits) / 2 / guesses_per_second
    if seconds < 1:
        return "أقل من ثانية", seconds
    if seconds < 60:
        return f"حوالي {int(seconds)} ثانية", seconds
    if seconds < 3600:
        return f"حوالي {int(seconds // 60)} دقيقة", seconds
    if seconds < 86400:
        return f"حوالي {int(seconds // 3600)} ساعة", seconds
    if seconds < 86400 * 365:
        return f"حوالي {int(seconds // 86400)} يوم", seconds
    years = seconds / (86400 * 365)
    if years < 1e3:
        return f"آلاف السنين ({int(years)} سنة تقريبًا)", seconds
    if years < 1e9:
        return f"ملايين السنين ({int(years):,} سنة تقريبًا)", seconds
    return "مليارات السنين — عمليًا مستحيلة الكسر", seconds


# ---------------------------------------------------------------------------
# 3) تحليل قوة كلمة المرور
# ---------------------------------------------------------------------------
def analyze_password(password: str) -> dict:
    """
    تحليل شامل لكلمة المرور يعيد:
      score (0-100), level (نص عربي), entropy, checks (قائمة فحوص),
      suggestions (اقتراحات تحسين), is_common, is_weak.
    """
    p = password or ""
    checks = []
    suggestions = []
    score = 0

    # --- الطول ---
    L = len(p)
    if L == 0:
        checks.append(("الطول", False, "كلمة المرور فارغة"))
    elif L < 8:
        checks.append(("الطول", False, f"الطول {L} — قصير جدًا (أقل من 8)"))
        suggestions.append("اجعل كلمة المرور 12 حرفًا على الأقل "
                           "(يفضّل 16 أو أكثر)")
    elif L < 12:
        checks.append(("الطول", True, f"الطول {L} — مقبول لكن الأفضل 12+"))
        score += 15
        suggestions.append("زيادة الطول إلى 12 حرفًا أو أكثر ترفع الأمان "
                           "بشكل كبير")
    else:
        checks.append(("الطول", True, f"الطول {L} — جيد"))
        score += 30 if L >= 16 else 25

    # --- الفئات ---
    has_lower = bool(re.search(r"[a-z]", p))
    has_upper = bool(re.search(r"[A-Z]", p))
    has_digit = bool(re.search(r"[0-9]", p))
    has_symbol = bool(re.search(r"[^a-zA-Z0-9]", p))
    classes = sum([has_lower, has_upper, has_digit, has_symbol])

    checks.append(("حروف صغيرة (a-z)", has_lower,
                   "موجودة" if has_lower else "غير موجودة"))
    checks.append(("حروف كبيرة (A-Z)", has_upper,
                   "موجودة" if has_upper else "غير موجودة"))
    checks.append(("أرقام (0-9)", has_digit,
                   "موجودة" if has_digit else "غير موجودة"))
    checks.append(("رموز (!@#$...)", has_symbol,
                   "موجودة" if has_symbol else "غير موجودة"))
    score += {0: 0, 1: 8, 2: 16, 3: 22, 4: 28}[classes]
    if not has_upper:
        suggestions.append("أضف حروفًا كبيرة لتوسيع مجال التخمين")
    if not has_digit:
        suggestions.append("أضف أرقامًا واحدة على الأقل")
    if not has_symbol:
        suggestions.append("أضف رموزًا مثل ! @ # $ لزيادة القوة")

    # --- كلمة شائعة ---
    is_common = p.lower() in COMMON_PASSWORDS
    if is_common:
        checks.append(("ليست كلمة شائعة", False,
                       "موجودة في قائمة الكلمات المسرّبة الشائعة"))
        score = max(0, score - 40)
        suggestions.append("تجنب كلمات المرور الشائعة المسرّبة نهائيًا — "
                           "هي أول ما يجرب برامج الكسر")
    else:
        checks.append(("ليست كلمة شائعة", True,
                       "غير موجودة في قائمة الكلمات الشائعة"))

    # --- تكرار حروف متتالٍ ---
    has_repeat = re.search(r"(.)\1{2,}", p) is not None
    checks.append(("لا تكرار متتالٍ (aaa)", not has_repeat,
                   "سليم" if not has_repeat else "يحتوي تكرارًا متتاليًا"))
    if has_repeat:
        score = max(0, score - 10)
        suggestions.append("تجنب تكرار نفس الحرف ثلاث مرات أو أكثر")

    # --- تسلسل منطقي (abc / 123 / qwerty) ---
    sequences = ("abcdefghijklmnopqrstuvwxyz", "0123456789",
                 "qwertyuiop", "asdfghjkl", "zxcvbnm")
    has_seq = False
    pl = p.lower()
    for s in sequences:
        for i in range(len(s) - 2):
            tri = s[i:i + 3]
            if tri in pl or tri[::-1] in pl:
                has_seq = True
                break
        if has_seq:
            break
    checks.append(("لا تسلسل (abc/123)", not has_seq,
                   "سليم" if not has_seq else "يحتوي تسلسلًا متوقعًا"))
    if has_seq:
        score = max(0, score - 12)
        suggestions.append("تجنب التسلسلات المتوقعة مثل abc أو 123 أو qwerty")

    # --- إنتروبيا ---
    entropy = raw_entropy_bits(p)
    if entropy >= 90:
        score += 22
    elif entropy >= 70:
        score += 17
    elif entropy >= 50:
        score += 10
    else:
        suggestions.append("الإنتروبيا منخفضة — استخدم المولّد الآلي "
                           "لإنشاء كلمة عشوائية أطول")

    score = max(0, min(100, score))

    if is_common or L < 8:
        level, is_weak = "ضعيفة جدًا", True
    elif score < 40:
        level, is_weak = "ضعيفة", True
    elif score < 60:
        level, is_weak = "متوسطة", False
    elif score < 80:
        level, is_weak = "قوية", False
    else:
        level, is_weak = "قوية جدًا", False

    return {
        "score": score,
        "level": level,
        "entropy_bits": round(entropy, 1),
        "checks": checks,
        "suggestions": suggestions,
        "is_common": is_common,
        "is_weak": is_weak,
        "crack_time": estimate_crack_time(p)[0] if p else "—",
    }


# ---------------------------------------------------------------------------
# 4) الكشف عن الحسابات الضعيفة والمكررة
# ---------------------------------------------------------------------------
def find_weak_accounts(accounts) -> list:
    """الحسابات التي كلمة مرورها ضعيفة/قصيرة/شائعة."""
    weak = []
    for acc in accounts:
        a = analyze_password(acc.get("password", ""))
        if a["is_weak"] or a["is_common"]:
            weak.append({
                "account": acc,
                "reason": ("كلمة مرور شائعة مسرّبة" if a["is_common"]
                           else "كلمة مرور ضعيفة"),
                "level": a["level"],
            })
    return weak


def find_duplicate_accounts(accounts) -> list:
    """
    الحسابات التي تشارك نفس كلمة المرور (بغض النظر عن الموقع).
    استراتيجية واحدة مسرّبة = اختراق كل الحسابات المشاركة للكلمة نفسها.
    """
    groups = {}
    for acc in accounts:
        groups.setdefault(acc.get("password", ""), []).append(acc)
    duplicates = []
    for pwd, accs in groups.items():
        if len(accs) > 1 and pwd:
            duplicates.append({
                "accounts": accs,
                "count": len(accs),
            })
    return duplicates


def improvement_suggestions(accounts) -> list:
    """اقتراحات تحسين عامة للخزنة بناءً على حالة الحسابات."""
    weak = find_weak_accounts(accounts)
    dups = find_duplicate_accounts(accounts)
    suggestions = []
    if weak:
        suggestions.append(
            f"لديك {len(weak)} حساب بكلمة مرور ضعيفة أو شائعة — "
            "استبدلها بكلمات مولّدة آلية من المولّد")
    if dups:
        suggestions.append(
            f"{len(dups)} مجموعة من الحسابات تستخدم كلمة المرور نفسها — "
            "فعّل التفرد بين الحسابات لأن تسريب أحدها يعني تعرضها جميعًا")
    if not any(a.get("url") for a in accounts):
        suggestions.append("أضف روابط المواقع لحساباتك ليسهل الوصول "
                           "إليها لاحقًا")
    if not suggestions:
        suggestions.append("حالة الخزنة ممتازة — استمر في استخدام "
                           "كلمات مرور مولّدة وفريدة لكل حساب")
    suggestions.append("فعّل المصادقة الثنائية (2FA) في المواقع التي "
                       "تدعمها لطبقة حماية إضافية")
    return suggestions
