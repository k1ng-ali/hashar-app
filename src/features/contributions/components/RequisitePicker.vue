<script setup lang="ts">
import { LuCopy } from '@kalimahapps/vue-icons/lu'
import type { Requisite } from '@/features/dashboard/types.ts'

defineProps<{
  requisites: Requisite[]
}>()

const selected = defineModel<number | null>({ required: true })

const emit = defineEmits<{
  (e: 'copy', value: string): void
}>()
</script>

<template>
  <div class="picker">
    <label
      v-for="requisite in requisites"
      :key="requisite.id"
      class="option"
      :class="{ 'option--selected': selected === requisite.id }"
    >
      <input v-model="selected" type="radio" :value="requisite.id" class="radio" />
      <span class="check" />

      <span class="body">
        <span class="top">
          <b>{{ requisite.bank_name }}</b>
          <span class="currency">{{ requisite.currency.toUpperCase() }}</span>
            <span class="kind">{{ $t(`requisites.kind.${requisite.kind}`) }}</span>
        </span>
        <span class="number">{{ requisite.card_or_account_number }}</span>
        <span class="recipient">{{ requisite.recipient_name }}</span>
        <span v-if="requisite.note" class="note">{{ requisite.note }}</span>
      </span>

      <button
        type="button"
        class="copy-btn"
        :aria-label="$t('requisites.copy')"
        @click.prevent="emit('copy', requisite.card_or_account_number.replace(/\s+/g, ''))"
      >
        <LuCopy />
      </button>
    </label>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.picker {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option {
  @include pressable;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px;
  border: 1.5px solid rgba(17, 24, 39, 0.1);
  border-radius: 16px;
  background: rgba(255, 255, 255, 0.85);
  cursor: pointer;

  &--selected {
    border-color: $teal;
    background: rgba(17, 24, 39, 0.08);

    .check {
      border-color: $teal;

      &::after {
        transform: scale(1);
      }
    }
  }
}

.radio {
  display: none;
}

.check {
  position: relative;
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  margin-top: 2px;
  border: 2px solid rgba(17, 24, 39, 0.25);
  border-radius: 50%;

  &::after {
    content: '';
    position: absolute;
    inset: 3px;
    border-radius: 50%;
    background: $gradient;
    transform: scale(0);
    transition: transform 0.2s ease;
  }
}

.body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  flex: 1;
  min-width: 0;
}

.top {
  display: flex;
  align-items: center;
  gap: 8px;

  b {
    color: $navy;
  }
}

.currency {
  padding: 1px 8px;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.14);
  color: #111827;
  font-size: 11px;
  font-weight: 700;
}

.number {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}

.recipient,
.note {
  font-size: 12px;
  color: $text-secondary;
}

.copy-btn {
  @include pressable;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.06);
  color: $navy;
}

.kind {
  margin-left: 6px;
  font-size: 11px;
  font-weight: 500;
  color: $text-muted;
}
</style>
