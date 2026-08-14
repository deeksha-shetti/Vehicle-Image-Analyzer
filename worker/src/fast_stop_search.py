import os
import glob
import cv2
import pytesseract
import re
import sys

sys.path.insert(0, "/app/src")
from heuristics import validate_indian_number_plate, fix_ocr_plate_confusion

def fast_search(crop_dir, target_name):
    files = glob.glob(f"{crop_dir}/*.png")
    print(f"\n==========================================")
    print(f"Fast searching {len(files)} crops in {target_name}")
    print(f"==========================================")
    
    psm_configs = ["--psm 6", "--psm 7", "--psm 11", "--psm 3", "--psm 8"]
    
    for f in files:
        img = cv2.imread(f)
        if img is None:
            continue
        
        up = cv2.resize(img, (800, 200), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        for p_name, p_img in [("clahe", clahe), ("otsu", otsu), ("gray", gray)]:
            for psm in psm_configs:
                try:
                    txt = pytesseract.image_to_string(p_img, config=psm).strip()
                    clean = re.sub(r'[^A-Z0-9]', '', txt.upper())
                    
                    val = validate_indian_number_plate(clean)
                    if val["hasValidIndianNumberPlate"]:
                        print(f"\n🎉 SUCCESS IN {target_name}!")
                        print(f"File: {os.path.basename(f)}")
                        print(f"Variant: [{p_name} | {psm}]")
                        print(f"Raw text: '{txt}'")
                        print(f"Clean text: '{clean}'")
                        print(f"Matched plate: {val['matchedPlate']}")
                        return
                    
                    # Also try fixing OCR confusions
                    fixed = fix_ocr_plate_confusion(clean)
                    val_fix = validate_indian_number_plate(fixed)
                    if val_fix["hasValidIndianNumberPlate"]:
                        print(f"\n🎉 SUCCESS WITH FIX IN {target_name}!")
                        print(f"File: {os.path.basename(f)}")
                        print(f"Variant: [{p_name} | {psm}]")
                        print(f"Raw text: '{txt}'")
                        print(f"Clean text: '{clean}' -> Fixed: '{fixed}'")
                        print(f"Matched plate: {val_fix['matchedPlate']}")
                        return
                except Exception:
                    pass

fast_search("/app/src/crops_img0", "img0.png (MH12KR1145 expected)")
fast_search("/app/src/crops_img1", "img1.png (TN05BT5754 expected)")
