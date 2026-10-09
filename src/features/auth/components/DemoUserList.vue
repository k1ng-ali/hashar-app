<script setup lang="ts">
import { LuChevronRight } from '@kalimahapps/vue-icons/lu'
import { useI18n } from 'vue-i18n'
import type { DemoUser } from '../types.ts'

defineProps<{
  users: DemoUser[]
  disabled: boolean
}>()

const emit = defineEmits<{
  (e: 'select', user: DemoUser): void
}>()

const { t } = useI18n()

function subtitle(user: DemoUser): string {
  if (user.is_platform_admin) return t('auth.platformAdmin')
  if (!user.memberships.length) return t('auth.noFunds')
  return user.memberships.map((m) => `${t(`roles.${m.role}`)} · ${m.fund_name}`).join(', ')
}
</script>

<template>
  <div class="demo-list">
    <button
      v-for="user in users"
      :key="user.id"
      class="demo-user"
      :disabled="disabled"
      @click="emit('select', user)"
    >
      <img v-if="user.avatar_url" :src="user.avatar_url" alt="" class="avatar" />
      <span v-else class="avatar avatar--fallback">{{ user.full_name.slice(0, 1) }}</span>

      <span class="info">
        <span class="name">{{ user.full_name }}</span>
        <span class="meta">{{ subtitle(user) }}</span>
      </span>

      <LuChevronRight class="chevron" />
    </button>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.demo-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.demo-user {
  @include glass-card(16px);
  @include pressable;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  text-align: left;

  &:disabled {
    opacity: 0.6;
  }
}

.avatar {
  flex-shrink: 0;
  width: 40px;
  height: 40px;
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
  flex: 1;
  min-width: 0;
}

.name {
  font-size: 14px;
  font-weight: 700;
  color: $navy;
}

.meta {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  color: $text-muted;
}

.chevron {
  flex-shrink: 0;
  color: $text-muted;
}
</style>
