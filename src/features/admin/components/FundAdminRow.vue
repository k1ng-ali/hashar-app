<script setup lang="ts">
import { LuTrash2 } from '@kalimahapps/vue-icons/lu'
import ProgressBar from '@/shared/components/ProgressBar.vue'
import { formatMoney } from '@/shared/lib/format.ts'
import type { TargetFund } from '@/features/targetFunds/types.ts'

defineProps<{
  fund: TargetFund
  canDelete: boolean
}>()

const emit = defineEmits<{
  (e: 'open', id: number): void
  (e: 'toggle', id: number): void
  (e: 'delete', id: number): void
}>()
</script>

<template>
  <div class="fund-row">
    <div class="top">
      <button class="title" @click="emit('open', fund.id)">{{ fund.title }}</button>
      <a-switch :checked="fund.is_active" @change="emit('toggle', fund.id)" />
    </div>

    <p class="description">{{ fund.description }}</p>

    <div class="numbers">
      <b>{{ formatMoney(fund.collected_amount, fund.currency) }}</b>
      <span>{{ $t('admin.funds.of', { amount: formatMoney(fund.target_amount, fund.currency) }) }}</span>
      <span class="percent">{{ fund.percent }}%</span>
      <button v-if="canDelete" class="icon-btn" :aria-label="$t('common.delete')" @click="emit('delete', fund.id)">
        <LuTrash2 />
      </button>
    </div>

    <ProgressBar :percent="fund.percent" />
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.fund-row {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 14px;
}

.top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.title {
  padding: 0;
  border: none;
  background: none;
  text-align: left;
  font-size: 14px;
  font-weight: 700;
  color: $navy;
}

.description {
  margin: 0;
  font-size: 12px;
  color: $text-secondary;
}

.numbers {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: $text-muted;

  b {
    font-size: 14px;
    color: $success;
  }
}

.percent {
  margin-left: auto;
  font-weight: 800;
  color: $teal;
}

.icon-btn {
  @include pressable;
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.08);
  color: $danger;
}
</style>
