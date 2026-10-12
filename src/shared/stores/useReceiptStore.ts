// src/shared/stores/useReceiptStore.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

/** Глобальный полноэкранный просмотр чека (ReceiptViewer в App.vue). */
export const useReceiptStore = defineStore('receipt', () => {
  // ── State ─────────────────────────────────────────────────────────────
  const isOpen = ref(false)
  const title = ref('')
  const image = ref('')

  // ── Actions ───────────────────────────────────────────────────────────
  function open(receiptTitle: string, receiptImage: string | null) {
    // Чужой чек участнику не приходит — открывать нечего
    if (!receiptImage) return
    title.value = receiptTitle
    image.value = receiptImage
    isOpen.value = true
  }

  function close() {
    isOpen.value = false
  }

  return { isOpen, title, image, open, close }
})
