<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import { copyText } from '@/shared/lib/browser.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import RequisiteCard from './RequisiteCard.vue'
import type { Requisite } from '../types.ts'

defineProps<{
  open: boolean
  requisites: Requisite[]
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const { t } = useI18n()
const headerStore = useHeaderStore()

async function handleCopy(value: string) {
  if (await copyText(value)) headerStore.showNotification(t('requisites.copied'))
}
</script>

<template>
  <BottomSheet
    :open="open"
    :title="$t('requisites.title')"
    :subtitle="$t('requisites.subtitle')"
    @close="emit('close')"
  >
    <div v-if="requisites.length" class="list">
      <RequisiteCard v-for="item in requisites" :key="item.id" :requisite="item" @copy="handleCopy" />
    </div>
    <EmptyState v-else icon="🏦" :title="$t('requisites.empty')" />
  </BottomSheet>
</template>

<style scoped lang="scss">
.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
</style>
