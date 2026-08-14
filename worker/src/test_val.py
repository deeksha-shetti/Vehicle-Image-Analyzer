import sys
sys.path.insert(0, "/app/src")
from heuristics import validate_indian_number_plate, fix_ocr_plate_confusion

tests = ["ANIMATION", "CREATIVITY", "PUNE", "MH12NW8556", "TN05BT5754", "MH12KR1145"]
for t in tests:
    res = validate_indian_number_plate(t)
    print(f"{t}: {res}")
