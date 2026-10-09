// src/features/announcements/store.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'
import { useFundsStore } from '@/features/funds/store.ts'
import * as api from './api.ts'
import type { Announcement, AnnouncementCategory, AnnouncementCreate } from './types.ts'

export type AnnouncementsFilter = 'all' | AnnouncementCategory

export const useAnnouncementsStore = defineStore('announcements', () => {
  const funds = useFundsStore()

  // ── State ─────────────────────────────────────────────────────────────
  const items = ref<Announcement[]>([])
  const filter = ref<AnnouncementsFilter>('all')
  const isLoading = ref(false)
  const isSubmitting = ref(false)
  const errorMessage = ref('')

  // ── Actions ───────────────────────────────────────────────────────────
  async function fetchItems(nextFilter: AnnouncementsFilter = filter.value) {
    filter.value = nextFilter
    isLoading.value = true
    errorMessage.value = ''
    try {
      const { data } = await api.listAnnouncements(funds.fundId, nextFilter === 'all' ? undefined : nextFilter)
      items.value = data
    } catch {
      errorMessage.value = 'errors.loadFailed'
    } finally {
      isLoading.value = false
    }
  }

  async function create(payload: AnnouncementCreate) {
    isSubmitting.value = true
    try {
      const { data } = await api.createAnnouncement(funds.fundId, payload)
      // Закреплённые остаются сверху — проще перечитать ленту
      await fetchItems()
      return data
    } finally {
      isSubmitting.value = false
    }
  }

  async function like(id: number) {
    const { data } = await api.toggleLike(funds.fundId, id)
    replace(data)
  }

  async function comment(id: number, text: string) {
    isSubmitting.value = true
    try {
      const { data } = await api.addComment(funds.fundId, id, text)
      const item = items.value.find((announcement) => announcement.id === id)
      if (item) item.comments = [...item.comments, data]
    } finally {
      isSubmitting.value = false
    }
  }

  async function remove(id: number) {
    await api.deleteAnnouncement(funds.fundId, id)
    items.value = items.value.filter((item) => item.id !== id)
  }

  function replace(announcement: Announcement) {
    items.value = items.value.map((item) => (item.id === announcement.id ? announcement : item))
  }

  return {
    items,
    filter,
    isLoading,
    isSubmitting,
    errorMessage,
    fetchItems,
    create,
    like,
    comment,
    remove,
  }
})
