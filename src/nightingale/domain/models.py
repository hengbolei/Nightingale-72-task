from __future__ import annotations

from datetime import UTC, date, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


def utc_now() -> datetime:
    return datetime.now(UTC)


class Role(StrEnum):
    PATIENT = "patient"
    STAFF = "staff"
    CLINICIAN = "clinician"
    ADMIN = "admin"
    SYSTEM = "system"


class EntryType(StrEnum):
    PATIENT_NOTE = "patient_note"
    STAFF_NOTE = "staff_note"
    CLINICIAN_NOTE = "clinician_note"
    AI_DOCTOR_CONSULT_SUMMARY = "ai_doctor_consult_summary"
    AI_NURSE_CONSULT_SUMMARY = "ai_nurse_consult_summary"
    AI_PATIENT_SESSION_SUMMARY = "ai_patient_session_summary"
    SYSTEM_EVENT = "system_event"


class ReviewStatus(StrEnum):
    AI_SUGGESTED = "ai_suggested"
    CLINICIAN_CONFIRMED = "clinician_confirmed"
    NEEDS_REVIEW = "needs_review"
    REJECTED = "rejected"


class ProvenanceSource(StrEnum):
    MANUAL_ENTRY = "manual_entry"
    PATIENT_SESSION = "patient_session"
    DOCTOR_CONSULT = "doctor_consult"
    NURSE_CONSULT = "nurse_consult"


class Actor(BaseModel):
    id: UUID
    role: Role
    clinic_id: UUID


class Patient(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    clinic_id: UUID
    display_name: str = Field(min_length=1, max_length=120)
    date_of_birth: date
    medical_record_number: str = Field(min_length=1, max_length=40)
    pronouns: str | None = Field(default=None, max_length=40)
    synthetic: Literal[True] = True


class ProvenancePointer(BaseModel):
    entry_id: UUID
    start: int = Field(ge=0)
    end: int = Field(gt=0)

    @model_validator(mode="after")
    def validate_span(self) -> ProvenancePointer:
        if self.end <= self.start:
            raise ValueError("provenance end must be greater than start")
        return self


# Backwards-compatible domain name used by the initial test scaffold.
SourceSpan = ProvenancePointer


class EntryOrigin(BaseModel):
    source: ProvenanceSource
    source_id: str = Field(min_length=1, max_length=120)
    source_label: str = Field(min_length=1, max_length=160)


class TimelineEntry(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    patient_id: UUID
    clinic_id: UUID
    author_role: Role
    author_id: UUID | None
    timestamp: datetime = Field(default_factory=utc_now)
    type: EntryType
    title: str = Field(min_length=1, max_length=160)
    content: str
    origin: EntryOrigin
    review_status: ReviewStatus | None = None
    internal: bool = True


class Highlight(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    patient_id: UUID
    text: str
    risk_reason: str
    suggested_action: str = Field(min_length=1, max_length=240)
    priority: int = Field(ge=0, le=100)
    status: ReviewStatus
    provenance_pointer: ProvenancePointer
    created_at: datetime = Field(default_factory=utc_now)


class PatientDetailResponse(BaseModel):
    patient: Patient
    highlights: list[Highlight]
    entries: list[TimelineEntry]


class SectionRevision(BaseModel):
    section: str
    version: int = Field(ge=1)
    content: str
    changed_by: UUID
    changed_at: datetime = Field(default_factory=utc_now)
    operation: str = "edit"


class SectionState(BaseModel):
    patient_id: UUID
    clinic_id: UUID
    section: str
    owner_role: Role
    content: str
    version: int = Field(ge=1)


class HealthResponse(BaseModel):
    status: str
    service: str
