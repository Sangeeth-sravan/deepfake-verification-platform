import os

import cv2
import numpy as np

from services.image_analysis import ImageForensicAnalyzer


class VideoForensicAnalyzer:
    """Lightweight video forensics based on evenly sampled frames.

    It deliberately reuses the image signal checks already used by the project,
    rather than requiring a large deep-learning model for the college demo.
    """

    @staticmethod
    def analyze(video_path: str, max_samples: int = 20) -> dict:
        capture = cv2.VideoCapture(video_path)
        if not capture.isOpened():
            raise ValueError("Unable to decode the uploaded video file.")

        try:
            frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = float(capture.get(cv2.CAP_PROP_FPS) or 0)
            width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            if frame_count <= 0 or width <= 0 or height <= 0:
                raise ValueError("The uploaded video has no readable frames.")

            sample_count = min(max_samples, frame_count)
            frame_indexes = np.linspace(0, frame_count - 1, sample_count, dtype=int)
            signals = []
            brightness_values = []

            for frame_index in frame_indexes:
                capture.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
                ok, frame = capture.read()
                if not ok or frame is None:
                    continue
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                ela = ImageForensicAnalyzer._perform_ela(rgb)
                frequency = ImageForensicAnalyzer._perform_fft_analysis(gray)
                noise = ImageForensicAnalyzer._perform_noise_analysis(gray)
                stats = ImageForensicAnalyzer._calculate_statistics(gray)
                signals.append({
                    "ela_score": ela["ela_score"],
                    "frequency_score": frequency["frequency_score"],
                    "noise_score": noise["noise_score"],
                    "sharpness_score": stats["sharpness"],
                })
                brightness_values.append(stats["brightness"])

            if not signals:
                raise ValueError("No usable frames could be extracted from the uploaded video.")

            def average(key: str) -> float:
                return float(np.mean([signal[key] for signal in signals]))

            return {
                "width": width,
                "height": height,
                "fps": round(fps, 2),
                "duration_seconds": round(frame_count / fps, 2) if fps > 0 else None,
                "total_frames": frame_count,
                "sampled_frames": len(signals),
                "ela_score": round(average("ela_score"), 4),
                "frequency_score": round(average("frequency_score"), 4),
                "noise_score": round(average("noise_score"), 4),
                "sharpness_score": round(average("sharpness_score"), 2),
                "temporal_brightness_variation": round(float(np.std(brightness_values)), 2),
            }
        finally:
            capture.release()
