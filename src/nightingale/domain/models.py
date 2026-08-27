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


class ActionStatus(StrEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


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
    patient_instruction: str | None = Field(default=None, max_length=500)
    priority: int = Field(ge=0, le=100)
    status: ReviewStatus
    provenance_pointer: ProvenancePointer
    assigned_to: Role | None = None
    action_status: ActionStatus = ActionStatus.OPEN
    disposition_note: str | None = Field(default=None, max_length=1000)
    version: int = Field(default=1, ge=1)
    updated_by: UUID | None = None
    updated_at: datetime | None = None
    completed_by: UUID | None = None
    completed_at: datetime | None = None
    created_at: datetime = Field(default_factory=utc_now)


class PatientAction(BaseModel):
    title: str
    instruction: str
    action_status: ActionStatus
    updated_at: datetime


class Comment(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    patient_id: UUID
    clinic_id: UUID
    author_id: UUID
    author_role: Role
    parent_id: UUID | None = None
    content: str = Field(min_length=1, max_length=1000)
    mentions: list[Role] = Field(default_factory=list)
    assigned_to: Role | None = None
    resolved: bool = False
    created_at: datetime = Field(default_factory=utc_now)
    resolved_at: datetime | None = None
    resolved_by: UUID | None = None
    version: int = Field(default=1, ge=1)


class PatientDetailResponse(BaseModel):
    patient: Patient
    highlights: list[Highlight]
    entries: list[TimelineEntry]
    patient_actions: list[PatientAction] = Field(default_factory=list)
    sections: list[SectionState] = Field(default_factory=list)
    comments: list[Comment] = Field(default_factory=list)


class SectionRevision(BaseModel):
    section: str
    version: int = Field(ge=1)
    content: str
    changed_by: UUID
    changed_at: datetime = Field(default_factory=utc_now)
    operation: str = "edit"
    diff: str | None = None


class SectionState(BaseModel):
    patient_id: UUID
    clinic_id: UUID
    section: str
    owner_role: Role
    content: str
    version: int = Field(ge=1)


class AuditEvent(BaseModel):
    patient_id: UUID
    clinic_id: UUID
    resource: str
    resource_id: str
    version: int = Field(ge=1)
    operation: str
    changed_by: UUID
    changed_at: datetime = Field(default_factory=utc_now)


class CommentCreateRequest(BaseModel):
    content: str = Field(min_length=1, max_length=1000)
    assigned_to: Role | None = None
    parent_id: UUID | None = None


class CommentResolveRequest(BaseModel):
    resolved: bool


class TimelineEntryCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    content: str = Field(min_length=1, max_length=10000)


class HighlightCreateRequest(BaseModel):
    entry_id: UUID
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    risk_reason: str = Field(min_length=1, max_length=500)
    suggested_action: str = Field(min_length=1, max_length=240)
    patient_instruction: str | None = Field(default=None, max_length=500)
    priority: int = Field(ge=0, le=100)
    status: ReviewStatus = ReviewStatus.NEEDS_REVIEW
    assigned_to: Role | None = None

    @model_validator(mode="after")
    def validate_span(self) -> HighlightCreateRequest:
        if self.end <= self.start:
            raise ValueError("highlight end must be greater than start")
        return self


class HighlightUpdateRequest(BaseModel):
    expected_version: int = Field(ge=1)
    status: ReviewStatus | None = None
    assigned_to: Role | None = None
    action_status: ActionStatus | None = None
    disposition_note: str | None = Field(default=None, max_length=1000)


class SectionUpdateRequest(BaseModel):
    content: str = Field(max_length=10000)
    expected_version: int = Field(ge=0)


class SectionRevertRequest(BaseModel):
    target_version: int = Field(ge=1)


class HealthResponse(BaseModel):
    status: str
    service: str
