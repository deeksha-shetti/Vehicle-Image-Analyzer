import cv2
import sys
import os

from heuristics import extract_enhanced_ocr_and_plate

def run_test():
    img1_path = "/app/test_img1.jpg"
    img2_path = "/app/test_img2.jpg"

    if os.path.exists(img1_path):
        print("=== TESTING IMAGE 1 (MH12KR1145) ===", flush=True)
        img1 = cv2.imread(img1_path)
        res1 = extract_enhanced_ocr_and_plate(img1)
        print("RESULT 1:", res1["numberPlate"], flush=True)

    if os.path.exists(img2_path):
        print("\n=== TESTING IMAGE 2 (TN05BT5754) ===", flush=True)
        img2 = cv2.imread(img2_path)
        res2 = extract_enhanced_ocr_and_plate(img2)
        print("RESULT 2:", res2["numberPlate"], flush=True)

if __name__ == "__main__":
    run_test()
