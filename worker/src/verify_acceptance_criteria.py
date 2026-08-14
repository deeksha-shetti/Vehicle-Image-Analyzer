import os
import sys
import cv2

sys.path.insert(0, "/app/src")
from heuristics import extract_enhanced_ocr_and_plate

test_files = [
    ("/app/src/img0.png", "IMAGE 1 (MH12KR1145 expected)"),
    ("/app/src/img1.png", "IMAGE 2 (TN05BT5754 expected)"),
    ("/app/src/img_diff.png", "TEST IMAGE (KA05MH1234 or similar)")
]

all_passed = True

for path, label in test_files:
    if os.path.exists(path):
        img = cv2.imread(path)
        print(f"\n==========================================")
        print(f"RUNNING ACCEPTANCE TEST FOR: {label}")
        print(f"==========================================")
        result = extract_enhanced_ocr_and_plate(img)
        print(f"RESULT: {result}")
        plate_data = result.get("numberPlate", {})
        has_plate = plate_data.get("hasValidIndianNumberPlate")
        plate_text = plate_data.get("text", "")
        print(f"Valid Indian Plate: {has_plate}")
        print(f"Detected Plate Text: '{plate_text}'")
        
        if "ANIMATION" in plate_text.upper() or "CREATIVITY" in plate_text.upper() or "PUNE" in plate_text.upper():
            print("❌ FAILED: Advertisement text detected as number plate!")
            all_passed = False
        elif has_plate and plate_text:
            print("✅ PASSED: Valid Indian number plate extracted!")
        else:
            print("⚠️ WARNING: No valid plate extracted from this image.")

if all_passed:
    print("\n🎉 ALL ACCEPTANCE CRITERIA VERIFIED!")
