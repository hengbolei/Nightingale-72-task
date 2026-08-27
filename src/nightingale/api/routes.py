from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException

from nightingale.data.seed import seed_demo_data
from nightingale.domain.models import (
    Actor,
    AuditEvent,
    Comment,
    CommentCreateRequest,
    CommentResolveRequest,
    HealthResponse,
    Highlight,
    HighlightCreateRequest,
    HighlightUpdateRequest,
    PatientDetailResponse,
    Role,
    SectionRevertRequest,
    SectionRevision,
    SectionState,
    SectionUpdateRequest,
    TimelineEntry,
    TimelineEntryCreateRequest,
)
from nightingale.repositories.memory import InMemoryCareNoteRepository
from nightingale.services.care_notes import (
    CareNoteService,
    ConcurrentEditError,
    PatientNotFoundError,
)

router = APIRouter(prefix="/api")
repository = InMemoryCareNoteRepository()
seed_demo_data(repository)
service = CareNoteService(repository)


def current_actor(
    x_actor_id: Annotated[UUID, Header()],
    x_actor_role: Annotated[Role, Header()],
    x_clinic_id: Annotated[UUID, Header()],
) -> Actor:
    # Header auth is a development seam. Replace it with verified identity middleware.
    return Actor(id=x_actor_id, role=x_actor_role, clinic_id=x_clinic_id)


ActorDependency = Annotated[Actor, Depends(current_actor)]


def translate_service_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PatientNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PermissionError):
        return HTTPException(status_code=403, detail=str(exc))
    if isinstance(exc, ConcurrentEditError):
        return HTTPException(status_code=409, detail=str(exc))
    if isinstance(exc, ValueError):
        return HTTPException(status_code=422, detail=str(exc))
    return HTTPException(status_code=404, detail=str(exc))


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="nightingale-care-note")


@router.get("/patients/{patient_id}", response_model=PatientDetailResponse)
def patient_view(
    patient_id: UUID,
    actor: ActorDependency,
) -> PatientDetailResponse:
    try:
        return service.get_patient_view(actor, patient_id)
    except (PatientNotFoundError, PermissionError) as exc:
        raise translate_service_error(exc) from exc


@router.post("/patients/{patient_id}/comments", response_model=Comment, status_code=201)
def create_comment(
    patient_id: UUID, payload: CommentCreateRequest, actor: ActorDependency
) -> Comment:
    try:
        return service.add_comment(
            actor,
            patient_id,
            payload.content,
            payload.assigned_to,
            payload.parent_id,
        )
    except (PatientNotFoundError, PermissionError, LookupError) as exc:
        raise translate_service_error(exc) from exc


@router.post("/patients/{patient_id}/entries", response_model=TimelineEntry, status_code=201)
def create_timeline_entry(
    patient_id: UUID,
    payload: TimelineEntryCreateRequest,
    actor: ActorDependency,
) -> TimelineEntry:
    try:
        return service.create_manual_entry(actor, patient_id, payload.title, payload.content)
    except (PatientNotFoundError, PermissionError) as exc:
        raise translate_service_error(exc) from exc


@router.post("/patients/{patient_id}/highlights", response_model=Highlight, status_code=201)
def create_highlight(
    patient_id: UUID,
    payload: HighlightCreateRequest,
    actor: ActorDependency,
) -> Highlight:
    try:
        return service.create_highlight(actor, patient_id, payload)
    except (PatientNotFoundError, LookupError, PermissionError, ValueError) as exc:
        raise translate_service_error(exc) from exc


@router.patch("/patients/{patient_id}/comments/{comment_id}", response_model=Comment)
def resolve_comment(
    patient_id: UUID,
    comment_id: UUID,
    payload: CommentResolveRequest,
    actor: ActorDependency,
) -> Comment:
    try:
        return service.set_comment_resolved(actor, patient_id, comment_id, payload.resolved)
    except (LookupError, PermissionError) as exc:
        raise translate_service_error(exc) from exc


@router.patch("/patients/{patient_id}/highlights/{highlight_id}", response_model=Highlight)
def update_highlight(
    patient_id: UUID,
    highlight_id: UUID,
    payload: HighlightUpdateRequest,
    actor: ActorDependency,
) -> Highlight:
    try:
        return service.update_highlight(actor, patient_id, highlight_id, payload)
    except (
        PatientNotFoundError,
        LookupError,
        PermissionError,
        ConcurrentEditError,
    ) as exc:
        raise translate_service_error(exc) from exc


@router.put("/patients/{patient_id}/sections/{section}", response_model=SectionState)
def update_section(
    patient_id: UUID,
    section: str,
    payload: SectionUpdateRequest,
    actor: ActorDependency,
) -> SectionState:
    try:
        service.get_patient_view(actor, patient_id)
        return service.update_section(
            actor, patient_id, section, payload.content, payload.expected_version
        )
    except (PatientNotFoundError, PermissionError, ConcurrentEditError) as exc:
        raise translate_service_error(exc) from exc


@router.get(
    "/patients/{patient_id}/sections/{section}/revisions",
    response_model=list[SectionRevision],
)
def section_revisions(
    patient_id: UUID, section: str, actor: ActorDependency
) -> list[SectionRevision]:
    try:
        return service.list_revisions(actor, patient_id, section)
    except (LookupError, PermissionError) as exc:
        raise translate_service_error(exc) from exc


@router.post("/patients/{patient_id}/sections/{section}/revert", response_model=SectionState)
def revert_section(
    patient_id: UUID,
    section: str,
    payload: SectionRevertRequest,
    actor: ActorDependency,
) -> SectionState:
    try:
        service.get_patient_view(actor, patient_id)
        return service.revert_section(actor, patient_id, section, payload.target_version)
    except (LookupError, PermissionError, ConcurrentEditError) as exc:
        raise translate_service_error(exc) from exc


@router.get("/patients/{patient_id}/audit", response_model=list[AuditEvent])
def patient_audit(patient_id: UUID, actor: ActorDependency) -> list[AuditEvent]:
    try:
        return service.list_audit_events(actor, patient_id)
    except (PatientNotFoundError, PermissionError) as exc:
        raise translate_service_error(exc) from exc
