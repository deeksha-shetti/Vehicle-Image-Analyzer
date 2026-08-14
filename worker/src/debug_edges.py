import cv2
import numpy as np
import pytesseract
import os

img = cv2.imread("/app/src/img0.png")
search_top = int(img.shape[0] * 0.45)
search_region = img[search_top:, :]
gray = cv2.cvtColor(search_region, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 50, 150)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 2))
closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"Total edge contours: {len(contours)}")

os.makedirs("/tmp/edge_crops", exist_ok=True)
idx = 0
for c in contours:
    x, y, w, h = cv2.boundingRect(c)
    if w >= 40 and h >= 15 and w > h:
        aspect = w / float(h)
        if 1.2 <= aspect <= 6.0:
            idx += 1
            print(f"\nCandidate Edge Contour {idx}: x={x}, y={search_top+y}, w={w}, h={h}, aspect={aspect}")
            crop = img[search_top+y:search_top+y+h, x:x+w]
            cv2.imwrite(f"/tmp/edge_crops/cand_{idx}.jpg", crop)
            # Try OCR
            gray_crop = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
            res = pytesseract.image_to_string(gray_crop, config="--psm 7 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
            print(f"OCR: {res.strip()}")
