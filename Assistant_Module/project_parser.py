import os
import json
import re
import google.generativeai as genai


# ─────────────────────────────────────────────────────────────
# Arabic/English digit mapping
# ─────────────────────────────────────────────────────────────
_AR_DIGITS = {
    '٠': 0, '١': 1, '٢': 2, '٣': 3, '٤': 4,
    '٥': 5, '٦': 6, '٧': 7, '٨': 8, '٩': 9,
}

_AR_WORDS = {
    'صفر': 0, 'واحد': 1, 'واحدة': 1, 'اثنين': 2, 'اثنتين': 2, 'اتنين': 2,
    'ثلاثة': 3, 'ثلاث': 3, 'تلاتة': 3, 'أربعة': 4, 'أربع': 4, 'اربعة': 4,
    'خمسة': 5, 'خمس': 5, 'ستة': 6, 'ست': 6, 'سبعة': 7, 'سبع': 7,
    'ثمانية': 8, 'ثماني': 8, 'تسعة': 9, 'تسع': 9, 'عشرة': 10, 'عشر': 10,
    'عشرين': 20, 'خمسة عشر': 15, 'خمستاشر': 15, 'عشرة': 10,
    'خمسة عشر': 15, 'ستة عشر': 16, 'سبعة عشر': 17, 'ثمانية عشر': 18,
    'تسعة عشر': 19, 'عشرين': 20, 'خمسة وعشرين': 25, 'ثلاثين': 30,
}


def _normalize_ar_digits(text: str) -> str:
    """Replace Arabic-Indic digits with Western digits."""
    for ar, en in _AR_DIGITS.items():
        text = text.replace(ar, str(en))
    return text


def _extract_number_before(pattern: str, text: str) -> int | None:
    """
    Extract the integer that appears immediately BEFORE a pattern.
    Handles Arabic word numbers and Arabic-Indic digits.
    """
    # Build a combined Arabic word pattern for use as number prefix
    ar_word_pattern = '|'.join(re.escape(w) for w in sorted(_AR_WORDS, key=len, reverse=True))
    # Full regex: (number|ar_word) ... pattern
    full_re = rf'(?:(\d+)|({ar_word_pattern}))\s*(?:{pattern})'
    m = re.search(full_re, text, re.IGNORECASE)
    if m:
        if m.group(1):  # Western digit match
            return int(m.group(1))
        if m.group(2):  # Arabic word match
            return _AR_WORDS.get(m.group(2).strip())
    return None


def _extract_number_after(pattern: str, text: str) -> int | None:
    """
    Extract the integer that appears immediately AFTER a pattern.
    """
    ar_word_pattern = '|'.join(re.escape(w) for w in sorted(_AR_WORDS, key=len, reverse=True))
    full_re = rf'(?:{pattern})\s*(?:(\d+)|({ar_word_pattern}))'
    m = re.search(full_re, text, re.IGNORECASE)
    if m:
        if m.group(1):
            return int(m.group(1))
        if m.group(2):
            return _AR_WORDS.get(m.group(2).strip())
    return None


def _regex_parse(text: str) -> dict:
    """
    Rule-based fallback parser for Arabic + English project descriptions.
    Handles Arabic dual forms (e.g. غرفتين = 2, تكييفين = 2).
    """
    t = _normalize_ar_digits(text)

    # ── Dual-form shortcuts (Arabic) ───────────────────────────
    dual_rooms    = bool(re.search(r'غرفتين|أوضتين|اوضتين', t))
    dual_acs      = bool(re.search(r'تكييفين|مكيفين', t))
    dual_lights   = bool(re.search(r'نقطتين إضاءة|نقطتين اضاءة', t))
    dual_sockets  = bool(re.search(r'بريزتين', t))

    # ── Rooms ───────────────────────────────────────────────────
    rooms = None
    if dual_rooms:
        rooms = 2
    else:
        # "5 غرف" / "5 أوضة" / "5 rooms" / "غرف 5"
        rooms = (
            _extract_number_before(r'غرف(?:ة)?|أوض(?:ة)?|اوض(?:ة)?|rooms?|bedrooms?', t) or
            _extract_number_after(r'rooms?\s*:?|bedrooms?\s*:?|عدد\s+الغرف\s*:?', t)
        )

    # ── AC Units ────────────────────────────────────────────────
    ac_units = None
    if dual_acs:
        ac_units = 2
    else:
        ac_units = (
            _extract_number_before(r'تكييف(?:ات)?|مكيف(?:ات)?|وحدات?\s+تكييف|air\s+conditioners?|a\.?c\.?\s+units?', t) or
            _extract_number_after(r'(?:تكييف|مكيف|air\s+conditioner|a\.?c\.?)\s*(?:units?)?\s*:?', t)
        )

    # ── Lighting points ─────────────────────────────────────────
    lighting = None
    if dual_lights:
        lighting = 2
    else:
        lighting = (
            _extract_number_before(r'نقاط?\s+إضاءة|نقاط?\s+اضاءة|نقط\s+إضاءة|lighting\s+points?|light\s+points?|lights?', t) or
            _extract_number_after(r'(?:نقاط?|نقط)\s+(?:إضاءة|اضاءة)\s*:?', t) or
            _extract_number_before(r'نقطة\s+(?:إضاءة|اضاءة)|نقاط?\s+(?:إضاءة|اضاءة)', t)
        )

    # ── Socket outlets ──────────────────────────────────────────
    sockets = None
    if dual_sockets:
        sockets = 2
    else:
        sockets = (
            _extract_number_before(r'بريز(?:ة|ات)|مقابس?|socket\s+outlets?|outlets?|sockets?', t) or
            _extract_number_after(r'(?:بريز(?:ة|ات)|socket\s+outlets?|outlets?)\s*:?', t)
        )

    # ── Kitchen ─────────────────────────────────────────────────
    kitchen = bool(re.search(r'مطبخ|kitchen', t, re.IGNORECASE))

    # ── Building type ───────────────────────────────────────────
    building_type = None
    if re.search(r'فيلا|villa', t, re.IGNORECASE):
        building_type = 'villa'
    elif re.search(r'شقة|apartment|flat', t, re.IGNORECASE):
        building_type = 'apartment'
    elif re.search(r'مكتب|office', t, re.IGNORECASE):
        building_type = 'office'
    elif re.search(r'محل|دكان|shop|store', t, re.IGNORECASE):
        building_type = 'shop'
    elif re.search(r'مستودع|مخزن|warehouse', t, re.IGNORECASE):
        building_type = 'warehouse'
    elif re.search(r'مستشفى|hospital', t, re.IGNORECASE):
        building_type = 'hospital'
    elif re.search(r'مدرسة|school', t, re.IGNORECASE):
        building_type = 'school'

    # ── Future equipment ────────────────────────────────────────
    generators      = _extract_number_before(r'مولد(?:ات)?|generators?', t) or (
                      1 if re.search(r'مولد|generator', t, re.IGNORECASE) else None)
    elevators       = _extract_number_before(r'مصعد(?:ات)?|أسانسير|elevators?|lifts?', t) or (
                      1 if re.search(r'مصعد|أسانسير|elevator|lift', t, re.IGNORECASE) else None)
    pumps           = _extract_number_before(r'طلمب(?:ة|ات)|مضخ(?:ة|ات)|pumps?', t) or (
                      1 if re.search(r'طلمبة|مضخة|pump', t, re.IGNORECASE) else None)
    solar           = bool(re.search(r'طاقة شمسية|solar', t, re.IGNORECASE)) or None

    return {
        "building_type": building_type,
        "rooms": rooms,
        "ac_units": ac_units,
        "lighting_points": lighting,
        "socket_outlets": sockets,
        "kitchen": kitchen if kitchen else None,
        "future_equipment": {
            "generators": generators,
            "elevators": elevators,
            "pumps": pumps,
            "industrial_machines": None,
            "solar_systems": solar,
        }
    }


# ─────────────────────────────────────────────────────────────
# Primary parser: Gemini → fallback to regex
# ─────────────────────────────────────────────────────────────
_GEMINI_MODELS = [
    'gemini-1.5-flash',
    'gemini-1.5-flash-latest',
    'gemini-2.0-flash',
]


def parse_project_description(text: str) -> dict:
    """
    Extract structured electrical parameters from an Arabic/English description.

    Strategy:
    1. Try Gemini API (iterating through fallback models).
    2. If API key missing, quota exceeded, or any error → use local regex parser.
    """
    api_key = os.environ.get("GEMINI_API_KEY")

    if api_key:
        genai.configure(api_key=api_key)
        prompt = f"""
You are a precise structured data extraction engine for an electrical engineering assistant.
Extract building parameters from the user's natural language description (English or Arabic).

### RULES:
1. Return ONLY a raw JSON object matching the SCHEMA below (no markdown, no explanation).
2. Set null for any property not mentioned.
3. Translate Arabic terms to English values (فيلا → villa, شقة → apartment, مطبخ → true).
4. Handle Arabic dual forms correctly (غرفتين → 2 rooms, تكييفين → 2 ac_units).
5. Never perform electrical calculations.

### SCHEMA:
{{
  "building_type": "apartment"|"villa"|"office"|"shop"|"warehouse"|"hospital"|"school"|null,
  "rooms": int|null,
  "ac_units": int|null,
  "lighting_points": int|null,
  "socket_outlets": int|null,
  "kitchen": bool|null,
  "future_equipment": {{
    "generators": int|null,
    "elevators": int|null,
    "pumps": int|null,
    "industrial_machines": int|null,
    "solar_systems": bool|null
  }}
}}

### USER DESCRIPTION:
"{text}"
"""
        for model_name in _GEMINI_MODELS:
            try:
                model = genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                response_text = response.text.strip()
                # Strip markdown fences if present
                if response_text.startswith("```"):
                    lines = response_text.splitlines()
                    response_text = "\n".join(lines[1:-1]).strip()
                data = json.loads(response_text)
                return data
            except Exception:
                continue  # Try next model or fall through to regex

    # ── Regex fallback (works offline / no API key / quota exceeded) ──
    return _regex_parse(text)
