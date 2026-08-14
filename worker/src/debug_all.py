"""Debug: Inspect img0, img1, img2 and test plate extraction directly."""
import cv2
import pytesseract
import re
import numpy as np

for img_idx, path in enumerate(["/app/src/img0.png", "/app/src/img1.png", "/app/src/img2.png"]):
    img = cv2.imread(path)
    if img is None:
        print(f"File {path} not found")
        continue
    h, w = img.shape[:2]
    print(f"\n================ IMAGE {img_idx}: {path} ({w}x{h}) ================")
    
    # Let's test specific regions in the lower half
    # For img0: rear auto with plate MH12NW8556 (or MH12KR1145) at bottom right
    # For img1: rear auto with plate TN05BT5754 at bottom center
    # For img2: let's see what's in img2
    
    # Try different slice configs:
    # 1. Lower center (x: 20-80%, y: 55-90%)
    # 2. Lower right (x: 45-95%, y: 55-90%)
    # 3. Lower left (x: 5-55%, y: 55-90%)
    regions = [
        ("LC", int(h*0.55), int(h*0.90), int(w*0.20), int(w*0.80)),
        ("LR", int(h*0.55), int(h*0.90), int(w*0.45), int(w*0.95)),
        ("LL", int(h*0.55), int(h*0.90), int(w*0.05), int(w*0.55)),
        ("BC_tight", int(h*0.65), int(h*0.88), int(w*0.25), int(w*0.75)),
        ("BR_tight", int(h*0.65), int(h*0.88), int(w*0.50), int(w*0.95)),
    ]
    
    for rname, y1, y2, x1, x2 in regions:
        crop = img[y1:y2, x1:x2]
        ch, cw = crop.shape[:2]
        if cw > 600 or ch > 350:
            scale = min(600/cw, 350/ch)
            crop_res = cv2.resize(crop, (int(cw*scale), int(ch*scale)), interpolation=cv2.INTER_AREA)
        else:
            crop_res = crop
            
        gray = cv2.cvtColor(crop_res, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        for vname, vimg in [("gray", gray), ("clahe", clahe), ("otsu", otsu)]:
            for psm in [11, 6, 3]:
                cfg = f"--psm {psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
                txt = pytesseract.image_to_string(vimg, config=cfg).strip()
                clean = re.sub(r'[^A-Z0-9]', '', txt.upper())
                if len(clean) >= 6:
                    for keyword in ["TN", "MH", "TS", "KA", "DL", "05", "12", "5754", "8556", "1145"]:
                        if keyword in clean:
                            print(f"[{rname} | {vname} | psm {psm}] -> {clean} (matched {keyword})")
                            break
