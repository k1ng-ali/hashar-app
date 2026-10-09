<script setup lang="ts">
import type { AuthProvider } from '../types.ts'

// Провайдеры появятся позже — кнопки уже на месте, но неактивны
const PROVIDERS: { id: AuthProvider; label: string; icon: string }[] = [
  { id: 'google', label: 'Google', icon: '🟢' },
  { id: 'telegram', label: 'Telegram', icon: '✈️' },
]
</script>

<template>
  <div class="providers">
    <div class="divider">
      <span>{{ $t('auth.or') }}</span>
    </div>
    <div class="buttons">
      <button v-for="provider in PROVIDERS" :key="provider.id" class="provider-btn" disabled>
        <span>{{ provider.icon }}</span>
        {{ provider.label }}
        <span class="soon">{{ $t('auth.soon') }}</span>
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.divider {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 4px 0 12px;
  font-size: 12px;
  color: $text-muted;

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1px;
    background: rgba(35, 73, 112, 0.1);
  }
}

.buttons {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.provider-btn {
  @include ghost-button;
  position: relative;
  padding: 12px;

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.soon {
  position: absolute;
  top: -8px;
  right: 8px;
  padding: 1px 8px;
  border-radius: 10px;
  background: $gradient;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
}
</style>
