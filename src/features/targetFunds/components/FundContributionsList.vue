<script setup lang="ts">
import { LuFileSearch } from '@kalimahapps/vue-icons/lu'
import StatusBadge from '@/shared/components/StatusBadge.vue'
import { formatDate, formatMoney } from '@/shared/lib/format.ts'
import type { Contribution } from '@/features/contributions/types.ts'

defineProps<{
  contributions: Contribution[]
}>()

const emit = defineEmits<{
  (e: 'open-receipt', contribution: Contribution): void
}>()
</script>

<template>
  <div class="list">
    <div v-for="contribution in contributions" :key="contribution.id" class="item">
      <span class="avatar">{{ contribution.user_name.slice(0, 1) }}</span>
      <div class="main">
        <div class="row">
          <span class="name">{{ contribution.user_name }}</span>
          <span class="amount">{{ formatMoney(contribution.amount, contribution.currency, true) }}</span>
        </div>
        <div class="meta">
          <span>{{ contribution.user_unit }} · {{ formatDate(contribution.created_at) }}</span>
          <StatusBadge v-if="contribution.status !== 'approved'" :status="contribution.status" />
        </div>
      </div>
      <button class="receipt-btn" :aria-label="$t('receipt.view')" @click="emit('open-receipt', contribution)">
        <LuFileSearch />
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.list {
  display: flex;
  flex-direction: column;
}

.item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 0;

  & + & {
    border-top: 1px solid rgba(35, 73, 112, 0.06);
  }
}

.avatar {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: rgba(78, 190, 194, 0.16);
  color: $navy;
  font-weight: 800;
}

.main {
  flex: 1;
  min-width: 0;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 8px;
}

.name {
  font-size: 14px;
  font-weight: 700;
  color: $navy;
}

.amount {
  font-size: 14px;
  font-weight: 800;
  color: $success;
}

.meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 2px;
  font-size: 12px;
  color: $text-muted;
}

.receipt-btn {
  @include pressable;
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 10px;
  background: rgba(35, 73, 112, 0.06);
  color: $navy;
  font-size: 16px;
}
</style>
