"""Check image filenames and test plate pipeline on all files in /app/src."""
import os
import cv2
import sys
sys.path.insert(0, "/app/src")
from heuristics import extract_enhanced_ocr_and_plate

files = [f for f in os.listdir("/app/src") if f.endswith(('.png', '.jpg', '.jpeg'))]
print("Found image files:", files)

for f in sorted(files):
    path = os.path.join("/app/src", f)
    img = cv2.imread(path)
    if img is None:
        continue
    h, w = img.shape[:2]
    print(f"\n================ {f} ({w}x{h}) ================")
    res = extract_enhanced_ocr_and_plate(img)
    plate = res.get("numberPlate", {})
    print(f"RESULT -> valid: {plate.get('hasValidIndianNumberPlate')} | text: '{plate.get('text')}' | conf: {plate.get('confidence')}")
