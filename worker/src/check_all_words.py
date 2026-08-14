"""Check what text exists anywhere in img1 and img2."""
import cv2
import pytesseract
import re

for idx, path in enumerate(["/app/src/img0.png", "/app/src/img1.png", "/app/src/img2.png"]):
    img = cv2.imread(path)
    print(f"\n--- ALL OCR ON {path} ---")
    data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    words = [w for w in data['text'] if w.strip()]
    print("Words found:", " | ".join(words))
