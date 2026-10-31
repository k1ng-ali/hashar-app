from fastapi import APIRouter, Depends, status

from app.deps.auth import require_platform_admin
from app.deps.services import get_pricing_service
from app.schemas.pricing import PlanDiscountIn, PlanDiscountOut, PlanPriceIn, PlanPriceOut, PricedPlan, PricingOut
from app.schemas.user import CurrentUser
from app.services.pricing_service import PricingService

router = APIRouter(prefix="/pricing", tags=["Admin • Pricing"])


@router.get("/", response_model=PricingOut)
async def get_pricing(
    user: CurrentUser = Depends(require_platform_admin),
    service: PricingService = Depends(get_pricing_service),
):
    return await service.overview()


@router.put("/prices/{plan}", response_model=PlanPriceOut)
async def set_plan_price(
    plan: PricedPlan,
    payload: PlanPriceIn,
    user: CurrentUser = Depends(require_platform_admin),
    service: PricingService = Depends(get_pricing_service),
):
    return await service.set_price(plan=plan, price_tjs=payload.price_tjs, admin_id=user.id)


# ─── Скидки и промокоды ───────────────────────────────────────────────────────


@router.post("/discounts", response_model=PlanDiscountOut, status_code=status.HTTP_201_CREATED)
async def create_discount(
    payload: PlanDiscountIn,
    user: CurrentUser = Depends(require_platform_admin),
    service: PricingService = Depends(get_pricing_service),
):
    return await service.create_discount(payload=payload, admin_id=user.id)


@router.put("/discounts/{discount_id}", response_model=PlanDiscountOut)
async def update_discount(
    discount_id: int,
    payload: PlanDiscountIn,
    user: CurrentUser = Depends(require_platform_admin),
    service: PricingService = Depends(get_pricing_service),
):
    return await service.update_discount(discount_id=discount_id, payload=payload, admin_id=user.id)


@router.delete("/discounts/{discount_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_discount(
    discount_id: int,
    user: CurrentUser = Depends(require_platform_admin),
    service: PricingService = Depends(get_pricing_service),
):
    await service.delete_discount(discount_id=discount_id, admin_id=user.id)
