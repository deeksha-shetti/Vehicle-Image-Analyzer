import os
import sys
import cv2

sys.path.insert(0, "/app/src")
from image_pipeline import run_image_analysis

img0 = cv2.imread("/app/src/img0.png")
img1 = cv2.imread("/app/src/img1.png")

print("\n==========================================")
print("TESTING FULL IMAGE PIPELINE FOR IMAGE 1 (img0.png)")
print("==========================================")
res0 = run_image_analysis(img0, [])
print("IMAGE 1 RESULT:")
print(res0.get("numberPlate"))

print("\n==========================================")
print("TESTING FULL IMAGE PIPELINE FOR IMAGE 2 (img1.png)")
print("==========================================")
res1 = run_image_analysis(img1, [])
print("IMAGE 2 RESULT:")
print(res1.get("numberPlate"))
