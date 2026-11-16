"""EXPERIMENTAL, NOT VALIDATED: classic image measurements of a few visible features.

This is not a trained or evaluated model. It measures simple colour and texture statistics on skin-coloured
pixels (inside the detected face when a face is found). Thresholds are uncalibrated guesses, results depend
heavily on lighting, camera and skin tone, and nothing here has been checked against expert labels.
Every output is labelled "Experimental image measurements — not validated".

Measured (only what one photo can plausibly show):
  visible_shine           share of bright, low-saturation (specular) skin pixels
  visible_redness         mean CIELAB a* of skin pixels relative to the image's own skin median
  uneven_tone_appearance  spread of low-frequency lightness across skin
  visible_texture         high-frequency lightness energy across skin
  dark_spots_appearance   share of small regions much darker than the surrounding skin
"""

from __future__ import annotations

import io
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

from .skin import ModelOutput, Observation, Severity, SkinModelAdapter

MODEL_VERSION = "heuristic-0.1"
LABEL = "Experimental image measurements — not validated"
YUNET = Path(__file__).resolve().parents[1] / "models" / "face_detection_yunet_2023mar.onnx"

# Uncalibrated thresholds (mild, moderate, pronounced). See docs/model-evaluation.md.
THRESHOLDS = {
    "visible_shine": (0.02, 0.05, 0.10),
    "visible_redness": (4.0, 7.0, 11.0),
    "uneven_tone_appearance": (5.0, 8.0, 12.0),
    "visible_texture": (6.0, 9.0, 13.0),
    "dark_spots_appearance": (0.004, 0.012, 0.03),
}
MAX_CONFIDENCE = 0.6  # never claims more than "moderate"; experimental


def detect_face(bgr: np.ndarray) -> tuple[int, int, int, int] | None:
    """Largest face via OpenCV YuNet, or None. Advisory only: absence never rejects a photo."""
    if not YUNET.exists() or not hasattr(cv2, "FaceDetectorYN"):
        return None
    h, w = bgr.shape[:2]
    det = cv2.FaceDetectorYN.create(str(YUNET), "", (w, h), 0.8)
    _, faces = det.detect(bgr)
    if faces is None or len(faces) == 0:
        return None
    x, y, fw, fh = max(faces, key=lambda f: f[2] * f[3])[:4]
    x, y = max(int(x), 0), max(int(y), 0)
    return x, y, min(int(fw), w - x), min(int(fh), h - y)


def skin_mask(bgr: np.ndarray) -> np.ndarray:
    """Broad YCrCb skin range (Chai & Ngan style). Crude: misses some tones, includes some backgrounds."""
    ycc = cv2.cvtColor(bgr, cv2.COLOR_BGR2YCrCb)
    m = cv2.inRange(ycc, (0, 133, 77), (255, 173, 127))
    return cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8)) > 0


def measure(bgr: np.ndarray) -> dict:
    face = detect_face(bgr)
    region = bgr
    if face:
        x, y, w, h = face
        region = bgr[y:y + h, x:x + w]
    if min(region.shape[:2]) < 64:
        region, face = bgr, None
    mask = skin_mask(region)
    cover = float(mask.mean())
    lab = cv2.cvtColor(region, cv2.COLOR_BGR2LAB).astype(np.float32)
    L, A = lab[..., 0] * 100 / 255, lab[..., 1] - 128
    hsv = cv2.cvtColor(region, cv2.COLOR_BGR2HSV)
    out = {"face_found": face is not None, "skin_coverage": round(cover, 4)}
    if mask.sum() < 500:
        return out
    s = mask
    out["visible_shine"] = float(((hsv[..., 2] > 235) & (hsv[..., 1] < 40) & s).sum() / s.sum())
    out["visible_redness"] = float(np.percentile(A[s], 90) - np.median(A[s]))
    low = cv2.GaussianBlur(L, (0, 0), max(region.shape[:2]) / 40)
    out["uneven_tone_appearance"] = float(np.std(low[s]))
    high = L - cv2.GaussianBlur(L, (0, 0), 2)
    out["visible_texture"] = float(np.std(high[s]) * 3)
    local = cv2.GaussianBlur(L, (0, 0), max(region.shape[:2]) / 60)
    out["dark_spots_appearance"] = float(((local - L > 8) & s).sum() / s.sum())
    return out


class HeuristicSkinAdapter(SkinModelAdapter):
    """Deterministic image statistics mapped to cosmetic observations. NOT a validated model."""

    MODEL_VERSION = MODEL_VERSION

    def analyze(self, jpeg_bytes: bytes) -> ModelOutput:
        rgb = np.asarray(Image.open(io.BytesIO(jpeg_bytes)).convert("RGB"))
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
        m = measure(bgr)
        # Confidence reflects how usable the measurement region was, capped low because nothing is validated.
        base = 0.45 + (0.1 if m["face_found"] else 0.0) + min(m["skin_coverage"], 0.5) * 0.1
        conf = round(min(base, MAX_CONFIDENCE), 2)
        obs = []
        for key, (mild, mod, pron) in THRESHOLDS.items():
            v = m.get(key)
            if v is None or v < mild:
                continue
            sev = Severity.PRONOUNCED if v >= pron else Severity.MODERATE if v >= mod else Severity.MILD
            obs.append(Observation(characteristic=key, confidence=conf, severity=sev))
        return ModelOutput(observations=tuple(obs), model_version=MODEL_VERSION, is_demo=False, label=LABEL)
