import math

import pytest

from app.services.measurement import (
    SUPPORTED_TASK_TYPES,
    SUPPORTED_VIEW_TYPES,
    calibrate_reference,
    evaluate_item,
    measure_geometry,
    task_requires_profile,
    task_view_supported,
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


def test_proper_task_contract_exposes_planar_and_profile_tasks():
    assert {
        "linear_dimension",
        "thickness_profile",
        "bend_angle",
        "inclination",
        "hole_diameter",
        "hole_center_distance",
        "hole_edge_distance",
        "hole_center_to_edge",
    } <= SUPPORTED_TASK_TYPES
    assert {"top", "profile", "side"} <= SUPPORTED_VIEW_TYPES
    assert task_requires_profile("thickness_profile") is True
    assert task_view_supported("thickness_profile", "top") is False
    assert task_view_supported("hole_diameter", "top") is True


def test_measure_geometry_uses_circle_radius_for_hole_diameter():
    calibration = calibrate_reference((0, 0), (100, 0), 50)

    result = measure_geometry(
        "hole_diameter",
        [],
        calibration,
        {"kind": "circle", "center": [40, 30], "radius_px": 20},
    )

    assert result["value"] == 20
    assert result["unit"] == "mm"
    assert result["pixel_value"] == 40
    assert result["geometry"]["center"] == [40.0, 30.0]


def test_measure_geometry_supports_hole_center_and_edge_distances():
    calibration = calibrate_reference((0, 0), (100, 0), 50)
    pair = {
        "kind": "circle_pair",
        "center_a": [0, 0],
        "center_b": [100, 0],
        "radius_a_px": 10,
        "radius_b_px": 10,
    }

    center = measure_geometry("hole_center_distance", [], calibration, pair)
    edge = measure_geometry("hole_edge_distance", [], calibration, pair)

    assert center["value"] == 50
    assert edge["value"] == 40
    assert center["unit"] == edge["unit"] == "mm"


def test_measure_geometry_supports_hole_center_to_component_edge():
    calibration = calibrate_reference((0, 0), (100, 0), 50)

    result = measure_geometry(
        "hole_center_to_edge",
        [],
        calibration,
        {
            "kind": "circle_to_edge",
            "center": [50, 20],
            "edge_a": [0, 100],
            "edge_b": [100, 100],
        },
    )

    assert result["value"] == 40
    assert result["unit"] == "mm"


def test_measure_geometry_supports_canonical_angle_and_inclination_types():
    calibration = calibrate_reference((0, 0), (100, 0), 50)

    bend = measure_geometry(
        "bend_angle",
        [(0, 0), (100, 0), (0, 0), (0, 100)],
        calibration,
    )
    inclination = measure_geometry("inclination", [(0, 0), (100, 100)], calibration)

    assert bend["value"] == 90
    assert inclination["value"] == 45
    assert inclination["unit"] == "deg"


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
