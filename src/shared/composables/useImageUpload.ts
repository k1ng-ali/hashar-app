import axios from 'axios'
import { onBeforeUnmount, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useFundsStore } from '@/features/funds/store.ts'
import { uploadReceipt } from '@/shared/api/uploads.ts'
import { compressImage } from '@/shared/lib/browser.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'

// Исходный файл может быть большим фото с камеры — перед загрузкой он сжимается
const MAX_FILE_SIZE = 20 * 1024 * 1024
// Предел после сжатия (backend принимает до 1,5 МБ, обычно выходит 100–400 КБ)
const MAX_UPLOAD_SIZE = 1.5 * 1024 * 1024

/**
 * Сжатие и загрузка фото (чек, фото расхода или сбора) в хранилище фонда.
 * upload() возвращает ключ для API или null — ошибку уже показали пользователю.
 * Превью — локальные blob-ссылки на сжатые файлы: previewOf(ключ).
 */
export function useImageUpload() {
  const { t } = useI18n()
  const headerStore = useHeaderStore()
  const fundsStore = useFundsStore()

  const uploading = ref(false)
  const previews = ref<Record<string, string>>({})

  function previewOf(value: string): string {
    // data: — демо-чек, https: — уже сохранённое фото (правка сбора), иначе ключ свежей загрузки
    return /^(data|https?):/.test(value) ? value : (previews.value[value] ?? '')
  }

  function forget(value: string) {
    const url = previews.value[value]
    if (!url) return
    URL.revokeObjectURL(url)
    const { [value]: _, ...rest } = previews.value
    previews.value = rest
  }

  onBeforeUnmount(() => Object.values(previews.value).forEach((url) => URL.revokeObjectURL(url)))

  async function upload(file: File): Promise<string | null> {
    if (file.size > MAX_FILE_SIZE) {
      headerStore.showNotification(t('receipt.tooLarge'), 'error')
      return null
    }
    let image: Blob
    try {
      image = await compressImage(file)
    } catch {
      headerStore.showNotification(t('receipt.unsupported'), 'error')
      return null
    }
    if (image.size > MAX_UPLOAD_SIZE) {
      headerStore.showNotification(t('receipt.tooLarge'), 'error')
      return null
    }

    uploading.value = true
    try {
      const { data } = await uploadReceipt(fundsStore.fundId, image)
      previews.value = { ...previews.value, [data.key]: URL.createObjectURL(image) }
      return data.key
    } catch (error) {
      // Сеть и 5xx уже показал перехватчик http
      const status = axios.isAxiosError(error) ? error.response?.status : undefined
      if (status === 413) headerStore.showNotification(t('receipt.tooLarge'), 'error')
      else if (status && status < 500) headerStore.showNotification(t('receipt.uploadFailed'), 'error')
      return null
    } finally {
      uploading.value = false
    }
  }

  return { uploading, upload, previewOf, forget }
}
