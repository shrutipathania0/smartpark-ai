"""
Indian Registration Number Validator and Normalizer
Supports standard Indian registration formats (e.g., DL01AB1234, MH12DE1234)
and Bharat Series (e.g., 22BH1234AA).
Performs position-aware character disambiguation (O/0, I/1, B/8, S/5, Z/2).
"""
import re
from typing import Dict, Any, Tuple

# Valid 2-letter State & UT codes in India
VALID_STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DN", "DL",
    "GA", "GJ", "HR", "HP", "JK", "JH", "KA", "KL", "LA", "LD",
    "MP", "MH", "MN", "ML", "MZ", "NL", "OD", "PB", "RJ", "SK",
    "TN", "TS", "TR", "UP", "UK", "WB", "BH"
}

DIGIT_TO_LETTER = {
    '0': 'O', '1': 'I', '2': 'Z', '4': 'A', '5': 'S', '6': 'G', '7': 'T', '8': 'B'
}

LETTER_TO_DIGIT = {
    'O': '0', 'Q': '0', 'D': '0',
    'I': '1', 'T': '1',
    'Z': '2',
    'S': '5',
    'B': '8', 'G': '6'
}

# State code correction mappings for common OCR character confusions
STATE_CODE_CORRECTIONS = {
    "TH": "TN",
    "TM": "TN",
    "RN": "TN",
    "1N": "TN",
    "6J": "GJ",
    "0L": "DL",
    "D1": "DL",
    "C6": "CG",
    "H9": "HP",
    "P8": "PB",
    "R1": "RJ",
    "M1": "MH"
}

def clean_ocr_text(raw_text: str) -> str:
    """Removes spaces, hyphens, dots, and non-alphanumeric characters."""
    if not raw_text:
        return ""
    # Strip non-alphanumeric
    cleaned = re.sub(r'[^A-Za-z0-9]', '', raw_text)
    return cleaned.upper()

def normalize_standard_plate(plate: str) -> str:
    """
    Standard format: [State 2 letters][RTO 2 digits][Series 1-3 letters][Number 4 digits]
    Example: DL 01 AB 1234 (total 9-11 chars)
    """
    if len(plate) < 8 or len(plate) > 11:
        return plate

    chars = list(plate)
    n = len(chars)

    # 1. First 2 characters must be state letters
    for i in range(min(2, n)):
        if chars[i] in DIGIT_TO_LETTER:
            chars[i] = DIGIT_TO_LETTER[chars[i]]

    # Apply known state code corrections
    state = "".join(chars[:2])
    if state in STATE_CODE_CORRECTIONS:
        chars[0] = STATE_CODE_CORRECTIONS[state][0]
        chars[1] = STATE_CODE_CORRECTIONS[state][1]

    # 2. Next 2 characters (pos 2, 3) must be RTO digits
    for i in range(2, min(4, n)):
        if chars[i] in LETTER_TO_DIGIT:
            chars[i] = LETTER_TO_DIGIT[chars[i]]

    # Special case: Tripura (TR) only has RTOs 01 to 08. If state is TR but RTO > 08 (e.g. 52), it is Tamil Nadu (TN)
    if chars[0] == 'T' and chars[1] == 'R' and n >= 4:
        rto_str = "".join(chars[2:4])
        if rto_str.isdigit() and int(rto_str) > 8:
            chars[1] = 'N'

    # 3. Last 4 characters must be numeric registration digits
    # In Indian plate typography, 'LL' in the tail is a frequent OCR misclassification of '44'
    tail_start = max(4, n - 4)
    tail_chars = chars[tail_start:n]
    tail_str = "".join(tail_chars)
    if "LL" in tail_str:
        tail_str = tail_str.replace("LL", "44")
        tail_chars = list(tail_str)

    for i in range(len(tail_chars)):
        if tail_chars[i] in LETTER_TO_DIGIT:
            tail_chars[i] = LETTER_TO_DIGIT[tail_chars[i]]
        elif tail_chars[i] == 'L':
            tail_chars[i] = '1'
    chars[tail_start:n] = tail_chars

    # 4. Characters in between (series letters) must be letters
    for i in range(4, max(4, n - 4)):
        if chars[i] in DIGIT_TO_LETTER:
            chars[i] = DIGIT_TO_LETTER[chars[i]]

    return "".join(chars)

def normalize_bharat_series(plate: str) -> str:
    """
    Bharat Series: [Year 2 digits] BH [Number 4 digits] [Series 1-2 letters]
    Example: 22BH1234AA
    """
    if len(plate) < 9 or len(plate) > 10:
        return plate

    chars = list(plate)
    n = len(chars)

    # First 2 digits (Year)
    for i in range(2):
        if chars[i] in LETTER_TO_DIGIT:
            chars[i] = LETTER_TO_DIGIT[chars[i]]

    # Next 2 letters (BH)
    chars[2] = 'B'
    chars[3] = 'H'

    # Next 4 digits
    for i in range(4, min(8, n)):
        if chars[i] in LETTER_TO_DIGIT:
            chars[i] = LETTER_TO_DIGIT[chars[i]]

    # Last 1-2 characters (Series)
    for i in range(8, n):
        if chars[i] in DIGIT_TO_LETTER:
            chars[i] = DIGIT_TO_LETTER[chars[i]]

    return "".join(chars)

def validate_and_normalize_plate(raw_text: str) -> Dict[str, Any]:
    """
    Validates, normalizes, and scores registration string against Indian number plate formats.
    Returns:
    {
        "raw_text": str,
        "normalized_text": str,
        "is_valid": bool,
        "format_type": "STANDARD" | "BHARAT_SERIES" | "CUSTOM" | "INVALID",
        "state_code": str,
        "confidence_penalty": float
    }
    """
    cleaned = clean_ocr_text(raw_text)
    if not cleaned:
        return {
            "raw_text": raw_text,
            "normalized_text": "",
            "is_valid": False,
            "format_type": "INVALID",
            "state_code": "",
            "confidence_penalty": 1.0
        }

    # Check for Bharat Series: e.g. 21BH..., 22BH...
    if re.search(r'^\d{2}BH', cleaned) or re.search(r'^[0-9OIZS]{2}BH', cleaned):
        normalized = normalize_bharat_series(cleaned)
        # Regex for BH: 2 digits, BH, 4 digits, 1-2 letters
        bh_pattern = r'^\d{2}BH\d{4}[A-Z]{1,2}$'
        is_match = bool(re.match(bh_pattern, normalized))
        return {
            "raw_text": raw_text,
            "normalized_text": normalized,
            "is_valid": is_match,
            "format_type": "BHARAT_SERIES" if is_match else "INVALID",
            "state_code": "BH",
            "confidence_penalty": 0.0 if is_match else 0.25
        }

    # Standard Indian Format
    normalized = normalize_standard_plate(cleaned)
    std_pattern = r'^([A-Z]{2})(\d{1,2})([A-Z]{0,3})(\d{4})$'
    match = re.match(std_pattern, normalized)

    if match:
        state = match.group(1)
        is_valid_state = state in VALID_STATE_CODES
        penalty = 0.0 if is_valid_state else 0.2
        return {
            "raw_text": raw_text,
            "normalized_text": normalized,
            "is_valid": is_valid_state,
            "format_type": "STANDARD" if is_valid_state else "UNKNOWN_STATE",
            "state_code": state,
            "confidence_penalty": penalty
        }

    # Fallback pattern for partial or older format (e.g. DL1Y1234 or DLA1234)
    fallback_pattern = r'^[A-Z]{2}[A-Z0-9]{4,8}\d{2,4}$'
    if re.match(fallback_pattern, normalized):
        state = normalized[:2]
        return {
            "raw_text": raw_text,
            "normalized_text": normalized,
            "is_valid": state in VALID_STATE_CODES,
            "format_type": "CUSTOM",
            "state_code": state,
            "confidence_penalty": 0.15
        }

    return {
        "raw_text": raw_text,
        "normalized_text": normalized,
        "is_valid": False,
        "format_type": "INVALID",
        "state_code": normalized[:2] if len(normalized) >= 2 else "",
        "confidence_penalty": 0.4
    }

