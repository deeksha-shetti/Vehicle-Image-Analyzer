"""Debug: Find the actual plate region in Image 3 and run OCR on targeted crops."""
import cv2
import pytesseract
import re

img = cv2.imread("/app/src/img2.png")
h, w = img.shape[:2]
print(f"Image 3: {w}x{h}")

# The expected plate is MH12KR1145 at lower-right
# Try multiple crops
crops = [
    # Lower-right quadrant: different y positions
    ("lower-right-58-80", int(h*0.58), int(h*0.80), int(w*0.50), w),
    ("lower-right-60-80", int(h*0.60), int(h*0.80), int(w*0.55), w),
    ("lower-right-65-82", int(h*0.65), int(h*0.82), int(w*0.50), w),
    ("lower-right-70-85", int(h*0.70), int(h*0.85), int(w*0.45), w),
    ("lower-right-75-90", int(h*0.75), int(h*0.90), int(w*0.45), w),
    # Full lower half
    ("lower-half", int(h*0.60), int(h*0.85), 0, w),
]

for name, y1, y2, x1, x2 in crops:
    crop = img[y1:y2, x1:x2]
    if crop.size == 0:
        continue
    # Scale down to 600x350 max
    ch, cw = crop.shape[:2]
    if cw > 600 or ch > 350:
        scale = min(600/cw, 350/ch)
        crop = cv2.resize(crop, (int(cw*scale), int(ch*scale)), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
    for psm in ["--psm 11", "--psm 3"]:
        raw = pytesseract.image_to_string(gray, config=f"{psm} -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789").strip()
        norm = re.sub(r'[^A-Z0-9]', '', raw.upper())
        if "MH12" in norm or "KR" in norm or "1145" in norm:
            print(f"  *** HIT: crop={name} psm={psm}: {norm}")
        elif len(norm) > 4:
            print(f"  crop={name} psm={psm}: {norm[:50]}")
