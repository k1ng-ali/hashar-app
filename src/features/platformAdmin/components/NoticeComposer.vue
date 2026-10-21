<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useNoticeText } from '@/features/notices/composables/useNoticeText.ts'
import type { NoticeAdmin } from '@/features/notices/types.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import { formatDateTime } from '@/shared/lib/format.ts'

const MIN_TEXT = 3
const MAX_TEXT = 1000
const TEMPLATES = ['growth', 'moderation', 'contacts'] as const

/** Админ платформы пишет совету фонда: шаблоны, текст и уже отправленные уведомления. */
const props = defineProps<{
  open: boolean
  fundName: string
  sent: NoticeAdmin[]
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'send', text: string): void
}>()

const { t } = useI18n()
const noticeText = useNoticeText()

const text = ref('')
const isValid = computed(() => text.value.trim().length >= MIN_TEXT)

// Новый фонд — пустое поле
watch(
  () => [props.open, props.fundName],
  () => {
    if (props.open) text.value = ''
  },
)

function useTemplate(key: (typeof TEMPLATES)[number]) {
  text.value = t(`platform.notify.templates.${key}.text`)
}
</script>

<template>
  <BottomSheet :open="open" :title="$t('platform.notify.title')" :subtitle="fundName" @close="emit('close')">
    <form class="composer" @submit.prevent="isValid && emit('send', text.trim())">
      <p class="hint">{{ $t('platform.notify.hint') }}</p>

      <div class="chips">
        <button v-for="key in TEMPLATES" :key="key" type="button" class="chip" @click="useTemplate(key)">
          {{ $t(`platform.notify.templates.${key}.label`) }}
        </button>
      </div>

      <textarea
        v-model="text"
        class="field"
        rows="5"
        :maxlength="MAX_TEXT"
        :placeholder="$t('platform.notify.placeholder')"
      />

      <button type="submit" class="send" :disabled="!isValid || isSubmitting">
        {{ $t('platform.notify.send') }}
      </button>

      <template v-if="sent.length">
        <h3 class="sent-title">{{ $t('platform.notify.sent') }}</h3>
        <div class="sent">
          <div v-for="notice in sent" :key="notice.id" class="sent-item">
            <b>{{ noticeText(notice).title }}</b>
            <span v-if="noticeText(notice).body" class="body">{{ noticeText(notice).body }}</span>
            <span class="meta">
              {{ formatDateTime(notice.created_at) }}<template v-if="notice.author_name"> · {{ notice.author_name }}</template>
            </span>
          </div>
        </div>
      </template>
    </form>
  </BottomSheet>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.composer {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.hint {
  margin: 0;
  font-size: 13px;
  color: $text-secondary;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  @include ghost-button;
  padding: 6px 12px;
  font-size: 12px;
}

.field {
  @include field-input;
  resize: vertical;
  min-height: 110px;
  font-family: inherit;
}

.send {
  @include cta-button;
}

.sent-title {
  @include section-title;
  margin-top: 4px;
  font-size: 15px;
}

.sent {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sent-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 12px;
  border-radius: 12px;
  background: $surface-muted;

  b {
    font-size: 13px;
    color: $navy;
  }
}

.body {
  font-size: 13px;
  color: $text-secondary;
  white-space: pre-line;
}

.meta {
  font-size: 11px;
  color: $text-muted;
}
</style>
