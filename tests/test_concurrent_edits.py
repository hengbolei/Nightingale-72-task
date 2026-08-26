import pytest

from nightingale.services.care_notes import ConcurrentEditError


def test_different_sections_do_not_overwrite_each_other(service, clinician, patient_id):
    assessment = service.update_section(clinician, patient_id, "assessment", "Stable", 0)
    plan = service.update_section(clinician, patient_id, "plan", "Follow up", 0)
    assert assessment.content == "Stable"
    assert plan.content == "Follow up"


def test_stale_same_section_edit_is_rejected(service, staff, patient_id):
    service.update_section(staff, patient_id, "handoff", "First edit", 0)
    with pytest.raises(ConcurrentEditError):
        service.update_section(staff, patient_id, "handoff", "Stale edit", 0)
