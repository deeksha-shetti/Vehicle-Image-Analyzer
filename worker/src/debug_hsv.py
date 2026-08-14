import cv2
import numpy as np

img = cv2.imread("/app/src/img0.png")
crop = img[1251:1280, 436:491]
hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
print("H:", np.min(hsv[:,:,0]), "-", np.max(hsv[:,:,0]))
print("S:", np.min(hsv[:,:,1]), "-", np.max(hsv[:,:,1]))
print("V:", np.min(hsv[:,:,2]), "-", np.max(hsv[:,:,2]))

cv2.imwrite("/tmp/bottom_right_plate.jpg", crop)
