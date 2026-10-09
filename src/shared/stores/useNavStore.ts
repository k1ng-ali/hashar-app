// src/shared/stores/useNavStore.ts
import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useNavStore = defineStore('nav', () => {
  // ── State ─────────────────────────────────────────────────────────────
  const isTabsVisible = ref(true)

  // ── Actions ───────────────────────────────────────────────────────────
  function hideTabs() {
    isTabsVisible.value = false
  }

  function showTabs() {
    isTabsVisible.value = true
  }

  return { isTabsVisible, hideTabs, showTabs }
})
