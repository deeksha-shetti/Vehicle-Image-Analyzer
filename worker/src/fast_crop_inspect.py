import os
import sys
import cv2
import numpy as np
import pytesseract

def inspect_candidates(img_path, img_name):
    img = cv2.imread(img_path)
    if img is None:
        print(f"Error reading {img_path}")
        return
    
    h, w = img.shape[:2]
    print(f"\n=========================================")
    print(f"Inspecting {img_name} ({w}x{h})")
    print(f"=========================================")
    
    # Resize for detection (smaller dim >= 800)
    min_dim = min(w, h)
    scale = 800.0 / float(min_dim) if min_dim < 800 else 1.0
    det_w, det_h = int(w * scale), int(h * scale)
    det_img = cv2.resize(img, (det_w, det_h), interpolation=cv2.INTER_CUBIC)
    
    # ROI: y = 45% to 100%
    roi_y1 = int(det_h * 0.45)
    vehicle_roi = det_img[roi_y1:det_h, 0:det_w]
    
    # Mask A & B
    hsv_roi = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2HSV)
    lower_a, upper_a = np.array([10, 40, 50]), np.array([45, 255, 255])
    mask_a = cv2.inRange(hsv_roi, lower_a, upper_a)
    
    lower_b, upper_b = np.array([5, 20, 40]), np.array([50, 255, 255])
    mask_b = cv2.inRange(hsv_roi, lower_b, upper_b)
    
    yellow_mask = cv2.bitwise_or(mask_a, mask_b)
    
    # Morphology
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_OPEN, kernel)
    yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
    
    yellow_contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"Yellow contours found: {len(yellow_contours)}")
    
    # Edge candidates
    gray_roi = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2GRAY)
    clahe_roi = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray_roi)
    filtered = cv2.bilateralFilter(clahe_roi, 9, 75, 75)
    edges = cv2.Canny(filtered, 50, 150)
    kernel_close = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 2))
    closed_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel_close)
    edge_contours, _ = cv2.findContours(closed_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"Edge contours found: {len(edge_contours)}")
    
    all_candidates = []
    
    for c_type, contours in [("yellow", yellow_contours), ("edge", edge_contours)]:
        for c in contours:
            cx, cy, cw, ch = cv2.boundingRect(c)
            if cw < 20 or ch < 5:
                continue
            aspect = cw / float(ch)
            if aspect < 1.5 or aspect > 8.0:
                continue
            
            orig_x = int(cx / scale)
            orig_y = int((roi_y1 + cy) / scale)
            orig_cw = int(cw / scale)
            orig_ch = int(ch / scale)
            
            # Additional padding around bbox
            pad_w = max(4, int(orig_cw * 0.15))
            pad_h = max(4, int(orig_ch * 0.20))
            px1 = max(0, orig_x - pad_w)
            py1 = max(0, orig_y - pad_h)
            px2 = min(w, orig_x + orig_cw + pad_w)
            py2 = min(h, orig_y + orig_ch + pad_h)
            
            crop = img[py1:py2, px1:px2]
            if crop.size == 0:
                continue
            
            all_candidates.append({
                "type": c_type,
                "bbox": (orig_x, orig_y, orig_cw, orig_ch),
                "crop": crop,
                "aspect": aspect,
                "y_rel": (orig_y + orig_ch / 2.0) / float(h)
            })
            
    print(f"Filtered candidate regions: {len(all_candidates)}")
    
    # Sort candidates by y_rel descending (lower vehicle ROI candidates first)
    all_candidates.sort(key=lambda item: item["y_rel"], reverse=True)
    
    # Test OCR on top 25 candidates
    psm_configs = ["--psm 7", "--psm 8", "--psm 6", "--psm 11"]
    
    for idx, cand in enumerate(all_candidates[:30]):
        crop = cand["crop"]
        bbox = cand["bbox"]
        c_type = cand["type"]
        y_rel = cand["y_rel"]
        aspect = cand["aspect"]
        
        # Test OCR variants
        up = cv2.resize(crop, (800, 200), interpolation=cv2.INTER_CUBIC)
        gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
        _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        _, otsu_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        results = []
        for v_name, v_img in [("gray", gray), ("clahe", clahe), ("otsu", otsu), ("otsu_inv", otsu_inv)]:
            for psm in psm_configs:
                try:
                    txt = pytesseract.image_to_string(v_img, config=f"{psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789").strip()
                    txt_clean = "".join(ch for ch in txt if ch.isalnum())
                    if len(txt_clean) >= 4:
                        results.append(f"{v_name}/{psm}: '{txt_clean}'")
                except Exception:
                    pass
        if results:
            print(f"  Cand #{idx+1} ({c_type}): bbox={bbox}, y_rel={y_rel:.2f}, aspect={aspect:.2f}")
            for r in results[:5]:
                print(f"      {r}")

inspect_candidates("/app/src/img0.png", "img0.png (MH12KR1145 expected)")
inspect_candidates("/app/src/img1.png", "img1.png (TN05BT5754 expected)")
