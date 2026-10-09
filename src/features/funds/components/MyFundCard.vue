<script setup lang="ts">
import { LuChevronRight } from '@kalimahapps/vue-icons/lu'
import type { MyFund } from '../types.ts'

defineProps<{
  fund: MyFund
  isCurrent?: boolean
}>()

const emit = defineEmits<{
  (e: 'open', fund: MyFund): void
  (e: 'cancel', fund: MyFund): void
}>()
</script>

<template>
  <div
    class="fund-card"
    :class="{ 'fund-card--active': fund.status === 'active', 'fund-card--current': isCurrent }"
    @click="fund.status === 'active' && emit('open', fund)"
  >
    <span class="logo">🏠</span>

    <div class="info">
      <span class="name">{{ fund.name }}</span>
      <span class="meta">
        {{ fund.address_unit ?? fund.address ?? fund.code }}
      </span>
    </div>

    <span v-if="fund.status === 'active'" class="role">{{ $t(`roles.${fund.role}`) }}</span>
    <span v-else class="status" :class="`status--${fund.status}`">{{ $t(`memberStatus.${fund.status}`) }}</span>

    <LuChevronRight v-if="fund.status === 'active'" class="chevron" />
    <button v-else-if="fund.status === 'pending'" class="cancel-btn" @click.stop="emit('cancel', fund)">
      {{ $t('funds.cancelRequest') }}
    </button>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.fund-card {
  @include glass-card(18px);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;

  &--active {
    @include pressable;
    cursor: pointer;
  }

  &--current {
    border-color: rgba(78, 190, 194, 0.6);
    box-shadow: 0 6px 24px rgba(78, 190, 194, 0.2);
  }
}

.logo {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  background: rgba(78, 190, 194, 0.14);
  font-size: 20px;
}

.info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 15px;
  font-weight: 700;
  color: $navy;
}

.meta {
  font-size: 12px;
  color: $text-muted;
}

.role {
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(78, 190, 194, 0.16);
  color: #0E7C80;
  font-size: 11px;
  font-weight: 700;
}

.status {
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;

  &--pending {
    background: rgba(245, 158, 11, 0.14);
    color: #B45309;
  }

  &--rejected,
  &--blocked {
    background: rgba(239, 68, 68, 0.1);
    color: #B91C1C;
  }
}

.chevron {
  flex-shrink: 0;
  color: $text-muted;
}

.cancel-btn {
  @include ghost-button;
  padding: 5px 10px;
  font-size: 11px;
}
</style>
