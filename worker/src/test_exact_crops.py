import cv2
import numpy as np
import pytesseract
import re
import sys

sys.path.insert(0, "/app/src")
from heuristics import validate_indian_number_plate, fix_ocr_plate_confusion

img0 = cv2.imread("/app/src/img0.png")
img1 = cv2.imread("/app/src/img1.png")

def test_crop_variations(img, bbox, label):
    x, y, w, h = bbox
    img_h, img_w = img.shape[:2]
    
    print(f"\n==========================================")
    print(f"Testing exact crop variations for {label}: bbox={bbox}")
    print(f"==========================================")
    
    # Try different padding percentages around bbox (10%, 20%, 30%, 40%)
    for pad_pct in [0.10, 0.20, 0.30, 0.40]:
        pad_w = int(w * pad_pct)
        pad_h = int(h * pad_pct)
        px1 = max(0, x - pad_w)
        py1 = max(0, y - pad_h)
        px2 = min(img_w, x + w + pad_w)
        py2 = min(img_h, y + h + pad_h)
        
        crop = img[py1:py2, px1:px2]
        if crop.size == 0:
            continue
            
        for target_w, target_h in [(600, 180), (800, 200), (400, 300)]:
            up = cv2.resize(crop, (target_w, target_h), interpolation=cv2.INTER_CUBIC)
            gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
            _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            _, otsu_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9)
            
            for p_name, p_img in [("clahe", clahe), ("otsu", otsu), ("otsu_inv", otsu_inv), ("adaptive", adaptive), ("gray", gray)]:
                for psm in ["--psm 7", "--psm 6", "--psm 8", "--psm 11", "--psm 3"]:
                    try:
                        txt = pytesseract.image_to_string(p_img, config=f"{psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n").strip()
                        clean = re.sub(r'[^A-Z0-9]', '', txt.upper())
                        fixed = fix_ocr_plate_confusion(clean)
                        
                        val = validate_indian_number_plate(clean)
                        val_fix = validate_indian_number_plate(fixed)
                        
                        if val["hasValidIndianNumberPlate"] or val_fix["hasValidIndianNumberPlate"]:
                            matched = val["matchedPlate"] if val["hasValidIndianNumberPlate"] else val_fix["matchedPlate"]
                            print(f"  🎉 VALID PLATE FOUND! pad={pad_pct}, size={target_w}x{target_h}, [{p_name}|{psm}] -> raw='{txt}' -> clean='{clean}' -> MATCH='{matched}'")
                        elif len(clean) >= 4 and any(k in clean for k in ["MH", "12", "KR", "1145", "TN", "05", "BT", "5754"]):
                            print(f"  PARTIAL OCR: pad={pad_pct}, size={target_w}x{target_h}, [{p_name}|{psm}] -> raw='{txt}' -> clean='{clean}' -> fixed='{fixed}'")
                    except Exception:
                        pass

test_crop_variations(img0, (448, 809, 36, 10), "img0 (MH12KR1145 expected)")
test_crop_variations(img1, (309, 1097, 100, 39), "img1 (TN05BT5754 expected)")
