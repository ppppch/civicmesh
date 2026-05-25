from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/ask", tags=["ask"])


class AskRequest(BaseModel):
    question: str = Field(min_length=8, max_length=500)


class AskResponse(BaseModel):
    question: str
    status: str
    plan: list[str]
    note: str


@router.post("", response_model=AskResponse, summary="Create a first-pass analysis plan")
def ask_nyc(payload: AskRequest) -> AskResponse:
    # Deterministic placeholder for Phase 1 planning pipeline.
    plan = [
        "Retrieve candidate datasets by topic, geography, and time signals",
        "Generate joins and aggregation strategy",
        "Queue verification work-units for ranking and claim checks",
        "Return reproducible insight card artifact",
    ]

    return AskResponse(
        question=payload.question,
        status="planned",
        plan=plan,
        note="Planner is currently stubbed and will be replaced by recipe compiler.",
    )
