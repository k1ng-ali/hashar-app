<script setup lang="ts">
withDefaults(
  defineProps<{
    lines?: number
    height?: number
  }>(),
  { lines: 3, height: 0 },
)
</script>

<template>
  <div class="card-skeleton" :style="height ? { height: `${height}px` } : undefined">
    <span v-for="i in lines" :key="i" class="line" :style="{ width: `${100 - i * 15}%` }" />
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.card-skeleton {
  @include glass-card;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 18px;
}

.line {
  height: 12px;
  border-radius: 6px;
  background: linear-gradient(90deg, #ECEEF1 25%, #F6F7F9 50%, #ECEEF1 75%);
  background-size: 200% 100%;
  animation: shimmer 1.2s infinite;

  &:first-child {
    height: 18px;
  }
}

@keyframes shimmer {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}
</style>
