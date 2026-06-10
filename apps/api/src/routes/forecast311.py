from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.services.forecast311 import ForecastRow, run_forecasting_pipeline

router = APIRouter(prefix="/forecast311", tags=["forecast311"])


class ForecastInputRow(BaseModel):
    zipcode: str = Field(min_length=3, max_length=12)
    complaint_type: str = Field(min_length=2, max_length=120)
    year: int = Field(ge=2010, le=2100)
    complaint_count: float = Field(ge=0)


class ForecastRequest(BaseModel):
    rows: list[ForecastInputRow] = Field(min_length=1)
    source_year: int = Field(default=2025, ge=2010, le=2100)
    target_year: int = Field(default=2026, ge=2011, le=2101)
    embedding_dim: int = Field(default=16, ge=4, le=128)


@router.post("/train-and-predict", summary="Train 311 ZIP complaint models and predict next-year counts")
def train_and_predict(payload: ForecastRequest) -> dict[str, object]:
    try:
        result = run_forecasting_pipeline(
            rows=[
                ForecastRow(
                    zipcode=item.zipcode,
                    complaint_type=item.complaint_type,
                    year=item.year,
                    complaint_count=item.complaint_count,
                )
                for item in payload.rows
            ],
            source_year=payload.source_year,
            target_year=payload.target_year,
            embedding_dim=payload.embedding_dim,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return result
