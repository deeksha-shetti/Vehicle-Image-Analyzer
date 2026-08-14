import cv2
import numpy as np
import pytesseract
import re
import sys

sys.path.insert(0, "/app/src")
from heuristics import validate_indian_number_plate, fix_ocr_plate_confusion

img0 = cv2.imread("/app/src/img0.png")
img1 = cv2.imread("/app/src/img1.png")

def test_crop(img, bbox, label):
    x, y, w, h = bbox
    img_h, img_w = img.shape[:2]
    
    print(f"\n==========================================")
    print(f"Testing {label} bbox={bbox}")
    print(f"==========================================")
    
    crop = img[y:y+h, x:x+w]
    if crop.size == 0:
        print("Crop size is 0!")
        return
        
    up = cv2.resize(crop, (600, 180), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    for p_name, p_img in [("clahe", clahe), ("otsu", otsu), ("gray", gray)]:
        for psm in ["--psm 6", "--psm 11", "--psm 7", "--psm 3"]:
            txt = pytesseract.image_to_string(p_img, config=psm).strip()
            clean = re.sub(r'[^A-Z0-9]', '', txt.upper())
            fixed = fix_ocr_plate_confusion(clean)
            val = validate_indian_number_plate(clean)
            val_fix = validate_indian_number_plate(fixed)
            
            print(f"  [{p_name}|{psm}] -> Raw: '{txt}' -> Clean: '{clean}' -> Fixed: '{fixed}'")
            if val["hasValidIndianNumberPlate"]:
                print(f"      🎉 VALID MATCH: {val['matchedPlate']}")
            elif val_fix["hasValidIndianNumberPlate"]:
                print(f"      🎉 VALID FIXED MATCH: {val_fix['matchedPlate']}")

test_crop(img0, (448, 809, 36, 10), "img0 (MH12KR1145 expected)")
test_crop(img1, (309, 1097, 100, 39), "img1 (TN05BT5754 expected)")
