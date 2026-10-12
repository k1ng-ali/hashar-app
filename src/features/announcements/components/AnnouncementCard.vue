<script setup lang="ts">
import { ref } from 'vue'
import { LuMessageCircle, LuPin, LuSend, LuThumbsUp, LuTrash2 } from '@kalimahapps/vue-icons/lu'
import { formatDateTime, formatMoney } from '@/shared/lib/format.ts'
import type { Announcement } from '../types.ts'

defineProps<{
  announcement: Announcement
  canDelete: boolean
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'like', id: number): void
  (e: 'comment', id: number, text: string): void
  (e: 'delete', id: number): void
}>()

const isCommentsOpen = ref(false)
const commentText = ref('')

function sendComment(id: number) {
  const text = commentText.value.trim()
  if (!text) return
  emit('comment', id, text)
  commentText.value = ''
}
</script>

<template>
  <article class="announcement" :class="{ 'announcement--pinned': announcement.is_pinned }">
    <div class="top">
      <div class="tags">
        <span v-if="announcement.is_pinned" class="pinned"><LuPin /> {{ $t('announcements.pinned') }}</span>
        <span class="category" :class="`category--${announcement.category}`">
          {{ $t(`announcementCategory.${announcement.category}`) }}
        </span>
      </div>
      <div class="top-right">
        <span class="date">{{ formatDateTime(announcement.created_at) }}</span>
        <button
          v-if="canDelete"
          class="icon-btn icon-btn--danger"
          :aria-label="$t('common.delete')"
          @click="emit('delete', announcement.id)"
        >
          <LuTrash2 />
        </button>
      </div>
    </div>

    <!-- Движение по счетам: заголовок и суммы — локализованно, текст — комментарий совета -->
    <template v-if="announcement.transfer">
      <h2 class="title">💱 {{ $t('transfers.announcementTitle') }}</h2>
      <div class="transfer">
        <span v-if="announcement.transfer.from_currency" class="transfer-out">
          −{{ formatMoney(announcement.transfer.from_amount ?? 0, announcement.transfer.from_currency) }}
        </span>
        <span v-if="announcement.transfer.from_currency && announcement.transfer.to_currency" class="arrow">→</span>
        <span v-if="announcement.transfer.to_currency" class="transfer-in">
          +{{ formatMoney(announcement.transfer.to_amount ?? 0, announcement.transfer.to_currency) }}
        </span>
      </div>
      <p class="content">{{ announcement.transfer.comment }}</p>
    </template>
    <template v-else>
      <h2 class="title">{{ announcement.title }}</h2>
      <p class="content">{{ announcement.content }}</p>
    </template>

    <div class="footer">
      <span class="author">
        {{ announcement.author_name }}
        <template v-if="announcement.author_role"> · {{ $t(`roles.${announcement.author_role}`) }}</template>
      </span>
      <div class="actions">
        <button class="action" @click="isCommentsOpen = !isCommentsOpen">
          <LuMessageCircle /> {{ announcement.comments.length }}
        </button>
        <button
          class="action"
          :class="{ 'action--liked': announcement.is_liked }"
          @click="emit('like', announcement.id)"
        >
          <LuThumbsUp /> {{ announcement.likes_count }}
        </button>
      </div>
    </div>

    <!-- Комментарии -->
    <div v-if="isCommentsOpen" class="comments">
      <div class="comments-title">{{ $t('announcements.comments', { n: announcement.comments.length }) }}</div>
      <div v-for="comment in announcement.comments" :key="comment.id" class="comment">
        <div class="comment-head">
          <b>{{ comment.user_name }}</b>
          <span>{{ comment.user_unit }} · {{ formatDateTime(comment.created_at) }}</span>
        </div>
        <p>{{ comment.text }}</p>
      </div>

      <form class="comment-form" @submit.prevent="sendComment(announcement.id)">
        <input v-model="commentText" :placeholder="$t('announcements.commentPlaceholder')" maxlength="2000" />
        <button type="submit" class="send-btn" :disabled="isSubmitting || !commentText.trim()" :aria-label="$t('announcements.send')">
          <LuSend />
        </button>
      </form>
    </div>
  </article>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.announcement {
  @include glass-card;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;

  &--pinned {
    border-color: rgba(17, 24, 39, 0.45);
  }
}

.top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}

.tags,
.top-right {
  display: flex;
  align-items: center;
  gap: 6px;
}

.pinned {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 20px;
  background: $gradient;
  color: #fff;
  font-size: 11px;
  font-weight: 700;
}

.category {
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(17, 24, 39, 0.08);
  color: $navy;
  font-size: 11px;
  font-weight: 700;

  &--meeting {
    background: rgba(99, 102, 241, 0.12);
    color: #4338CA;
  }

  &--emergency {
    background: rgba(239, 68, 68, 0.12);
    color: #B91C1C;
  }

  &--cleanup {
    background: rgba(16, 185, 129, 0.12);
    color: #047857;
  }

  &--finance {
    background: rgba(99, 102, 241, 0.12);
    color: #4338CA;
  }
}

.date {
  font-size: 11px;
  color: $text-muted;
}

.icon-btn {
  @include pressable;
  display: grid;
  place-items: center;
  width: 30px;
  height: 30px;
  border: none;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.06);
  color: $navy;

  &--danger {
    color: $danger;
  }
}

.title {
  margin: 0;
  font-size: 16px;
  font-weight: 700;
  color: $navy;
}

.content {
  margin: 0;
  white-space: pre-line;
  font-size: 14px;
  line-height: 1.55;
  color: #374151;
}

/* ── Footer ───────────────────────────────────────────────────────────────── */
.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(17, 24, 39, 0.06);
}

.transfer {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(99, 102, 241, 0.08);
  font-size: 16px;
  font-weight: 700;

  .transfer-out {
    color: $danger;
  }

  .transfer-in {
    color: $success;
  }

  .arrow {
    color: $text-muted;
  }
}

.author {
  font-size: 12px;
  color: $text-secondary;
}

.actions {
  display: flex;
  gap: 6px;
}

.action {
  @include ghost-button;
  padding: 6px 12px;

  &--liked {
    border-color: transparent;
    background: rgba(17, 24, 39, 0.16);
    color: #111827;
  }
}

/* ── Comments ─────────────────────────────────────────────────────────────── */
.comments {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(17, 24, 39, 0.04);
}

.comments-title {
  font-size: 12px;
  font-weight: 700;
  color: $navy;
}

.comment {
  .comment-head {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    font-size: 12px;
    color: $text-muted;

    b {
      color: $navy;
    }
  }

  p {
    margin: 2px 0 0;
    font-size: 13px;
    color: #374151;
  }
}

.comment-form {
  display: flex;
  gap: 8px;
  margin-top: 4px;

  input {
    @include field-input;
    padding: 10px 12px;
    font-size: 14px;
  }
}

.send-btn {
  @include cta-button;
  flex-shrink: 0;
  width: 42px;
  padding: 0;
}
</style>
