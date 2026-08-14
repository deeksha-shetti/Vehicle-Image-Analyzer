import os
import glob
import cv2
import pytesseract
import re

def search_crops(crop_dir, target_name, keywords):
    files = glob.glob(f"{crop_dir}/*.png")
    print(f"\n==========================================")
    print(f"Searching {len(files)} crops in {target_name} for keywords {keywords}")
    print(f"==========================================")
    
    matches = []
    for f in files:
        img = cv2.imread(f)
        if img is None:
            continue
        
        # Preprocess
        up = cv2.resize(img, (800, 200), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, otsu_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        for p_name, p_img in [("gray", gray), ("clahe", clahe), ("otsu", otsu), ("otsu_inv", otsu_inv)]:
            for psm in ["--psm 6", "--psm 7", "--psm 11", "--psm 3"]:
                try:
                    txt = pytesseract.image_to_string(p_img, config=psm).strip()
                    clean = re.sub(r'[^A-Z0-9]', '', txt.upper())
                    if any(k in clean for k in keywords):
                        fname = os.path.basename(f)
                        matches.append((fname, p_name, psm, txt, clean))
                except Exception:
                    pass

    print(f"Found {len(matches)} matches:")
    for m in matches[:30]:
        print(f"  File: {m[0]} | [{m[1]}|{m[2]}] -> raw='{m[3]}' clean='{m[4]}'")

search_crops("/app/src/crops_img0", "img0.png", ["MH12", "KR11", "1145", "MH", "KR"])
search_crops("/app/src/crops_img1", "img1.png", ["TN05", "BT57", "5754", "TN05BT", "TN05BT5754"])
