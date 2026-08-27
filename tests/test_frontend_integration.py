from fastapi.testclient import TestClient

from nightingale.data.seed import (
    DEMO_CLINIC_ID,
    DEMO_CLINICIAN_ID,
    DEMO_PATIENT_ID,
)
from nightingale.main import app

client = TestClient(app)


def test_patient_page_serves_accessible_app_shell_and_modules():
    page = client.get("/")
    api_module = client.get("/static/api.js")
    app_module = client.get("/static/app.js")

    assert page.status_code == api_module.status_code == app_module.status_code == 200
    assert 'aria-labelledby="patient-name"' in page.text
    assert 'id="screen-state"' in page.text
    assert 'id="highlight-list"' in page.text
    assert 'id="timeline-list"' in page.text
    assert 'id="workspace-panel"' in page.text
    assert 'id="save-section"' in page.text
    assert 'id="comment-list"' in page.text
    assert 'type="module" src="/static/app.js"' in page.text
    assert "/api/patients/${context.patientId}" in api_module.text
    assert '"x-actor-role": context.actorRole' in api_module.text
    assert "/sections/${section}/revisions" in api_module.text
    assert "/comments/${commentId}" in api_module.text


def test_patient_api_supplies_every_field_required_by_frontend():
    response = client.get(
        f"/api/patients/{DEMO_PATIENT_ID}",
        headers={
            "x-actor-id": str(DEMO_CLINICIAN_ID),
            "x-actor-role": "clinician",
            "x-clinic-id": str(DEMO_CLINIC_ID),
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert {
        "display_name",
        "date_of_birth",
        "medical_record_number",
        "pronouns",
        "synthetic",
    } <= body["patient"].keys()
    assert all(
        {
            "text",
            "risk_reason",
            "suggested_action",
            "priority",
            "status",
            "provenance_pointer",
        }
        <= highlight.keys()
        for highlight in body["highlights"]
    )
    assert all(
        {
            "id",
            "timestamp",
            "type",
            "title",
            "content",
            "origin",
            "author_role",
        }
        <= entry.keys()
        for entry in body["entries"]
    )


def test_frontend_declares_loading_empty_forbidden_and_error_states():
    app_module = client.get("/static/app.js").text
    for state in ("loading", "empty", "forbidden", "notFound", "error"):
        assert f"{state}:" in app_module
