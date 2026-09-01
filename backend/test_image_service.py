import sys
import os

# Insert workspace root and backend root into sys.path FIRST
workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
backend_root = os.path.abspath(os.path.dirname(__file__))
# Keep the workspace root first: it contains models/deepfake, whereas backend/models
# contains the SQLAlchemy package with the same top-level name.
for path in (workspace_root, backend_root):
    if path in sys.path:
        sys.path.remove(path)
sys.path.insert(0, workspace_root)
sys.path.insert(1, backend_root)

import cv2
import numpy as np
from PIL import Image

from services.image_analysis import ImageForensicAnalyzer
from models.deepfake.baseline_detector import BaselineForensicDetector

def run_image_tests():
    print("=== STARTING IMAGE FORENSIC & DETECTOR UNIT TESTS ===")
    
    test_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "datasets", "test"))
    os.makedirs(test_dir, exist_ok=True)
    sample_path = os.path.join(test_dir, "sample_test_image.jpg")

    # Generate a sample synthetic image matrix for testing
    img = np.zeros((300, 300, 3), dtype=np.uint8)
    cv2.circle(img, (150, 150), 80, (255, 200, 150), -1)
    cv2.putText(img, "TEST", (110, 160), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    cv2.imwrite(sample_path, img)

    try:
        # 1. Run Image Forensic Analysis
        forensics = ImageForensicAnalyzer.analyze(sample_path)
        print("[PASS] ImageForensicAnalyzer executed successfully.")
        print(f"       File Size: {forensics['file_size_mb']} MB, Dimensions: {forensics['width']}x{forensics['height']}")
        print(f"       ELA Score: {forensics['ela_score']}, Frequency Score: {forensics['frequency_score']}, Noise Score: {forensics['noise_score']}")

        # 2. Run Baseline Detector Prediction
        detector = BaselineForensicDetector()
        pred = detector.predict(sample_path, forensics)
        print("[PASS] BaselineForensicDetector executed successfully.")
        print(f"       Classification: {pred['classification']}, Risk Score: {pred['risk_score']}/100, Level: {pred['risk_level']}")
        print(f"       Explanation: {pred['explanation']}")

        assert pred["classification"] in ["REAL", "SUSPICIOUS", "LIKELY_MANIPULATED"], "Invalid classification"
        assert 0 <= pred["risk_score"] <= 100, "Risk score out of range"

    finally:
        if os.path.exists(sample_path):
            os.remove(sample_path)
            print("[PASS] Cleaned up temporary test image.")

    print("=== ALL IMAGE ANALYSIS SERVICE TESTS PASSED SUCCESSFULLY ===")

if __name__ == "__main__":
    run_image_tests()


def test_image_service():
    run_image_tests()
