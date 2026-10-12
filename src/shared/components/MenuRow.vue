<script setup lang="ts">
import { LuChevronRight } from '@kalimahapps/vue-icons/lu'

/** Строка списка-меню: иконка в круге, заголовок, подсказка, счётчик, стрелка. */
defineProps<{
  title: string
  hint?: string
  badge?: number
  danger?: boolean
}>()

const emit = defineEmits<{
  (e: 'click'): void
}>()
</script>

<template>
  <button type="button" class="menu-row" :class="{ 'menu-row--danger': danger }" @click="emit('click')">
    <span class="icon"><slot name="icon" /></span>
    <span class="text">
      <span class="title">{{ title }}</span>
      <span v-if="hint" class="hint">{{ hint }}</span>
    </span>
    <span v-if="badge" class="badge">{{ badge }}</span>
    <LuChevronRight v-if="!danger" class="chevron" />
  </button>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.menu-row {
  @include pressable;
  display: flex;
  align-items: center;
  gap: 12px;
  width: 100%;
  padding: 12px 14px;
  border: none;
  background: transparent;
  text-align: left;

  & + & {
    border-top: 1px solid $hairline;
  }

  &--danger {
    .icon {
      background: rgba(229, 72, 77, 0.1);
      color: $danger;
    }

    .title {
      color: $danger;
    }
  }
}

.icon {
  @include icon-circle(40px);
}

.text {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.title {
  font-size: 15px;
  font-weight: 500;
  color: $navy;
}

.hint {
  overflow: hidden;
  font-size: 12px;
  color: $text-muted;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  min-width: 22px;
  padding: 0 7px;
  border-radius: 11px;
  background: $danger;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  line-height: 22px;
  text-align: center;
}

.chevron {
  flex-shrink: 0;
  color: $text-muted;
}
</style>
