from nightingale.domain.models import (
    EntryOrigin,
    EntryType,
    Highlight,
    ProvenanceSource,
    ReviewStatus,
    Role,
    SourceSpan,
    TimelineEntry,
)


def test_highlight_pointer_resolves_to_timeline_span(repository, patient_id, clinic_id):
    entry = repository.add_entry(
        TimelineEntry(
            patient_id=patient_id,
            clinic_id=clinic_id,
            author_role=Role.SYSTEM,
            author_id=None,
            type=EntryType.AI_NURSE_CONSULT_SUMMARY,
            title="Synthetic nurse consultation",
            content="Patient reports dizziness after medication.",
            origin=EntryOrigin(
                source=ProvenanceSource.NURSE_CONSULT,
                source_id="test-nurse-consult",
                source_label="Synthetic nurse consultation",
            ),
        )
    )
    highlight = repository.add_highlight(
        Highlight(
            patient_id=patient_id,
            text="dizziness",
            risk_reason="New symptom after medication",
            suggested_action="Review medication timing",
            priority=90,
            status=ReviewStatus.AI_SUGGESTED,
            provenance_pointer=SourceSpan(entry_id=entry.id, start=16, end=25),
        )
    )
    source = repository.entries[highlight.provenance_pointer.entry_id]
    span = highlight.provenance_pointer
    assert source.content[span.start : span.end] == highlight.text
