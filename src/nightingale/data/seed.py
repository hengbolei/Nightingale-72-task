from datetime import UTC, date, datetime
from uuid import UUID

from nightingale.domain.models import (
    EntryOrigin,
    EntryType,
    Highlight,
    Patient,
    ProvenancePointer,
    ProvenanceSource,
    ReviewStatus,
    Role,
    SectionRevision,
    SectionState,
    TimelineEntry,
)
from nightingale.repositories.memory import InMemoryCareNoteRepository

DEMO_CLINIC_ID = UUID("10000000-0000-4000-8000-000000000001")
DEMO_PATIENT_ID = UUID("20000000-0000-4000-8000-000000000001")
DEMO_STAFF_ID = UUID("30000000-0000-4000-8000-000000000001")
DEMO_CLINICIAN_ID = UUID("40000000-0000-4000-8000-000000000001")


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value).replace(tzinfo=UTC)


def _origin(source: ProvenanceSource, source_id: str, label: str) -> EntryOrigin:
    return EntryOrigin(source=source, source_id=source_id, source_label=label)


def _highlight(
    highlight_id: UUID,
    entry: TimelineEntry,
    text: str,
    risk_reason: str,
    suggested_action: str,
    priority: int,
    status: ReviewStatus,
) -> Highlight:
    start = entry.content.index(text)
    return Highlight(
        id=highlight_id,
        patient_id=entry.patient_id,
        text=text,
        risk_reason=risk_reason,
        suggested_action=suggested_action,
        priority=priority,
        status=status,
        provenance_pointer=ProvenancePointer(
            entry_id=entry.id,
            start=start,
            end=start + len(text),
        ),
    )


def seed_demo_data(repository: InMemoryCareNoteRepository) -> None:
    """Load deterministic synthetic data; safe to call more than once."""
    patient = Patient(
        id=DEMO_PATIENT_ID,
        clinic_id=DEMO_CLINIC_ID,
        display_name="Maya Chen (Synthetic)",
        date_of_birth=date(1985, 4, 12),
        medical_record_number="SYN-000184",
        pronouns="she/her",
    )
    repository.add_patient(patient)

    entries = [
        TimelineEntry(
            id=UUID("50000000-0000-4000-8000-000000000001"),
            patient_id=patient.id,
            clinic_id=patient.clinic_id,
            author_role=Role.PATIENT,
            author_id=patient.id,
            timestamp=_timestamp("2026-08-20T08:30:00"),
            type=EntryType.PATIENT_NOTE,
            title="Pre-visit symptom update",
            content="I have felt light-headed twice this week, usually before breakfast.",
            origin=_origin(
                ProvenanceSource.MANUAL_ENTRY,
                "patient-message-20260820",
                "Synthetic patient portal message",
            ),
            internal=False,
        ),
        TimelineEntry(
            id=UUID("50000000-0000-4000-8000-000000000002"),
            patient_id=patient.id,
            clinic_id=patient.clinic_id,
            author_role=Role.SYSTEM,
            author_id=None,
            timestamp=_timestamp("2026-08-21T09:05:00"),
            type=EntryType.AI_PATIENT_SESSION_SUMMARY,
            title="AI patient session summary",
            content=(
                "Patient reports intermittent light-headedness before breakfast and no loss "
                "of consciousness. This summary is AI-generated and needs review."
            ),
            origin=_origin(
                ProvenanceSource.PATIENT_SESSION,
                "ai-patient-session-20260821",
                "Synthetic AI patient session",
            ),
            review_status=ReviewStatus.NEEDS_REVIEW,
        ),
        TimelineEntry(
            id=UUID("50000000-0000-4000-8000-000000000003"),
            patient_id=patient.id,
            clinic_id=patient.clinic_id,
            author_role=Role.STAFF,
            author_id=DEMO_STAFF_ID,
            timestamp=_timestamp("2026-08-22T10:15:00"),
            type=EntryType.STAFF_NOTE,
            title="Medication reconciliation",
            content="Medication list reconciled. Patient started lisinopril 10 mg seven days ago.",
            origin=_origin(
                ProvenanceSource.MANUAL_ENTRY,
                "staff-note-20260822",
                "Synthetic staff medication reconciliation",
            ),
        ),
        TimelineEntry(
            id=UUID("50000000-0000-4000-8000-000000000004"),
            patient_id=patient.id,
            clinic_id=patient.clinic_id,
            author_role=Role.SYSTEM,
            author_id=None,
            timestamp=_timestamp("2026-08-23T11:40:00"),
            type=EntryType.AI_NURSE_CONSULT_SUMMARY,
            title="AI nurse consultation summary",
            content=(
                "Patient describes new dizziness after morning dose. Home blood pressure was "
                "98/62 mmHg. Nurse advised hydration and escalation if fainting occurs."
            ),
            origin=_origin(
                ProvenanceSource.NURSE_CONSULT,
                "ai-nurse-consult-20260823",
                "Synthetic AI nurse consultation",
            ),
            review_status=ReviewStatus.AI_SUGGESTED,
        ),
        TimelineEntry(
            id=UUID("50000000-0000-4000-8000-000000000005"),
            patient_id=patient.id,
            clinic_id=patient.clinic_id,
            author_role=Role.CLINICIAN,
            author_id=DEMO_CLINICIAN_ID,
            timestamp=_timestamp("2026-08-24T14:20:00"),
            type=EntryType.CLINICIAN_NOTE,
            title="Clinician assessment",
            content=(
                "Likely medication-related hypotension. Hold morning lisinopril pending review "
                "and arrange a blood pressure check within 48 hours."
            ),
            origin=_origin(
                ProvenanceSource.MANUAL_ENTRY,
                "clinician-note-20260824",
                "Synthetic clinician assessment",
            ),
            review_status=ReviewStatus.CLINICIAN_CONFIRMED,
        ),
        TimelineEntry(
            id=UUID("50000000-0000-4000-8000-000000000006"),
            patient_id=patient.id,
            clinic_id=patient.clinic_id,
            author_role=Role.SYSTEM,
            author_id=None,
            timestamp=_timestamp("2026-08-25T15:10:00"),
            type=EntryType.AI_DOCTOR_CONSULT_SUMMARY,
            title="AI doctor consultation summary",
            content=(
                "Discussion focused on symptomatic low blood pressure after a new medicine. "
                "Follow-up blood pressure check remains unresolved. AI-generated summary; "
                "clinician confirmation required."
            ),
            origin=_origin(
                ProvenanceSource.DOCTOR_CONSULT,
                "ai-doctor-consult-20260825",
                "Synthetic AI doctor consultation",
            ),
            review_status=ReviewStatus.NEEDS_REVIEW,
        ),
    ]
    for entry in entries:
        repository.add_entry(entry)

    nurse_summary = entries[3]
    clinician_note = entries[4]
    doctor_summary = entries[5]
    highlights = [
        _highlight(
            UUID("60000000-0000-4000-8000-000000000001"),
            clinician_note,
            "Hold morning lisinopril pending review",
            "Clinician-confirmed medication action",
            "Confirm the hold instruction with the patient",
            100,
            ReviewStatus.CLINICIAN_CONFIRMED,
        ),
        _highlight(
            UUID("60000000-0000-4000-8000-000000000002"),
            nurse_summary,
            "98/62 mmHg",
            "Low home blood-pressure reading after a new medication",
            "Repeat blood pressure and assess symptoms",
            92,
            ReviewStatus.AI_SUGGESTED,
        ),
        _highlight(
            UUID("60000000-0000-4000-8000-000000000003"),
            doctor_summary,
            "Follow-up blood pressure check remains unresolved",
            "Time-sensitive follow-up task has no completion record",
            "Assign the blood-pressure follow-up",
            88,
            ReviewStatus.NEEDS_REVIEW,
        ),
    ]
    for highlight in highlights:
        repository.add_highlight(highlight)

    if repository.get_section(patient.id, "plan") is None:
        repository.save_section(
            SectionState(
                patient_id=patient.id,
                clinic_id=patient.clinic_id,
                section="plan",
                owner_role=Role.CLINICIAN,
                content=(
                    "Hold morning lisinopril pending review. Repeat blood pressure within "
                    "48 hours and reassess dizziness."
                ),
                version=1,
            ),
            SectionRevision(
                section="plan",
                version=1,
                content=(
                    "Hold morning lisinopril pending review. Repeat blood pressure within "
                    "48 hours and reassess dizziness."
                ),
                changed_by=DEMO_CLINICIAN_ID,
                operation="seed",
            ),
        )
