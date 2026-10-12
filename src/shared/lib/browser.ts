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

/** Читает файл как data URL (для чеков). */
export function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(reader.result as string)
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}
