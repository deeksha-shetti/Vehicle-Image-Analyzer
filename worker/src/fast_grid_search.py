import cv2
import numpy as np
import pytesseract
import re

def search_windows(img_path, img_name):
    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to read {img_path}")
        return
    h, w = img.shape[:2]
    print(f"\n=========================================")
    print(f"Grid Search in {img_name} ({w}x{h})")
    print(f"=========================================")
    
    # We create a grid of windows over the lower half (y: 50% -> 95%, x: 10% -> 90%)
    # Window sizes relative to image: width 25%-45%, height 8%-18%
    windows = []
    for y_pct in [0.50, 0.60, 0.70, 0.78]:
        for x_pct in [0.10, 0.30, 0.50, 0.65]:
            for w_pct in [0.30, 0.40]:
                for h_pct in [0.10, 0.15]:
                    x = int(w * x_pct)
                    y = int(h * y_pct)
                    win_w = int(w * w_pct)
                    win_h = int(h * h_pct)
                    if x + win_w <= w and y + win_h <= h:
                        windows.append((x, y, win_w, win_h))
                        
    print(f"Total grid windows to test: {len(windows)}")
    
    psm_config = "--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    
    for idx, (x, y, win_w, win_h) in enumerate(windows):
        crop = img[y:y+win_h, x:x+win_w]
        up = cv2.resize(crop, (800, 200), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        for p_name, p_img in [("clahe", clahe), ("otsu", otsu)]:
            try:
                raw = pytesseract.image_to_string(p_img, config=psm_config).strip()
                clean = re.sub(r'[^A-Z0-9]', '', raw.upper())
                if len(clean) >= 4:
                    print(f"  Win #{idx+1} bbox=({x},{y},{win_w},{win_h}) [{p_name}] -> raw='{raw}' clean='{clean}'")
            except Exception:
                pass

search_windows("/app/src/img0.png", "img0.png (MH12KR1145 expected)")
search_windows("/app/src/img1.png", "img1.png (TN05BT5754 expected)")
