<script setup lang="ts">
import { LuFileSpreadsheet } from '@kalimahapps/vue-icons/lu'
import type { ExportKind } from '../types.ts'

defineProps<{
  exportingKind: ExportKind | null
}>()

const emit = defineEmits<{
  (e: 'export', kind: ExportKind): void
}>()

const BUTTONS: { kind: ExportKind; label: string; tone: string }[] = [
  { kind: 'contributions', label: 'reports.exportContributions', tone: 'income' },
  { kind: 'expenses', label: 'reports.exportExpenses', tone: 'expense' },
  { kind: 'debtors', label: 'reports.exportDebtors', tone: 'debt' },
]
</script>

<template>
  <div class="exports">
    <button
      v-for="button in BUTTONS"
      :key="button.kind"
      class="export-btn"
      :disabled="exportingKind !== null"
      @click="emit('export', button.kind)"
    >
      <span class="icon" :class="`icon--${button.tone}`"><LuFileSpreadsheet /></span>
      <span class="text">
        <span class="title">{{ $t(button.label) }}</span>
        <span class="sub">{{ exportingKind === button.kind ? $t('common.loading') : $t('reports.exportFormat') }}</span>
      </span>
    </button>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.exports {
  display: grid;
  gap: 10px;
}

.export-btn {
  @include glass-card(16px);
  @include pressable;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  text-align: left;

  &:disabled {
    opacity: 0.7;
  }
}

.icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  font-size: 20px;

  &--income {
    background: rgba(16, 185, 129, 0.12);
    color: $success;
  }

  &--expense {
    background: rgba(239, 68, 68, 0.1);
    color: $danger;
  }

  &--debt {
    background: rgba(245, 158, 11, 0.14);
    color: #B45309;
  }
}

.text {
  display: flex;
  flex-direction: column;
}

.title {
  font-size: 14px;
  font-weight: 700;
  color: $navy;
}

.sub {
  font-size: 12px;
  color: $text-muted;
}

@media (min-width: 768px) {
  .exports {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
