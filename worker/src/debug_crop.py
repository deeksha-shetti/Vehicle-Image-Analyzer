import cv2

img = cv2.imread("/app/src/img0.png")
crop = img[750:950, 450:720]
cv2.imwrite("/tmp/actual_plate_region.jpg", crop)
