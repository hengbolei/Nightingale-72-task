from uuid import UUID

from nightingale.domain.models import (
    Actor,
    EntryType,
    Highlight,
    PatientDetailResponse,
    Role,
    SectionRevision,
    SectionState,
    TimelineEntry,
)
from nightingale.repositories.memory import InMemoryCareNoteRepository

AI_ENTRY_TYPES = {
    EntryType.AI_DOCTOR_CONSULT_SUMMARY,
    EntryType.AI_NURSE_CONSULT_SUMMARY,
    EntryType.AI_PATIENT_SESSION_SUMMARY,
}


class AccessDeniedError(PermissionError):
    pass


class ConcurrentEditError(RuntimeError):
    pass


class PatientNotFoundError(LookupError):
    pass


class CareNoteService:
    def __init__(self, repository: InMemoryCareNoteRepository) -> None:
        self.repository = repository

    def get_patient_view(self, actor: Actor, patient_id: UUID) -> PatientDetailResponse:
        patient = self.repository.get_patient(patient_id, actor.clinic_id)
        if patient is None:
            raise PatientNotFoundError("patient not found in actor's clinic")
        if actor.role is Role.PATIENT and actor.id != patient_id:
            raise AccessDeniedError("patients can only access their own record")
        entries = self.repository.list_entries(patient_id, actor.clinic_id)
        if actor.role is Role.PATIENT:
            entries = [
                item for item in entries if not item.internal and item.type not in AI_ENTRY_TYPES
            ]
            highlights: list[Highlight] = []
        else:
            highlights = self.repository.list_highlights(patient_id)
        return PatientDetailResponse(
            patient=patient,
            highlights=highlights,
            entries=entries,
        )

    def add_entry(self, actor: Actor, entry: TimelineEntry) -> TimelineEntry:
        if actor.clinic_id != entry.clinic_id:
            raise AccessDeniedError("cross-clinic writes are forbidden")
        ownership = {
            EntryType.STAFF_NOTE: Role.STAFF,
            EntryType.CLINICIAN_NOTE: Role.CLINICIAN,
            EntryType.PATIENT_NOTE: Role.PATIENT,
        }
        required_role = ownership.get(entry.type)
        if required_role is not None and actor.role is not required_role:
            raise AccessDeniedError(f"{actor.role} cannot write {entry.type}")
        if entry.author_role is not actor.role or entry.author_id != actor.id:
            raise AccessDeniedError("entry authorship must match the authenticated actor")
        return self.repository.add_entry(entry)

    def update_section(
        self,
        actor: Actor,
        patient_id: UUID,
        section: str,
        content: str,
        expected_version: int,
    ) -> SectionState:
        current = self.repository.get_section(patient_id, section)
        owner = current.owner_role if current else actor.role
        clinic_id = current.clinic_id if current else actor.clinic_id
        if clinic_id != actor.clinic_id:
            raise AccessDeniedError("cross-clinic writes are forbidden")
        if actor.role is not owner:
            raise AccessDeniedError(f"{actor.role} cannot modify a {owner} section")
        current_version = current.version if current else 0
        if expected_version != current_version:
            raise ConcurrentEditError(
                f"expected version {expected_version}, current version is {current_version}"
            )
        next_version = current_version + 1
        state = SectionState(
            patient_id=patient_id,
            clinic_id=actor.clinic_id,
            section=section,
            owner_role=owner,
            content=content,
            version=next_version,
        )
        revision = SectionRevision(
            section=section,
            version=next_version,
            content=content,
            changed_by=actor.id,
        )
        return self.repository.save_section(state, revision)

    def revert_section(
        self, actor: Actor, patient_id: UUID, section: str, target_version: int
    ) -> SectionState:
        current = self.repository.get_section(patient_id, section)
        if current is None:
            raise LookupError("section does not exist")
        target = next(
            (
                revision
                for revision in self.repository.list_revisions(patient_id, section)
                if revision.version == target_version
            ),
            None,
        )
        if target is None:
            raise LookupError("target revision does not exist")
        state = self.update_section(
            actor, patient_id, section, target.content, expected_version=current.version
        )
        revisions = self.repository.revisions[(patient_id, section)]
        revisions[-1] = revisions[-1].model_copy(update={"operation": "revert"})
        return state
