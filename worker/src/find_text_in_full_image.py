import cv2
import pytesseract

def locate_chars(img_path, img_name):
    img = cv2.imread(img_path)
    if img is None:
        print(f"Cannot read {img_path}")
        return
    h, w = img.shape[:2]
    print(f"\n==========================================")
    print(f"Locating characters in {img_name} ({w}x{h})")
    print(f"==========================================")
    
    # Preprocess full image & ROI
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Try running image_to_data on full image & lower ROI
    for region_name, roi_img, offset_y in [("full", gray, 0), ("lower_half", gray[int(h*0.4):h, :], int(h*0.4))]:
        try:
            data = pytesseract.image_to_data(roi_img, output_type=pytesseract.Output.DICT)
            n_boxes = len(data['text'])
            for i in range(n_boxes):
                text = data['text'][i].strip()
                if not text:
                    continue
                clean = "".join(c for c in text if c.isalnum())
                if any(k in clean.upper() for k in ["MH", "12", "KR", "1145", "TN", "05", "BT", "5754"]):
                    x, y, w_box, h_box = data['left'][i], data['top'][i] + offset_y, data['width'][i], data['height'][i]
                    print(f"  [{region_name}] Found '{text}' (clean: '{clean}') at bbox=({x}, {y}, {w_box}, {h_box})")
        except Exception as e:
            print(f"  Error: {e}")

locate_chars("/app/src/img0.png", "img0.png (MH12KR1145 expected)")
locate_chars("/app/src/img1.png", "img1.png (TN05BT5754 expected)")
