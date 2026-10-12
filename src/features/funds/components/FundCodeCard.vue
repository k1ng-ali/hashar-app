<script setup lang="ts">
import { computed } from 'vue'
import { LuCopy, LuShare2 } from '@kalimahapps/vue-icons/lu'

const props = defineProps<{
  code: string
}>()

const emit = defineEmits<{
  (e: 'copy', value: string): void
}>()

// Ссылка-приглашение ведёт на /join/<code> этого же приложения
const link = computed(() => `${window.location.origin}/join/${props.code}`)
</script>

<template>
  <div class="code-card">
    <span class="label">{{ $t('funds.code.title') }}</span>
    <div class="code">{{ code }}</div>
    <p class="hint">{{ $t('funds.code.hint') }}</p>

    <div class="link">{{ link }}</div>

    <div class="actions">
      <button class="ghost-btn" @click="emit('copy', code)"><LuCopy /> {{ $t('funds.code.copyCode') }}</button>
      <button class="cta-btn" @click="emit('copy', link)"><LuShare2 /> {{ $t('funds.code.copyLink') }}</button>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.code-card {
  @include glass-card;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 18px;
  text-align: center;
}

.label {
  font-size: 12px;
  font-weight: 700;
  color: $text-muted;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.code {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 30px;
  font-weight: 700;
  letter-spacing: 4px;
  background: $gradient;
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hint {
  margin: 0;
  font-size: 12px;
  color: $text-secondary;
}

.link {
  max-width: 100%;
  margin-top: 4px;
  padding: 8px 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  border-radius: 12px;
  background: rgba(17, 24, 39, 0.05);
  font-size: 12px;
  color: $navy;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 8px;
  margin-top: 6px;
}

.ghost-btn {
  @include ghost-button;
}

.cta-btn {
  @include cta-button;
  padding: 10px 16px;
  font-size: 13px;
}
</style>
