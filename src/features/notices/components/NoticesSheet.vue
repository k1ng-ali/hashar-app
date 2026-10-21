<script setup lang="ts">
import { LuChevronRight } from '@kalimahapps/vue-icons/lu'
import type { AttentionItem } from '@/features/dashboard/components/AttentionCard.vue'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import { formatDateTime } from '@/shared/lib/format.ts'
import { useNoticeText } from '../composables/useNoticeText.ts'
import type { Notice } from '../types.ts'

/** Окно по колокольчику у совета: дела фонда и уведомления от платформы. */
defineProps<{
  open: boolean
  notices: Notice[]
  attention: AttentionItem[]
  /** Продлить тариф может только председатель. */
  canRenew: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'go', to: string): void
}>()

const noticeText = useNoticeText()
</script>

<template>
  <BottomSheet :open="open" :title="$t('notices.title')" @close="emit('close')">
    <div class="notices">
      <!-- 1. Дела совета -->
      <section v-if="attention.length" class="attention">
        <button v-for="item in attention" :key="item.key" type="button" class="row" @click="emit('go', item.to)">
          <span class="label">{{ item.label }}</span>
          <span v-if="item.count" class="count">{{ item.count }}</span>
          <LuChevronRight class="chevron" />
        </button>
      </section>

      <!-- 2. От платформы -->
      <h3 class="section-title">{{ $t('notices.fromPlatform') }}</h3>
      <div v-if="notices.length" class="list">
        <article
          v-for="notice in notices"
          :key="notice.id"
          class="notice"
          :class="{ 'notice--unread': notice.is_unread, [`notice--${notice.kind}`]: true }"
        >
          <div class="notice-top">
            <b>{{ noticeText(notice).title }}</b>
            <span v-if="notice.is_unread" class="dot" :aria-label="$t('notices.new')" />
          </div>
          <p v-if="noticeText(notice).body" class="body">{{ noticeText(notice).body }}</p>
          <div class="notice-bottom">
            <span class="date">{{ formatDateTime(notice.created_at) }}</span>
            <button
              v-if="canRenew && noticeText(notice).aboutPlan"
              type="button"
              class="renew"
              @click="emit('go', '/fund/settings')"
            >
              {{ $t('notices.renew') }}
            </button>
          </div>
        </article>
      </div>
      <p v-else class="empty">{{ $t('notices.empty') }}</p>
    </div>
  </BottomSheet>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.notices {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* ── Дела совета ──────────────────────────────────────────────────────── */
.attention {
  display: flex;
  flex-direction: column;
  padding: 4px 14px;
  border: 1px solid rgba(217, 119, 6, 0.2);
  border-radius: 16px;
  background: #fffbeb;
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
  cursor: pointer;
}

.label {
  flex: 1;
  font-size: 14px;
  color: $navy;
}

.count {
  min-width: 22px;
  padding: 1px 7px;
  border-radius: 20px;
  background: #92400e;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  text-align: center;
}

.chevron {
  color: $text-muted;
}

/* ── Уведомления ──────────────────────────────────────────────────────── */
.section-title {
  @include section-title;
  font-size: 15px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.notice {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 14px;
  border: 1px solid $hairline;
  border-radius: 14px;
  background: $surface;

  &--unread {
    border-color: rgba(17, 24, 39, 0.35);
  }

  // Отказ и блокировка — заметнее остальных
  &--plan_rejected,
  &--plan_lapsed {
    border-left: 3px solid $danger;
  }

  &--plan_expiring,
  &--plan_expired {
    border-left: 3px solid $warning;
  }
}

.notice-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 10px;

  b {
    font-size: 14px;
    color: $navy;
  }
}

.dot {
  flex-shrink: 0;
  width: 8px;
  height: 8px;
  margin-top: 5px;
  border-radius: 50%;
  background: $danger;
}

.body {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
  color: $text-secondary;
  white-space: pre-line;
}

.notice-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.date {
  font-size: 11px;
  color: $text-muted;
}

.renew {
  @include pressable;
  padding: 6px 12px;
  border: none;
  border-radius: 10px;
  background: #111827;
  color: #fff;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.empty {
  margin: 0;
  font-size: 13px;
  color: $text-muted;
}
</style>
