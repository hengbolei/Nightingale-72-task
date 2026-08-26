def test_revision_increments_and_revert_restores_content(
    service, repository, clinician, patient_id
):
    first = service.update_section(clinician, patient_id, "plan", "Initial plan", 0)
    second = service.update_section(clinician, patient_id, "plan", "Updated plan", first.version)
    reverted = service.revert_section(clinician, patient_id, "plan", first.version)

    assert second.version == 2
    assert reverted.version == 3
    assert reverted.content == "Initial plan"
    audit = repository.list_revisions(patient_id, "plan")
    assert audit[-1].changed_by == clinician.id
    assert audit[-1].operation == "revert"
