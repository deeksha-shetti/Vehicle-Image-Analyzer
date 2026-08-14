import cv2
import numpy as np

crop = cv2.imread("/app/src/debug_crop_plate.jpg")
hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
lower = np.array([10, 40, 60])
upper = np.array([45, 255, 255])
mask = cv2.inRange(hsv, lower, upper)
cv2.imwrite("/tmp/mask_test.jpg", mask)
