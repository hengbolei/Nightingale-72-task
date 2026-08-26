from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Header, HTTPException

from nightingale.data.seed import seed_demo_data
from nightingale.domain.models import Actor, HealthResponse, PatientDetailResponse, Role
from nightingale.repositories.memory import InMemoryCareNoteRepository
from nightingale.services.care_notes import CareNoteService, PatientNotFoundError

router = APIRouter(prefix="/api")
repository = InMemoryCareNoteRepository()
seed_demo_data(repository)
service = CareNoteService(repository)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="nightingale-care-note")


@router.get("/patients/{patient_id}", response_model=PatientDetailResponse)
def patient_view(
    patient_id: UUID,
    x_actor_id: Annotated[UUID, Header()],
    x_actor_role: Annotated[Role, Header()],
    x_clinic_id: Annotated[UUID, Header()],
) -> PatientDetailResponse:
    # Header auth is a development seam. Replace it with verified identity middleware.
    actor = Actor(id=x_actor_id, role=x_actor_role, clinic_id=x_clinic_id)
    try:
        return service.get_patient_view(actor, patient_id)
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
