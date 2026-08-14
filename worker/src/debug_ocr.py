import cv2
import pytesseract

img = cv2.imread("/app/src/img0.png")
crop = img[1251:1280, 436:491]

# Resize
h, w = crop.shape[:2]
target_w = int(w * 4)
target_h = int(h * 4)
resized = cv2.resize(crop, (target_w, target_h), interpolation=cv2.INTER_CUBIC)

gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8)).apply(gray)
_, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
adaptive = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 9)

for name, variant in [("gray", gray), ("clahe", clahe), ("otsu", otsu), ("adaptive", adaptive)]:
    for psm in ["--psm 7", "--psm 8", "--psm 6", "--psm 11"]:
        try:
            res = pytesseract.image_to_string(variant, config=psm + " -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789").strip()
            print(f"{name} / {psm}: {res}")
        except:
            pass
