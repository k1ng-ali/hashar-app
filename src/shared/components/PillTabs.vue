<script setup lang="ts" generic="T extends string">
defineProps<{
  options: { value: T; label: string; badge?: number }[]
  modelValue: T
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: T): void
}>()
</script>

<template>
  <div class="pill-tabs">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      class="pill"
      :class="{ 'pill--active': option.value === modelValue }"
      @click="emit('update:modelValue', option.value)"
    >
      {{ option.label }}
      <span v-if="option.badge" class="pill-badge">{{ option.badge }}</span>
    </button>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.pill-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  scrollbar-width: none;
  padding-bottom: 2px;

  &::-webkit-scrollbar {
    display: none;
  }
}

.pill {
  @include pressable;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 8px 14px;
  border: 1px solid rgba(17, 24, 39, 0.1);
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.8);
  color: $text-secondary;
  font-size: 13px;
  font-weight: 600;

  &--active {
    border-color: transparent;
    background: $gradient;
    color: #fff;
    box-shadow: none;

    .pill-badge {
      background: #fff;
      color: $navy;
    }
  }
}

.pill-badge {
  min-width: 18px;
  padding: 1px 6px;
  border-radius: 10px;
  background: $danger;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}
</style>
