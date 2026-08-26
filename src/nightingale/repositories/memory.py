from uuid import UUID

from nightingale.domain.models import (
    Highlight,
    Patient,
    SectionRevision,
    SectionState,
    TimelineEntry,
)


class InMemoryCareNoteRepository:
    """Development adapter; replace with a clinic-scoped database adapter."""

    def __init__(self) -> None:
        self.patients: dict[UUID, Patient] = {}
        self.entries: dict[UUID, TimelineEntry] = {}
        self.highlights: dict[UUID, Highlight] = {}
        self.sections: dict[tuple[UUID, str], SectionState] = {}
        self.revisions: dict[tuple[UUID, str], list[SectionRevision]] = {}

    def add_patient(self, patient: Patient) -> Patient:
        self.patients[patient.id] = patient
        return patient

    def get_patient(self, patient_id: UUID, clinic_id: UUID) -> Patient | None:
        patient = self.patients.get(patient_id)
        if patient is None or patient.clinic_id != clinic_id:
            return None
        return patient

    def add_entry(self, entry: TimelineEntry) -> TimelineEntry:
        self.entries[entry.id] = entry
        return entry

    def list_entries(self, patient_id: UUID, clinic_id: UUID) -> list[TimelineEntry]:
        return sorted(
            (
                item
                for item in self.entries.values()
                if item.patient_id == patient_id and item.clinic_id == clinic_id
            ),
            key=lambda item: item.timestamp,
            reverse=True,
        )

    def add_highlight(self, highlight: Highlight) -> Highlight:
        source = self.entries.get(highlight.provenance_pointer.entry_id)
        if source is None or source.patient_id != highlight.patient_id:
            raise ValueError("provenance_pointer must resolve to this patient's timeline")
        if highlight.provenance_pointer.end > len(source.content):
            raise ValueError("provenance span is outside the source entry")
        self.highlights[highlight.id] = highlight
        return highlight

    def list_highlights(self, patient_id: UUID) -> list[Highlight]:
        return sorted(
            (item for item in self.highlights.values() if item.patient_id == patient_id),
            key=lambda item: item.priority,
            reverse=True,
        )

    def get_section(self, patient_id: UUID, section: str) -> SectionState | None:
        return self.sections.get((patient_id, section))

    def save_section(self, state: SectionState, revision: SectionRevision) -> SectionState:
        key = (state.patient_id, state.section)
        self.sections[key] = state
        self.revisions.setdefault(key, []).append(revision)
        return state

    def list_revisions(self, patient_id: UUID, section: str) -> list[SectionRevision]:
        return list(self.revisions.get((patient_id, section), []))
