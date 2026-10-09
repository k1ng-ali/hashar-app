// src/shared/stores/useHeaderStore.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export type NotificationType = 'success' | 'error'

export const useHeaderStore = defineStore('header', () => {
  // ── State ─────────────────────────────────────────────────────────────
  const title = ref('')
  const leftAction = ref<(() => void) | null>(null)
  const notification = ref<{ message: string; type: NotificationType } | null>(null)
  let notificationTimer: ReturnType<typeof setTimeout> | null = null

  // ── Actions ───────────────────────────────────────────────────────────
  function setTitle(value: string) {
    title.value = value
  }

  /** Кнопка «назад» слева в шапке; null — убрать. */
  function setLeftAction(action: (() => void) | null) {
    leftAction.value = action
  }

  function showNotification(message: string, type: NotificationType = 'success', ms = 2500) {
    notification.value = { message, type }
    if (notificationTimer) clearTimeout(notificationTimer)
    notificationTimer = setTimeout(() => {
      notification.value = null
    }, ms)
  }

  function reset() {
    title.value = ''
    leftAction.value = null
  }

  return {
    title,
    leftAction,
    notification,
    setTitle,
    setLeftAction,
    showNotification,
    reset,
  }
})
