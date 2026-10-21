import { http } from '@/shared/api/http.ts'

// Фото чека грузится отдельно от формы: в ответ — ключ, он уходит в receipt_image(s) взноса или расхода
const UPLOAD_TIMEOUT_MS = 60_000

export const uploadReceipt = (fundId: number, image: Blob) => {
  const form = new FormData()
  form.append('file', image, `receipt.${image.type.split('/')[1] ?? 'jpg'}`)
  return http.post<{ key: string }>(`/funds/${fundId}/uploads/receipt`, form, { timeout: UPLOAD_TIMEOUT_MS })
}
