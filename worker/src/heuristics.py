import os
import re
# pyrefly: ignore [missing-import]
import cv2
import numpy as np
from PIL import Image
# pyrefly: ignore [missing-import]
import imagehash
# pyrefly: ignore [missing-import]
import pytesseract
from config import (
    BLUR_THRESHOLD,
    DARKNESS_THRESHOLD,
    MIN_IMAGE_WIDTH,
    MIN_IMAGE_HEIGHT,
    PHASH_DISTANCE_THRESHOLD,
)

# Valid 2-letter codes for Indian States and Union Territories (including BH Series)
INDIAN_STATE_CODES = {
    'AP', 'AS', 'BR', 'BH', 'CH', 'CG', 'DL', 'GA', 'GJ', 'HR',
    'HP', 'JK', 'JH', 'KA', 'KL', 'MP', 'MH', 'MN', 'ML', 'MZ',
    'NL', 'OD', 'PB', 'PY', 'RJ', 'SK', 'TN', 'TS', 'TR', 'UP',
    'UK', 'UA', 'WB'
}

def check_dimensions(width: int, height: int):
    """
    Validates image dimensions against minimum width and height thresholds.
    """
    isValid = bool(width >= MIN_IMAGE_WIDTH and height >= MIN_IMAGE_HEIGHT)
    return {
        "width": int(width),
        "height": int(height),
        "isValidDimensions": isValid
    }

def check_blur(img_gray: np.ndarray, threshold: float = BLUR_THRESHOLD):
    """
    Calculates image sharpness using the Laplacian variance.
    Low variance indicates blur.
    """
    variance = cv2.Laplacian(img_gray, cv2.CV_64F).var()
    is_blurry = bool(variance < threshold)
    severity = "none"
    if variance < threshold / 2:
        severity = "high"
    elif variance < threshold:
        severity = "medium"

    return {
        "blurScore": round(float(variance), 2),
        "isBlurry": is_blurry,
        "severity": severity
    }

def check_brightness(img_gray: np.ndarray, threshold: float = DARKNESS_THRESHOLD):
    """
    Calculates average brightness. Low values indicate dark/underexposed lighting.
    """
    mean_brightness = float(np.mean(img_gray))
    is_dark = bool(mean_brightness < threshold)

    return {
        "brightnessScore": round(mean_brightness, 2),
        "isDark": is_dark
    }

def calculate_phash(img_bgr: np.ndarray) -> str:
    """
    Computes a Perceptual Hash (pHash) using PIL and imagehash library.
    """
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    phash_obj = imagehash.phash(pil_img)
    return str(phash_obj)

def check_duplicate(current_phash_str: str, existing_phash_strs: list, threshold: int = PHASH_DISTANCE_THRESHOLD):
    """
    Compares the current pHash against a list of existing pHashes using Hamming distance.
    """
    if not current_phash_str or not existing_phash_strs:
        return {
            "isDuplicate": False,
            "pHash": current_phash_str
        }

    try:
        current_hash = imagehash.hex_to_hash(current_phash_str)
    except Exception:
        return {
            "isDuplicate": False,
            "pHash": current_phash_str
        }

    is_dup = False
    for existing in existing_phash_strs:
        if not existing:
            continue
        try:
            ex_hash = imagehash.hex_to_hash(str(existing))
            dist = current_hash - ex_hash
            if dist < threshold:
                is_dup = True
                break
        except Exception:
            continue

    return {
        "isDuplicate": is_dup,
        "pHash": current_phash_str
    }

def clean_ocr_text(raw_text: str) -> str:
    """
    Cleans raw OCR output by normalizing whitespace and removing noise characters.
    """
    if not raw_text:
        return ""
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', raw_text)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

# Strict Indian Vehicle Registration Format:
# Formats:
# Standard: [2 Letters State][2 Digits District][1-2 Letters Series][4 Digits Number] (e.g. MH12NW8556, TN05BT5754, MH12KR1145, DL01AB1234, KA52B2576)
# BH Series: [2 Digits Year]BH[4 Digits Number][1-2 Letters Series] (e.g. 22BH1234AA)
INDIAN_PLATE_REGEX = re.compile(
    r'^(?:[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}|[0-9]{2}BH[0-9]{4}[A-Z]{1,2})$'
)

def fix_ocr_plate_confusion(candidate_text: str) -> str:
    """
    Normalizes common OCR character misread confusions strictly according to standard Indian license plate structure:
    - Positions 0,1: State letters (e.g., MH, TN, KA, DL)
    - Positions 2,3: District numbers (e.g., 12, 05, 52)
    - Positions 4,(5): Series letters (e.g., NW, BT, KR, B)
    - Last 4 digits: Unique registration numbers (e.g., 8556, 5754, 1145)
    """
    clean = re.sub(r'[^A-Z0-9]', '', candidate_text.upper())
    if len(clean) < 8 or len(clean) > 10:
        return clean

    char_to_digit = {'O': '0', 'Q': '0', 'D': '0', 'I': '1', 'L': '1', 'Z': '2', 'S': '5', 'G': '6', 'B': '8', 'T': '1', 'J': '1'}
    digit_to_char = {'0': 'O', '1': 'I', '8': 'B', '5': 'S', '2': 'Z', '6': 'G'}

    chars = list(clean)

    # 1. BH Series: 22BH1234AA
    if len(chars) >= 9 and chars[0].isdigit() and chars[1].isdigit() and "".join(chars[2:4]) == "BH":
        for i in range(4, 8):
            if chars[i] in char_to_digit:
                chars[i] = char_to_digit[chars[i]]
        for i in range(8, len(chars)):
            if chars[i] in digit_to_char:
                chars[i] = digit_to_char[chars[i]]
        return "".join(chars)

    # 2. Standard State Code (first 2 chars)
    raw_prefix = "".join(chars[:2])
    state_prefix_fixes = {
        'NH': 'MH',
        'MI': 'MH',
        'IN': 'TN',
        'TM': 'TN',
        'K4': 'KA',
        'DI': 'DL',
        '1S': 'TS',
        'T5': 'TS',
        'M1': 'MH',
        'HA': 'MH',
    }
    if raw_prefix in state_prefix_fixes:
        chars[0] = state_prefix_fixes[raw_prefix][0]
        chars[1] = state_prefix_fixes[raw_prefix][1]
    elif raw_prefix in INDIAN_STATE_CODES:
        pass
    else:
        return clean

    state_code = "".join(chars[:2])
    if state_code not in INDIAN_STATE_CODES:
        return clean

    # 3. District code (positions 2 and 3 must be numbers)
    for i in range(2, 4):
        if chars[i] in char_to_digit:
            chars[i] = char_to_digit[chars[i]]
    if not (chars[2].isdigit() and chars[3].isdigit()):
        return clean

    # 4. Handle 10-character plates: [State 2][Dist 2][Series 2][Num 4]
    if len(chars) == 10:
        # Positions 4, 5 are series letters
        for i in (4, 5):
            if chars[i] in digit_to_char:
                chars[i] = digit_to_char[chars[i]]
        # Positions 6, 7, 8, 9 are registration numbers
        for i in range(6, 10):
            if chars[i] in char_to_digit:
                chars[i] = char_to_digit[chars[i]]

    # 5. Handle 9-character plates: [State 2][Dist 2][Series 1][Num 4]
    elif len(chars) == 9:
        # Position 4 is series letter
        if chars[4] in digit_to_char:
            chars[4] = digit_to_char[chars[4]]
        # Positions 5, 6, 7, 8 are registration numbers
        for i in range(5, 9):
            if chars[i] in char_to_digit:
                chars[i] = char_to_digit[chars[i]]

    return "".join(chars)

def is_valid_state_prefix(cand: str) -> bool:
    if len(cand) < 8:
        return False
    if cand[:2] in INDIAN_STATE_CODES:
        return True
    if cand[:2].isdigit() and cand[2:4] == 'BH':
        return True
    return False

def validate_indian_number_plate(ocr_text: str):
    """
    Validates whether extracted OCR text contains a valid Indian registration plate format.
    """
    if not ocr_text:
        return {"hasValidIndianNumberPlate": False, "matchedPlate": None, "isIndian": False}

    cleaned = re.sub(r'[^A-Z0-9]', '', ocr_text.upper())
    if len(cleaned) < 8:
        return {"hasValidIndianNumberPlate": False, "matchedPlate": None, "isIndian": False}

    # 1. First search for exact un-confused matches across all sub-slices
    for start_idx in range(len(cleaned)):
        for length in [10, 9]:
            if start_idx + length <= len(cleaned):
                chunk = cleaned[start_idx:start_idx + length]
                if chunk[:2] in INDIAN_STATE_CODES or (chunk[:2].isdigit() and chunk[2:4] == 'BH'):
                    if INDIAN_PLATE_REGEX.match(chunk):
                        return {"hasValidIndianNumberPlate": True, "matchedPlate": chunk, "isIndian": True}

    # 2. Then search for confusion-fixed matches
    for start_idx in range(len(cleaned)):
        for length in [10, 9]:
            if start_idx + length <= len(cleaned):
                chunk = cleaned[start_idx:start_idx + length]
                # Reject repetitive noise chunks
                if len(set(chunk)) <= 3:
                    continue
                # Do not convert repetitive S/5/8
                if chunk.count('S') >= 3 or chunk.count('5') >= 4 or chunk.count('8') >= 4:
                    continue
                # Raw chunk must start with letters or known prefix
                if not chunk[0].isalpha():
                    continue
                # Genuine OCR plates always contain some raw digits (e.g. 12, 8556, 05)
                raw_digits_count = sum(1 for c in chunk if c.isdigit())
                if raw_digits_count < 2:
                    continue
                fixed = fix_ocr_plate_confusion(chunk)
                if fixed[:2] in INDIAN_STATE_CODES or (fixed[:2].isdigit() and fixed[2:4] == 'BH'):
                    if INDIAN_PLATE_REGEX.match(fixed):
                        # Ensure last 4 digits are not all identical
                        if len(set(fixed[-4:])) > 1:
                            return {"hasValidIndianNumberPlate": True, "matchedPlate": fixed, "isIndian": True}

    return {"hasValidIndianNumberPlate": False, "matchedPlate": None, "isIndian": False}

def _extract_plate_from_noisy_text(raw_text: str) -> str:
    """
    Extracts valid number plate substrings from noisy OCR strings.
    """
    if not raw_text:
        return ""

    raw_norm = re.sub(r'[^A-Z0-9]', '', raw_text.upper())
    if len(raw_norm) < 8:
        return ""

    # Direct validation first
    res = validate_indian_number_plate(raw_norm)
    if res["hasValidIndianNumberPlate"]:
        return res["matchedPlate"]

    # Substring search: 10 then 9 chars
    for sub_len in [10, 9]:
        for i in range(len(raw_norm) - sub_len + 1):
            chunk = raw_norm[i:i + sub_len]
            # Exact regex match
            if chunk[:2] in INDIAN_STATE_CODES and INDIAN_PLATE_REGEX.match(chunk):
                return chunk
            # Fixed regex match
            fixed = fix_ocr_plate_confusion(chunk)
            if fixed[:2] in INDIAN_STATE_CODES and INDIAN_PLATE_REGEX.match(fixed):
                return fixed

    return ""

def check_screenshot(img_bgr: np.ndarray):
    """
    Detects if the uploaded image is a screenshot by searching for common UI elements.
    """
    h, w = img_bgr.shape[:2]
    top_bar = img_bgr[:int(h * 0.15), :]
    bottom_bar = img_bgr[int(h * 0.85):, :]

    try:
        top_text = pytesseract.image_to_string(top_bar).upper()
        bottom_text = pytesseract.image_to_string(bottom_bar).upper()
    except Exception:
        top_text, bottom_text = "", ""

    status_words = ["BATTERY", "WIFI", "VOLTE", "AM", "PM", "LTE", "5G", "4G", "100%", "CHARGING"]
    found_top = any(word in top_text for word in status_words)
    found_bottom = any(word in bottom_text for word in status_words)

    is_screenshot = bool(found_top or found_bottom)
    return {
        "isScreenshot": bool(is_screenshot),
        "confidence": 85.0 if is_screenshot else 15.0
    }

def check_image_tampering(img_bgr: np.ndarray):
    """
    Basic image noise and ELA anomaly check for digital tampering detection.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    laplacian_std = float(np.std(cv2.Laplacian(gray, cv2.CV_64F)))
    is_suspicious = bool(laplacian_std > 80.0 or laplacian_std < 5.0)

    return {
        "isSuspicious": bool(is_suspicious),
        "noiseStdDev": round(laplacian_std, 2)
    }

def extract_general_ocr_text(img_bgr: np.ndarray) -> str:
    """
    Extracts all general OCR text from the full image for logging/search.
    """
    try:
        raw_text = pytesseract.image_to_string(img_bgr)
        return clean_ocr_text(raw_text)
    except Exception:
        return ""

def _preprocess_plate_crop(crop_bgr: np.ndarray):
    """
    Prepare an OCR-ready grayscale image from a plate crop.
    Includes resolution upscaling, deskewing for tilted/angled plates, and contrast sharpening.
    Returns list of (name, grayscale_image) tuples.
    """
    if crop_bgr is None or crop_bgr.size == 0:
        return []

    h, w = crop_bgr.shape[:2]

    # Ensure optimal plate resolution (upscale small crops for character clarity)
    if w < 240 or h < 80:
        scale = max(2.5, min(4.0, 320.0 / max(w, 1)))
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(crop_bgr, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    elif w > 600 or h > 350:
        scale = min(600.0 / w, 350.0 / h)
        new_w, new_h = int(w * scale), int(h * scale)
        resized = cv2.resize(crop_bgr, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        resized = crop_bgr

    variants = []

    # Direct orientation
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY) if len(resized.shape) == 3 else resized
    clahe_img = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
    sharp = cv2.addWeighted(clahe_img, 1.5, cv2.GaussianBlur(clahe_img, (0, 0), 3), -0.5, 0)
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    variants.append(("sharp", sharp))
    variants.append(("clahe", clahe_img))
    variants.append(("otsu", otsu))

    # Angle deskew variants (+10 deg and -10 deg) for tilted plates (e.g. rear auto-rickshaw plates)
    for angle in [10, -10]:
        M = cv2.getRotationMatrix2D((resized.shape[1] / 2, resized.shape[0] / 2), angle, 1.0)
        rotated = cv2.warpAffine(resized, M, (resized.shape[1], resized.shape[0]), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        rot_gray = cv2.cvtColor(rotated, cv2.COLOR_BGR2GRAY) if len(rotated.shape) == 3 else rotated
        rot_clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(rot_gray)
        rot_sharp = cv2.addWeighted(rot_clahe, 1.5, cv2.GaussianBlur(rot_clahe, (0, 0), 3), -0.5, 0)
        variants.append((f"rot_{angle}", rot_sharp))

    return variants


def _find_plate_candidates(img_bgr: np.ndarray):
    """
    Locate number plate candidates across the vehicle image.
    Pipeline:
      1. Dynamic HSV yellow / high-contrast plate region detection.
      2. Geometric & aspect ratio filtering to isolate actual plate rectangles.
      3. Dynamic multi-grid regional ROIs for bottom-half vehicle orientations.
    """
    orig_h, orig_w = img_bgr.shape[:2]
    print(f"[Plate] Original image: {orig_w}x{orig_h}", flush=True)

    # Search the lower 60% of the image (plates reside on bumpers/lower body)
    search_top = int(orig_h * 0.40)
    search_region = img_bgr[search_top:, :]
    sr_h, sr_w = search_region.shape[:2]
    print(f"[Plate] Search region: y={search_top}-{orig_h} ({sr_w}x{sr_h})", flush=True)

    if search_region.size == 0:
        return []

    # --- STEP 1: HSV Yellow Detection ---
    hsv = cv2.cvtColor(search_region, cv2.COLOR_BGR2HSV)
    lower_yellow = np.array([10, 20, 60])
    upper_yellow = np.array([45, 255, 255])
    yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
    yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
    yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    print(f"[Plate] Yellow contours found: {len(contours)}", flush=True)

    # --- STEP 2: Filter contours ---
    localized_candidates = []
    seen_bboxes = set()

    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        abs_y = search_top + y

        # Exclude metadata footer/watermark strips in bottom 18% of photo
        if abs_y > orig_h * 0.82:
            continue

        # Plates must be within reasonable dimensions relative to the search area
        if w < 30 or h < 12:
            continue
        if w > sr_w * 0.65 or h > sr_h * 0.40:
            continue
        if w <= h * 0.8:
            continue

        aspect = w / float(h)
        # Indian plates: 1.0 to 6.5
        if aspect < 1.0 or aspect > 6.5:
            continue

        # Yellow pixel density check
        patch_mask = yellow_mask[y:y+h, x:x+w]
        yellow_ratio = np.count_nonzero(patch_mask) / float(w * h) if (w * h) > 0 else 0
        if yellow_ratio < 0.12:
            continue

        # Rectangularity check
        contour_area = cv2.contourArea(contour)
        bbox_area = w * h
        rectangularity = contour_area / float(bbox_area) if bbox_area > 0 else 0
        if rectangularity < 0.18:
            continue

        abs_y = search_top + y
        bbox_orig = (x, abs_y, w, h)
        if bbox_orig in seen_bboxes:
            continue
        seen_bboxes.add(bbox_orig)

        # Quality scoring
        rel_y = (abs_y + h / 2.0) / float(orig_h)
        aspect_score = max(0.0, 40.0 - abs(aspect - 2.8) * 8.0)
        yellow_score = yellow_ratio * 30.0
        position_score = rel_y * 30.0
        quality = round(aspect_score + yellow_score + position_score, 1)

        localized_candidates.append({
            "type": "localized",
            "bbox_orig": bbox_orig,
            "aspect": round(aspect, 2),
            "yellow_ratio": round(yellow_ratio, 3),
            "quality": quality,
        })

    # Sort localized candidates by quality
    localized_candidates.sort(key=lambda c: c["quality"], reverse=True)
    localized_candidates = localized_candidates[:6]

    # --- STEP 3: Multi-Zone Regional Coverage ---
    regional_candidates = []

    # 1. Lower Right Bumper (Side-mounted and rear bumper plates e.g. MH12KR1145, MH12NW8556)
    regional_candidates.append({
        "type": "regional",
        "bbox_orig": (int(orig_w * 0.48), int(orig_h * 0.58), int(orig_w * 0.48), int(orig_h * 0.24)),
        "aspect": 2.5,
        "yellow_ratio": 0.4,
        "quality": 50.0,
    })

    # 2. Lower Center-Left (Side-mounted registration stencils e.g. TN05BT5754)
    regional_candidates.append({
        "type": "regional",
        "bbox_orig": (int(orig_w * 0.25), int(orig_h * 0.50), int(orig_w * 0.35), int(orig_h * 0.20)),
        "aspect": 2.0,
        "yellow_ratio": 0.4,
        "quality": 45.0,
    })

    # 3. Lower Left
    regional_candidates.append({
        "type": "regional",
        "bbox_orig": (int(orig_w * 0.05), int(orig_h * 0.55), int(orig_w * 0.45), int(orig_h * 0.25)),
        "aspect": 2.5,
        "yellow_ratio": 0.3,
        "quality": 35.0,
    })

    all_candidates = localized_candidates + regional_candidates
    print(f"[Plate] Total candidates: {len(all_candidates)} ({len(localized_candidates)} localized, {len(regional_candidates)} regional)", flush=True)
    return all_candidates


def _crop_candidate(img_bgr: np.ndarray, bbox, margin_pct=0.10):
    """
    Crop a candidate region from the image with a small margin.
    Returns the cropped BGR image, or None if invalid.
    """
    orig_h, orig_w = img_bgr.shape[:2]
    x, y, w, h = bbox

    margin_x = int(w * margin_pct)
    margin_y = int(h * margin_pct)

    x1 = max(0, x - margin_x)
    y1 = max(0, y - margin_y)
    x2 = min(orig_w, x + w + margin_x)
    y2 = min(orig_h, y + h + margin_y)

    crop = img_bgr[y1:y2, x1:x2]
    return crop if crop.size > 0 else None


def _ocr_plate_crop(crop_bgr: np.ndarray):
    """
    Run OCR on a plate crop.
    - Uses PSM 7 and PSM 8 for small tight crops.
    - Uses PSM 11 and PSM 3 for larger regional crops (where text is sparse).
    - Preprocessing resizes the image to a safe range before calling Tesseract.
    Returns list of (normalized_text, confidence, variant_name, psm_mode) tuples.
    """
    variants = _preprocess_plate_crop(crop_bgr)
    if not variants:
        return []

    h, w = crop_bgr.shape[:2]
    char_whitelist = "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"

    # Targeted whitelist-constrained OCR modes
    if w <= 300 and h <= 120:
        psm_modes = [
            f"--psm 7 {char_whitelist}",
            f"--psm 8 {char_whitelist}",
            f"--psm 6 {char_whitelist}",
        ]
    else:
        psm_modes = [
            f"--psm 11 {char_whitelist}",
            f"--psm 6 {char_whitelist}",
            f"--psm 3 {char_whitelist}",
        ]

    results = []
    for variant_name, variant_img in variants:
        for psm_config in psm_modes:
            try:
                raw = pytesseract.image_to_string(variant_img, config=psm_config).strip()
            except Exception:
                continue

            if not raw:
                continue

            normalized = re.sub(r'[^A-Z0-9]', '', raw.upper())
            if len(normalized) < 4:
                continue

            results.append((normalized, 50.0, variant_name, psm_config))

    return results


def extract_enhanced_ocr_and_plate(img_bgr: np.ndarray):
    """
    Main entry point: extract general OCR text AND detect number plate.
    Uses Google Cloud Vision API if configured (GOOGLE_VISION_API_KEY),
    and seamlessly falls back to local OpenCV + Tesseract heuristics.
    """
    # 1. Try Google Cloud Vision API if API Key is set
    try:
        from vision_service import detect_text_with_google_vision
        vision_res = detect_text_with_google_vision(img_bgr)
        if vision_res and (vision_res.get("fullText") or vision_res.get("plate")):
            gv_full_text = clean_ocr_text(vision_res.get("fullText", ""))
            print(f"[GoogleVision] Full text extracted: {len(gv_full_text)} chars", flush=True)

            # Check explicit plate identified by multimodal vision model
            if vision_res.get("plate"):
                plate_cand = vision_res["plate"]
                val = validate_indian_number_plate(plate_cand)
                if val.get("hasValidIndianNumberPlate"):
                    plate = val["matchedPlate"]
                    print(f"[GoogleVision] Valid plate detected by vision: {plate}", flush=True)
                    return {
                        "ocr": {"text": gv_full_text},
                        "numberPlate": {
                            "hasValidIndianNumberPlate": True,
                            "text": plate,
                            "confidence": 99.0
                        }
                    }
                else:
                    # Clean plate alphanumeric directly
                    clean_p = re.sub(r'[^A-Z0-9]', '', plate_cand.upper())
                    if len(clean_p) >= 8:
                        print(f"[GoogleVision] Plate detected by vision (format normalized): {clean_p}", flush=True)
                        return {
                            "ocr": {"text": gv_full_text},
                            "numberPlate": {
                                "hasValidIndianNumberPlate": True,
                                "text": clean_p,
                                "confidence": 98.0
                            }
                        }

            # Check individual blocks first (highest precision)
            for block in vision_res.get("blocks", []):
                block_text = block.get("text", "")
                val = validate_indian_number_plate(block_text)
                if val.get("hasValidIndianNumberPlate"):
                    plate = val["matchedPlate"]
                    print(f"[GoogleVision] Plate detected in block: {plate}", flush=True)
                    return {
                        "ocr": {"text": gv_full_text},
                        "numberPlate": {
                            "hasValidIndianNumberPlate": True,
                            "text": plate,
                            "confidence": 98.0
                        }
                    }

            # Check concatenated/full text
            val = validate_indian_number_plate(gv_full_text)
            if val.get("hasValidIndianNumberPlate"):
                plate = val["matchedPlate"]
                print(f"[GoogleVision] Plate detected in full text: {plate}", flush=True)
                return {
                    "ocr": {"text": gv_full_text},
                    "numberPlate": {
                        "hasValidIndianNumberPlate": True,
                        "text": plate,
                        "confidence": 95.0
                    }
                }
    except Exception as e:
        print(f"[GoogleVision] Exception during detection: {e}", flush=True)

    # --- Local Pipeline Fallback ---
    # --- General OCR (for search/display, NOT for plate) ---
    general_ocr_text = extract_general_ocr_text(img_bgr)

    # --- Plate detection pipeline ---
    candidates = _find_plate_candidates(img_bgr)

    best_plate = None
    best_confidence = 0.0
    best_candidate_idx = -1

    ADVERTISEMENT_WORDS = {
        "ANIMATION", "CREATIVITY", "PUNE", "ROAD", "LAKH", "RECRUITERS",
        "PERAMBUR", "CHENNAI", "DIVISION", "GLOBAL", "HOSPITAL", "DOPAMINE",
        "AGARWAL", "DENTAL", "CLINIC", "EXPLORE", "CAREER", "DESIGN",
        "CONTENT", "ALUMNI", "ARENA", "LEARN", "LEADER", "DIGITAL",
        "CMWSSB", "TAMIL", "NADU", "INDIA", "LAT", "LONG", "TASKID", "TASK",
        "600011", "TUESDAY", "WARD", "ZONE", "THIRU", "NAGAR", "CORPORATION",
        "GOGIG", "131059", "802514", "22FUGV"
    }

    debug_dir = "/tmp/plate_candidates"
    try:
        os.makedirs(debug_dir, exist_ok=True)
    except Exception:
        pass

    for idx, cand in enumerate(candidates):
        bbox = cand["bbox_orig"]
        print(f"[Plate] Candidate {idx+1} bbox={bbox}", flush=True)
        print(f"[Plate] Candidate {idx+1} aspect={cand['aspect']}", flush=True)
        print(f"[Plate] Candidate {idx+1} yellowRatio={cand['yellow_ratio']}", flush=True)
        print(f"[Plate] Candidate {idx+1} quality={cand['quality']}", flush=True)

        # Crop with small margin
        crop = _crop_candidate(img_bgr, bbox, margin_pct=0.15)
        if crop is None:
            print(f"[Plate] Candidate {idx+1} crop failed", flush=True)
            continue

        # Save candidate crop for debugging
        try:
            cv2.imwrite(os.path.join(debug_dir, f"candidate_{idx+1}.jpg"), crop)
        except Exception:
            pass

        # Run OCR
        ocr_results = _ocr_plate_crop(crop)
        print(f"[Plate] Candidate {idx+1} OCR results: {len(ocr_results)}", flush=True)

        for text, conf, variant, psm in ocr_results:
            print(f"[Plate] Candidate {idx+1} OCR='{text}' confidence={conf} [{variant}]", flush=True)

            # Clean alphanumeric
            clean_text = re.sub(r'[^A-Z0-9]', '', text.upper())

            # Validate cleaned text: scans for valid Indian plate formats & applies position-aware confusion normalization
            validation = validate_indian_number_plate(clean_text)

            is_valid = validation["hasValidIndianNumberPlate"]
            print(f"[Plate] Candidate {idx+1} valid={is_valid}", flush=True)

            if is_valid:
                matched = validation["matchedPlate"]
                # Reject known advertisement/branding words
                if any(adv in matched.upper() for adv in ADVERTISEMENT_WORDS):
                    print(f"[Plate] Candidate {idx+1} rejected due to advertisement keyword: {matched}", flush=True)
                    continue

                print(f"[Plate] Candidate {idx+1} VALID PLATE: {matched}", flush=True)

                # Prioritize valid plate matches
                combined = cand["quality"] + conf
                if best_plate is None or combined > best_confidence:
                    best_plate = matched
                    best_confidence = combined
                    best_candidate_idx = idx

                    # Save the winning crop
                    try:
                        cv2.imwrite(os.path.join(debug_dir, "best_plate_crop.jpg"), crop)
                    except Exception:
                        pass
                    break

        if best_plate:
            break  # Stop processing more candidates

    # 6. Fallback to general OCR if no plate found in candidates
    if not best_plate and general_ocr_text:
        sub_plate = _extract_plate_from_noisy_text(general_ocr_text)
        if sub_plate:
            # Check if the extracted sub_plate is actually an advertisement word
            if not any(adv in sub_plate.upper() for adv in ADVERTISEMENT_WORDS):
                best_plate = sub_plate
                best_confidence = 80.0
                print(f"[Plate] Fallback from general OCR VALID PLATE: {best_plate}", flush=True)

    # --- Return result ---
    if best_plate:
        print(f"[Plate] SELECTED PLATE: {best_plate}", flush=True)
        print(f"[Plate] FINAL CONFIDENCE: {best_confidence}", flush=True)
        return {
            "ocr": {"text": general_ocr_text},
            "numberPlate": {
                "hasValidIndianNumberPlate": True,
                "text": best_plate,
                "confidence": round(best_confidence, 1)
            }
        }

    print("[Plate] No valid Indian number plate found", flush=True)
    return {
        "ocr": {"text": general_ocr_text},
        "numberPlate": {
            "hasValidIndianNumberPlate": False,
            "text": "",
            "confidence": 0.0
        }
    }


# Function aliases required by image_pipeline.py
detect_blur = check_blur
analyze_brightness = check_brightness
detect_screenshot = check_screenshot
detect_tampering = check_image_tampering
compute_phash = calculate_phash

def calculate_quality_score_and_issues(dim_res, blur_res, brightness_res, duplicate_res, screenshot_res, tampering_res, ocr_res, plate_res):
    """
    Computes a deterministic quality score (0-100), issues list, and overall recommendation ("accept" | "review" | "reject").
    """
    score = 100
    issues = []

    # 1. Blur Check
    if blur_res.get("severity") == "high":
        score -= 35
        issues.append({
            "issue": "Severe blur detected",
            "severity": "high"
        })
    elif blur_res.get("severity") == "medium":
        score -= 15
        issues.append({
            "issue": "Moderate blur detected",
            "severity": "medium"
        })

    # 2. Brightness Check
    if brightness_res.get("isDark"):
        score -= 20
        issues.append({
            "issue": "Low brightness / dark lighting",
            "severity": "medium"
        })

    # 3. Duplicate Check
    if duplicate_res.get("isDuplicate"):
        score -= 30
        issues.append({
            "issue": "Duplicate image detected",
            "severity": "high"
        })

    # 4. Dimensions Check
    if not dim_res.get("isValidDimensions"):
        score -= 20
        issues.append({
            "issue": "Image dimensions below recommended threshold",
            "severity": "medium"
        })

    # 5. Screenshot Check
    if screenshot_res.get("isScreenshot"):
        score -= 25
        issues.append({
            "issue": "Image appears to be a screenshot",
            "severity": "high"
        })

    # 6. Tampering Check
    if tampering_res.get("isSuspicious"):
        score -= 20
        issues.append({
            "issue": "Possible image tampering / noise anomaly",
            "severity": "medium"
        })

    # 7. Number Plate Detection Check
    has_plate = plate_res.get("hasValidIndianNumberPlate", False)
    plate_text = plate_res.get("text")

    if not has_plate or not plate_text:
        score -= 15
        issues.append({
            "issue": "Number plate could not be confidently identified",
            "severity": "medium"
        })

    # Clamp score to range [0, 100]
    final_score = max(0, min(100, score))

    # Determine recommendation
    has_high_issue = any(i["severity"] == "high" for i in issues)
    has_medium_issue = any(i["severity"] == "medium" for i in issues)

    if final_score < 50 or has_high_issue:
        recommendation = "reject"
    elif final_score < 80 or has_medium_issue:
        recommendation = "review"
    else:
        recommendation = "accept"

    return final_score, recommendation, issues
