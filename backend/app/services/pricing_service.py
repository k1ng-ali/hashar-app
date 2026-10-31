from dataclasses import dataclass
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.plans import discount_state, discounted_price
from app.enums import PLAN_MEMBER_LIMITS, DiscountStateEnum, PlanEnum, PromoStatusEnum
from app.models.plan_pricing import PlanDiscount
from app.repositories.audit_repo import AuditRepository
from app.repositories.pricing_repo import PricingRepository
from app.schemas.pricing import (
    PlanDiscountIn,
    PlanDiscountOut,
    PlanOptionOut,
    PlanPriceOut,
    PlanSaleOut,
    PricingOut,
    normalize_code,
)


@dataclass
class ResolvedPrice:
    """Итоговая цена тарифа за месяц для конкретной заявки."""

    list_price: int | None
    price: int | None
    discount: PlanDiscount | None = None
    promo_status: PromoStatusEnum = PromoStatusEnum.none

    @property
    def label(self) -> str | None:
        if self.discount is None:
            return None
        return self.discount.code or self.discount.title


def _discount_out(discount: PlanDiscount, uses: int) -> PlanDiscountOut:
    return PlanDiscountOut(
        id=discount.id,
        title=discount.title,
        code=discount.code,
        kind=discount.kind,
        value=discount.value,
        plans=discount.plans,
        starts_at=discount.starts_at,
        ends_at=discount.ends_at,
        max_uses=discount.max_uses,
        uses=uses,
        is_active=discount.is_active,
        state=discount_state(discount, uses),
        created_at=discount.created_at,
    )


class PricingService:
    """Цены платформы: прайс, распродажи и промокоды. Единственный источник цен для витрины и заявок."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = PricingRepository(db=db)
        self.audit = AuditRepository(db=db)

    # ─── Витрина ───────────────────────────────────────────────────────────────

    async def catalog(self) -> list[PlanOptionOut]:
        now = datetime.now(timezone.utc)
        prices = {row.plan: row.price_tjs for row in await self.repo.list_prices()}
        sales = await self.repo.list_running_sales(now)

        options = []
        for plan in PlanEnum:
            list_price = 0 if plan == PlanEnum.free else prices.get(plan.value)
            sale = self._best_sale(plan, list_price, sales) if list_price else None
            options.append(
                PlanOptionOut(
                    plan=plan,
                    member_limit=PLAN_MEMBER_LIMITS[plan],
                    price_tjs=discounted_price(list_price, sale.kind, sale.value) if sale else list_price,
                    list_price_tjs=list_price,
                    sale=(
                        PlanSaleOut(title=sale.title, kind=sale.kind, value=sale.value, ends_at=sale.ends_at)
                        if sale
                        else None
                    ),
                )
            )
        return options

    async def list_price(self, plan: PlanEnum) -> int | None:
        """Текущая цена тарифа без скидок. None — у тарифа нет цены в прайсе (individual)."""
        row = await self.repo.get_price(plan.value)
        return row.price_tjs if row else None

    # ─── Расчёт цены заявки ────────────────────────────────────────────────────

    async def resolve(
        self, plan: PlanEnum, fund_id: int, promo_code: str | None = None, for_update: bool = False
    ) -> ResolvedPrice:
        """
        Цена для заявки фонда: лучшая из распродажи и промокода, скидки не суммируются.

        for_update — при создании заявки: блокирует промокод, чтобы два фонда
        одновременно не заняли последнее применение.
        """
        code = normalize_code(promo_code) if promo_code else None
        list_price = await self.list_price(plan)
        promo = await self._valid_promo(code, plan, fund_id, for_update) if code else None
        if list_price is None:
            return ResolvedPrice(list_price=None, price=None)

        now = datetime.now(timezone.utc)
        sale = self._best_sale(plan, list_price, await self.repo.list_running_sales(now))
        sale_price = discounted_price(list_price, sale.kind, sale.value) if sale else list_price
        if promo is None:
            return ResolvedPrice(list_price=list_price, price=sale_price, discount=sale)

        promo_price = discounted_price(list_price, promo.kind, promo.value)
        if promo_price < sale_price:
            return ResolvedPrice(
                list_price=list_price, price=promo_price, discount=promo, promo_status=PromoStatusEnum.applied
            )
        return ResolvedPrice(
            list_price=list_price, price=sale_price, discount=sale, promo_status=PromoStatusEnum.not_better
        )

    async def _valid_promo(self, code: str, plan: PlanEnum, fund_id: int, for_update: bool) -> PlanDiscount:
        promo = await self.repo.get_by_code(code, for_update=for_update)
        if promo is None or not promo.is_active:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Promo code not found")
        uses = await self.repo.count_uses(promo.id)
        state = discount_state(promo, uses)
        if state == DiscountStateEnum.scheduled:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promo code is not active yet")
        if state == DiscountStateEnum.expired:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promo code has expired")
        if state == DiscountStateEnum.exhausted:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promo code usage limit reached")
        if plan.value not in promo.plans:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promo code is not valid for this plan")
        if await self.repo.count_uses(promo.id, fund_id=fund_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promo code was already used by this fund")
        return promo

    @staticmethod
    def _best_sale(plan: PlanEnum, list_price: int, sales: list[PlanDiscount]) -> PlanDiscount | None:
        matching = [sale for sale in sales if plan.value in sale.plans]
        return min(matching, key=lambda s: discounted_price(list_price, s.kind, s.value), default=None)

    # ─── Админ платформы ───────────────────────────────────────────────────────

    async def overview(self) -> PricingOut:
        uses = await self.repo.uses_by_discount()
        return PricingOut(
            prices=[PlanPriceOut.model_validate(row) for row in await self.repo.list_prices()],
            discounts=[_discount_out(d, uses.get(d.id, 0)) for d in await self.repo.list_discounts()],
        )

    async def set_price(self, plan: PlanEnum, price_tjs: int, admin_id: int) -> PlanPriceOut:
        row = await self.repo.get_price(plan.value, for_update=True)
        if row is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Plan price not found")

        old_price = row.price_tjs
        row.price_tjs = price_tjs
        row.updated_by_id = admin_id
        row.updated_at = datetime.now(timezone.utc)
        self._audit("pricing.price", admin_id, plan=plan.value, old_price=old_price, price=price_tjs)
        await self.db.commit()
        return PlanPriceOut.model_validate(row)

    async def create_discount(self, payload: PlanDiscountIn, admin_id: int) -> PlanDiscountOut:
        await self._ensure_code_free(payload.code)
        discount = await self.repo.create_discount(**self._fields(payload), created_by_id=admin_id)
        self._audit("pricing.discount_create", admin_id, entity_id=discount.id, **self._snapshot(discount))
        await self.db.commit()
        return _discount_out(discount, uses=0)

    async def update_discount(self, discount_id: int, payload: PlanDiscountIn, admin_id: int) -> PlanDiscountOut:
        discount = await self._get_discount_or_404(discount_id)
        if payload.code != discount.code:
            await self._ensure_code_free(payload.code)
        for field, value in self._fields(payload).items():
            setattr(discount, field, value)
        self._audit("pricing.discount_update", admin_id, entity_id=discount.id, **self._snapshot(discount))
        uses = await self.repo.count_uses(discount.id)
        await self.db.commit()
        return _discount_out(discount, uses=uses)

    async def delete_discount(self, discount_id: int, admin_id: int) -> None:
        """Удалить можно только неиспользованную скидку; использованную — выключить, история заявок сохранится."""
        discount = await self._get_discount_or_404(discount_id)
        if await self.repo.count_uses(discount.id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Discount was used, disable it instead")
        self._audit("pricing.discount_delete", admin_id, entity_id=discount.id, **self._snapshot(discount))
        await self.repo.delete_discount(discount)
        await self.db.commit()

    # ─── Helpers ───────────────────────────────────────────────────────────────

    async def _get_discount_or_404(self, discount_id: int) -> PlanDiscount:
        discount = await self.repo.get_discount(discount_id, for_update=True)
        if discount is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Discount not found")
        return discount

    async def _ensure_code_free(self, code: str | None) -> None:
        if code and await self.repo.get_by_code(code):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Promo code already exists")

    @staticmethod
    def _fields(payload: PlanDiscountIn) -> dict:
        fields = payload.model_dump()
        fields["kind"] = payload.kind.value
        fields["plans"] = sorted({plan.value for plan in payload.plans})
        return fields

    @staticmethod
    def _snapshot(discount: PlanDiscount) -> dict:
        return {
            "title": discount.title,
            "code": discount.code,
            "kind": discount.kind,
            "value": discount.value,
            "plans": discount.plans,
            "is_active": discount.is_active,
        }

    def _audit(self, action: str, admin_id: int, entity_id: int | None = None, **details) -> None:
        # Цены общие для платформы — запись журнала не привязана к фонду
        self.audit.add(
            fund_id=None, actor_id=admin_id, action=action, entity="pricing", entity_id=entity_id, details=details
        )
