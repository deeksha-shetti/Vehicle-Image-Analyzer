import cv2
import pytesseract
import re

img = cv2.imread("/app/src/img0.png")
# The actual plate is in this region
crop = img[750:950, 450:720]

# Resize to scale up
h, w = crop.shape[:2]
resized = cv2.resize(crop, (w*3, h*3), interpolation=cv2.INTER_CUBIC)

gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
_, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 51, 15)

print("--- OCR on Correct Crop ---")
for name, variant in [("gray", gray), ("otsu", otsu), ("adaptive", adaptive)]:
    for psm in ["--psm 3", "--psm 6", "--psm 7", "--psm 11", "--psm 12"]:
        try:
            raw = pytesseract.image_to_string(variant, config=psm).strip()
            clean = re.sub(r'[^A-Z0-9]', '', raw.upper())
            print(f"{name} / {psm}: Raw='{raw.replace(chr(10), ' ')}' Clean='{clean}'")
        except Exception as e:
            print(f"{name} / {psm}: Error: {e}")
