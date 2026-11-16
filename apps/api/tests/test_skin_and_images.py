"""FR-06..FR-10, SC-02: image validation, mock adapter labelling, concern mapping. FR-12/13: OCR."""

import io

import numpy as np
import pytest
from PIL import Image, ImageDraw, ImageFilter, ImageFont

from skinsync.domain.images import ImageRejected, validate_and_sanitize
from skinsync.domain.knowledge import EvidenceRecord, KnowledgeLoadError
from skinsync.domain.skin import (
    FORBIDDEN_TERMS,
    MEDICAL_BOUNDARY,
    OBSERVATION_VOCABULARY,
    MockSkinModelAdapter,
    ModelOutput,
    Observation,
    SkinType,
    UnavailableSkinModelAdapter,
    build_concern_map,
    map_concerns,
)


def textured(w=800, h=800, mean=128, seed=1, fmt="JPEG", exif=None):
    rng = np.random.default_rng(seed)
    arr = np.clip(rng.normal(mean, 40, (h, w, 3)), 0, 255).astype("uint8")
    img = Image.fromarray(arr)
    buf = io.BytesIO()
    kwargs = {"exif": exif} if exif is not None else {}
    img.save(buf, format=fmt, **kwargs)
    return buf.getvalue(), img


def test_fr07_good_image_is_accepted_and_reencoded():
    data, _ = textured()
    out = validate_and_sanitize(data, require_face=False)
    assert out.jpeg_bytes.startswith(b"\xff\xd8\xff") and out.width == 800
    assert out.quality.face_check == "not_performed"


def test_fr07_png_and_webp_accepted():
    for fmt in ("PNG", "WEBP"):
        data, _ = textured(fmt=fmt)
        assert validate_and_sanitize(data, require_face=False).detected_format == fmt.lower()


def test_exif_and_gps_metadata_are_stripped():
    _, img = textured()
    exif = img.getexif()
    exif[0x010F] = "CameraMaker"           # Make
    exif[0x8825] = {2: (28, 37, 0)}         # GPS IFD
    buf = io.BytesIO()
    img.save(buf, format="JPEG", exif=exif)
    out = validate_and_sanitize(buf.getvalue(), require_face=False)
    assert len(Image.open(io.BytesIO(out.jpeg_bytes)).getexif()) == 0


@pytest.mark.parametrize("data,code", [
    (b"", "EMPTY_FILE"),
    (b"GIF89a" + b"\x00" * 100, "UNSUPPORTED_TYPE"),
    (b"%PDF-1.7 not an image", "UNSUPPORTED_TYPE"),
    (b"\xff\xd8\xff" + b"<script>alert(1)</script>" * 20, "CORRUPT_IMAGE"),  # polyglot-ish
])
def test_fr07_malicious_or_wrong_files_rejected(data, code):
    with pytest.raises(ImageRejected) as e:
        validate_and_sanitize(data, require_face=False)
    assert e.value.code == code and e.value.guidance


def test_oversized_file_rejected():
    with pytest.raises(ImageRejected) as e:
        validate_and_sanitize(b"\xff\xd8\xff" + b"0" * (9 * 1024 * 1024), require_face=False)
    assert e.value.code == "FILE_TOO_LARGE"


def test_decompression_bomb_rejected():
    buf = io.BytesIO()
    Image.new("L", (7000, 7000), 128).save(buf, format="PNG")  # 49M px > cap, tiny file
    with pytest.raises(ImageRejected) as e:
        validate_and_sanitize(buf.getvalue(), require_face=False)
    assert e.value.code == "TOO_MANY_PIXELS"


def test_low_resolution_rejected():
    data, _ = textured(200, 200)
    with pytest.raises(ImageRejected) as e:
        validate_and_sanitize(data, require_face=False)
    assert e.value.code == "LOW_RESOLUTION"


def test_blurry_rejected():
    _, img = textured()
    buf = io.BytesIO()
    img.filter(ImageFilter.GaussianBlur(12)).save(buf, format="JPEG")
    with pytest.raises(ImageRejected) as e:
        validate_and_sanitize(buf.getvalue(), require_face=False)
    assert e.value.code == "BLURRY"


def test_too_dark_and_too_bright_rejected():
    for mean, code in ((20, "TOO_DARK"), (240, "TOO_BRIGHT")):
        data, _ = textured(mean=mean)
        with pytest.raises(ImageRejected) as e:
            validate_and_sanitize(data, require_face=False)
        assert e.value.code == code


def test_mock_adapter_is_deterministic_labelled_and_cosmetic_only():
    data, _ = textured()
    a, b = MockSkinModelAdapter().analyze(data), MockSkinModelAdapter().analyze(data)
    assert a == b and a.is_demo and a.model_version == "mock-0.1"
    for o in a.observations:
        assert o.characteristic in OBSERVATION_VOCABULARY


def test_observation_vocabulary_names_no_conditions():
    for term in OBSERVATION_VOCABULARY:
        assert not any(f in term for f in FORBIDDEN_TERMS)
    assert "not a medical diagnosis" in MEDICAL_BOUNDARY


def test_adapter_output_is_validated():
    with pytest.raises(Exception):
        Observation(characteristic="acne", confidence=0.9, severity="mild")


def test_unavailable_adapter_never_fakes_results():
    with pytest.raises(RuntimeError, match="ANALYSIS_UNAVAILABLE"):
        UnavailableSkinModelAdapter().analyze(b"x")


EV = {"EV-FIX-9": EvidenceRecord(id="EV-FIX-9", claim="fixture", source_type="fixture",
                                  citation="FIXTURE (fictional)", strength="limited")}
MAPS = [{"observation": "visible_shine", "concern_category": "Oil control (fixture)",
         "ingredient_classes": ["test-active-class"], "intended_role": "Fixture role", "evidence_ids": ["EV-FIX-9"]}]


def test_fr10_concern_mapping_separates_confidence_from_evidence():
    cmap = build_concern_map(MAPS, EV)
    out = ModelOutput(observations=(Observation(characteristic="visible_shine", confidence=0.9, severity="mild"),
                                    Observation(characteristic="visible_pores", confidence=0.8, severity="mild"),
                                    Observation(characteristic="visible_texture", confidence=0.3, severity="mild")),
                      model_version="m", is_demo=True)
    r = map_concerns(out, SkinType.UNSURE, cmap, EV)
    (rec,) = r.recommendations
    assert rec.observation_confidence == 0.9 and rec.evidence_strength.value == "limited"
    assert r.unmapped_observations == ("visible_pores",)  # no reviewed mapping: says so, invents nothing
    low = [v for v in r.observations if v.low_confidence]
    assert [v.characteristic for v in low] == ["visible_texture"]
    assert r.is_demo_model


def test_concern_mapping_requires_evidence_and_rejects_medical_terms():
    with pytest.raises(KnowledgeLoadError):
        build_concern_map([{**MAPS[0], "evidence_ids": ["NOPE"]}], EV)
    with pytest.raises(KnowledgeLoadError):
        build_concern_map([{**MAPS[0], "concern_category": "Acne treatment"}], EV)


def test_ocr_extracts_label_text_and_reports_confidence():
    from skinsync.domain.ocr import TesseractOCRAdapter

    img = Image.new("L", (1400, 300), 255)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 48)
    except OSError:
        font = ImageFont.load_default(size=48)
    draw.text((30, 100), "Ingredients: Aqua, Glycerin, Panthenol", fill=0, font=font)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    res = TesseractOCRAdapter().extract(buf.getvalue())
    assert "Glycerin" in res.raw_text and res.words
    assert res.status in ("auto_extracted", "pending_review")


def test_ocr_blank_image_goes_to_review():
    from skinsync.domain.ocr import TesseractOCRAdapter

    buf = io.BytesIO()
    Image.new("L", (800, 400), 255).save(buf, format="PNG")
    res = TesseractOCRAdapter().extract(buf.getvalue())
    assert res.status == "pending_review" and res.mean_confidence == 0.0
