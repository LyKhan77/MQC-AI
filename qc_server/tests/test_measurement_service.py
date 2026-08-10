import math

import pytest

from app.services.measurement import (
    calibrate_reference,
    evaluate_item,
    measure_geometry,
)


def test_calibrate_reference_converts_pixels_to_mm():
    result = calibrate_reference((0, 0), (100, 0), 50)

    assert result["valid"] is True
    assert result["reference_px"] == 100
    assert result["mm_per_pixel"] == 0.5
    assert result["px_per_mm"] == 2


@pytest.mark.parametrize(
    "point_a,point_b,known_mm",
    [((0, 0), (0, 0), 50), ((0, 0), (100, 0), 0), ((0, 0), (100, 0), -1)],
)
def test_calibrate_reference_rejects_invalid_reference(point_a, point_b, known_mm):
    with pytest.raises(ValueError):
        calibrate_reference(point_a, point_b, known_mm)


def test_measure_geometry_returns_linear_mm_value():
    calibration = calibrate_reference((0, 0), (100, 0), 50)

    result = measure_geometry("edge_length", [(10, 10), (110, 10)], calibration)

    assert result["value"] == 50
    assert result["unit"] == "mm"
    assert result["pixel_value"] == 100


def test_measure_geometry_returns_planar_angle_in_degrees():
    calibration = calibrate_reference((0, 0), (100, 0), 50)

    result = measure_geometry(
        "angle",
        [(0, 0), (100, 0), (0, 0), (0, 100)],
        calibration,
    )

    assert math.isclose(result["value"], 90.0)
    assert result["unit"] == "deg"


def test_measure_geometry_supports_hole_diameter():
    calibration = calibrate_reference((0, 0), (100, 0), 50)

    result = measure_geometry("hole_diameter", [(0, 0), (20, 0)], calibration)

    assert result["value"] == 20
    assert result["unit"] == "mm"


def test_evaluate_item_passes_at_tolerance_bounds():
    result = evaluate_item(
        measured=142,
        unit="mm",
        nominal=140,
        tolerance=2,
        confidence=0.95,
        calibration_valid=True,
    )

    assert result == {
        "measured": 142,
        "unit": "mm",
        "nominal": 140,
        "tolerance": 2,
        "min": 138,
        "max": 142,
        "deviation": 2,
        "status": "PASS",
        "reason": "",
    }


def test_evaluate_item_fails_outside_tolerance():
    result = evaluate_item(
        measured=142.1,
        unit="mm",
        nominal=140,
        tolerance=2,
        confidence=0.95,
        calibration_valid=True,
    )

    assert result["status"] == "FAIL"
    assert result["reason"] == "outside_tolerance"


def test_evaluate_item_requires_review_for_invalid_calibration_or_low_confidence():
    invalid_calibration = evaluate_item(
        measured=140,
        unit="mm",
        nominal=140,
        tolerance=2,
        confidence=0.99,
        calibration_valid=False,
    )
    low_confidence = evaluate_item(
        measured=140,
        unit="mm",
        nominal=140,
        tolerance=2,
        confidence=0.49,
        calibration_valid=True,
    )

    assert invalid_calibration["status"] == "REVIEW"
    assert invalid_calibration["reason"] == "invalid_calibration"
    assert low_confidence["status"] == "REVIEW"
    assert low_confidence["reason"] == "low_confidence"


def test_evaluate_item_requires_nominal_and_tolerance():
    result = evaluate_item(
        measured=140,
        unit="mm",
        nominal=None,
        tolerance=None,
        confidence=0.99,
        calibration_valid=True,
    )

    assert result["status"] == "REVIEW"
    assert result["reason"] == "missing_nominal_or_tolerance"
