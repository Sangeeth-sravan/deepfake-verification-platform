import os
import io
import cv2
import numpy as np
from PIL import Image

class ImageForensicAnalyzer:
    """
    Modular forensic image analyzer implementing Error Level Analysis (ELA),
    2D Discrete Fourier Transform (DFT) frequency domain analysis, noise variance,
    and image quality/sharpness metrics.
    """

    @staticmethod
    def analyze(image_path: str) -> dict:
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found at path: {image_path}")

        file_size_bytes = os.path.getsize(image_path)
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

        # 1. Basic Image Validation & Metadata Loading
        try:
            with Image.open(image_path) as pil_img:
                pil_img.verify()
            with Image.open(image_path) as pil_img:
                width, height = pil_img.size
                image_format = pil_img.format or "UNKNOWN"
                mode = pil_img.mode
        except Exception as e:
            raise ValueError(f"Invalid or corrupted image file: {str(e)}")

        # Read image with OpenCV for matrix calculations
        img_bgr = cv2.imread(image_path)
        if img_bgr is None:
            raise ValueError("Unable to decode image file via OpenCV.")

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

        # 2. Error Level Analysis (ELA)
        ela_results = ImageForensicAnalyzer._perform_ela(img_rgb)

        # 3. Frequency Domain Analysis (2D FFT / DFT)
        freq_results = ImageForensicAnalyzer._perform_fft_analysis(gray)

        # 4. Noise Anomaly Analysis
        noise_results = ImageForensicAnalyzer._perform_noise_analysis(gray)

        # 5. Image Statistics (Sharpness, Brightness, Contrast)
        stats = ImageForensicAnalyzer._calculate_statistics(gray)

        return {
            "width": width,
            "height": height,
            "file_size_bytes": file_size_bytes,
            "file_size_mb": file_size_mb,
            "image_format": image_format,
            "color_mode": mode,
            "ela_score": round(ela_results["ela_score"], 4),
            "ela_mean_error": round(ela_results["mean_error"], 2),
            "ela_max_error": round(ela_results["max_error"], 2),
            "frequency_score": round(freq_results["frequency_score"], 4),
            "high_freq_ratio": round(freq_results["high_freq_ratio"], 4),
            "noise_score": round(noise_results["noise_score"], 4),
            "noise_variance": round(noise_results["noise_variance"], 2),
            "sharpness_score": round(stats["sharpness"], 2),
            "brightness": round(stats["brightness"], 2),
            "contrast": round(stats["contrast"], 2),
        }

    @staticmethod
    def _perform_ela(img_rgb: np.ndarray, quality: int = 90) -> dict:
        """
        Re-saves image at controlled JPEG quality and measures absolute compression delta.
        """
        pil_img = Image.fromarray(img_rgb)
        buffer = io.BytesIO()
        pil_img.save(buffer, format="JPEG", quality=quality)
        buffer.seek(0)

        recompressed_pil = Image.open(buffer)
        recompressed_np = np.array(recompressed_pil)

        # Compute absolute difference matrix
        diff = cv2.absdiff(img_rgb, recompressed_np)
        mean_error = float(np.mean(diff))
        max_error = float(np.max(diff))
        var_error = float(np.var(diff))

        # ELA Score normalized to 0.0 - 1.0 (mean_error typically ranges from 1 to 25)
        ela_score = min(1.0, mean_error / 20.0)

        return {
            "ela_score": ela_score,
            "mean_error": mean_error,
            "max_error": max_error,
            "var_error": var_error,
        }

    @staticmethod
    def _perform_fft_analysis(gray: np.ndarray) -> dict:
        """
        Computes 2D Discrete Fourier Transform magnitude spectrum to detect high-frequency artifacts.
        """
        f = np.fft.fft2(gray)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = np.abs(fshift)

        h, w = gray.shape
        cy, cx = h // 2, w // 2

        # Create high-pass mask (mask out low central frequencies)
        r = min(h, w) // 8
        y, x = np.ogrid[:h, :w]
        mask = (x - cx) ** 2 + (y - cy) ** 2 > r ** 2

        total_energy = np.sum(magnitude_spectrum) + 1e-8
        high_freq_energy = np.sum(magnitude_spectrum[mask])
        high_freq_ratio = float(high_freq_energy / total_energy)

        # Normalize frequency anomaly score (Organic photos typically have high_freq_ratio 0.40 - 0.70)
        # Extreme high frequency or unnatural smoothness alters this ratio
        deviation = abs(high_freq_ratio - 0.55)
        frequency_score = min(1.0, deviation * 2.5)

        return {
            "frequency_score": frequency_score,
            "high_freq_ratio": high_freq_ratio,
        }

    @staticmethod
    def _perform_noise_analysis(gray: np.ndarray) -> dict:
        """
        Estimates image noise using median filter residual.
        """
        blur = cv2.medianBlur(gray, 3)
        noise = cv2.absdiff(gray, blur)
        noise_variance = float(np.var(noise))

        # Normalized noise score (0.0 - 1.0)
        # Extremely low noise variance (< 1.0) or high uneven noise (> 50) indicates synthetic smoothing or noise injection
        if noise_variance < 2.0:
            noise_score = 0.8  # Unnaturally smooth / synthetic
        elif noise_variance > 45.0:
            noise_score = 0.7  # Heavy artificial grain
        else:
            noise_score = max(0.0, min(1.0, abs(noise_variance - 15.0) / 30.0))

        return {
            "noise_score": noise_score,
            "noise_variance": noise_variance,
        }

    @staticmethod
    def _calculate_statistics(gray: np.ndarray) -> dict:
        brightness = float(np.mean(gray))
        contrast = float(np.std(gray))
        sharpness = float(cv2.Laplacian(gray, cv2.CV_64F).var())

        return {
            "brightness": brightness,
            "contrast": contrast,
            "sharpness": sharpness,
        }
