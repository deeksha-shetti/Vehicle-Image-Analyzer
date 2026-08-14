import os
import sys
import cv2

# Add worker/src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from heuristics import extract_enhanced_ocr_and_plate

test_images = [
    "c:/Users/Deeksha/Gogig Assignment/image.png",
    "c:/Users/Deeksha/Gogig Assignment/image (1).png",
    "c:/Users/Deeksha/Gogig Assignment/image (2).png",
    "c:/Users/Deeksha/Gogig Assignment/different_test_image.png"
]

for img_path in test_images:
    if not os.path.exists(img_path):
        print(f"File not found: {img_path}")
        continue
    img = cv2.imread(img_path)
    if img is None:
        print(f"Failed to read: {img_path}")
        continue
    print(f"\n==========================================")
    print(f"Testing: {os.path.basename(img_path)} ({img.shape[1]}x{img.shape[0]})")
    print(f"==========================================")
    result = extract_enhanced_ocr_and_plate(img)
    print("RESULT:", result)
