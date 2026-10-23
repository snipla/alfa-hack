from fastapi import APIRouter, HTTPException

from app.schemas.prediction import CreditScoringFeatures, PredictionResult
from app.shared.dependencies import ModelService
from app.shared.dependencies.auth import RequireAuth

router = APIRouter(prefix="/predict", tags=["model"])


@router.post("/request", response_model=PredictionResult)
async def predict_req(
    _: RequireAuth, serv: ModelService, data: CreditScoringFeatures
) -> PredictionResult:
    try:
        return await serv.predict_one_async(data, log_transformed=False)
    except Exception:
        raise HTTPException(
            detail="While computing an error was occured", status_code=500
        )
