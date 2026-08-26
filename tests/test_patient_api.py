from uuid import uuid4

from fastapi.testclient import TestClient

from nightingale.data.seed import (
    DEMO_CLINIC_ID,
    DEMO_CLINICIAN_ID,
    DEMO_PATIENT_ID,
)
from nightingale.main import app

client = TestClient(app)


def _headers(actor_id, role, clinic_id=DEMO_CLINIC_ID):
    return {
        "x-actor-id": str(actor_id),
        "x-actor-role": role,
        "x-clinic-id": str(clinic_id),
    }


def test_clinician_can_get_seeded_patient_detail():
    response = client.get(
        f"/api/patients/{DEMO_PATIENT_ID}",
        headers=_headers(DEMO_CLINICIAN_ID, "clinician"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["patient"]["synthetic"] is True
    assert len(body["entries"]) == 6
    assert len(body["highlights"]) == 3


def test_patient_response_does_not_expose_internal_ai_content():
    response = client.get(
        f"/api/patients/{DEMO_PATIENT_ID}",
        headers=_headers(DEMO_PATIENT_ID, "patient"),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["highlights"] == []
    assert len(body["entries"]) == 1
    assert body["entries"][0]["internal"] is False


def test_cross_clinic_patient_is_not_discoverable():
    response = client.get(
        f"/api/patients/{DEMO_PATIENT_ID}",
        headers=_headers(DEMO_CLINICIAN_ID, "clinician", uuid4()),
    )
    assert response.status_code == 404
