"""Label OCR adapter (FR-12/13, US-005). OCR is an extraction aid, never ground truth.

TesseractOCRAdapter runs the locally installed Tesseract via pytesseract:
grayscale -> upscale small images -> Otsu threshold -> optional deskew -> image_to_data.
Mean word confidence below REVIEW_THRESHOLD yields status pending_review, and the
extracted text is always shown to the user to confirm or correct.
"""

from __future__ import annotations

import io
from abc import ABC, abstractmethod

import cv2
import numpy as np
from PIL import Image
from pydantic import BaseModel, ConfigDict, Field

REVIEW_THRESHOLD = 80.0  # Tesseract word confidence is 0-100


class OCRWord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str
    confidence: float = Field(ge=0, le=100)
    left: int
    top: int
    width: int
    height: int


class OCRResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    raw_text: str
    words: tuple[OCRWord, ...]
    mean_confidence: float
    status: str  # "pending_review" | "auto_extracted"  (a user still confirms either way)
    engine: str


class OCRAdapter(ABC):
    @abstractmethod
    def extract(self, image_bytes: bytes) -> OCRResult: ...


def _preprocess(image_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(image_bytes)).convert("L")
    arr = np.asarray(img)
    h, w = arr.shape
    if max(h, w) < 1500:  # Tesseract does better on larger glyphs
        scale = 1500 / max(h, w)
        arr = cv2.resize(arr, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)
    _, binar = cv2.threshold(arr, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    # Deskew: angle of the minimum-area rectangle around dark pixels.
    coords = np.column_stack(np.where(binar < 128))
    if len(coords) > 50:
        angle = cv2.minAreaRect(coords.astype(np.float32))[-1]
        angle = angle - 90 if angle > 45 else angle
        if 0.5 < abs(angle) < 15:
            h2, w2 = binar.shape
            m = cv2.getRotationMatrix2D((w2 / 2, h2 / 2), angle, 1.0)
            binar = cv2.warpAffine(binar, m, (w2, h2), flags=cv2.INTER_CUBIC, borderValue=255)
    return binar


class TesseractOCRAdapter(OCRAdapter):
    def __init__(self, lang: str = "eng"):
        self.lang = lang

    def extract(self, image_bytes: bytes) -> OCRResult:
        import pytesseract

        arr = _preprocess(image_bytes)
        data = pytesseract.image_to_data(arr, lang=self.lang, config="--psm 6",
                                         output_type=pytesseract.Output.DICT)
        words = []
        for i, txt in enumerate(data["text"]):
            conf = float(data["conf"][i])
            if txt.strip() and conf >= 0:
                words.append(OCRWord(text=txt, confidence=conf, left=data["left"][i], top=data["top"][i],
                                     width=data["width"][i], height=data["height"][i]))
        # Rebuild lines in reading order from Tesseract's block/line numbering.
        lines: dict[tuple, list[str]] = {}
        for i, txt in enumerate(data["text"]):
            if txt.strip() and float(data["conf"][i]) >= 0:
                lines.setdefault((data["block_num"][i], data["par_num"][i], data["line_num"][i]), []).append(txt)
        raw = "\n".join(" ".join(ws) for _, ws in sorted(lines.items()))
        mean = round(sum(w.confidence for w in words) / len(words), 2) if words else 0.0
        return OCRResult(
            raw_text=raw,
            words=tuple(words),
            mean_confidence=mean,
            status="auto_extracted" if words and mean >= REVIEW_THRESHOLD else "pending_review",
            engine=f"tesseract-{pytesseract.get_tesseract_version()}",
        )
