// src/features/funds/planSale.ts
import type { DiscountKind } from './types.ts'

type Translate = (key: string, params?: Record<string, unknown>) => string

/** «−20%» или «−50 смн / мес». */
export function discountValueLabel(discount: { kind: DiscountKind; value: number }, t: Translate): string {
  return discount.kind === 'percent' ? `−${discount.value}%` : t('plans.saleFixed', { value: discount.value })
}
