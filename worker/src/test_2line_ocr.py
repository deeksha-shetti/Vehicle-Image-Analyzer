import cv2
import numpy as np
import pytesseract
import re

def test_2line_ocr(img_path, img_name):
    img = cv2.imread(img_path)
    if img is None:
        return
    h, w = img.shape[:2]
    
    print(f"\n==========================================")
    print(f"Testing 2-line OCR on {img_name} ({w}x{h})")
    print(f"==========================================")
    
    # Resize for detection (smaller dim >= 800)
    min_dim = min(w, h)
    scale = 800.0 / float(min_dim) if min_dim < 800 else 1.0
    det_w, det_h = int(w * scale), int(h * scale)
    det_img = cv2.resize(img, (det_w, det_h), interpolation=cv2.INTER_CUBIC)
    
    # ROI: y = 45% -> 100%
    roi_y1 = int(det_h * 0.45)
    vehicle_roi = det_img[roi_y1:det_h, 0:det_w]
    
    # Yellow mask
    hsv_roi = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2HSV)
    lower_a, upper_a = np.array([10, 40, 50]), np.array([45, 255, 255])
    mask_a = cv2.inRange(hsv_roi, lower_a, upper_a)
    lower_b, upper_b = np.array([5, 20, 40]), np.array([50, 255, 255])
    mask_b = cv2.inRange(hsv_roi, lower_b, upper_b)
    yellow_mask = cv2.bitwise_or(mask_a, mask_b)
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_OPEN, kernel)
    yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    for c in contours:
        cx, cy, cw, ch = cv2.boundingRect(c)
        if cw < 20 or ch < 15: # 2-line plates have larger height
            continue
        aspect = cw / float(ch)
        if aspect < 0.8 or aspect > 6.0:
            continue
            
        orig_x = int(cx / scale)
        orig_y = int((roi_y1 + cy) / scale)
        orig_cw = int(cw / scale)
        orig_ch = int(ch / scale)
        
        # Add padding around bounding box
        pad_x = max(6, int(orig_cw * 0.15))
        pad_y = max(6, int(orig_ch * 0.15))
        px1 = max(0, orig_x - pad_x)
        py1 = max(0, orig_y - pad_y)
        px2 = min(w, orig_x + orig_cw + pad_x)
        py2 = min(h, orig_y + orig_ch + pad_y)
        
        crop = img[py1:py2, px1:px2]
        if crop.size == 0:
            continue
            
        # Upscale crop to 400x300 for 2-line OCR
        up = cv2.resize(crop, (400, 300), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, otsu_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        psm_configs = ["--psm 6", "--psm 3", "--psm 11", "--psm 4", "--psm 7"]
        
        for p_name, p_img in [("gray", gray), ("clahe", clahe), ("otsu", otsu), ("otsu_inv", otsu_inv)]:
            for psm in psm_configs:
                try:
                    txt = pytesseract.image_to_string(p_img, config=f"{psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789\n").strip()
                    clean = re.sub(r'[^A-Z0-9]', '', txt.upper())
                    if len(clean) >= 6 and any(k in clean for k in ["MH", "12", "KR", "1145", "TN", "05", "BT", "5754"]):
                        print(f"  MATCH FOUND! bbox=({orig_x},{orig_y},{orig_cw},{orig_ch}), aspect={aspect:.2f} | [{p_name}|{psm}] -> raw='{txt}' -> clean='{clean}'")
                except Exception:
                    pass

test_2line_ocr("/app/src/img0.png", "img0.png (MH12KR1145 expected)")
test_2line_ocr("/app/src/img1.png", "img1.png (TN05BT5754 expected)")
