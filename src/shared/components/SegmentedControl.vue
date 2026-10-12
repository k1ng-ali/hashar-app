<script setup lang="ts" generic="T extends string">
/** Сегменты равной ширины (подразделы одного экрана). Для длинных списков — PillTabs. */
defineProps<{
  options: { value: T; label: string; badge?: number; dot?: boolean }[]
  modelValue: T
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: T): void
}>()
</script>

<template>
  <div class="segmented" role="tablist">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      role="tab"
      class="segment"
      :class="{ 'segment--active': option.value === modelValue }"
      :aria-selected="option.value === modelValue"
      @click="emit('update:modelValue', option.value)"
    >
      {{ option.label }}
      <span v-if="option.badge" class="badge">{{ option.badge }}</span>
      <span v-else-if="option.dot" class="dot" />
    </button>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.segmented {
  display: grid;
  grid-auto-columns: 1fr;
  grid-auto-flow: column;
  gap: 4px;
  padding: 4px;
  border-radius: 16px;
  background: rgba(17, 24, 39, 0.06);
}

.segment {
  @include pressable;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  min-width: 0;
  padding: 9px 4px;
  border: none;
  border-radius: 12px;
  background: transparent;
  color: $text-secondary;
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;

  &--active {
    background: $surface;
    color: $navy;
    font-weight: 600;
    box-shadow: 0 1px 3px rgba(17, 24, 39, 0.08);
  }
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: $danger;
}

.badge {
  min-width: 18px;
  padding: 0 5px;
  border-radius: 9px;
  background: $danger;
  color: #fff;
  font-size: 11px;
  line-height: 18px;
}
</style>
