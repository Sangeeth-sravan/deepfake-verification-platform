import wave

import numpy as np


class AudioForensicAnalyzer:
    """Dependency-free WAV forensic analysis for the project MVP.

    The service examines measurable acoustic indicators; it is not a claim of
    production-grade speaker or voice-clone attribution.
    """

    @staticmethod
    def _decode_samples(raw: bytes, sample_width: int) -> np.ndarray:
        if sample_width == 1:
            return (np.frombuffer(raw, dtype=np.uint8).astype(np.float64) - 128.0) / 128.0
        if sample_width == 2:
            return np.frombuffer(raw, dtype="<i2").astype(np.float64) / 32768.0
        if sample_width == 3:
            values = np.frombuffer(raw, dtype=np.uint8)
            values = values[: len(values) - (len(values) % 3)].reshape(-1, 3)
            signed = values[:, 0].astype(np.int32) | (values[:, 1].astype(np.int32) << 8) | (values[:, 2].astype(np.int32) << 16)
            signed[signed >= 0x800000] -= 0x1000000
            return signed.astype(np.float64) / 8388608.0
        if sample_width == 4:
            return np.frombuffer(raw, dtype="<i4").astype(np.float64) / 2147483648.0
        raise ValueError("Unsupported WAV sample width. Use standard 8-bit, 16-bit, 24-bit, or 32-bit PCM WAV audio.")

    @staticmethod
    def analyze(audio_path: str, max_seconds: int = 90) -> dict:
        try:
            with wave.open(audio_path, "rb") as audio:
                channels = audio.getnchannels()
                sample_width = audio.getsampwidth()
                sample_rate = audio.getframerate()
                total_frames = audio.getnframes()
                compression = audio.getcomptype()
                if compression != "NONE":
                    raise ValueError("Only uncompressed PCM WAV audio is supported for analysis.")
                if channels < 1 or sample_rate < 8000 or total_frames < sample_rate // 4:
                    raise ValueError("Audio is too short or has an unsupported sample rate.")
                frames_to_read = min(total_frames, sample_rate * max_seconds)
                samples = AudioForensicAnalyzer._decode_samples(audio.readframes(frames_to_read), sample_width)
        except wave.Error as error:
            raise ValueError(f"Invalid WAV audio file: {error}")

        samples = samples[: len(samples) - (len(samples) % channels)].reshape(-1, channels).mean(axis=1)
        if not len(samples):
            raise ValueError("The audio file contains no readable samples.")

        duration = total_frames / sample_rate
        rms = float(np.sqrt(np.mean(np.square(samples))))
        clipping_ratio = float(np.mean(np.abs(samples) >= 0.985))
        zero_crossing_rate = float(np.mean(np.diff(np.signbit(samples)) != 0))

        segment_size = max(sample_rate // 2, 1)
        segments = [samples[index:index + segment_size] for index in range(0, len(samples), segment_size)]
        segment_rms = [float(np.sqrt(np.mean(np.square(segment)))) for segment in segments if len(segment)]
        rms_variation = float(np.std(segment_rms)) if segment_rms else 0.0

        window = samples[: min(len(samples), sample_rate * 15)]
        spectrum = np.abs(np.fft.rfft(window * np.hanning(len(window))))
        frequencies = np.fft.rfftfreq(len(window), d=1 / sample_rate)
        total_energy = float(np.sum(spectrum)) + 1e-9
        high_frequency_ratio = float(np.sum(spectrum[frequencies >= min(7000, sample_rate * 0.42)]) / total_energy)

        # Indicators are scaled for a transparent prototype score, not a trained AI classifier.
        spectral_score = min(1.0, abs(high_frequency_ratio - 0.055) * 8.0)
        waveform_score = min(1.0, clipping_ratio * 14.0 + abs(zero_crossing_rate - 0.09) * 3.0)
        consistency_score = min(1.0, abs(rms_variation - 0.055) * 5.0)
        risk_signal = 0.45 * spectral_score + 0.30 * waveform_score + 0.25 * consistency_score

        return {
            "duration_seconds": round(duration, 2),
            "analyzed_seconds": round(len(samples) / sample_rate, 2),
            "sample_rate_hz": sample_rate,
            "channels": channels,
            "sample_width_bits": sample_width * 8,
            "rms_amplitude": round(rms, 4),
            "rms_variation": round(rms_variation, 4),
            "zero_crossing_rate": round(zero_crossing_rate, 4),
            "clipping_ratio": round(clipping_ratio, 4),
            "high_frequency_ratio": round(high_frequency_ratio, 4),
            "spectral_anomaly_score": round(spectral_score, 4),
            "waveform_anomaly_score": round(waveform_score, 4),
            "consistency_anomaly_score": round(consistency_score, 4),
            "audio_risk_signal": round(risk_signal, 4),
        }

    @staticmethod
    def predict(forensics: dict) -> dict:
        score = forensics["audio_risk_signal"]
        issues = []
        if forensics["spectral_anomaly_score"] > 0.55:
            issues.append("Unusual high-frequency spectral energy distribution detected.")
        if forensics["waveform_anomaly_score"] > 0.55:
            issues.append("Waveform clipping or zero-crossing pattern is outside the typical range.")
        if forensics["consistency_anomaly_score"] > 0.55:
            issues.append("Amplitude consistency varies substantially between audio segments.")
        if not issues:
            issues.append("No strong acoustic irregularities were found in the sampled WAV signal.")

        if score >= 0.65:
            result, level, risk = "SYNTHETIC_AUDIO_SUSPECTED", "HIGH", int(70 + (score - 0.65) / 0.35 * 30)
            confidence = min(0.95, round(0.74 + score * 0.2, 2))
            explanation = "Several acoustic consistency indicators are elevated. Review the recording alongside its source context."
        elif score >= 0.35:
            result, level, risk = "SUSPICIOUS", "MEDIUM", int(30 + (score - 0.35) / 0.30 * 39)
            confidence = round(0.68 + score * 0.14, 2)
            explanation = "The recording contains moderate spectral or waveform inconsistencies. Manual review is recommended."
        else:
            result, level, risk = "LIKELY_AUTHENTIC", "LOW", int(score / 0.35 * 29)
            confidence = round(0.82 + (1 - score) * 0.12, 2)
            explanation = "The sampled audio has relatively consistent waveform and spectral characteristics."
        return {"classification": result, "risk_level": level, "risk_score": min(100, max(0, risk)), "confidence": confidence, "suspicious_indicators": issues, "explanation": explanation}
