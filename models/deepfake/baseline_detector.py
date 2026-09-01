from models.deepfake.model_interface import BaseDeepfakeDetector

class BaselineForensicDetector(BaseDeepfakeDetector):
    """
    Baseline Forensic Detector
    Modular baseline image analysis engine using Error Level Analysis (ELA),
    Fourier frequency domain anomalies, noise variance, and image sharpness heuristics.
    Note: Prototype baseline rule engine. Performance depends on image quality and manipulation type.
    """

    def __init__(self):
        self.model_name = "Baseline Forensic Detector v1.0"

    def predict(self, image_path: str, forensic_data: dict) -> dict:
        ela_score = forensic_data.get("ela_score", 0.0)
        freq_score = forensic_data.get("frequency_score", 0.0)
        noise_score = forensic_data.get("noise_score", 0.0)
        sharpness = forensic_data.get("sharpness_score", 100.0)

        suspicious_indicators = []

        # 1. Evaluate Error Level Analysis (ELA)
        if ela_score > 0.65:
            suspicious_indicators.append(
                f"Elevated Error Level Analysis (ELA) compression anomaly detected (Score: {ela_score:.2f})."
            )
        elif ela_score > 0.40:
            suspicious_indicators.append(
                f"Moderate ELA compression variation observed (Score: {ela_score:.2f})."
            )

        # 2. Evaluate Frequency Spectrum (DFT)
        if freq_score > 0.60:
            suspicious_indicators.append(
                f"Fourier frequency spectrum anomaly detected (Score: {freq_score:.2f})."
            )

        # 3. Evaluate Noise Distribution
        if noise_score > 0.60:
            suspicious_indicators.append(
                f"Inconsistent noise variance signature detected (Score: {noise_score:.2f})."
            )

        # 4. Evaluate Blur / Over-smoothing
        if sharpness < 15.0:
            suspicious_indicators.append(
                f"Unnatural facial/image blur or smoothing detected (Sharpness: {sharpness:.1f})."
            )

        # Weighted composite deepfake probability calculation
        raw_deepfake_score = (
            (ela_score * 0.40) +
            (freq_score * 0.30) +
            (noise_score * 0.20) +
            ((1.0 if sharpness < 15.0 else 0.0) * 0.10)
        )
        deepfake_score = round(min(1.0, max(0.0, raw_deepfake_score)), 4)

        # Classification Mapping
        if deepfake_score >= 0.65:
            classification = "LIKELY_MANIPULATED"
            risk_level = "HIGH"
            risk_score = int(70 + (deepfake_score - 0.65) / 0.35 * 30)
            confidence = round(0.75 + (deepfake_score * 0.20), 2)
            explanation = (
                "Forensic inspection identified multiple synthetic manipulation markers, "
                "including Error Level Analysis anomalies and unnatural frequency spectrum characteristics."
            )
        elif deepfake_score >= 0.35:
            classification = "SUSPICIOUS"
            risk_level = "MEDIUM"
            risk_score = int(30 + (deepfake_score - 0.35) / 0.30 * 39)
            confidence = round(0.70 + (deepfake_score * 0.15), 2)
            explanation = (
                "Image exhibits moderate forensic inconsistencies in compression or noise variance. "
                "Manual review is recommended."
            )
        else:
            classification = "REAL"
            risk_level = "LOW"
            risk_score = int(deepfake_score / 0.35 * 29)
            confidence = round(0.85 + ((1.0 - deepfake_score) * 0.10), 2)
            explanation = (
                "Image forensic analysis indicates uniform compression levels, natural noise distribution, "
                "and consistent frequency characteristics."
            )

        # Clean fallback message if no specific indicators triggered
        if not suspicious_indicators:
            suspicious_indicators.append("No significant forensic manipulation artifacts detected.")

        return {
            "model_name": self.model_name,
            "deepfake_score": deepfake_score,
            "confidence": min(0.99, confidence),
            "classification": classification,
            "risk_score": min(100, max(0, risk_score)),
            "risk_level": risk_level,
            "suspicious_indicators": suspicious_indicators,
            "explanation": explanation
        }
