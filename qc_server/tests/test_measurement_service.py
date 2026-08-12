import math

import pytest

from app.services.measurement import (
    SUPPORTED_TASK_TYPES,
    SUPPORTED_VIEW_TYPES,
    calibrate_axes,
    calibrate_reference,
    calibration_quality,
    calibration_verdict_eligible,
    evaluate_item,
    measure_geometry,
    normalize_task_types,
    pose_task_supported,
    profile_supports_measurement,
    scaled_distance,
    task_requires_profile,
    task_view_supported,
    validate_measurement_profile,
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


def test_calibrate_axes_builds_independent_xy_scales():
    result = calibrate_axes(
        {"point_a": [0, 4], "point_b": [100, 4], "known_mm": 50},
        {"point_a": [8, 0], "point_b": [8, 200], "known_mm": 80},
        "independent_artifact",
    )

    assert result["scale_x_mm_per_px"] == 0.5
    assert result["scale_y_mm_per_px"] == 0.4
    assert result["verdict_eligible"] is True


def test_scaled_distance_uses_both_axes():
    calibration = calibrate_axes(
        {"point_a": [0, 0], "point_b": [100, 0], "known_mm": 50},
        {"point_a": [0, 0], "point_b": [0, 100], "known_mm": 25},
        "independent_artifact",
    )

    assert scaled_distance([0, 0], [6, 8], calibration) == pytest.approx(3.605551275463989)


def test_component_reference_is_valid_but_not_verdict_eligible():
    result = calibrate_axes(
        {"point_a": [0, 0], "point_b": [100, 0], "known_mm": 50},
        {"point_a": [0, 0], "point_b": [0, 100], "known_mm": 50},
        "component_demo",
    )

    assert result["valid"] is True
    assert calibration_verdict_eligible(result) is False


def test_calibrate_axes_rejects_wrong_axis_direction():
    with pytest.raises(ValueError, match="horizontal"):
        calibrate_axes(
            {"point_a": [0, 0], "point_b": [50, 50], "known_mm": 50},
            {"point_a": [0, 0], "point_b": [0, 100], "known_mm": 50},
            "independent_artifact",
        )


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


def test_pose_task_rules_separate_planar_and_profile_measurements():
    assert pose_task_supported("linear_dimension", "TOP_FACE") is True
    assert pose_task_supported("linear_dimension", "REVERSE_FACE") is True
    assert pose_task_supported("thickness_profile", "TOP_FACE") is False
    assert pose_task_supported("thickness_profile", "PROFILE_FACE") is True


def test_global_profile_rejects_one_mm_feature_at_large_scale():
    profile = {
        "resolution_width": 2560,
        "resolution_height": 1440,
        "camera_id": "global",
        "capability": {
            "minimum_supported_feature_mm": 8,
            "maximum_supported_span_mm": 2100,
        },
    }

    assert profile_supports_measurement(profile, nominal=1) is False
    assert profile_supports_measurement(profile, nominal=2100) is True


def test_valid_measurement_profile_matches_frame_and_camera():
    profile = {
        "id": "profile-global",
        "status": "valid",
        "camera_id": "global",
        "resolution_width": 2560,
        "resolution_height": 1440,
        "calibration": {"valid": True, "mm_per_pixel": 0.8},
    }

    result = validate_measurement_profile(profile, 2560, 1440, "global")

    assert result == {
        "valid": True,
        "reason": "",
        "profile_id": "profile-global",
        "calibration": profile["calibration"],
    }


def test_manual_axes_profile_is_valid_and_task_types_are_normalized():
    calibration = calibrate_axes(
        {"point_a": [0, 0], "point_b": [100, 0], "known_mm": 50},
        {"point_a": [0, 0], "point_b": [0, 100], "known_mm": 50},
        "independent_artifact",
    )
    profile = {
        "id": "profile-axes",
        "status": "approved",
        "resolution_width": 2560,
        "resolution_height": 1440,
        "calibration": calibration,
    }

    result = validate_measurement_profile(profile, 2560, 1440)

    assert result["valid"] is True
    assert normalize_task_types('["linear_dimension", "bend_angle", "linear_dimension"]', "linear_dimension") == [
        "linear_dimension",
        "bend_angle",
    ]
    assert calibration_quality(calibration)["verdict_eligible"] is True
