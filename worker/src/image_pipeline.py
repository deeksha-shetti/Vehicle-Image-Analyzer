import cv2
from heuristics import (
    check_dimensions,
    detect_blur,
    analyze_brightness,
    detect_screenshot,
    detect_tampering,
    compute_phash,
    check_duplicate,
    extract_enhanced_ocr_and_plate,
    calculate_quality_score_and_issues,
)

def run_image_analysis(img_bgr, existing_phashes=None):
    """
    Executes the full vehicle image analysis pipeline including usability & integrity heuristics.
    Returns structured analysis payload matching API contract.
    """
    if existing_phashes is None:
        existing_phashes = []

    height, width, channels = img_bgr.shape
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    # 1. Dimensions check
    dim_res = check_dimensions(width, height)

    # 2. Blur detection
    blur_res = detect_blur(gray)

    # 3. Brightness analysis
    brightness_res = analyze_brightness(gray)

    # 4. Screenshot / Photo-of-photo detection
    screenshot_res = detect_screenshot(img_bgr)

    # 5. Tampering / noise anomaly detection
    tampering_res = detect_tampering(img_bgr)

    # 6. Duplicate detection via pHash
    phash_str = compute_phash(img_bgr)
    duplicate_res = check_duplicate(phash_str, existing_phashes)

    # 7. Enhanced OCR and Indian Number Plate Extraction
    ocr_and_plate = extract_enhanced_ocr_and_plate(img_bgr)
    ocr_res = ocr_and_plate["ocr"]
    plate_res = ocr_and_plate["numberPlate"]

    # 8. Quality Score, Recommendation ("accept" | "review" | "reject"), and Issues
    quality_score, recommendation, issues = calculate_quality_score_and_issues(
        dim_res, blur_res, brightness_res, duplicate_res, screenshot_res, tampering_res, ocr_res, plate_res
    )

    analysis_payload = {
        "recommendation": recommendation,
        "dimensions": {
            "width": int(width),
            "height": int(height)
        },
        "blur": blur_res,
        "brightness": brightness_res,
        "duplicate": duplicate_res,
        "screenshotDetection": screenshot_res,
        "tampering": tampering_res,
        "ocr": ocr_res,
        "numberPlate": plate_res,
        "qualityScore": int(quality_score),
        "issues": issues
    }

    return analysis_payload
