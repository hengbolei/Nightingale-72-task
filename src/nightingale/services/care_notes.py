import re
from difflib import unified_diff
from uuid import UUID

from nightingale.domain.models import (
    Actor,
    AuditEvent,
    Comment,
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
            sections: list[SectionState] = []
            comments: list[Comment] = []
        else:
            highlights = self.repository.list_highlights(patient_id)
            sections = self.repository.list_sections(patient_id, actor.clinic_id)
            comments = self.repository.list_comments(patient_id, actor.clinic_id)
        return PatientDetailResponse(
            patient=patient,
            highlights=highlights,
            entries=entries,
            sections=sections,
            comments=comments,
        )

    def add_comment(
        self,
        actor: Actor,
        patient_id: UUID,
        content: str,
        assigned_to: Role | None = None,
        parent_id: UUID | None = None,
    ) -> Comment:
        self._require_internal_collaborator(actor)
        if self.repository.get_patient(patient_id, actor.clinic_id) is None:
            raise PatientNotFoundError("patient not found in actor's clinic")
        mentions = [
            role
            for role in (Role.STAFF, Role.CLINICIAN, Role.ADMIN)
            if re.search(rf"(?<!\w)@{role.value}\b", content, flags=re.IGNORECASE)
        ]
        if assigned_to is Role.PATIENT or assigned_to is Role.SYSTEM:
            raise AccessDeniedError("comments can only be assigned to an internal care role")
        if parent_id is not None:
            parent = self.repository.get_comment(parent_id)
            if (
                parent is None
                or parent.patient_id != patient_id
                or parent.clinic_id != actor.clinic_id
            ):
                raise LookupError("parent comment does not exist")
        return self.repository.add_comment(
            Comment(
                patient_id=patient_id,
                clinic_id=actor.clinic_id,
                author_id=actor.id,
                author_role=actor.role,
                parent_id=parent_id,
                content=content,
                mentions=mentions,
                assigned_to=assigned_to,
            )
        )

    def set_comment_resolved(
        self, actor: Actor, patient_id: UUID, comment_id: UUID, resolved: bool
    ) -> Comment:
        self._require_internal_collaborator(actor)
        comment = self.repository.get_comment(comment_id)
        if (
            comment is None
            or comment.patient_id != patient_id
            or comment.clinic_id != actor.clinic_id
        ):
            raise LookupError("comment does not exist")
        from nightingale.domain.models import utc_now

        updated = comment.model_copy(
            update={
                "resolved": resolved,
                "resolved_at": utc_now() if resolved else None,
                "resolved_by": actor.id if resolved else None,
            }
        )
        return self.repository.save_comment(updated)

    def list_revisions(self, actor: Actor, patient_id: UUID, section: str) -> list[SectionRevision]:
        self._require_internal_collaborator(actor)
        current = self.repository.get_section(patient_id, section)
        if current is None or current.clinic_id != actor.clinic_id:
            raise LookupError("section does not exist")
        return self.repository.list_revisions(patient_id, section)

    @staticmethod
    def _require_internal_collaborator(actor: Actor) -> None:
        if actor.role not in {Role.STAFF, Role.CLINICIAN, Role.ADMIN}:
            raise AccessDeniedError("internal collaboration requires a care-team role")

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
            diff="\n".join(
                unified_diff(
                    (current.content if current else "").splitlines(),
                    content.splitlines(),
                    fromfile=f"{section}@{current_version}",
                    tofile=f"{section}@{next_version}",
                    lineterm="",
                )
            ),
        )
        saved = self.repository.save_section(state, revision)
        self.repository.add_audit_event(
            AuditEvent(
                patient_id=patient_id,
                clinic_id=actor.clinic_id,
                resource="section",
                resource_id=section,
                version=next_version,
                operation="edit",
                changed_by=actor.id,
            )
        )
        return saved

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
        self.repository.audit_events[-1] = self.repository.audit_events[-1].model_copy(
            update={"operation": "revert"}
        )
        return state

    def list_audit_events(self, actor: Actor, patient_id: UUID) -> list[AuditEvent]:
        self._require_internal_collaborator(actor)
        if self.repository.get_patient(patient_id, actor.clinic_id) is None:
            raise PatientNotFoundError("patient not found in actor's clinic")
        return self.repository.list_audit_events(patient_id, actor.clinic_id)
