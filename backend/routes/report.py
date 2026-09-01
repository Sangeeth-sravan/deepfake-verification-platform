"""
PDF Report Generator – Phase 9 enhanced version.
Dependency-free PDF builder that includes forensic signal details for all
four verification types: IMAGE, VIDEO, AUDIO, DIGITAL_IDENTITY.
"""

import json
import re
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import VerificationRecord

router = APIRouter(tags=["Verification Reports"])


# ---------------------------------------------------------------------------
# PDF helpers
# ---------------------------------------------------------------------------

def _pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _safe_line(value: object) -> str:
    """Strip non-printable ASCII and cap line length for PDF safety."""
    return re.sub(r"[^\x20-\x7e]", "?", str(value))[:90]


def build_simple_pdf(lines: list[str]) -> bytes:
    """Create a small dependency-free PDF with Helvetica text."""
    content = ["BT", "/F1 11 Tf", "50 770 Td", "15 TL"]
    for index, line in enumerate(lines):
        if index:
            content.append("T*")
        content.append(f"({_pdf_escape(_safe_line(line))}) Tj")
    content.append("ET")
    stream = "\n".join(content).encode("latin-1")
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
    ]
    output = BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(output.tell())
        output.write(f"{number} 0 obj\n".encode())
        output.write(obj)
        output.write(b"\nendobj\n")
    xref_offset = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode())
    output.write(
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF".encode()
    )
    return output.getvalue()


def _fmt_pct(val) -> str:
    try:
        return f"{float(val) * 100:.1f}%"
    except (TypeError, ValueError):
        return "N/A"


def _fmt_float(val, dp: int = 4) -> str:
    try:
        return f"{float(val):.{dp}f}"
    except (TypeError, ValueError):
        return "N/A"


def _build_forensic_lines(vtype: str, details: dict) -> list[str]:
    """Return human-readable forensic metric lines for the PDF."""
    forensics = details.get("forensics") or {}
    lines: list[str] = []

    if not forensics:
        return lines

    lines.append("")
    lines.append("-- FORENSIC SIGNAL METRICS --")

    if vtype == "AUDIO":
        lines.append(f"  Duration            : {forensics.get('duration_seconds', 'N/A')} s")
        lines.append(f"  Sample Rate         : {forensics.get('sample_rate_hz', 'N/A')} Hz")
        lines.append(f"  Channels            : {forensics.get('channels', 'N/A')}")
        lines.append(f"  Sample Width        : {forensics.get('sample_width_bits', 'N/A')}-bit")
        lines.append(f"  Spectral Anomaly    : {_fmt_pct(forensics.get('spectral_anomaly_score'))}")
        lines.append(f"  Waveform Anomaly    : {_fmt_pct(forensics.get('waveform_anomaly_score'))}")
        lines.append(f"  Consistency Anomaly : {_fmt_pct(forensics.get('consistency_anomaly_score'))}")
        lines.append(f"  Clipping Ratio      : {_fmt_pct(forensics.get('clipping_ratio'))}")
        lines.append(f"  ZCR                 : {_fmt_float(forensics.get('zero_crossing_rate'))}")
        lines.append(f"  Audio Risk Signal   : {_fmt_float(forensics.get('audio_risk_signal'))}")

    elif vtype == "DIGITAL_IDENTITY":
        lines.append(f"  ID Document Size    : {forensics.get('id_width', '?')}x{forensics.get('id_height', '?')} px")
        lines.append(f"  ID ELA Score        : {_fmt_pct(forensics.get('id_ela_score'))}")
        lines.append(f"  ID Edge Risk Score  : {_fmt_pct(forensics.get('id_edge_risk_score'))}")
        lines.append(f"  ID Faces Detected   : {forensics.get('id_face_count', 'N/A')}")
        lines.append(f"  ID Sharpness        : {_fmt_float(forensics.get('id_sharpness'))}")
        lines.append(f"  Selfie Size         : {forensics.get('selfie_width', '?')}x{forensics.get('selfie_height', '?')} px")
        lines.append(f"  Selfie Faces        : {forensics.get('selfie_face_count', 'N/A')}")
        liveness = forensics.get('selfie_liveness_passed')
        liveness_str = ("PASSED" if liveness else "FAILED") if liveness is not None else "N/A"
        lines.append(f"  Liveness Check      : {liveness_str}")
        lines.append(f"  Liveness Texture Var: {_fmt_float(forensics.get('selfie_liveness_texture_var'))}")
        lines.append(f"  Face Similarity     : {_fmt_float(forensics.get('face_similarity_score'))}")

    else:
        # IMAGE and VIDEO share the same forensic schema
        lines.append(f"  Dimensions          : {forensics.get('width', '?')}x{forensics.get('height', '?')} px")
        lines.append(f"  File Size           : {forensics.get('file_size_mb', 'N/A')} MB")
        lines.append(f"  ELA Score           : {_fmt_pct(forensics.get('ela_score'))}")
        lines.append(f"  ELA Mean Error      : {_fmt_float(forensics.get('ela_mean_error'))}")
        lines.append(f"  Frequency Score     : {_fmt_pct(forensics.get('frequency_score'))}")
        lines.append(f"  High-Freq Ratio     : {_fmt_float(forensics.get('high_freq_ratio'))}")
        lines.append(f"  Noise Score         : {_fmt_pct(forensics.get('noise_score'))}")
        lines.append(f"  Noise Variance      : {_fmt_float(forensics.get('noise_variance'))}")
        lines.append(f"  Sharpness (Lap Var) : {_fmt_float(forensics.get('sharpness_score'))}")
        lines.append(f"  Brightness          : {_fmt_float(forensics.get('brightness'))}")
        lines.append(f"  Contrast (std-dev)  : {_fmt_float(forensics.get('contrast'))}")
        if vtype == "VIDEO":
            lines.append(f"  Sampled Frames      : {forensics.get('sampled_frames', 'N/A')}")
            lines.append(f"  FPS                 : {_fmt_float(forensics.get('fps'), 2)}")

    return lines


# ---------------------------------------------------------------------------
# Report route
# ---------------------------------------------------------------------------

@router.get("/report/{verification_id}/download", summary="Download verification PDF report")
async def download_report(verification_id: str, db: Session = Depends(get_db)):
    record = db.query(VerificationRecord).filter(
        VerificationRecord.verification_id == verification_id.upper()
    ).first()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Verification record not found."
        )

    # Parse stored JSON details
    try:
        details = json.loads(record.details or "{}")
    except json.JSONDecodeError:
        details = {}

    detected_issues = details.get("detected_issues") or []
    explanation = details.get("explanation") or ""
    model_name = details.get("model_name") or "Forensic Analyzer"

    lines: list[str] = [
        "=" * 60,
        "  DEEPFAKE VERIFICATION PLATFORM",
        "  Forensic Verification Report",
        "=" * 60,
        "",
        f"  Verification ID   : {record.verification_id}",
        f"  Scan Type         : {record.verification_type}",
        f"  Filename          : {record.filename or 'Not retained'}",
        f"  Result            : {record.result}",
        f"  Confidence        : {record.confidence * 100:.1f}%",
        f"  Risk Score        : {record.risk_score}/100",
        f"  Risk Level        : {record.risk_level}",
        f"  Analysis Engine   : {model_name}",
        f"  Generated         : {record.created_at.isoformat()}",
    ]

    # Forensic metrics block
    lines.extend(_build_forensic_lines(record.verification_type, details))

    # Detected signals
    if detected_issues:
        lines.append("")
        lines.append("-- DETECTED SIGNALS --")
        for issue in detected_issues[:12]:          # cap at 12 to fit PDF page
            lines.append(f"  * {issue}")

    # Explanation
    if explanation:
        lines.append("")
        lines.append("-- ANALYSIS SUMMARY --")
        # Word-wrap at ~80 chars
        words = explanation.split()
        current = "  "
        for word in words:
            if len(current) + len(word) + 1 > 88:
                lines.append(current.rstrip())
                current = "  " + word + " "
            else:
                current += word + " "
        if current.strip():
            lines.append(current.rstrip())

    lines.extend([
        "",
        "-" * 60,
        "DISCLAIMER: This is an academic prototype. Forensic indicator",
        "scores are computed from signal heuristics and should support,",
        "not replace, expert human review.",
        "-" * 60,
    ])

    return Response(
        content=build_simple_pdf(lines),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{record.verification_id}-report.pdf"'
        },
    )
