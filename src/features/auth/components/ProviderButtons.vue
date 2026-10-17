<script setup lang="ts">
import { isGoogleEnabled } from '../google.ts'
import GoogleButton from './GoogleButton.vue'

defineProps<{
  disabled: boolean
}>()

const emit = defineEmits<{
  (e: 'google', idToken: string): void
  (e: 'error'): void
}>()
</script>

<template>
  <div class="providers">
    <div class="divider">
      <span>{{ $t('auth.or') }}</span>
    </div>
    <div class="buttons">
      <GoogleButton
        v-if="isGoogleEnabled"
        :disabled="disabled"
        @token="(idToken) => emit('google', idToken)"
        @error="emit('error')"
      />
      <button v-else type="button" class="provider-btn" disabled>
        Google
        <span class="soon">{{ $t('auth.soon') }}</span>
      </button>

      <button type="button" class="provider-btn" disabled>
        ✈️ Telegram
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
    background: rgba(17, 24, 39, 0.1);
  }
}

.buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.provider-btn {
  @include ghost-button;
  position: relative;
  gap: 10px;
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
