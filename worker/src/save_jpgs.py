"""Inspect img1 and img2 crops visually to understand plate positions."""
import cv2

for path, out_name in [("/app/src/img0.png", "/tmp/img0.jpg"), ("/app/src/img1.png", "/tmp/img1.jpg"), ("/app/src/img2.png", "/tmp/img2.jpg")]:
    img = cv2.imread(path)
    if img is not None:
        cv2.imwrite(out_name, img)
        print(f"Saved {out_name} shape={img.shape}")
