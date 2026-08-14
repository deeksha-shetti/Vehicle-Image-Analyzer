import cv2
import numpy as np
import pytesseract
import re

def search_tight_boxes(img_path, target_name, expected_prefix):
    img = cv2.imread(img_path)
    if img is None:
        return
    h, w = img.shape[:2]
    print(f"\n==========================================")
    print(f"Tight Box Search in {target_name} ({w}x{h}) - Expected prefix: {expected_prefix}")
    print(f"==========================================")
    
    # We test tight bounding boxes in lower half:
    # win_w: 60 to 220, win_h: 20 to 90
    y_start = int(h * 0.50)
    
    found = []
    
    for win_h in [25, 35, 45, 60, 75]:
        for win_w in [70, 100, 130, 160, 200]:
            aspect = win_w / float(win_h)
            if aspect < 1.4 or aspect > 5.5:
                continue
            for y in range(y_start, h - win_h, int(win_h * 0.4)):
                for x in range(0, w - win_w, int(win_w * 0.4)):
                    crop = img[y:y+win_h, x:x+win_w]
                    if crop.size == 0:
                        continue
                        
                    up = cv2.resize(crop, (400, 120), interpolation=cv2.INTER_CUBIC)
                    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
                    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    _, otsu_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
                    
                    for p_name, p_img in [("clahe", clahe), ("otsu", otsu), ("otsu_inv", otsu_inv)]:
                        for psm in ["--psm 7", "--psm 6", "--psm 8", "--psm 11"]:
                            try:
                                txt = pytesseract.image_to_string(p_img, config=f"{psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n").strip()
                                clean = re.sub(r'[^A-Z0-9]', '', txt.upper())
                                if len(clean) >= 4 and len(clean) <= 15:
                                    if any(p in clean for p in expected_prefix):
                                        found.append({
                                            "bbox": (x, y, win_w, win_h),
                                            "proc": p_name,
                                            "psm": psm,
                                            "raw": txt.replace('\n', ' '),
                                            "clean": clean
                                        })
                            except Exception:
                                pass

    print(f"Found {len(found)} tight plate box matches:")
    for item in found[:30]:
        print(f"  bbox={item['bbox']} [{item['proc']}|{item['psm']}] -> raw='{item['raw']}' clean='{item['clean']}'")

search_tight_boxes("/app/src/img0.png", "img0.png", ["MH12", "KR11", "1145", "MH"])
search_tight_boxes("/app/src/img1.png", "img1.png", ["TN05", "BT57", "5754", "TN05BT"])
