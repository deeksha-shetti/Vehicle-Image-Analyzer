import cv2
import numpy as np
import pytesseract

def test_manual_crops():
    img0 = cv2.imread("/app/src/img0.png")
    img1 = cv2.imread("/app/src/img1.png")
    
    print("\n--- Testing img0 (MH12KR1145 expected) ---")
    h0, w0 = img0.shape[:2]
    # Let's try various sub-regions in the lower right (x: 40% to 95%, y: 55% to 95%)
    for y_pct in [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
        for x_pct in [0.45, 0.50, 0.55, 0.60, 0.65]:
            for crop_w in [150, 220, 300]:
                for crop_h in [40, 60, 90]:
                    x = int(w0 * x_pct)
                    y = int(h0 * y_pct)
                    if x + crop_w > w0 or y + crop_h > h0:
                        continue
                    crop = img0[y:y+crop_h, x:x+crop_w]
                    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    up = cv2.resize(gray, (800, 200), interpolation=cv2.INTER_CUBIC)
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(up)
                    _, otsu = cv2.threshold(up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    for psm in ["--psm 7", "--psm 6"]:
                        for p_name, p_img in [("gray", up), ("clahe", clahe), ("otsu", otsu)]:
                            txt = pytesseract.image_to_string(p_img, config=f"{psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789").strip()
                            clean = "".join(c for c in txt if c.isalnum())
                            if "MH12" in clean or "KR11" in clean or "1145" in clean or "MH" in clean:
                                print(f"  FOUND IN img0! bbox=({x},{y},{crop_w},{crop_h}), [{p_name}|{psm}] -> raw='{txt}' clean='{clean}'")

    print("\n--- Testing img1 (TN05BT5754 expected) ---")
    h1, w1 = img1.shape[:2]
    for y_pct in [0.55, 0.60, 0.65, 0.70, 0.75, 0.80]:
        for x_pct in [0.20, 0.30, 0.40, 0.50]:
            for crop_w in [180, 260, 350]:
                for crop_h in [50, 80, 110]:
                    x = int(w1 * x_pct)
                    y = int(h1 * y_pct)
                    if x + crop_w > w1 or y + crop_h > h1:
                        continue
                    crop = img1[y:y+crop_h, x:x+crop_w]
                    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    up = cv2.resize(gray, (800, 200), interpolation=cv2.INTER_CUBIC)
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(up)
                    _, otsu = cv2.threshold(up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                    
                    for psm in ["--psm 7", "--psm 6"]:
                        for p_name, p_img in [("gray", up), ("clahe", clahe), ("otsu", otsu)]:
                            txt = pytesseract.image_to_string(p_img, config=f"{psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789").strip()
                            clean = "".join(c for c in txt if c.isalnum())
                            if "TN05" in clean or "BT57" in clean or "5754" in clean or "TN" in clean:
                                print(f"  FOUND IN img1! bbox=({x},{y},{crop_w},{crop_h}), [{p_name}|{psm}] -> raw='{txt}' clean='{clean}'")

test_manual_crops()
