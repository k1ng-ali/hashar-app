<script setup lang="ts">
import type { FundPublic } from '../types.ts'

defineProps<{
  fund: FundPublic
}>()

const emit = defineEmits<{
  (e: 'join', fund: FundPublic): void
}>()
</script>

<template>
  <div class="result">
    <span class="logo">🏠</span>
    <div class="info">
      <span class="name">{{ fund.name }}</span>
      <span class="meta">
        {{ fund.address ?? fund.code }} · {{ $t('funds.membersCount', { n: fund.members_count }) }}
      </span>
    </div>

    <!-- Уже участник или заявка подана — показываем статус -->
    <span v-if="fund.my_status && fund.my_status !== 'rejected'" class="status" :class="`status--${fund.my_status}`">
      {{ $t(`memberStatus.${fund.my_status}`) }}
    </span>
    <button v-else class="join-btn" @click="emit('join', fund)">{{ $t('funds.join.button') }}</button>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.result {
  @include glass-card(16px);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
}

.logo {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 40px;
  height: 40px;
  border-radius: 12px;
  background: rgba(35, 73, 112, 0.06);
  font-size: 18px;
}

.info {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.name {
  font-size: 14px;
  font-weight: 700;
  color: $navy;
}

.meta {
  font-size: 12px;
  color: $text-muted;
}

.join-btn {
  @include cta-button;
  flex-shrink: 0;
  padding: 8px 14px;
  font-size: 12px;
}

.status {
  flex-shrink: 0;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;

  &--active {
    background: rgba(16, 185, 129, 0.14);
    color: #047857;
  }

  &--pending {
    background: rgba(245, 158, 11, 0.14);
    color: #B45309;
  }

  &--blocked {
    background: rgba(239, 68, 68, 0.1);
    color: #B91C1C;
  }
}
</style>
