<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    percent: number
    // auto — цвет по прогрессу сбора, brand — всегда фирменный градиент
    tone?: 'auto' | 'brand'
  }>(),
  { tone: 'auto' },
)

const width = computed(() => `${Math.min(100, Math.max(props.percent, 0))}%`)
</script>

<template>
  <div class="progress-track">
    <div
      class="progress-fill"
      :class="tone === 'auto' && { 'progress-fill--done': percent >= 100, 'progress-fill--low': percent < 30 }"
      :style="{ width }"
    />
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.progress-track {
  height: 10px;
  border-radius: 10px;
  background: rgba(35, 73, 112, 0.08);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 10px;
  background: $gradient;
  transition: width 0.6s ease;

  &--low {
    background: linear-gradient(135deg, #FBBF24, #F59E0B);
  }

  &--done {
    background: linear-gradient(135deg, #34D399, #10B981);
  }
}
</style>
