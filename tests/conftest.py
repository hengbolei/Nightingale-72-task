from uuid import uuid4

import pytest

from nightingale.domain.models import Actor, Role
from nightingale.repositories.memory import InMemoryCareNoteRepository
from nightingale.services.care_notes import CareNoteService


@pytest.fixture
def clinic_id():
    return uuid4()


@pytest.fixture
def patient_id():
    return uuid4()


@pytest.fixture
def staff(clinic_id):
    return Actor(id=uuid4(), role=Role.STAFF, clinic_id=clinic_id)


@pytest.fixture
def clinician(clinic_id):
    return Actor(id=uuid4(), role=Role.CLINICIAN, clinic_id=clinic_id)


@pytest.fixture
def repository():
    return InMemoryCareNoteRepository()


@pytest.fixture
def service(repository):
    return CareNoteService(repository)
