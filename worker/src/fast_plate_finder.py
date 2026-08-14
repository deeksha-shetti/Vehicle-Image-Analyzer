import cv2
import numpy as np
import pytesseract
import re

def test_crop_region(img_path, roi_coords, label, expected_sub):
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    x1, y1, x2, y2 = roi_coords
    crop = img[y1:y2, x1:x2]
    
    print(f"\n==========================================")
    print(f"Testing ROI for {label}: bbox=({x1},{y1},{x2-x1},{y2-y1}) in image ({w}x{h})")
    print(f"==========================================")
    
    # Save crop for inspection
    cv2.imwrite(f"/app/src/{label}_crop.jpg", crop)
    
    # Preprocess variants
    up = cv2.resize(crop, (800, 200), interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(up, cv2.COLOR_BGR2GRAY)
    
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8)).apply(gray)
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    _, otsu_inv = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9)
    
    for v_name, v_img in [("gray", gray), ("clahe", clahe), ("otsu", otsu), ("otsu_inv", otsu_inv), ("adaptive", adaptive)]:
        for psm in ["--psm 7", "--psm 8", "--psm 6", "--psm 11"]:
            try:
                txt = pytesseract.image_to_string(v_img, config=f"{psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
                clean = re.sub(r'[^A-Z0-9]', '', txt.upper())
                print(f"  [{v_name} | {psm}] Raw: '{txt.strip()}' -> Clean: '{clean}'")
            except Exception as e:
                print(f"  Error: {e}")

# img0: 720x1280 -> LOWER-RIGHT auto region (x: 400->700, y: 800->1250)
test_crop_region("/app/src/img0.png", (350, 750, 700, 1250), "img0_lower_right", "MH12")

# img1: 960x1280 -> LOWER-CENTER auto region (x: 200->750, y: 800->1250)
test_crop_region("/app/src/img1.png", (200, 800, 750, 1250), "img1_lower_center", "TN05")
