<script setup lang="ts">
defineProps<{
  icon: string
  title: string
  hint?: string
}>()
</script>

<template>
  <div class="empty-state">
    <div class="empty-icon">{{ icon }}</div>
    <h3>{{ title }}</h3>
    <p v-if="hint">{{ hint }}</p>
    <slot />
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 36px 16px;
  text-align: center;
  color: $text-secondary;

  .empty-icon {
    font-size: 40px;
  }

  h3 {
    margin: 10px 0 2px;
    font-size: 16px;
    color: $navy;
  }

  p {
    margin: 0 0 8px;
    font-size: 14px;
  }
}
</style>
