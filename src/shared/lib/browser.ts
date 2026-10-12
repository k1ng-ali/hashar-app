/** Копирует текст в буфер; false — если браузер не дал доступ. */
export async function copyText(text: string): Promise<boolean> {
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return false
  }
}

// Сколько держать blob-ссылку живой: браузер начинает скачивание асинхронно
const REVOKE_DELAY_MS = 60_000

/** Сохраняет Blob как файл. */
export function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.rel = 'noopener'
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  link.remove()
  // Сразу отзывать ссылку нельзя: Safari, Firefox и мобильные браузеры тогда отменяют скачивание
  setTimeout(() => URL.revokeObjectURL(url), REVOKE_DELAY_MS)
}

/** Имя файла из заголовка Content-Disposition. */
export function filenameFromDisposition(header: string | undefined, fallback: string): string {
  const match = header?.match(/filename="?([^";]+)"?/)
  return match?.[1] ?? fallback
}

// Чек сжимаем до разумного размера: текст на скриншоте читается, а БД не раздувается
const RECEIPT_MAX_SIDE = 1600
const RECEIPT_QUALITY = 0.82

/**
 * Фото или скриншот чека → JPEG data URL не больше RECEIPT_MAX_SIDE по большей стороне.
 * Бросает ошибку, если браузер не смог прочитать картинку (например, HEIC вне Safari).
 */
export async function compressImage(file: File): Promise<string> {
  const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
  const scale = Math.min(1, RECEIPT_MAX_SIDE / Math.max(bitmap.width, bitmap.height))
  const canvas = document.createElement('canvas')
  canvas.width = Math.round(bitmap.width * scale)
  canvas.height = Math.round(bitmap.height * scale)

  const context = canvas.getContext('2d')
  if (!context) throw new Error('Canvas is not supported')
  // Белый фон: у PNG-скриншотов с прозрачностью в JPEG иначе будет чёрный фон
  context.fillStyle = '#ffffff'
  context.fillRect(0, 0, canvas.width, canvas.height)
  context.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
  bitmap.close()
  return canvas.toDataURL('image/jpeg', RECEIPT_QUALITY)
}
