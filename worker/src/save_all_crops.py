import cv2
import numpy as np
import os

def dump_crops(img_path, output_dir, name):
    img = cv2.imread(img_path)
    if img is None:
        return
    h, w = img.shape[:2]
    os.makedirs(output_dir, exist_ok=True)
    
    # Let's crop grid regions in lower 50%
    y_start = int(h * 0.45)
    
    count = 0
    # Sliding windows
    for win_w in [int(w * 0.25), int(w * 0.35), int(w * 0.45)]:
        for win_h in [int(h * 0.08), int(h * 0.12), int(h * 0.18)]:
            for y in range(y_start, h - win_h, int(win_h * 0.5)):
                for x in range(0, w - win_w, int(win_w * 0.5)):
                    crop = img[y:y+win_h, x:x+win_w]
                    if crop.size > 0:
                        count += 1
                        cv2.imwrite(f"{output_dir}/crop_{count:03d}_x{x}_y{y}_w{win_w}_h{win_h}.png", crop)
                        
    print(f"Saved {count} crops for {name} in {output_dir}")

dump_crops("/app/src/img0.png", "/app/src/crops_img0", "img0.png")
dump_crops("/app/src/img1.png", "/app/src/crops_img1", "img1.png")
