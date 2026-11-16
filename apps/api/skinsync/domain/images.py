"""Server-side image validation and sanitisation (FR-07, NFR-02, OWASP file-upload guidance).

validate_and_sanitize(raw_bytes) -> SanitizedImage | raises ImageRejected

Checks, in order: size limit, magic bytes (not extension or client MIME), Pillow decode
with a decompression-bomb pixel cap, dimension limits, full load (catches truncation),
then quality: blur (variance of Laplacian), exposure (mean/clipped luminance), and an
optional face-presence check. Accepted images are re-encoded to JPEG with all metadata
(EXIF, GPS, ICC, XMP) dropped.
"""

from __future__ import annotations

import hashlib
import io
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageOps

MAX_BYTES = 8 * 1024 * 1024
MAX_PIXELS = 40_000_000
MIN_SIDE = 480
MIN_SIDE_LABEL = 160  # ingredient strips are wide and short
MAX_SIDE = 8000
BLUR_MIN_VARIANCE = 60.0
DARK_MEAN = 50
BRIGHT_MEAN = 215
CLIPPED_FRACTION = 0.25
OUTPUT_MAX_SIDE = 2048

_SIGNATURES = {
    b"\xff\xd8\xff": "jpeg",
    b"\x89PNG\r\n\x1a\n": "png",
}


class ImageRejected(ValueError):
    def __init__(self, code: str, message: str, guidance: str):
        super().__init__(message)
        self.code, self.message, self.guidance = code, message, guidance


@dataclass(frozen=True)
class QualityReport:
    blur_variance: float
    mean_luminance: float
    clipped_fraction: float
    face_check: str  # "passed" | "not_detected" (advisory, never rejects) | "not_performed"


@dataclass(frozen=True)
class SanitizedImage:
    jpeg_bytes: bytes
    width: int
    height: int
    sha256: str
    detected_format: str
    quality: QualityReport


def sniff_format(data: bytes) -> str | None:
    for sig, fmt in _SIGNATURES.items():
        if data.startswith(sig):
            return fmt
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def _face_found(img_rgb) -> bool | None:
    """Advisory face check with OpenCV YuNet. None = detector unavailable. Never used to reject a photo:
    the detector has not been verified on a representative set of real faces (docs/model-evaluation.md)."""
    try:
        from .skin_heuristics import detect_face
    except Exception:
        return None
    bgr = cv2.cvtColor(np.asarray(img_rgb), cv2.COLOR_RGB2BGR)
    return detect_face(bgr) is not None


def validate_and_sanitize(data: bytes, *, require_face: bool = True, check_quality: bool = True) -> SanitizedImage:
    if len(data) == 0:
        raise ImageRejected("EMPTY_FILE", "The file is empty.", "Choose a photo and try again.")
    if len(data) > MAX_BYTES:
        raise ImageRejected("FILE_TOO_LARGE", f"The file is larger than {MAX_BYTES // 1024 // 1024} MB.",
                            "Use a smaller photo or lower the camera resolution.")
    fmt = sniff_format(data)
    if fmt is None:
        raise ImageRejected("UNSUPPORTED_TYPE", "Only JPEG, PNG or WebP photos are accepted.",
                            "Export or take the photo as JPEG, PNG or WebP.")

    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        with Image.open(io.BytesIO(data)) as probe:
            if probe.format is None or probe.format.lower() != ("jpeg" if fmt == "jpeg" else fmt):
                raise ImageRejected("TYPE_MISMATCH", "The file contents do not match an image type.",
                                    "Upload an unmodified photo.")
            w, h = probe.size
            if w * h > MAX_PIXELS:
                raise ImageRejected("TOO_MANY_PIXELS", "The image is too large to process.", "Use a smaller photo.")
            probe.verify()
        img = Image.open(io.BytesIO(data))
        img.load()
    except ImageRejected:
        raise
    except (Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ImageRejected("TOO_MANY_PIXELS", "The image is too large to process.", "Use a smaller photo.") from None
    except Exception:
        raise ImageRejected("CORRUPT_IMAGE", "The image could not be read; it may be damaged.",
                            "Take a new photo and upload it again.") from None

    img = ImageOps.exif_transpose(img).convert("RGB")  # apply orientation, then drop metadata
    w, h = img.size
    min_side = MIN_SIDE if check_quality else MIN_SIDE_LABEL
    if min(w, h) < min_side:
        raise ImageRejected("LOW_RESOLUTION", f"The photo is too small (shortest side under {min_side}px).",
                            "Move a little closer or use the main camera at full resolution.")
    if max(w, h) > MAX_SIDE:
        raise ImageRejected("TOO_LARGE_DIMENSIONS", "The photo dimensions are too large.", "Use a smaller photo.")

    gray = np.asarray(img.convert("L"))
    blur = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    mean = float(gray.mean())
    clipped = float(((gray < 8) | (gray > 247)).mean())
    if check_quality:
        if blur < BLUR_MIN_VARIANCE:
            raise ImageRejected("BLURRY", "The photo looks blurry.", "Hold the camera steady, tap to focus, and retake.")
        if mean < DARK_MEAN:
            raise ImageRejected("TOO_DARK", "The photo is too dark.", "Face a window or soft, even light and retake.")
        if mean > BRIGHT_MEAN or clipped > CLIPPED_FRACTION:
            raise ImageRejected("TOO_BRIGHT", "The photo is over-exposed.",
                                "Avoid direct flash or harsh light and retake.")

    face_check = "not_performed"
    if require_face and check_quality:
        found = _face_found(img)
        face_check = "not_performed" if found is None else ("passed" if found else "not_detected")

    if max(w, h) > OUTPUT_MAX_SIDE:
        img.thumbnail((OUTPUT_MAX_SIDE, OUTPUT_MAX_SIDE))
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=90, optimize=True)  # no exif= argument -> no metadata written
    jpeg = out.getvalue()
    return SanitizedImage(
        jpeg_bytes=jpeg,
        width=img.size[0],
        height=img.size[1],
        sha256=hashlib.sha256(jpeg).hexdigest(),
        detected_format=fmt,
        quality=QualityReport(round(blur, 2), round(mean, 2), round(clipped, 4), face_check),
    )
