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

const IMAGE_EXTENSIONS: Record<string, string> = {
  'image/png': 'png',
  'image/jpeg': 'jpg',
  'image/webp': 'webp',
  'image/svg+xml': 'svg',
}

/**
 * Сохраняет чек как файл: data URL (демо-чек) или подписанную ссылку на хранилище.
 * Ссылку на другой домен атрибут download не скачивает — поэтому файл сначала загружается
 * (нужен CORS бакета). В Android-приложении — через «Поделиться».
 */
export async function downloadImage(src: string, basename: string) {
  if (src.startsWith('data:')) {
    const type = src.slice(5, src.search(/[;,]/))
    const filename = `${basename}.${IMAGE_EXTENSIONS[type] ?? 'jpg'}`
    if (Capacitor.isNativePlatform()) {
      await shareNative(dataUrlToBase64(src), filename)
      return
    }
    clickDownloadLink(src, filename)
    return
  }
  // no-store: иначе браузер может отдать картинку из кеша <img> — без CORS-заголовков, и fetch упадёт
  const response = await fetch(src, { cache: 'no-store' })
  if (!response.ok) throw new Error(`Download failed: ${response.status}`)
  const blob = await response.blob()
  await downloadBlob(blob, `${basename}.${IMAGE_EXTENSIONS[blob.type] ?? 'jpg'}`)
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

// Чек сжимаем до разумного размера: текст на скриншоте читается, файл — 100–400 КБ
const RECEIPT_MAX_SIDE = 1600
const RECEIPT_QUALITY = 0.8

/**
 * Фото или скриншот чека → WebP (или JPEG) не больше RECEIPT_MAX_SIDE по большей стороне.
 * Перерисовка через canvas заодно убирает EXIF — с геопозицией и моделью телефона.
 * Бросает ошибку, если браузер не смог прочитать картинку (например, HEIC вне Safari).
 */
export async function compressImage(file: File): Promise<Blob> {
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

  const webp = await canvasToBlob(canvas, 'image/webp')
  // Браузер без кодировщика WebP (часть версий Safari) молча отдаёт PNG — тогда JPEG
  return webp.type === 'image/webp' ? webp : canvasToBlob(canvas, 'image/jpeg')
}

function canvasToBlob(canvas: HTMLCanvasElement, type: string): Promise<Blob> {
  return new Promise((resolve, reject) => {
    canvas.toBlob((blob) => (blob ? resolve(blob) : reject(new Error('Canvas encoding failed'))), type, RECEIPT_QUALITY)
  })
}
