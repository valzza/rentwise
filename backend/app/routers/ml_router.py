from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, require_role
from app.models.user_models import User
from app.schemas.ml_schemas import PriceEstimateRequest, PriceEstimateResponse
from app.repositories.mongo_repository import MongoRepository

router = APIRouter()


@router.post("/estimate-price", response_model=PriceEstimateResponse)
async def estimate_price(
    data: PriceEstimateRequest,
    request: Request,
    current_user: User = Depends(require_role("landlord", "admin")),
    db: AsyncSession = Depends(get_db),
):
    predictor = getattr(request.app.state, "predictor", None)
    if predictor is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML model not loaded. Run: python -m app.ml.train",
        )

    features = data.model_dump(exclude={"property_id"})
    result = predictor.predict(features)

    # Persist to PostgreSQL
    from app.models.domain_models import PriceEstimationLog
    from sqlalchemy import insert
    await db.execute(
        insert(PriceEstimationLog).values(
            property_id=data.property_id,
            user_id=current_user.id,
            input_features=features,
            predicted_price=result["suggested_price"],
        )
    )
    await db.commit()

    # Persist to MongoDB asynchronously
    mongo = MongoRepository()
    await mongo.log_prediction(
        property_id=data.property_id,
        features=features,
        prediction=result,
        model_version=result["model_version"],
    )

    return PriceEstimateResponse(**result)
