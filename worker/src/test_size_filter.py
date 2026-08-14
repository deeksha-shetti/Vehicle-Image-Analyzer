import cv2
import numpy as np

def test_filter(img_path, name):
    img = cv2.imread(img_path)
    h, w = img.shape[:2]
    min_dim = min(w, h)
    scale = 800.0 / float(min_dim) if min_dim < 800 else 1.0
    det_w, det_h = int(w * scale), int(h * scale)
    det_img = cv2.resize(img, (det_w, det_h), interpolation=cv2.INTER_CUBIC)
    
    roi_y1 = int(det_h * 0.45)
    vehicle_roi = det_img[roi_y1:det_h, 0:det_w]
    
    hsv = cv2.cvtColor(vehicle_roi, cv2.COLOR_BGR2HSV)
    mask_a = cv2.inRange(hsv, np.array([10, 30, 40]), np.array([45, 255, 255]))
    mask_b = cv2.inRange(hsv, np.array([5, 20, 30]), np.array([50, 255, 255]))
    mask = cv2.bitwise_or(mask_a, mask_b)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    print(f"\n==========================================")
    print(f"Testing size filter on {name} ({det_w}x{det_h})")
    print(f"Total contours: {len(contours)}")
    
    filtered = []
    for c in contours:
        cx, cy, cw, ch = cv2.boundingRect(c)
        if cw < 40 or ch < 12: # Min width 40px, min height 12px
            continue
        aspect = cw / float(ch)
        if aspect < 1.2 or aspect > 7.0:
            continue
        
        orig_x = int(cx / scale)
        orig_y = int((roi_y1 + cy) / scale)
        orig_w = int(cw / scale)
        orig_h = int(ch / scale)
        
        rel_y = (roi_y1 + cy + ch/2.0) / float(det_h)
        rel_x = (cx + cw/2.0) / float(det_w)
        
        filtered.append((orig_x, orig_y, orig_w, orig_h, aspect, rel_x, rel_y))
        
    print(f"Filtered candidates (cw>=40, ch>=12): {len(filtered)}")
    for f in filtered:
        print(f"  orig_bbox=({f[0]}, {f[1]}, {f[2]}, {f[3]}), aspect={f[4]:.2f}, rel_x={f[5]:.2f}, rel_y={f[6]:.2f}")

test_filter("/app/src/img0.png", "img0.png (MH12KR1145 expected)")
test_filter("/app/src/img1.png", "img1.png (TN05BT5754 expected)")
