<script setup lang="ts">
import { LuChevronRight } from '@kalimahapps/vue-icons/lu'

export interface AttentionItem {
  key: string
  label: string
  count?: number
  to: string
}

/** «Требует внимания» — дела совета на главном экране. */
defineProps<{
  items: AttentionItem[]
}>()

const emit = defineEmits<{
  (e: 'open', to: string): void
}>()
</script>

<template>
  <section class="attention">
    <h3 class="title">{{ $t('attention.title') }}</h3>
    <button v-for="item in items" :key="item.key" class="row" @click="emit('open', item.to)">
      <span class="label">{{ item.label }}</span>
      <span v-if="item.count" class="count">{{ item.count }}</span>
      <LuChevronRight class="chevron" />
    </button>
  </section>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.attention {
  display: flex;
  flex-direction: column;
  padding: 14px 16px 6px;
  border: 1px solid rgba(217, 119, 6, 0.2);
  border-radius: 20px;
  background: #FFFBEB;
}

.title {
  margin: 0 0 4px;
  font-size: 13px;
  font-weight: 600;
  color: #92400E;
}

.row {
  @include pressable;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  border: none;
  background: none;
  text-align: left;

  & + & {
    border-top: 1px solid rgba(217, 119, 6, 0.12);
  }
}

.label {
  flex: 1;
  font-size: 14px;
  color: $navy;
}

.count {
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
  color: #B45309;
}
</style>
