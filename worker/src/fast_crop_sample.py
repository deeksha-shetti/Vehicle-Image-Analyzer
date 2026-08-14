import os
import glob
import cv2
import pytesseract
import re
import sys

sys.path.insert(0, "/app/src")
from heuristics import validate_indian_number_plate, fix_ocr_plate_confusion

def test_samples(crop_dir, target_name):
    files = sorted(glob.glob(f"{crop_dir}/*.png"))
    print(f"\n==========================================")
    print(f"Sampling {len(files)} crops in {target_name}")
    print(f"==========================================")
    
    count = 0
    for f in files:
        # Check filename coordinates e.g. crop_001_x300_y700_w250_h100.png
        fname = os.path.basename(f)
        img = cv2.imread(f)
        if img is None:
            continue
            
        count += 1
        up = cv2.resize(img, (600, 180), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
        
        for psm in ["--psm 6", "--psm 11", "--psm 7"]:
            try:
                txt = pytesseract.image_to_string(clahe, config=psm).strip()
                clean = re.sub(r'[^A-Z0-9]', '', txt.upper())
                if len(clean) >= 5:
                    fixed = fix_ocr_plate_confusion(clean)
                    val = validate_indian_number_plate(clean)
                    val_fix = validate_indian_number_plate(fixed)
                    
                    if val["hasValidIndianNumberPlate"] or val_fix["hasValidIndianNumberPlate"]:
                        plate = val["matchedPlate"] if val["hasValidIndianNumberPlate"] else val_fix["matchedPlate"]
                        print(f"\n🎉 FOUND PLATE IN {fname}!")
                        print(f"    Raw: '{txt}' -> Clean: '{clean}' -> Fixed: '{fixed}'")
                        print(f"    Matched Plate: {plate}")
                        return
                    elif any(k in clean for k in ["MH", "TN", "1145", "5754", "12KR", "05BT"]):
                        print(f"  Partial match in {fname} [{psm}]: '{txt}' (clean: '{clean}')")
            except Exception:
                pass

test_samples("/app/src/crops_img0", "img0.png (MH12KR1145 expected)")
test_samples("/app/src/crops_img1", "img1.png (TN05BT5754 expected)")
