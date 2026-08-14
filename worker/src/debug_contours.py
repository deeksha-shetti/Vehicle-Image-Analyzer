import cv2
import numpy as np

img = cv2.imread("/app/src/img0.png")
search_top = int(img.shape[0] * 0.45)
search_region = img[search_top:, :]
hsv = cv2.cvtColor(search_region, cv2.COLOR_BGR2HSV)

lower_yellow = np.array([10, 40, 60])
upper_yellow = np.array([45, 255, 255])
yellow_mask = cv2.inRange(hsv, lower_yellow, upper_yellow)

kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 3))
yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_CLOSE, kernel)
yellow_mask = cv2.morphologyEx(yellow_mask, cv2.MORPH_OPEN, kernel)

contours, _ = cv2.findContours(yellow_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
print(f"Total contours: {len(contours)}")
for c in contours:
    x, y, w, h = cv2.boundingRect(c)
    print(f"Contour: x={x}, y={search_top+y}, w={w}, h={h}")
