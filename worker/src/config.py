import os

# Configurable heuristic thresholds for vehicle image analysis

# Blur detection (OpenCV Laplacian Variance)
# Heuristic: Images with Laplacian variance below 100.0 are considered blurry
BLUR_THRESHOLD = float(os.getenv("BLUR_THRESHOLD", "100.0"))

# Brightness analysis (Average Grayscale Intensity 0-255)
# Heuristic: Images with average grayscale intensity below 50.0 are considered low brightness / dark
DARKNESS_THRESHOLD = float(os.getenv("DARKNESS_THRESHOLD", "50.0"))

# Image resolution thresholds
# Heuristic: Images below 600x400 are flagged as low resolution
MIN_IMAGE_WIDTH = int(os.getenv("MIN_IMAGE_WIDTH", "600"))
MIN_IMAGE_HEIGHT = int(os.getenv("MIN_IMAGE_HEIGHT", "400"))

# Perceptual hash (pHash) Hamming distance threshold
# Heuristic: pHash Hamming distance < 10 between two images indicates potential duplicate
PHASH_DISTANCE_THRESHOLD = int(os.getenv("PHASH_DISTANCE_THRESHOLD", "10"))
