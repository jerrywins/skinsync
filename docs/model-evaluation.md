# Model evaluation (skin analysis and OCR)

## Skin analysis: feasibility gate (SkinIQ implementation prompt §A.5)

| Step | Result |
|---|---|
| Model files available | **None.** No weights were supplied with the project. |
| Datasets available | **None.** No labelled, consented skin-image dataset was supplied. |
| Architecture / preprocessing | Not applicable without a model. |
| Inference test | `MockSkinModelAdapter` (does **not** look at skin; hash-seeded) and `HeuristicSkinAdapter` (classic image statistics, see below). Neither is a trained model. |
| Per-concern precision, recall, F1, calibration, false-positive rate | **Not measurable.** Nothing to evaluate. |
| Variation across skin tones, lighting, camera, age, angle | **Not measurable.** |

**Status: implemented with a development adapter and an experimental heuristic adapter; awaiting model weights and an evaluation dataset.**
Every mock result is labelled "Demo model — not a real analysis" in the API (`is_demo_model`,
`demo_label`) and the UI, and is stored with `model_version = mock-0.1`.

## Experimental heuristic adapter (`heuristic-0.1`, default)

Chosen by the project owner as an interim step: simple, deterministic image measurements, **not** a trained or
validated model. Code: `apps/api/skinsync/domain/skin_heuristics.py`. Tests: `tests/test_skin_heuristics.py`
(12) and `test_heuristic_adapter_end_to_end_is_labelled_and_uses_real_knowledge`.

| Item | Detail |
|---|---|
| Face region | OpenCV YuNet (`face_detection_yunet_2023mar.onnx`, MIT, from opencv_zoo, sha256 `8f2383e4…`). **Advisory only**: if no face is found the photo is still accepted, the whole image is used and confidence is lower. Upload response reports `face_check` = passed / not_detected / not_performed. |
| Skin pixels | Fixed YCrCb range Cr 133–173, Cb 77–127. Crude; known to miss some skin tones and to include skin-coloured backgrounds. |
| visible_shine | share of skin pixels with V > 235 and S < 40 (specular highlights) |
| visible_redness | 90th percentile minus median of CIELAB a* on skin pixels |
| uneven_tone_appearance | std of heavily blurred lightness on skin |
| visible_texture | std of fine (high-pass) lightness × 3 |
| dark_spots_appearance | share of skin pixels > 8 L-units darker than their blurred surroundings |
| Severity | fixed thresholds (mild / moderate / pronounced) in `THRESHOLDS`; **uncalibrated guesses** |
| Confidence | 0.45 + 0.1 if a face was found + up to 0.05 for skin coverage, **capped at 0.6** |
| Labelling | `label` = "Experimental image measurements — not validated", returned as `demo_label`; UI shows an "Experimental — not validated" notice and the Explain panel lists "a validated skin model" as missing |
| Knowledge | uses the **real** knowledge version, so no product suggestions appear until reviewed concern mappings exist |

**What has been verified:** determinism; output vocabulary; confidence cap; severity banding; synthetic
images with a flush, dark spots or highlights move the corresponding measure in the expected direction;
non-skin images yield no observations; the face check never rejects.

**Not verified / known limitations:**
- Never run on a set of real face photos (none available; we did not download photos of real people). YuNet
  did not detect drawn synthetic faces, which is expected for a model trained on photographs.
- Strongly saturated red areas fall outside the skin range and are ignored, so pronounced redness can be
  under-reported (`test_known_limitation_very_red_area_is_outside_skin_mask`).
- Lighting, white balance, camera processing, make-up and skin tone all shift every measure. No per-tone
  analysis has been done, so results may be systematically different across skin tones.
- Thresholds are not tied to any expert labels.

### What a real model must satisfy before replacing the mock or heuristic adapter

1. Implement `SkinModelAdapter.analyze(jpeg_bytes) -> ModelOutput` (`domain/skin.py`); output is validated
   against the cosmetic observation vocabulary.
2. Report per-observation precision, recall, F1 and expected calibration error on a held-out set, broken
   down by Fitzpatrick skin type (or an equivalent tone scale), lighting and device.
3. Set observation-specific confidence thresholds from calibration (the current global 0.5 cut-off is a
   placeholder).
4. Document consent and licensing for every training and evaluation image.
5. Select it with `SKINSYNC_SKIN_MODEL_ADAPTER`; the mock and heuristic adapters stay available for tests.

## OCR (Tesseract 5)

| Check | Result |
|---|---|
| Engine | Tesseract 5.3.4 locally (5.x in the container image), `eng`, `--psm 6`, grayscale + Otsu + deskew |
| Clean rendered label | Reads text correctly (`test_ocr_extracts_label_text_and_reports_confidence`, API OCR test) |
| Blank image | `pending_review`, confidence 0 |
| Curved packaging, low light, multi-column, real photos | **Not evaluated**: no labelled photo set |

OCR output is never used without user confirmation; low mean confidence (< 80) is also sent to the admin
review queue.
