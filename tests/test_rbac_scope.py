from datetime import date
from uuid import uuid4

import pytest

from nightingale.domain.models import (
    EntryOrigin,
    EntryType,
    Patient,
    ProvenanceSource,
    Role,
    TimelineEntry,
)
from nightingale.services.care_notes import AccessDeniedError


def test_staff_cannot_write_clinician_note(service, staff, patient_id, clinic_id):
    entry = TimelineEntry(
        patient_id=patient_id,
        clinic_id=clinic_id,
        author_role=Role.STAFF,
        author_id=staff.id,
        type=EntryType.CLINICIAN_NOTE,
        title="Synthetic clinician note",
        content="Synthetic note",
        origin=EntryOrigin(
            source=ProvenanceSource.MANUAL_ENTRY,
            source_id="test-clinician-note",
            source_label="Synthetic test entry",
        ),
    )
    with pytest.raises(AccessDeniedError):
        service.add_entry(staff, entry)


def test_cross_clinic_write_is_denied(service, staff, patient_id):
    entry = TimelineEntry(
        patient_id=patient_id,
        clinic_id=uuid4(),
        author_role=Role.STAFF,
        author_id=staff.id,
        type=EntryType.STAFF_NOTE,
        title="Synthetic staff note",
        content="Synthetic note",
        origin=EntryOrigin(
            source=ProvenanceSource.MANUAL_ENTRY,
            source_id="test-staff-note",
            source_label="Synthetic test entry",
        ),
    )
    with pytest.raises(AccessDeniedError):
        service.add_entry(staff, entry)


def test_patient_view_excludes_internal_and_raw_ai_entries(
    service, repository, patient_id, clinic_id
):
    from nightingale.domain.models import Actor

    repository.add_patient(
        Patient(
            id=patient_id,
            clinic_id=clinic_id,
            display_name="Synthetic Patient",
            date_of_birth=date(1990, 1, 1),
            medical_record_number="SYN-TEST",
        )
    )
    repository.add_entry(
        TimelineEntry(
            patient_id=patient_id,
            clinic_id=clinic_id,
            author_role=Role.SYSTEM,
            author_id=None,
            type=EntryType.AI_PATIENT_SESSION_SUMMARY,
            title="Synthetic AI session summary",
            content="Raw synthetic AI output",
            origin=EntryOrigin(
                source=ProvenanceSource.PATIENT_SESSION,
                source_id="test-patient-session",
                source_label="Synthetic patient session",
            ),
        )
    )
    patient = Actor(id=uuid4(), role=Role.PATIENT, clinic_id=clinic_id)
    with pytest.raises(AccessDeniedError):
        service.get_patient_view(patient, patient_id)

    patient = patient.model_copy(update={"id": patient_id})
    assert service.get_patient_view(patient, patient_id).entries == []
