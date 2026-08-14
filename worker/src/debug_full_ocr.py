import cv2
import pytesseract

for i in range(3):
    img = cv2.imread(f"/app/src/img{i}.png")
    if img is None:
        print(f"img{i} not found")
        continue
    print(f"\n================ IMAGE {i} ===============")
    text = pytesseract.image_to_string(img, config="--psm 3")
    print("PSM 3 text:")
    print(text)
