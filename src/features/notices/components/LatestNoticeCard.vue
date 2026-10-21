<script setup lang="ts">
import { computed } from 'vue'
import { LuBell } from '@kalimahapps/vue-icons/lu'
import { useNoticeText } from '../composables/useNoticeText.ts'
import type { Notice } from '../types.ts'

/** Последнее непрочитанное уведомление от платформы — на главной у совета. */
const props = defineProps<{
  notice: Notice
}>()

const emit = defineEmits<{
  (e: 'open'): void
}>()

const noticeText = useNoticeText()
const text = computed(() => noticeText(props.notice))
</script>

<template>
  <button type="button" class="card" @click="emit('open')">
    <span class="icon"><LuBell /></span>
    <span class="content">
      <b>{{ text.title }}</b>
      <span v-if="text.body" class="body">{{ text.body }}</span>
      <span class="more">{{ $t('notices.openAll') }}</span>
    </span>
  </button>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.card {
  @include glass-card(20px);
  @include pressable;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  border-color: rgba(17, 24, 39, 0.3);
  text-align: left;
  cursor: pointer;
}

.icon {
  @include icon-circle(36px);
  font-size: 16px;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;

  b {
    font-size: 14px;
    color: $navy;
  }
}

.body {
  display: -webkit-box;
  overflow: hidden;
  font-size: 13px;
  line-height: 1.45;
  color: $text-secondary;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
}

.more {
  font-size: 12px;
  font-weight: 600;
  color: $navy;
  text-decoration: underline;
}
</style>
