import cv2

img = cv2.imread("/app/src/img0.png")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
edges = cv2.Canny(gray, 50, 150)
kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 2))
closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

# USE RETR_LIST to find internal contours
contours, _ = cv2.findContours(closed, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

for c in contours:
    x, y, w, h = cv2.boundingRect(c)
    # The actual plate is around x=500, y=850, w=150, h=80
    if 450 < x < 600 and 800 < y < 900:
        if w > 100 and h > 40:
            print(f"FOUND: x={x}, y={y}, w={w}, h={h}")
