import json

import cv2
import numpy as np


def _png_bytes():
    frame = np.zeros((120, 160, 3), dtype=np.uint8)
    cv2.rectangle(frame, (20, 30), (140, 90), (255, 255, 255), 3)
    ok, buffer = cv2.imencode(".png", frame)
    assert ok
    return buffer.tobytes()


def _hole_png_bytes():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    cv2.circle(frame, (160, 120), 36, (255, 255, 255), -1)
    ok, buffer = cv2.imencode(".png", frame)
    assert ok
    return buffer.tobytes()


def _rounded_component_png_bytes():
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    mask = np.zeros((240, 320), dtype=np.uint8)
    radius = 24
    cv2.rectangle(mask, (60 + radius, 40), (260 - radius, 200), 255, -1)
    cv2.rectangle(mask, (60, 40 + radius), (260, 200 - radius), 255, -1)
    for center in ((84, 64), (236, 64), (84, 176), (236, 176)):
        cv2.circle(mask, center, radius, 255, -1)
    frame[mask > 0] = (255, 255, 255)
    ok, buffer = cv2.imencode(".png", frame)
    assert ok
    return buffer.tobytes()


def _green_jig_png_bytes():
    frame = np.zeros((120, 200, 3), dtype=np.uint8)
    for point in ((30, 20), (170, 20), (30, 100), (170, 100)):
        cv2.circle(frame, point, 7, (0, 255, 0), -1)
    ok, buffer = cv2.imencode(".png", frame)
    assert ok
    return buffer.tobytes()


def _calibration():
    return json.dumps({
        "point_a": [0, 0],
        "point_b": [100, 0],
        "known_mm": 50,
    })


def _axes_calibration():
    return json.dumps({
        "mode": "manual_axes",
        "source": "independent_artifact",
        "x": {"point_a": [0, 0], "point_b": [100, 0], "known_mm": 50},
        "y": {"point_a": [0, 0], "point_b": [0, 100], "known_mm": 50},
    })


def _demo_axes_calibration():
    payload = json.loads(_axes_calibration())
    payload["source"] = "component_demo"
    return json.dumps(payload)


def _process_upload(client):
    return client.post(
        "/api/measurements/process",
        files={"file": ("bracket.png", _png_bytes(), "image/png")},
        data={"calibration": _calibration()},
    )


def test_process_upload_returns_candidates_and_serves_frame(client):
    response = _process_upload(client)

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "image"
    assert body["source_filename"] == "bracket.png"
    assert body["readiness"] == "ready"
    assert body["candidates"]
    assert body["frame_url"].startswith("/api/measurements/files/tmp-")
    assert client.get(body["frame_url"]).status_code == 200


def test_process_accepts_dual_axes_and_returns_logical_edges(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("bracket.png", _png_bytes(), "image/png")},
        data={
            "task_types": json.dumps(["linear_dimension"]),
            "calibration": _axes_calibration(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_types"] == ["linear_dimension"]
    assert body["logical_edges"]
    assert body["calibration_quality"]["verdict_eligible"] is True


def test_process_outer_dimension_returns_overall_candidates(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("rounded.png", _rounded_component_png_bytes(), "image/png")},
        data={
            "task_types": json.dumps(["outer_dimension"]),
            "calibration": _axes_calibration(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["readiness"] == "ready"
    assert body["task_readiness"]["outer_dimension"]["status"] == "ready"
    by_axis = {item["axis"]: item for item in body["overall_candidates"]}
    assert set(by_axis) == {"x", "y"}
    assert abs(by_axis["x"]["value_mm"] - 100.0) <= 1.0
    assert abs(by_axis["y"]["value_mm"] - 80.0) <= 1.0
    assert by_axis["x"]["geometry"]["kind"] == "outer_extent"


def test_process_normalizes_calibration_points_to_processed_frame(client):
    calibration = json.loads(_axes_calibration())
    calibration["coordinate_width"] = 80
    calibration["coordinate_height"] = 60
    calibration["x"]["point_a"] = [10, 15]
    calibration["x"]["point_b"] = [70, 15]
    calibration["y"]["point_a"] = [10, 15]
    calibration["y"]["point_b"] = [10, 45]

    response = client.post(
        "/api/measurements/process",
        files={"file": ("bracket.png", _png_bytes(), "image/png")},
        data={"calibration": json.dumps(calibration)},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["calibration"]["x"]["point_a"] == [20.0, 30.0]
    assert body["calibration"]["x"]["point_b"] == [140.0, 30.0]
    assert body["calibration"]["y"]["point_b"] == [20.0, 90.0]


def test_detect_jig_returns_automatic_axes_but_not_physical_length(client):
    response = client.post(
        "/api/measurements/detect-jig",
        files={"file": ("jig.png", _green_jig_png_bytes(), "image/png")},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["x"]["point_a"] == [30.0, 20.0]
    assert body["x"]["point_b"] == [170.0, 20.0]
    assert body["y"]["point_a"] == [30.0, 20.0]
    assert body["y"]["point_b"] == [30.0, 100.0]
    assert "known_mm" not in body


def test_process_multi_task_returns_corner_candidates_and_readiness(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("rounded.png", _rounded_component_png_bytes(), "image/png")},
        data={
            "task_types": json.dumps(["linear_dimension", "corner_radius"]),
            "calibration": _axes_calibration(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_types"] == ["linear_dimension", "corner_radius"]
    assert body["logical_edges"]
    assert body["corner_arcs"]
    assert body["task_readiness"]["corner_radius"]["status"] == "ready"


def test_process_bend_profile_requires_profile_pose(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("profile.png", _png_bytes(), "image/png")},
        data={
            "task_types": json.dumps(["bend_angle"]),
            "view_type": "profile",
            "pose_type": "TOP_FACE",
            "calibration": _axes_calibration(),
        },
    )

    assert response.status_code == 200
    assert response.json()["readiness"] == "review"
    assert response.json()["reason"] == "unsupported_pose"


def test_process_bend_profile_returns_bend_candidates(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("profile.png", _png_bytes(), "image/png")},
        data={
            "task_types": json.dumps(["bend_angle"]),
            "view_type": "profile",
            "pose_type": "PROFILE_FACE",
            "calibration": _axes_calibration(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["readiness"] == "ready"
    assert body["bend_candidates"]
    assert body["task_readiness"]["bend_angle"]["status"] == "ready"


def test_process_hole_task_returns_circle_candidates(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("holes.png", _hole_png_bytes(), "image/png")},
        data={
            "task_type": "hole_diameter",
            "view_type": "top",
            "calibration": _calibration(),
            "options": json.dumps({"min_radius_px": 30, "max_radius_px": 42}),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["task_type"] == "hole_diameter"
    assert body["view_type"] == "top"
    assert body["holes"]
    assert body["holes"][0]["center"]


def test_process_profile_task_on_top_view_requires_review(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("profile.png", _png_bytes(), "image/png")},
        data={
            "task_type": "thickness_profile",
            "view_type": "top",
            "calibration": _calibration(),
        },
    )

    assert response.status_code == 200
    assert response.json()["readiness"] == "review"
    assert response.json()["reason"] == "unsupported_view"


def test_process_live_camera_uses_registered_camera_and_grab_one(client, monkeypatch):
    from app.routers import measurements

    client.post(
        "/api/cameras",
        json={"id": "cam-measure", "name": "QC Top", "type": "usb", "source": "0"},
    )
    monkeypatch.setattr(measurements, "grab_one", lambda source: cv2.imdecode(
        np.frombuffer(_png_bytes(), np.uint8), cv2.IMREAD_COLOR
    ))

    response = client.post(
        "/api/measurements/process",
        data={"camera_id": "cam-measure", "calibration": _calibration()},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "live_camera"
    assert body["source_camera_id"] == "cam-measure"
    assert body["source_filename"] == "cam-measure.jpg"


def test_capture_live_camera_stages_frame_without_processing(client, monkeypatch):
    from app.routers import measurements

    client.post(
        "/api/cameras",
        json={"id": "cam-stage", "name": "QC Top", "type": "usb", "source": "0"},
    )
    monkeypatch.setattr(measurements, "grab_one", lambda source: cv2.imdecode(
        np.frombuffer(_png_bytes(), np.uint8), cv2.IMREAD_COLOR
    ))

    response = client.post("/api/measurements/capture", data={"camera_id": "cam-stage"})

    assert response.status_code == 200
    body = response.json()
    assert body["source_type"] == "live_camera"
    assert body["source_camera_id"] == "cam-stage"
    assert body["source_filename"] == "cam-stage.jpg"
    assert client.get(body["frame_url"]).status_code == 200


def test_processes_a_staged_live_frame_after_calibration(client, monkeypatch):
    from app.routers import measurements

    client.post(
        "/api/cameras",
        json={"id": "cam-process-staged", "name": "QC Top", "type": "usb", "source": "0"},
    )
    monkeypatch.setattr(measurements, "grab_one", lambda source: cv2.imdecode(
        np.frombuffer(_png_bytes(), np.uint8), cv2.IMREAD_COLOR
    ))
    captured = client.post("/api/measurements/capture", data={"camera_id": "cam-process-staged"}).json()

    response = client.post(
        "/api/measurements/process",
        data={
            "source_key": captured["source_key"],
            "source_filename": captured["source_filename"],
            "source_camera_id": captured["source_camera_id"],
            "source_type": "live_camera",
            "calibration": _calibration(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["source_key"] == captured["source_key"]
    assert body["source_type"] == "live_camera"
    assert body["source_camera_id"] == "cam-process-staged"


def test_process_mobile_camera_file_preserves_mobile_source_type(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("mobile.jpg", _png_bytes(), "image/jpeg")},
        data={"source_type": "mobile_camera", "calibration": _calibration()},
    )

    assert response.status_code == 200
    assert response.json()["source_type"] == "mobile_camera"


def test_process_rejects_unknown_file_source_type(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("capture.jpg", _png_bytes(), "image/jpeg")},
        data={"source_type": "camera", "calibration": _calibration()},
    )

    assert response.status_code == 400


def test_process_rejects_missing_calibration(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("bracket.png", _png_bytes(), "image/png")},
    )

    assert response.status_code == 422


def test_process_rejects_invalid_image(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("broken.png", b"not-an-image", "image/png")},
        data={"calibration": _calibration()},
    )

    assert response.status_code == 400


def test_process_returns_calibration_validation_detail(client):
    payload = json.loads(_axes_calibration())
    payload["x"]["point_b"] = [20, 120]
    response = client.post(
        "/api/measurements/process",
        files={"file": ("bracket.png", _png_bytes(), "image/png")},
        data={"calibration": json.dumps(payload)},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "invalid calibration: horizontal reference must be within 10 degrees of horizontal"


def test_process_rejects_unknown_camera(client):
    response = client.post(
        "/api/measurements/process",
        data={"camera_id": "missing", "calibration": _calibration()},
    )

    assert response.status_code == 404


def test_process_rejects_unavailable_live_camera(client, monkeypatch):
    from app.routers import measurements

    client.post(
        "/api/cameras",
        json={"id": "cam-offline", "name": "Offline", "type": "usb", "source": "0"},
    )
    monkeypatch.setattr(measurements, "grab_one", lambda source: None)

    response = client.post(
        "/api/measurements/process",
        data={"camera_id": "cam-offline", "calibration": _calibration()},
    )

    assert response.status_code == 503


def test_save_list_detail_delete_measurement_and_audit(client):
    processed = _process_upload(client).json()
    payload = {
        "name": "BRKT-001",
        "source_key": processed["source_key"],
        "source_filename": processed["source_filename"],
        "source_type": processed["source_type"],
        "calibration": processed["calibration"],
        "task_types": ["linear_dimension", "corner_radius"],
        "processing": {
            "task_readiness": {"linear_dimension": {"status": "ready", "reason": ""}},
            "calibration_quality": {"verdict_eligible": True},
        },
        "items": [{
            "id": "E1",
            "type": "edge_length",
            "label": "Overall length",
            "points": [[20, 30], [140, 30]],
            "nominal": 60,
            "tolerance": 2,
            "confidence": 0.95,
        }],
    }

    saved = client.post("/api/measurements", json=payload)

    assert saved.status_code == 201
    body = saved.json()
    assert body["name"] == "BRKT-001"
    assert body["items"][0]["measured"] == 60
    assert body["items"][0]["status"] == "PASS"
    assert body["processing"]["task_type"] == "linear_dimension"
    assert body["processing"]["task_types"] == ["linear_dimension", "corner_radius"]
    assert body["processing"]["task_readiness"]["linear_dimension"]["status"] == "ready"
    assert body["processing"]["view_type"] == "top"
    assert client.get(body["source_url"]).status_code == 200

    listed = client.get("/api/measurements").json()
    assert listed[0]["id"] == body["id"]
    assert client.get(f"/api/measurements/{body['id']}").json()["name"] == "BRKT-001"
    assert any(item["action"] == "MEASUREMENT_SAVED" for item in client.get("/api/audit").json())

    deleted = client.delete(f"/api/measurements/{body['id']}")

    assert deleted.status_code == 200
    assert client.get(f"/api/measurements/{body['id']}").status_code == 404
    assert client.get(body["source_url"]).status_code == 404
    assert any(item["action"] == "MEASUREMENT_DELETED" for item in client.get("/api/audit").json())


def test_save_rejects_missing_tolerance_with_review_not_pass(client):
    processed = _process_upload(client).json()
    payload = {
        "name": "BRKT-REVIEW",
        "source_key": processed["source_key"],
        "source_filename": processed["source_filename"],
        "source_type": processed["source_type"],
        "calibration": processed["calibration"],
        "items": [{
            "id": "E1",
            "type": "edge_length",
            "points": [[20, 30], [140, 30]],
            "nominal": None,
            "tolerance": None,
            "confidence": 0.95,
        }],
    }

    response = client.post("/api/measurements", json=payload)

    assert response.status_code == 201
    assert response.json()["summary"]["status"] == "REVIEW"


def test_component_demo_calibration_stays_review_after_save(client):
    processed = client.post(
        "/api/measurements/process",
        files={"file": ("bracket.png", _png_bytes(), "image/png")},
        data={"calibration": _demo_axes_calibration()},
    ).json()
    response = client.post("/api/measurements", json={
        "name": "BRKT-DEMO",
        "source_key": processed["source_key"],
        "source_filename": processed["source_filename"],
        "source_type": processed["source_type"],
        "calibration": processed["calibration"],
        "items": [{
            "id": "E1",
            "type": "edge_length",
            "points": [[20, 30], [140, 30]],
            "nominal": 60,
            "tolerance": 2,
            "confidence": 0.95,
        }],
    })

    assert response.status_code == 201
    assert response.json()["summary"]["status"] == "REVIEW"
    assert response.json()["items"][0]["reason"] == "reference_not_independent"


def test_measurement_profile_and_session_rows_persist():
    from app.database import SessionLocal
    from app.models import MeasurementProfile, MeasurementSession

    with SessionLocal() as db:
        db.add(MeasurementProfile(
            id="profile-global",
            name="Global top-down",
            station_id="QC-01",
            scale_type="GLOBAL",
            capability={"minimum_supported_feature_mm": 8},
        ))
        db.add(MeasurementSession(
            id="session-1",
            created_at="2026-08-11T00:00:00Z",
            updated_at="2026-08-11T00:00:00Z",
            name="BRKT-001",
        ))
        db.commit()

    with SessionLocal() as db:
        profile = db.get(MeasurementProfile, "profile-global")
        session = db.get(MeasurementSession, "session-1")
        assert profile.capability["minimum_supported_feature_mm"] == 8
        assert session.status == "in_progress"


def test_measurement_profile_crud_and_audit(client):
    payload = {
        "name": "Global top-down",
        "station_id": "QC-01",
        "camera_id": "cam-global",
        "scale_type": "GLOBAL",
        "resolution_width": 2560,
        "resolution_height": 1440,
        "revision": "cal-01",
        "calibration": {"valid": True, "mm_per_pixel": 0.8},
        "capability": {
            "minimum_supported_feature_mm": 8,
            "maximum_supported_span_mm": 2100,
        },
        "status": "valid",
    }

    created = client.post("/api/measurement-profiles", json=payload)

    assert created.status_code == 201
    profile_id = created.json()["id"]
    assert client.get("/api/measurement-profiles").json()[0]["id"] == profile_id

    updated = client.patch(
        f"/api/measurement-profiles/{profile_id}",
        json={"name": "Global top-down v2", "revision": "cal-02"},
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Global top-down v2"
    assert updated.json()["revision"] == "cal-02"

    deleted = client.delete(f"/api/measurement-profiles/{profile_id}")

    assert deleted.status_code == 200
    assert client.get(f"/api/measurement-profiles/{profile_id}").status_code == 404
    actions = [entry["action"] for entry in client.get("/api/audit").json()]
    assert "MEASUREMENT_PROFILE_CREATED" in actions
    assert "MEASUREMENT_PROFILE_UPDATED" in actions
    assert "MEASUREMENT_PROFILE_DELETED" in actions


def test_measurement_session_view_lifecycle_and_audit(client):
    session = client.post("/api/measurement-sessions", json={"name": "BRKT-001"})
    assert session.status_code == 201
    session_id = session.json()["id"]
    processed = _process_upload(client).json()

    saved = client.post(
        f"/api/measurement-sessions/{session_id}/views",
        json={
            "name": "BRKT-001",
            "source_key": processed["source_key"],
            "source_filename": processed["source_filename"],
            "source_type": "image",
            "view_label": "top face",
            "pose_type": "TOP_FACE",
            "task_type": "linear_dimension",
            "view_type": "top",
            "calibration": processed["calibration"],
            "items": [],
        },
    )

    assert saved.status_code == 201
    view_id = saved.json()["id"]
    assert saved.json()["session_id"] == session_id
    assert saved.json()["view_label"] == "top face"
    assert saved.json()["pose_type"] == "TOP_FACE"

    reopened = client.get(f"/api/measurement-sessions/{session_id}")
    assert reopened.status_code == 200
    assert reopened.json()["views"][0]["id"] == view_id
    assert reopened.json()["summary"]["view_count"] == 1

    completed = client.patch(
        f"/api/measurement-sessions/{session_id}",
        json={"status": "complete"},
    )
    assert completed.status_code == 200
    assert completed.json()["status"] == "complete"

    deleted = client.delete(f"/api/measurement-sessions/{session_id}")
    assert deleted.status_code == 200
    assert client.get(f"/api/measurement-sessions/{session_id}").status_code == 404
    actions = [entry["action"] for entry in client.get("/api/audit").json()]
    assert "MEASUREMENT_SESSION_CREATED" in actions
    assert "MEASUREMENT_VIEW_SAVED" in actions
    assert "MEASUREMENT_SESSION_COMPLETED" in actions


def test_process_binds_valid_measurement_profile_metadata(client):
    profile = client.post("/api/measurement-profiles", json={
        "name": "Development detail",
        "scale_type": "DETAIL",
        "resolution_width": 160,
        "resolution_height": 120,
        "calibration": {"valid": True, "mm_per_pixel": 0.1},
        "capability": {
            "minimum_supported_feature_mm": 1,
            "maximum_supported_span_mm": 250,
        },
        "status": "valid",
    }).json()

    response = client.post(
        "/api/measurements/process",
        files={"file": ("detail.png", _png_bytes(), "image/png")},
        data={
            "profile_id": profile["id"],
            "pose_type": "TOP_FACE",
            "view_label": "detail face",
            "calibration": _calibration(),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["scale_profile_id"] == profile["id"]
    assert body["pose_type"] == "TOP_FACE"
    assert body["view_label"] == "detail face"


def test_process_rejects_profile_task_with_flat_top_pose(client):
    response = client.post(
        "/api/measurements/process",
        files={"file": ("profile.png", _png_bytes(), "image/png")},
        data={
            "task_type": "thickness_profile",
            "view_type": "profile",
            "pose_type": "TOP_FACE",
            "calibration": _calibration(),
        },
    )

    assert response.status_code == 200
    assert response.json()["readiness"] == "review"
    assert response.json()["reason"] == "unsupported_pose"
