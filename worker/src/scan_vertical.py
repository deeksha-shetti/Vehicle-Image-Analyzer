"""Examine /app/src/img1.png and /app/src/img2.png OCR."""
import cv2
import pytesseract
import re

# Let's inspect where TN05BT5754 is in img1
img1 = cv2.imread("/app/src/img1.png")
h1, w1 = img1.shape[:2]
print("=== IMG 1 ===")
# Try multiple vertical bands in img1
for y_pct in range(40, 85, 5):
    for h_pct in [10, 15, 20]:
        y1, y2 = int(h1 * y_pct / 100), int(h1 * (y_pct + h_pct) / 100)
        crop = img1[y1:y2, int(w1*0.2):int(w1*0.8)]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        txt = pytesseract.image_to_string(gray, config="--psm 11 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789").strip()
        norm = re.sub(r'[^A-Z0-9]', '', txt.upper())
        if "TN" in norm or "BT" in norm or "5754" in norm or "05" in norm:
            print(f"y={y_pct}-{y_pct+h_pct}% -> {norm}")

print("\n=== IMG 2 ===")
img2 = cv2.imread("/app/src/img2.png")
h2, w2 = img2.shape[:2]
for y_pct in range(40, 85, 5):
    for h_pct in [10, 15, 20]:
        y1, y2 = int(h2 * y_pct / 100), int(h2 * (y_pct + h_pct) / 100)
        crop = img2[y1:y2, int(w2*0.4):int(w2*0.95)]
        gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
        txt = pytesseract.image_to_string(gray, config="--psm 11 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789").strip()
        norm = re.sub(r'[^A-Z0-9]', '', txt.upper())
        if "MH" in norm or "KR" in norm or "1145" in norm or "12" in norm:
            print(f"y={y_pct}-{y_pct+h_pct}% -> {norm}")
