"""
Identity Document Forensic Analyzer – Phase 8
==============================================
Implements lightweight, dependency-free (cv2 + PIL + numpy) forensic checks
for digital identity verification.  No external API calls; no large ML models.

Checks performed
----------------
1. Document image quality (sharpness, brightness, contrast)
2. Error Level Analysis (ELA) on the ID document – detects JPEG re-saves / tampering
3. Face region detection on both ID document and selfie via OpenCV Haar cascade
4. Passive liveness proxy on selfie (Laplacian texture variance)
5. Structural cross-similarity between ID photo region and selfie (ORB keypoint match)
6. Edge-integrity check on the ID document (detects warping / compositing boundaries)
7. Noise analysis – unnaturally smooth regions may indicate digital print or screen photo
"""

import io
import os
from typing import Optional

import cv2
import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _load_gray(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Cannot decode image: {path}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)


def _load_bgr(path: str) -> np.ndarray:
    img = cv2.imread(path)
    if img is None:
        raise ValueError(f"Cannot decode image: {path}")
    return img


def _sharpness(gray: np.ndarray) -> float:
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _brightness_contrast(gray: np.ndarray) -> tuple[float, float]:
    return float(np.mean(gray)), float(np.std(gray))


def _noise_variance(gray: np.ndarray) -> float:
    blur = cv2.medianBlur(gray, 3)
    return float(np.var(cv2.absdiff(gray, blur)))


def _ela_score(image_path: str, quality: int = 85) -> tuple[float, float]:
    """
    Error Level Analysis: re-save at known quality and measure residual.
    High ELA on an ID document indicates localised re-compression (tampering).
    """
    with Image.open(image_path) as pil_img:
        rgb = pil_img.convert("RGB")
    buf = io.BytesIO()
    rgb.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    recomp = np.array(Image.open(buf).convert("RGB"))
    orig = np.array(rgb)
    diff = cv2.absdiff(orig, recomp).astype(np.float32)
    mean_err = float(np.mean(diff))
    max_err = float(np.max(diff))
    ela = min(1.0, mean_err / 18.0)  # normalised 0-1
    return round(ela, 4), round(mean_err, 2)


def _detect_faces(gray: np.ndarray) -> list[tuple[int, int, int, int]]:
    """
    Detect face bounding boxes using the bundled OpenCV Haar frontal-face cascade.
    Returns a list of (x, y, w, h) tuples.  Empty list if no faces found.
    """
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    if not os.path.exists(cascade_path):
        return []
    cascade = cv2.CascadeClassifier(cascade_path)
    faces = cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=4,
        minSize=(30, 30),
    )
    if len(faces) == 0:
        return []
    return [(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]


def _crop_face_region(gray: np.ndarray, faces: list) -> Optional[np.ndarray]:
    if not faces:
        return None
    x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
    return gray[y : y + h, x : x + w]


def _liveness_score(selfie_gray: np.ndarray, selfie_faces: list) -> tuple[float, bool]:
    """
    Passive liveness proxy: a printed photo / screen replay will have lower
    Laplacian texture variance than a genuine live capture.
    Returns (texture_variance, liveness_passed).
    """
    face_crop = _crop_face_region(selfie_gray, selfie_faces)
    region = face_crop if face_crop is not None else selfie_gray
    lap_var = float(cv2.Laplacian(region, cv2.CV_64F).var())
    # Threshold calibrated for college-demo use: screens/prints often < 50
    liveness_ok = lap_var >= 40.0
    return round(lap_var, 2), liveness_ok


def _orb_similarity(region_a: Optional[np.ndarray], region_b: Optional[np.ndarray]) -> float:
    """
    ORB keypoint descriptor match between two grayscale regions.
    Returns a normalised match ratio in [0, 1].  0.0 if either region is None.
    """
    if region_a is None or region_b is None:
        return 0.0
    if region_a.size == 0 or region_b.size == 0:
        return 0.0
    try:
        orb = cv2.ORB_create(nfeatures=300)
        kp1, des1 = orb.detectAndCompute(region_a, None)
        kp2, des2 = orb.detectAndCompute(region_b, None)
        if des1 is None or des2 is None or len(des1) < 2 or len(des2) < 2:
            return 0.0
        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        matches = bf.match(des1, des2)
        if not matches:
            return 0.0
        # Good matches: distance < 50 (tight threshold)
        good = [m for m in matches if m.distance < 50]
        ratio = len(good) / max(len(kp1), len(kp2), 1)
        return min(1.0, round(ratio * 3.5, 4))  # scale up for readability
    except cv2.error:
        return 0.0


def _edge_integrity_score(gray: np.ndarray) -> float:
    """
    Canny edge density variance across quadrants.
    Composited IDs often show abrupt edge discontinuities at splice boundaries.
    Returns a splice-risk score in [0, 1].
    """
    edges = cv2.Canny(gray, 50, 150)
    h, w = edges.shape
    hh, hw = h // 2, w // 2
    quadrants = [
        edges[:hh, :hw],
        edges[:hh, hw:],
        edges[hh:, :hw],
        edges[hh:, hw:],
    ]
    densities = [float(np.mean(q)) for q in quadrants if q.size > 0]
    if len(densities) < 2:
        return 0.0
    cv_coeff = np.std(densities) / (np.mean(densities) + 1e-6)
    return min(1.0, round(float(cv_coeff) / 1.5, 4))


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

class IdentityForensicAnalyzer:
    """
    Orchestrates all identity-verification forensic checks and returns a
    structured result payload compatible with the existing VerificationRecord schema.
    """

    @staticmethod
    def analyze(id_doc_path: str, selfie_path: str) -> dict:
        """
        Run all checks and return a forensics dict with all raw metrics.
        """
        # --- ID Document checks ---
        id_gray = _load_gray(id_doc_path)
        id_h, id_w = id_gray.shape
        id_sharpness = _sharpness(id_gray)
        id_brightness, id_contrast = _brightness_contrast(id_gray)
        id_noise_var = _noise_variance(id_gray)
        id_ela, id_ela_mean = _ela_score(id_doc_path)
        id_faces = _detect_faces(id_gray)
        id_face_count = len(id_faces)
        id_edge_risk = _edge_integrity_score(id_gray)

        # --- Selfie checks ---
        selfie_gray = _load_gray(selfie_path)
        selfie_h, selfie_w = selfie_gray.shape
        selfie_sharpness = _sharpness(selfie_gray)
        selfie_brightness, selfie_contrast = _brightness_contrast(selfie_gray)
        selfie_noise_var = _noise_variance(selfie_gray)
        selfie_faces = _detect_faces(selfie_gray)
        selfie_face_count = len(selfie_faces)
        selfie_liveness_var, selfie_liveness_ok = _liveness_score(selfie_gray, selfie_faces)

        # --- Cross-image face region similarity ---
        id_face_crop = _crop_face_region(id_gray, id_faces)
        selfie_face_crop = _crop_face_region(selfie_gray, selfie_faces)
        face_similarity = _orb_similarity(id_face_crop, selfie_face_crop)

        return {
            # ID document metrics
            "id_width": id_w,
            "id_height": id_h,
            "id_sharpness": round(id_sharpness, 2),
            "id_brightness": round(id_brightness, 2),
            "id_contrast": round(id_contrast, 2),
            "id_noise_variance": round(id_noise_var, 2),
            "id_ela_score": id_ela,
            "id_ela_mean_error": id_ela_mean,
            "id_face_count": id_face_count,
            "id_edge_risk_score": id_edge_risk,
            # Selfie metrics
            "selfie_width": selfie_w,
            "selfie_height": selfie_h,
            "selfie_sharpness": round(selfie_sharpness, 2),
            "selfie_brightness": round(selfie_brightness, 2),
            "selfie_contrast": round(selfie_contrast, 2),
            "selfie_noise_variance": round(selfie_noise_var, 2),
            "selfie_face_count": selfie_face_count,
            "selfie_liveness_texture_var": selfie_liveness_var,
            "selfie_liveness_passed": selfie_liveness_ok,
            # Cross-image
            "face_similarity_score": face_similarity,
        }

    @staticmethod
    def predict(forensics: dict) -> dict:
        """
        Derive a risk classification from the forensics dict.
        Returns a payload matching the existing route/DB schema conventions.
        """
        issues: list[str] = []
        risk_signals: list[float] = []

        # ---- Rule 1: ID document ELA (tampering) ----
        ela = forensics["id_ela_score"]
        if ela > 0.55:
            issues.append(
                f"ID document ELA score is elevated ({ela:.2f}), indicating possible "
                "localised re-compression or digital splicing."
            )
            risk_signals.append(min(1.0, ela * 1.1))
        elif ela > 0.35:
            issues.append(
                f"ID document ELA score is moderately elevated ({ela:.2f}); "
                "minor JPEG re-save artefacts detected."
            )
            risk_signals.append(ela * 0.7)

        # ---- Rule 2: ID edge integrity (compositing) ----
        edge_risk = forensics["id_edge_risk_score"]
        if edge_risk > 0.60:
            issues.append(
                f"Edge density is uneven across document quadrants (score {edge_risk:.2f}), "
                "suggesting possible photo-splicing or compositing."
            )
            risk_signals.append(edge_risk * 0.9)
        elif edge_risk > 0.35:
            issues.append(
                f"Mild edge-density asymmetry detected in ID document (score {edge_risk:.2f})."
            )
            risk_signals.append(edge_risk * 0.5)

        # ---- Rule 3: ID document sharpness / quality ----
        id_sharp = forensics["id_sharpness"]
        if id_sharp < 25.0:
            issues.append(
                f"ID document is very blurry (Laplacian variance {id_sharp:.1f}), "
                "making forensic text and face extraction unreliable."
            )
            risk_signals.append(0.45)
        elif id_sharp < 60.0:
            issues.append(
                f"ID document sharpness is below optimal ({id_sharp:.1f}); "
                "a higher-resolution scan is recommended."
            )
            risk_signals.append(0.20)

        # ---- Rule 4: ID face detection ----
        id_faces = forensics["id_face_count"]
        if id_faces == 0:
            issues.append(
                "No face region was detected on the ID document. "
                "Please ensure the photo area is clearly visible."
            )
            risk_signals.append(0.55)
        elif id_faces > 2:
            issues.append(
                f"{id_faces} face regions detected on the ID document; "
                "expected at most 1–2 (photo + possible secondary)."
            )
            risk_signals.append(0.30)

        # ---- Rule 5: Selfie face detection ----
        selfie_faces = forensics["selfie_face_count"]
        if selfie_faces == 0:
            issues.append(
                "No face region was detected in the selfie. "
                "Ensure the photo is a clear front-facing portrait."
            )
            risk_signals.append(0.55)
        elif selfie_faces > 1:
            issues.append(
                f"{selfie_faces} faces detected in the selfie; "
                "only one face is expected for identity verification."
            )
            risk_signals.append(0.25)

        # ---- Rule 6: Liveness proxy ----
        if not forensics["selfie_liveness_passed"]:
            lap_var = forensics["selfie_liveness_texture_var"]
            issues.append(
                f"Selfie passive liveness check FAILED – texture variance ({lap_var:.1f}) "
                "is below the threshold for a live capture. "
                "A printed photo or screen replay is suspected."
            )
            risk_signals.append(0.70)
        else:
            lap_var = forensics["selfie_liveness_texture_var"]
            issues.append(
                f"Passive liveness check PASSED – selfie texture variance ({lap_var:.1f}) "
                "is consistent with a live camera capture."
            )

        # ---- Rule 7: Cross-image face similarity ----
        sim = forensics["face_similarity_score"]
        if forensics["id_face_count"] > 0 and forensics["selfie_face_count"] > 0:
            if sim >= 0.15:
                issues.append(
                    f"ORB keypoint face similarity score is {sim:.3f} — "
                    "structural features between ID photo and selfie show a reasonable match."
                )
            else:
                issues.append(
                    f"ORB keypoint face similarity score is low ({sim:.3f}); "
                    "the ID photo and selfie may not be the same person, "
                    "or image quality is too low for reliable matching."
                )
                risk_signals.append(min(0.65, 0.65 - sim * 2))
        else:
            # Cannot compare — already reported face detection issues above
            issues.append(
                "Face region comparison could not be performed because one or both "
                "images lacked a detectable face."
            )

        # ---- Rule 8: ID noise (print/screen detection proxy) ----
        id_noise = forensics["id_noise_variance"]
        if id_noise < 1.5:
            issues.append(
                f"ID document noise variance is unusually low ({id_noise:.2f}), "
                "which may indicate a digitally generated document or screen capture."
            )
            risk_signals.append(0.45)

        # ---- Aggregate risk score ----
        if not risk_signals:
            agg_risk = 0.05
        else:
            agg_risk = float(np.mean(risk_signals)) * 0.7 + float(np.max(risk_signals)) * 0.3

        agg_risk = round(min(1.0, agg_risk), 4)
        risk_score_int = int(round(agg_risk * 100))

        # ---- Classification ----
        if agg_risk >= 0.60:
            classification = "IDENTITY_UNVERIFIED"
            risk_level = "HIGH"
            confidence = round(min(0.93, 0.65 + agg_risk * 0.20), 2)
            explanation = (
                "Multiple forensic indicators raised significant concerns. "
                "Manual review by a trained operator is strongly recommended before "
                "accepting this identity submission."
            )
        elif agg_risk >= 0.30:
            classification = "REQUIRES_REVIEW"
            risk_level = "MEDIUM"
            confidence = round(min(0.88, 0.72 + (1 - agg_risk) * 0.12), 2)
            explanation = (
                "One or more moderate forensic anomalies were detected. "
                "The submission should be reviewed alongside original supporting documents."
            )
        else:
            classification = "VERIFIED"
            risk_level = "LOW"
            confidence = round(min(0.96, 0.88 + (1 - agg_risk) * 0.08), 2)
            explanation = (
                "No significant forensic anomalies were detected. "
                "The ID document and selfie passed all automated quality and integrity checks."
            )

        return {
            "classification": classification,
            "risk_level": risk_level,
            "risk_score": risk_score_int,
            "confidence": confidence,
            "suspicious_indicators": issues,
            "explanation": explanation,
            "model_name": "Identity Forensic Analyzer v1.0 (ELA + Haar + ORB)",
        }
