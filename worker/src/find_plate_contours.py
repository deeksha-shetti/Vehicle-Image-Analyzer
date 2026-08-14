import cv2
import numpy as np
import pytesseract
import os

def find_all_yellow_and_edge_contours(img_path, name):
    img = cv2.imread(img_path)
    if img is None:
        return
    h, w = img.shape[:2]
    
    print(f"\n==========================================")
    print(f"ANALYZING ALL CONTOURS IN {name} ({w}x{h})")
    print(f"==========================================")
    
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    
    # Yellow masks
    lower_a = np.array([10, 30, 40])
    upper_a = np.array([45, 255, 255])
    mask_a = cv2.inRange(hsv, lower_a, upper_a)
    
    lower_b = np.array([5, 20, 30])
    upper_b = np.array([50, 255, 255])
    mask_b = cv2.inRange(hsv, lower_b, upper_b)
    
    yellow_mask = cv2.bitwise_or(mask_a, mask_b)
    
    contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"Total yellow contours in full image: {len(contours)}")
    
    candidates = []
    for idx, c in enumerate(contours):
        x, y, cw, ch = cv2.boundingRect(c)
        area = cw * ch
        if cw < 20 or ch < 5:
            continue
        aspect = cw / float(ch)
        if aspect < 1.2 or aspect > 9.0:
            continue
        
        # Crop region
        pad_w = max(4, int(cw * 0.15))
        pad_h = max(4, int(ch * 0.20))
        px1 = max(0, x - pad_w)
        py1 = max(0, y - pad_h)
        px2 = min(w, x + cw + pad_w)
        py2 = min(h, y + ch + pad_h)
        crop = img[py1:py2, px1:px2]
        
        if crop.size == 0:
            continue
        
        # Test OCR on crop
        up = cv2.resize(crop, (800, 200), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        for psm in ["--psm 7", "--psm 8", "--psm 6"]:
            for proc_name, proc_img in [("gray", gray), ("clahe", clahe), ("otsu", otsu)]:
                try:
                    txt = pytesseract.image_to_string(proc_img, config=f"{psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789").strip()
                    clean = "".join(c for c in txt if c.isalnum())
                    if len(clean) >= 4:
                        candidates.append({
                            "bbox": (x, y, cw, ch),
                            "aspect": aspect,
                            "y_rel": (y + ch/2.0)/float(h),
                            "proc": proc_name,
                            "psm": psm,
                            "raw": txt,
                            "clean": clean
                        })
                except Exception:
                    pass

    print(f"Candidates with OCR text >= 4 chars: {len(candidates)}")
    for item in candidates:
        print(f"  bbox=({item['bbox'][0]},{item['bbox'][1]},{item['bbox'][2]},{item['bbox'][3]}), y_rel={item['y_rel']:.2f}, aspect={item['aspect']:.2f} | [{item['proc']}|{item['psm']}] clean='{item['clean']}'")

find_all_yellow_and_edge_contours("/app/src/img0.png", "img0.png (MH12KR1145 expected)")
find_all_yellow_and_edge_contours("/app/src/img1.png", "img1.png (TN05BT5754 expected)")
