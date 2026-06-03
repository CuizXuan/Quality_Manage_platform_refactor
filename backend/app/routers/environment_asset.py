from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.environment_asset import EnvironmentCreate, EnvironmentResponse, RenderRequestPayload, RenderRequestResponse
from app.services.environment_service import EnvironmentService

router = APIRouter(prefix="/api/environments", tags=["environment"])


@router.get("", response_model=list[EnvironmentResponse])
def list_environments(project_id: int | None = None, db: Session = Depends(get_db)):
    return EnvironmentService(db).list_environments(project_id=project_id)


@router.post("", response_model=EnvironmentResponse)
def create_environment(data: EnvironmentCreate, db: Session = Depends(get_db)):
    return EnvironmentService(db).create_environment(data.model_dump())


@router.post("/render", response_model=RenderRequestResponse)
def render_request(data: RenderRequestPayload, db: Session = Depends(get_db)):
    return EnvironmentService(db).render_request(data.model_dump())
