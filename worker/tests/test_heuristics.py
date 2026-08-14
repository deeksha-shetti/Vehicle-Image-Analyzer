import os
import sys
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from heuristics import (
    detect_blur,
    analyze_brightness,
    detect_screenshot,
    detect_tampering,
    clean_ocr_text,
    fix_ocr_plate_confusion,
    validate_indian_number_plate,
    calculate_quality_score_and_issues,
    extract_enhanced_ocr_and_plate,
    locate_plate_candidate_crops,
)

def test_detect_blur():
    sharp = np.zeros((100, 100), dtype=np.uint8)
    sharp[::2, ::2] = 255
    res_sharp = detect_blur(sharp, threshold=100.0)
    assert res_sharp["isBlurred"] is False
    assert res_sharp["severity"] == "low"
    assert res_sharp["blurScore"] > 100.0

    blurry = np.full((100, 100), 128, dtype=np.uint8)
    res_blurry = detect_blur(blurry, threshold=100.0)
    assert res_blurry["isBlurred"] is True
    assert res_blurry["severity"] == "high"
    assert res_blurry["blurScore"] == 0.0

def test_analyze_brightness():
    bright = np.full((50, 50), 200, dtype=np.uint8)
    res_bright = analyze_brightness(bright, threshold=50.0)
    assert res_bright["isDark"] is False

    dark = np.full((50, 50), 20, dtype=np.uint8)
    res_dark = analyze_brightness(dark, threshold=50.0)
    assert res_dark["isDark"] is True

def test_detect_screenshot():
    img_screen = np.zeros((900, 1950, 3), dtype=np.uint8)
    res = detect_screenshot(img_screen)
    assert res["isLikelyScreenshot"] is True
    assert res["confidence"] >= 0.6

def test_detect_tampering():
    img_normal = np.full((200, 200, 3), 128, dtype=np.uint8)
    res = detect_tampering(img_normal)
    assert res["isSuspicious"] is False

def test_clean_ocr_text():
    assert clean_ocr_text("  MH-12  AB.1234\n ") == "MH12 AB1234"
    assert clean_ocr_text("!!!KA-01-AB-1234???") == "KA01AB1234"

def test_fix_ocr_plate_confusion():
    assert fix_ocr_plate_confusion("MHl2AB123O") == "MH12AB1230"
    assert fix_ocr_plate_confusion("XX12AB1234") == "XX12AB1234"

def test_valid_indian_plate_candidate():
    assert validate_indian_number_plate("MH12KR1145")["hasValidIndianNumberPlate"] is True
    assert validate_indian_number_plate("KA01AB1234")["hasValidIndianNumberPlate"] is True
    assert validate_indian_number_plate("DL01C5678")["hasValidIndianNumberPlate"] is True
    assert validate_indian_number_plate("22BH1234AA")["hasValidIndianNumberPlate"] is True

def test_false_ocr_advertisement_rejection():
    # Arbitrary advertisement text matching regex (e.g. AS50SS5555) must NOT be accepted on blank/low-visual images
    blank_ad_img = np.full((300, 300, 3), 220, dtype=np.uint8)
    res = extract_enhanced_ocr_and_plate(blank_ad_img)
    assert res["numberPlate"]["hasValidIndianNumberPlate"] is False
    assert res["numberPlate"]["text"] is None

def test_invalid_state_prefix():
    # Prefix XX is NOT a valid Indian state or UT code
    assert validate_indian_number_plate("XX12AB1234")["hasValidIndianNumberPlate"] is False

def test_no_detectable_plate_returns_uncertainty():
    synthetic_no_plate = np.full((400, 400, 3), 180, dtype=np.uint8)
    res = extract_enhanced_ocr_and_plate(synthetic_no_plate)
    assert res["numberPlate"]["hasValidIndianNumberPlate"] is False
    assert res["numberPlate"]["text"] is None
    assert isinstance(res["numberPlate"]["confidence"], float)

def test_multiple_candidate_crops_generated():
    img = np.full((400, 600, 3), 120, dtype=np.uint8)
    crops = locate_plate_candidate_crops(img)
    assert isinstance(crops, list)
    assert len(crops) > 0

def test_calculate_quality_score_and_issues():
    dim = {"isSuspicious": False}
    blur = {"severity": "low"}
    bright = {"isDark": False}
    dup = {"isDuplicate": False}
    screen = {"isLikelyScreenshot": False}
    tamper = {"isSuspicious": False}
    ocr = {"text": "General background text"}
    plate = {"hasValidIndianNumberPlate": True, "text": "MH12KR1145", "confidence": 95.0}

    score, rec, issues = calculate_quality_score_and_issues(dim, blur, bright, dup, screen, tamper, ocr, plate)
    assert score == 100
    assert rec == "accept"
    assert len(issues) == 0

    # Missing plate -> issue added & review recommendation
    plate_invalid = {"hasValidIndianNumberPlate": False, "text": None, "confidence": 20.0}
    score_rev, rec_rev, issues_rev = calculate_quality_score_and_issues(dim, blur, bright, dup, screen, tamper, ocr, plate_invalid)
    assert score_rev == 85
    assert rec_rev == "review"
    issue_names = [i["issue"] for i in issues_rev]
    assert "Number plate could not be confidently identified" in issue_names
