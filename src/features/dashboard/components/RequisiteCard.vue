<script setup lang="ts">
import { formatPhone, phoneHref } from '@/shared/lib/formatters.ts'
import { LuCopy } from '@kalimahapps/vue-icons/lu'
import type { Requisite } from '../types.ts'

defineProps<{
  requisite: Requisite
}>()

const emit = defineEmits<{
  (e: 'copy', value: string): void
}>()
</script>

<template>
  <div class="requisite" :class="{ 'requisite--inactive': !requisite.is_active }">
    <div class="top">
      <span class="bank">
        {{ requisite.bank_name }}
        <span class="currency">{{ requisite.currency.toUpperCase() }}</span>
      </span>
      <span class="state">{{ requisite.is_active ? $t('requisites.active') : $t('requisites.inactive') }}</span>
    </div>

    <div class="number">{{ requisite.card_or_account_number }}</div>

    <div class="row">
      <span class="label">{{ $t('requisites.recipient') }}</span>
      <span>{{ requisite.recipient_name }}</span>
    </div>
    <div v-if="requisite.phone_number" class="row">
      <span class="label">{{ $t('requisites.sbp') }}</span>
      <a class="phone-link" :href="phoneHref(requisite.phone_number)">{{ formatPhone(requisite.phone_number) }}</a>
    </div>
    <p v-if="requisite.note" class="note">{{ requisite.note }}</p>

    <button
      class="copy-btn"
      :disabled="!requisite.is_active"
      @click="emit('copy', requisite.card_or_account_number.replace(/\s+/g, ''))"
    >
      <LuCopy /> {{ $t('requisites.copy') }}
    </button>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.requisite {
  @include glass-card;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 16px;

  &--inactive {
    opacity: 0.55;
  }
}

.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.bank {
  font-size: 15px;
  font-weight: 700;
  color: $navy;
}

.currency {
  margin-left: 6px;
  padding: 2px 8px;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.14);
  color: #111827;
  font-size: 11px;
  font-weight: 700;
}

.state {
  padding: 2px 10px;
  border-radius: 20px;
  background: rgba(16, 185, 129, 0.12);
  color: #047857;
  font-size: 11px;
  font-weight: 700;

  .requisite--inactive & {
    background: rgba(17, 24, 39, 0.08);
    color: $text-secondary;
  }
}

.number {
  margin: 4px 0;
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 1px;
  color: #111827;
}

.row {
  display: flex;
  gap: 6px;
  font-size: 13px;
  color: #111827;
}

.label {
  color: $text-muted;
}

.note {
  margin: 4px 0 0;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.08);
  font-size: 12px;
  color: $text-secondary;
}

.copy-btn {
  @include ghost-button;
  margin-top: 6px;

  &:disabled {
    opacity: 0.5;
  }
}

.phone-link {
  font-weight: 700;
  color: $navy;
  text-decoration: none;
}
</style>
