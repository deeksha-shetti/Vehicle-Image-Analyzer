import os
import sys
import cv2
import numpy as np
import pytesseract

def scan_image(img_path, expected):
    img = cv2.imread(img_path)
    if img is None:
        print(f"Cannot read {img_path}")
        return
    h, w = img.shape[:2]
    print(f"\n==========================================")
    print(f"Scanning {os.path.basename(img_path)} ({w}x{h}) - Looking for {expected}")
    print(f"==========================================")
    
    # We will slide a window over the bottom 50% of the image
    y_start = int(h * 0.40)
    
    found_matches = []
    
    for win_h in [30, 50, 70, 90, 120, 150]:
        for win_w in [80, 120, 160, 200, 250, 300]:
            aspect = win_w / float(win_h)
            if aspect < 1.5 or aspect > 6.0:
                continue
            for y in range(y_start, h - win_h, int(win_h * 0.4)):
                for x in range(0, w - win_w, int(win_w * 0.4)):
                    crop = img[y:y+win_h, x:x+win_w]
                    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                    up = cv2.resize(gray, (800, 200), interpolation=cv2.INTER_CUBIC)
                    
                    for thresh_type in ["plain", "otsu", "clahe"]:
                        if thresh_type == "otsu":
                            _, proc = cv2.threshold(up, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        elif thresh_type == "clahe":
                            clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(up)
                            _, proc = cv2.threshold(clahe, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                        else:
                            proc = up
                            
                        txt = pytesseract.image_to_string(proc, config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789").strip()
                        txt_clean = "".join(c for c in txt if c.isalnum())
                        
                        if any(sub in txt_clean for sub in ["MH12", "KR11", "1145", "TN05", "BT57", "5754"]):
                            found_matches.append((x, y, win_w, win_h, thresh_type, txt_clean))

    print(f"Found {len(found_matches)} sliding window matches:")
    for m in found_matches[:20]:
        print(f"  bbox=({m[0]}, {m[1]}, {m[2]}, {m[3]}), thresh={m[4]}, text='{m[5]}'")

scan_image("/app/src/img0.png", "MH12KR1145")
scan_image("/app/src/img1.png", "TN05BT5754")
