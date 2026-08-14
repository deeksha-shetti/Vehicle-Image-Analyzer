import os
import sys
import cv2
import numpy as np
import pytesseract

img0 = cv2.imread("/app/src/img0.png")
img1 = cv2.imread("/app/src/img1.png")

print(f"img0 shape: {img0.shape if img0 is not None else 'None'}")
print(f"img1 shape: {img1.shape if img1 is not None else 'None'}")

# Let's inspect yellow contours on img0 (720x1280) and img1 (960x1280)
def debug_image(img, name):
    h, w = img.shape[:2]
    # Resize to scaled det_img where min dim >= 800
    min_dim = min(w, h)
    scale = 800.0 / float(min_dim) if min_dim < 800 else 1.0
    det_w, det_h = int(w * scale), int(h * scale)
    det_img = cv2.resize(img, (det_w, det_h), interpolation=cv2.INTER_CUBIC)
    
    # ROI: y = 45% to 100%
    roi_y1 = int(det_h * 0.45)
    vehicle_roi = det_img[roi_y1:det_h, 0:det_w]
    
    hsv = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2HSV)
    lower_a = np.array([10, 40, 50])
    upper_a = np.array([45, 255, 255])
    mask_a = cv2.inRange(hsv, lower_a, upper_a)
    
    lower_b = np.array([5, 20, 40])
    upper_b = np.array([50, 255, 255])
    mask_b = cv2.inRange(hsv, lower_b, upper_b)
    
    mask = cv2.bitwise_or(mask_a, mask_b)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"\n--- {name} ---")
    print(f"det_w: {det_w}, det_h: {det_h}, roi_y1: {roi_y1}, total contours: {len(contours)}")
    
    for i, c in enumerate(contours):
        cx, cy, cw, ch = cv2.boundingRect(c)
        if cw < 15 or ch < 5:
            continue
        aspect = cw / float(ch)
        if 1.2 <= aspect <= 8.0:
            orig_x = int(cx / scale)
            orig_y = int((roi_y1 + cy) / scale)
            orig_w = int(cw / scale)
            orig_h = int(ch / scale)
            crop = img[orig_y:orig_y+orig_h, orig_x:orig_x+orig_w]
            
            # OCR crop test
            if crop.size > 0:
                crop_gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                crop_up = cv2.resize(crop_gray, (800, 200), interpolation=cv2.INTER_CUBIC)
                txt = pytesseract.image_to_string(crop_up, config="--psm 7").strip()
                print(f"  Contour {i}: bbox=({orig_x}, {orig_y}, {orig_w}, {orig_h}), aspect={aspect:.2f}, OCR='{txt}'")

debug_image(img0, "img0.png (MH12KR1145 expected)")
debug_image(img1, "img1.png (TN05BT5754 expected)")
