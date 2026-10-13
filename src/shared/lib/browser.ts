import { Capacitor } from '@capacitor/core'

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

/**
 * Сохраняет Blob как файл. В Android-приложении WebView не скачивает файлы по ссылке —
 * там файл открывается в системном меню «Поделиться» (сохранить, отправить в мессенджер).
 */
export async function downloadBlob(blob: Blob, filename: string) {
  if (Capacitor.isNativePlatform()) {
    await shareNative(await blobToBase64(blob), filename)
    return
  }
  const url = URL.createObjectURL(blob)
  clickDownloadLink(url, filename)
  // Сразу отзывать ссылку нельзя: Safari, Firefox и мобильные браузеры тогда отменяют скачивание
  setTimeout(() => URL.revokeObjectURL(url), REVOKE_DELAY_MS)
}

/** Сохраняет картинку из data URL (чек) как файл. В Android-приложении — через «Поделиться». */
export async function downloadDataUrl(dataUrl: string, filename: string) {
  if (Capacitor.isNativePlatform()) {
    await shareNative(dataUrlToBase64(dataUrl), filename)
    return
  }
  clickDownloadLink(dataUrl, filename)
}

function clickDownloadLink(href: string, filename: string) {
  const link = document.createElement('a')
  link.href = href
  link.download = filename
  link.rel = 'noopener'
  link.style.display = 'none'
  document.body.appendChild(link)
  link.click()
  link.remove()
}

// ── Android ─────────────────────────────────────────────────────────────────
// Плагины грузятся только в приложении — в веб-сборку не попадают лишним кодом

async function shareNative(base64: string, filename: string) {
  const [{ Filesystem, Directory }, { Share }] = await Promise.all([
    import('@capacitor/filesystem'),
    import('@capacitor/share'),
  ])
  const { uri } = await Filesystem.writeFile({ path: filename, data: base64, directory: Directory.Cache })
  try {
    await Share.share({ files: [uri] })
  } catch (error) {
    // Пользователь закрыл меню «Поделиться» — это не ошибка
    if (error instanceof Error && /cancel/i.test(error.message)) return
    throw error
  }
}

function blobToBase64(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(dataUrlToBase64(reader.result as string))
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(blob)
  })
}

/** data:...;base64,XXX → XXX; текстовый data URL (SVG-чек) кодируется в base64 из UTF-8. */
function dataUrlToBase64(dataUrl: string): string {
  const comma = dataUrl.indexOf(',')
  const header = dataUrl.slice(0, comma)
  const payload = dataUrl.slice(comma + 1)
  if (header.endsWith(';base64')) return payload
  const bytes = new TextEncoder().encode(decodeURIComponent(payload))
  let binary = ''
  bytes.forEach((byte) => (binary += String.fromCharCode(byte)))
  return btoa(binary)
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
