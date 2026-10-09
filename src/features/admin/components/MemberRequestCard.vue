<script setup lang="ts">
import { LuCheck, LuX } from '@kalimahapps/vue-icons/lu'
import { formatDateTime } from '@/shared/lib/format.ts'
import type { Member } from '../types.ts'

defineProps<{
  member: Member
}>()

const emit = defineEmits<{
  (e: 'approve', member: Member): void
  (e: 'reject', member: Member): void
}>()
</script>

<template>
  <div class="request">
    <img v-if="member.avatar_url" :src="member.avatar_url" alt="" class="avatar" />
    <span v-else class="avatar avatar--fallback">{{ member.full_name.slice(0, 1) }}</span>

    <div class="info">
      <span class="name">
        {{ member.full_name }}
        <span v-if="member.address_unit" class="unit">{{ member.address_unit }}</span>
      </span>
      <span class="contact">{{ member.phone ?? member.email }}</span>
      <span v-if="member.message" class="message">«{{ member.message }}»</span>
      <span class="date">{{ formatDateTime(member.created_at) }}</span>
    </div>

    <div class="actions">
      <button class="icon-btn icon-btn--approve" :aria-label="$t('admin.members.approve')" @click="emit('approve', member)">
        <LuCheck />
      </button>
      <button class="icon-btn icon-btn--reject" :aria-label="$t('admin.members.reject')" @click="emit('reject', member)">
        <LuX />
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.request {
  @include glass-card(18px);
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-color: rgba(245, 158, 11, 0.35);
}

.avatar {
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  object-fit: cover;

  &--fallback {
    display: grid;
    place-items: center;
    background: $gradient;
    color: #fff;
    font-weight: 700;
  }
}

.info {
  display: flex;
  flex-direction: column;
  gap: 1px;
  flex: 1;
  min-width: 0;
}

.name {
  font-size: 14px;
  font-weight: 700;
  color: $navy;
}

.unit {
  margin-left: 4px;
  font-size: 12px;
  color: $teal;
}

.contact,
.date {
  font-size: 12px;
  color: $text-muted;
}

.message {
  font-size: 12px;
  font-style: italic;
  color: $text-secondary;
}

.actions {
  display: flex;
  gap: 6px;
}

.icon-btn {
  @include pressable;
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 12px;
  font-size: 18px;

  &--approve {
    background: linear-gradient(135deg, #34D399, #10B981);
    color: #fff;
  }

  &--reject {
    background: rgba(239, 68, 68, 0.1);
    color: $danger;
  }
}
</style>
