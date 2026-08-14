import cv2
import numpy as np
import pytesseract
import re
import sys

sys.path.insert(0, "/app/src")
from heuristics import validate_indian_number_plate, fix_ocr_plate_confusion

def dense_search(img_path, img_name, keywords):
    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to read {img_path}")
        return
    h, w = img.shape[:2]
    print(f"\n==========================================")
    print(f"Dense Search in {img_name} ({w}x{h}) - Searching for {keywords}")
    print(f"==========================================")
    
    # We step y from 40% of h to 85% of h in steps of 35px
    # We step x from 10% of w to 80% of w in steps of 40px
    # Window sizes: (160x60), (220x80), (300x100)
    
    found_count = 0
    
    for win_w in [160, 220, 280]:
        for win_h in [50, 75, 100]:
            for y in range(int(h * 0.40), int(h * 0.85), 35):
                for x in range(int(w * 0.10), int(w * 0.80), 40):
                    if x + win_w > w or y + win_h > h:
                        continue
                        
                    crop = img[y:y+win_h, x:x+win_w]
                    up = cv2.resize(crop, (600, 180), interpolation=cv2.INTER_CUBIC)
                    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
                    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    for p_name, p_img in [("clahe", clahe), ("otsu", otsu)]:
                        for psm in ["--psm 6", "--psm 7", "--psm 11"]:
                            try:
                                txt = pytesseract.image_to_string(p_img, config=psm).strip()
                                clean = re.sub(r'[^A-Z0-9]', '', txt.upper())
                                fixed = fix_ocr_plate_confusion(clean)
                                
                                val = validate_indian_number_plate(clean)
                                val_fix = validate_indian_number_plate(fixed)
                                
                                if val["hasValidIndianNumberPlate"] or val_fix["hasValidIndianNumberPlate"]:
                                    matched = val["matchedPlate"] if val["hasValidIndianNumberPlate"] else val_fix["matchedPlate"]
                                    print(f"  🎉 FOUND VALID PLATE! bbox=({x},{y},{win_w},{win_h}) [{p_name}|{psm}] -> raw='{txt}' -> clean='{clean}' -> MATCH='{matched}'")
                                    found_count += 1
                                    if found_count >= 10:
                                        return
                                elif any(k in clean for k in keywords):
                                    print(f"  PARTIAL KEYWORD: bbox=({x},{y},{win_w},{win_h}) [{p_name}|{psm}] -> raw='{txt}' -> clean='{clean}' -> fixed='{fixed}'")
                            except Exception:
                                pass

dense_search("/app/src/img0.png", "img0.png (MH12KR1145 expected)", ["MH12", "KR11", "1145", "MH", "KR"])
dense_search("/app/src/img1.png", "img1.png (TN05BT5754 expected)", ["TN05", "BT57", "5754", "TN", "BT"])
