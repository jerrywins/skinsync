"""Experimental heuristic skin adapter: determinism, labelling, vocabulary, caps.

These tests check the code does what it says on synthetic images. They say NOTHING about whether the
measurements match what a person or dermatologist would see; that has not been evaluated.
"""

import io

import numpy as np
import pytest
from PIL import Image

from skinsync.domain import skin_heuristics as h
from skinsync.domain.images import validate_and_sanitize
from skinsync.domain.skin import ModelOutput, Severity, get_adapter

SKIN_BGR = (150, 170, 215)  # light skin-like tone inside the YCrCb range


def jpeg(arr_bgr: np.ndarray) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(arr_bgr[..., ::-1].copy()).save(buf, format="JPEG", quality=95)
    return buf.getvalue()


def skin_image(seed=0, noise=2.0, red_patch=False, spots=0, shine=False):
    rng = np.random.default_rng(seed)
    img = np.zeros((600, 600, 3), np.float32) + SKIN_BGR
    img += rng.normal(0, noise, img.shape)
    if red_patch:
        img[100:300, 100:300] = (130, 140, 215)  # mild flush; very saturated red falls outside the skin mask (documented limitation)
    if shine:
        img[350:450, 350:450] = (250, 250, 250)
    for i in range(spots):
        y, x = 50 + (i * 97) % 500, 50 + (i * 53) % 500
        img[y:y + 8, x:x + 8] = (70, 85, 120)
    return np.clip(img, 0, 255).astype(np.uint8)


def test_registered_and_labelled():
    a = get_adapter("heuristic")
    out = a.analyze(jpeg(skin_image()))
    assert isinstance(out, ModelOutput)
    assert out.is_demo is False
    assert out.model_version == "heuristic-0.1"
    assert out.label == h.LABEL and "not validated" in out.label


def test_deterministic():
    data = jpeg(skin_image(seed=5, red_patch=True, spots=6))
    a, b = h.HeuristicSkinAdapter().analyze(data), h.HeuristicSkinAdapter().analyze(data)
    assert a.model_dump() == b.model_dump()


def test_vocabulary_and_confidence_cap():
    out = h.HeuristicSkinAdapter().analyze(jpeg(skin_image(red_patch=True, spots=12, shine=True, noise=8)))
    assert out.observations, "a strongly patterned image should produce some observations"
    for o in out.observations:
        assert o.characteristic in h.THRESHOLDS
        assert 0 < o.confidence <= h.MAX_CONFIDENCE


def test_plain_even_skin_yields_few_or_no_observations():
    out = h.HeuristicSkinAdapter().analyze(jpeg(skin_image(noise=1.0)))
    assert {o.characteristic for o in out.observations} <= {"visible_texture"}


def test_red_patch_raises_redness_measure():
    plain = h.measure(skin_image())
    red = h.measure(skin_image(red_patch=True))
    assert red["visible_redness"] > plain["visible_redness"]


def test_dark_spots_raise_spot_measure():
    assert h.measure(skin_image(spots=15))["dark_spots_appearance"] > h.measure(skin_image())["dark_spots_appearance"]


def test_no_skin_pixels_gives_no_observations():
    blue = np.full((600, 600, 3), (200, 60, 20), np.uint8)
    m = h.measure(blue)
    assert m["skin_coverage"] < 0.01 and "visible_redness" not in m
    assert h.HeuristicSkinAdapter().analyze(jpeg(blue)).observations == ()


@pytest.mark.parametrize("v,expected", [(0.03, Severity.MILD), (0.06, Severity.MODERATE), (0.2, Severity.PRONOUNCED)])
def test_severity_bands(monkeypatch, v, expected):
    monkeypatch.setattr(h, "measure", lambda bgr: {"face_found": False, "skin_coverage": 0.9, "visible_shine": v})
    out = h.HeuristicSkinAdapter().analyze(jpeg(skin_image()))
    assert [(o.characteristic, o.severity) for o in out.observations] == [("visible_shine", expected)]


def test_face_check_is_advisory_never_rejects():
    rng = np.random.default_rng(3)
    arr = np.clip(rng.normal(130, 40, (800, 800, 3)), 0, 255).astype("uint8")
    buf = io.BytesIO()
    Image.fromarray(arr).save(buf, format="JPEG")
    clean = validate_and_sanitize(buf.getvalue())
    assert clean.quality.face_check in ("not_detected", "not_performed")


def test_known_limitation_very_red_area_is_outside_skin_mask():
    """Documented in docs/model-evaluation.md: strongly red pixels fall outside the YCrCb skin range."""
    very_red = np.full((10, 10, 3), (120, 120, 225), np.uint8)
    assert not h.skin_mask(very_red).any()
