import os
import sys
import cv2

# Set path
sys.path.insert(0, "/app/src")
from heuristics import extract_enhanced_ocr_and_plate

test_files = [
    ("/app/src/img0.png", "img0.png"),
    ("/app/src/img1.png", "img1.png"),
    ("/app/src/img2.png", "img2.png"),
    ("/app/src/img_diff.png", "img_diff.png")
]

for file_path, name in test_files:
    if os.path.exists(file_path):
        img = cv2.imread(file_path)
        if img is not None:
            print(f"\n==========================================", flush=True)
            print(f"TESTING: {name} ({img.shape[1]}x{img.shape[0]})", flush=True)
            print(f"==========================================", flush=True)
            res = extract_enhanced_ocr_and_plate(img)
            print(f"RESULT for {name}: {res}", flush=True)
        else:
            print(f"Failed to read {name}", flush=True)
    else:
        print(f"Not found: {file_path}", flush=True)
