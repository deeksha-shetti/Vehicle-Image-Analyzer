import cv2
import numpy as np
import pytesseract
import re
import sys

sys.path.insert(0, "/app/src")
from heuristics import validate_indian_number_plate, fix_ocr_plate_confusion

img0 = cv2.imread("/app/src/img0.png")
img1 = cv2.imread("/app/src/img1.png")

def test_box_ocr(img, bbox, label):
    x, y, w, h = bbox
    img_h, img_w = img.shape[:2]
    
    print(f"\n==========================================")
    print(f"Testing {label} with bbox={bbox}")
    print(f"==========================================")
    
    # Try multiple padding multipliers (0.1, 0.2, 0.3, 0.5, 0.8)
    for mult in [0.1, 0.2, 0.3, 0.5, 0.8, 1.0]:
        pad_w = int(w * mult)
        pad_h = int(h * mult)
        px1 = max(0, x - pad_w)
        py1 = max(0, y - pad_h)
        px2 = min(img_w, x + w + pad_w)
        py2 = min(img_h, y + h + pad_h)
        
        crop = img[py1:py2, px1:px2]
        if crop.size == 0:
            continue
            
        up = cv2.resize(crop, (600, 180), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, otsu_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9)
        
        for p_name, p_img in [("clahe", clahe), ("otsu", otsu), ("otsu_inv", otsu_inv), ("adaptive", adaptive), ("gray", gray)]:
            for psm in ["--psm 6", "--psm 11", "--psm 7", "--psm 3", "--psm 4"]:
                txt = pytesseract.image_to_string(p_img, config=psm).strip()
                clean = re.sub(r'[^A-Z0-9]', '', txt.upper())
                fixed = fix_ocr_plate_confusion(clean)
                val = validate_indian_number_plate(clean)
                val_fix = validate_indian_number_plate(fixed)
                
                if val["hasValidIndianNumberPlate"] or val_fix["hasValidIndianNumberPlate"]:
                    matched = val["matchedPlate"] if val["hasValidIndianNumberPlate"] else val_fix["matchedPlate"]
                    print(f"  🎉 MATCH FOUND! mult={mult}, [{p_name}|{psm}] -> raw='{txt}' -> clean='{clean}' -> MATCH='{matched}'")
                elif any(k in clean for k in ["MH", "12", "KR", "1145", "TN", "05", "BT", "5754"]):
                    print(f"  PARTIAL KEYWORD: mult={mult}, [{p_name}|{psm}] -> raw='{txt}' -> clean='{clean}' -> fixed='{fixed}'")

test_box_ocr(img0, (448, 809, 36, 10), "img0 bbox=(448, 809, 36, 10)")
test_box_ocr(img1, (309, 1097, 100, 39), "img1 bbox=(309, 1097, 100, 39)")
