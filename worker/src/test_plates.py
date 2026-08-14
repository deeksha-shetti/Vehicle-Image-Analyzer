"""Test script: run plate detection on the 3 test images."""
import sys
import cv2
sys.path.insert(0, "/app/src")
from heuristics import extract_enhanced_ocr_and_plate

test_images = [
    ("/app/src/img0.png", "IMAGE 1 (expected: MH12NW8556)"),
    ("/app/src/img1.png", "IMAGE 2 (expected: TN05BT5754)"),
    ("/app/src/img2.png", "IMAGE 3 (expected: MH12KR1145)"),
]

for path, label in test_images:
    img = cv2.imread(path)
    if img is None:
        print(f"\n=== SKIPPING {label}: file not found at {path} ===")
        continue
    h, w = img.shape[:2]
    print(f"\n{'='*60}")
    print(f"TESTING: {label}")
    print(f"Image size: {w}x{h}")
    print(f"{'='*60}")
    result = extract_enhanced_ocr_and_plate(img)
    plate = result.get("numberPlate", {})
    print(f"\n--- RESULT ---")
    print(f"hasValidIndianNumberPlate: {plate.get('hasValidIndianNumberPlate')}")
    print(f"text: '{plate.get('text', '')}'")
    print(f"confidence: {plate.get('confidence', 0)}")
    print(f"--------------")
