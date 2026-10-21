// src/features/notices/store.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from './api.ts'
import type { Notice } from './types.ts'

/** Уведомления совету фонда от платформы (окно по колокольчику). */
export const useNoticesStore = defineStore('notices', () => {
  // ── State ─────────────────────────────────────────────────────────────
  const fundId = ref<number | null>(null)
  const items = ref<Notice[]>([])
  const unread = ref(0)
  const isLoading = ref(false)
  // Окно уведомлений открывается из шапки (колокольчик) и с главной (карточка уведомления)
  const isOpen = ref(false)

  // ── Actions ───────────────────────────────────────────────────────────
  async function fetch(id: number) {
    // Другой фонд — не показываем чужие уведомления, пока грузятся свои
    if (fundId.value !== id) {
      items.value = []
      unread.value = 0
    }
    fundId.value = id
    isLoading.value = true
    try {
      const { data } = await api.listNotices(id)
      if (fundId.value !== id) return
      items.value = data.items
      unread.value = data.unread
    } finally {
      isLoading.value = false
    }
  }

  /** Окно открыто — всё прочитано. Отметки «новое» в списке остаются до следующей загрузки. */
  async function markRead() {
    if (!fundId.value || !unread.value) return
    unread.value = 0
    await api.markNoticesRead(fundId.value)
  }

  function reset() {
    fundId.value = null
    items.value = []
    unread.value = 0
  }

  return { fundId, items, unread, isLoading, isOpen, fetch, markRead, reset }
})
