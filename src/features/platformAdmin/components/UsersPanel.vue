<script setup lang="ts">
import { onUnmounted } from 'vue'
import { LuSearch } from '@kalimahapps/vue-icons/lu'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import { formatDate, formatDateTime } from '@/shared/lib/format.ts'
import { formatPhone, phoneHref } from '@/shared/lib/formatters.ts'
import type { UserAdmin, UserDetailAdmin, UserFilter } from '../types.ts'

const SEARCH_DELAY = 350
const FILTERS: UserFilter[] = ['all', 'unverified', 'admins', 'deleted']

defineProps<{
  users: UserAdmin[]
  total: number
  detail: UserDetailAdmin | null
  isLoadingMore: boolean
}>()

const query = defineModel<string>('query', { required: true })
const filter = defineModel<UserFilter>('filter', { required: true })

const emit = defineEmits<{
  (e: 'change'): void
  (e: 'more'): void
  (e: 'open', user: UserAdmin): void
  (e: 'close'): void
}>()

function setFilter(value: UserFilter) {
  filter.value = value
  emit('change')
}

let searchTimer: ReturnType<typeof setTimeout> | undefined
function onSearch(event: Event) {
  query.value = (event.target as HTMLInputElement).value
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => emit('change'), SEARCH_DELAY)
}
onUnmounted(() => clearTimeout(searchTimer))
</script>

<template>
  <div class="users">
    <div class="filters">
      <label class="search">
        <LuSearch />
        <input :value="query" type="search" :placeholder="$t('platform.users.search')" @input="onSearch" />
      </label>
      <div class="chips">
        <button
          v-for="value in FILTERS"
          :key="value"
          type="button"
          class="chip"
          :class="{ 'chip--active': filter === value }"
          @click="setFilter(value)"
        >
          {{ $t(`platform.users.filters.${value}`) }}
        </button>
      </div>
    </div>

    <span class="found">{{ $t('platform.users.found', { n: total }) }}</span>

    <div v-if="users.length" class="list">
      <button v-for="user in users" :key="user.id" type="button" class="user" @click="emit('open', user)">
        <div class="user-top">
          <b>{{ user.full_name }}</b>
          <span v-if="user.is_platform_admin" class="badge">{{ $t('platform.users.admin') }}</span>
          <span v-if="user.deleted_at" class="badge badge--muted">{{ $t('platform.users.deleted') }}</span>
          <span v-else-if="!user.verified_at" class="badge badge--warn">{{ $t('platform.users.unverified') }}</span>
        </div>
        <span class="meta">
          {{ [user.phone ? formatPhone(user.phone) : null, user.email].filter(Boolean).join(' · ') || '—' }}
        </span>
        <span class="meta">
          {{ $t('platform.users.fundsCount', { n: user.funds_count }) }} ·
          {{
            user.last_seen_at
              ? $t('platform.users.lastSeen', { date: formatDate(user.last_seen_at) })
              : $t('platform.users.neverSeen')
          }}
          <template v-if="user.providers.length"> · {{ user.providers.join(', ') }}</template>
        </span>
      </button>

      <button v-if="users.length < total" type="button" class="more-btn" :disabled="isLoadingMore" @click="emit('more')">
        {{ $t('platform.loadMore') }}
      </button>
    </div>
    <EmptyState v-else icon="👤" :title="$t('platform.users.empty')" />

    <!-- Карточка пользователя — только просмотр -->
    <BottomSheet :open="!!detail" :title="detail?.full_name ?? ''" @close="emit('close')">
      <div v-if="detail" class="detail">
        <dl class="facts">
          <dt>{{ $t('platform.users.phone') }}</dt>
          <dd>
            <a v-if="detail.phone" :href="phoneHref(detail.phone)">{{ formatPhone(detail.phone) }}</a>
            <template v-else>—</template>
          </dd>
          <dt>Email</dt>
          <dd>{{ detail.email ?? '—' }}</dd>
          <dt>{{ $t('platform.users.registered') }}</dt>
          <dd>{{ formatDate(detail.created_at) }}</dd>
          <dt>{{ $t('platform.users.verifiedAt') }}</dt>
          <dd>{{ detail.verified_at ? formatDate(detail.verified_at) : $t('platform.users.unverified') }}</dd>
          <dt>{{ $t('platform.users.lastSeenLabel') }}</dt>
          <dd>{{ detail.last_seen_at ? formatDateTime(detail.last_seen_at) : '—' }}</dd>
          <dt>{{ $t('platform.users.sessions') }}</dt>
          <dd>{{ detail.sessions_active }}</dd>
          <dt>{{ $t('platform.users.providers') }}</dt>
          <dd>{{ detail.providers.length ? detail.providers.join(', ') : $t('platform.users.passwordOnly') }}</dd>
        </dl>

        <h3 class="detail-title">{{ $t('platform.users.memberships') }}</h3>
        <div v-if="detail.memberships.length" class="memberships">
          <div v-for="m in detail.memberships" :key="m.fund_id" class="membership">
            <div>
              <b>{{ m.fund_name }}</b>
              <span class="meta">
                {{ $t(`roles.${m.role}`) }}<template v-if="m.address_unit"> · {{ m.address_unit }}</template>
              </span>
            </div>
            <span class="badge badge--muted">{{ $t(`memberStatus.${m.status}`) }}</span>
          </div>
        </div>
        <p v-else class="meta">{{ $t('platform.users.noFunds') }}</p>
      </div>
    </BottomSheet>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.users {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filters {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px;
}

.search {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  border: 1px solid $field-border;
  border-radius: 12px;
  background: #fff;
  color: $text-muted;

  input {
    flex: 1;
    min-width: 0;
    padding: 10px 0;
    border: none;
    outline: none;
    background: transparent;
    font-size: 14px;
    color: $navy;
  }
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

  &--active {
    border-color: transparent;
    background: $gradient;
    color: #fff;
  }
}

.found {
  font-size: 13px;
  font-weight: 700;
  color: $navy;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.user {
  @include glass-card(14px);
  @include pressable;
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 10px 14px;
  cursor: pointer;
  text-align: left;
}

.user-top {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;

  b {
    color: $navy;
  }
}

.badge {
  padding: 1px 8px;
  border-radius: 20px;
  background: #111827;
  color: #fff;
  font-size: 11px;
  font-weight: 600;

  &--muted {
    background: $surface-muted;
    color: $text-secondary;
  }

  &--warn {
    background: rgba(217, 119, 6, 0.12);
    color: #92400e;
  }
}

.meta {
  font-size: 12px;
  color: $text-muted;
}

.more-btn {
  @include ghost-button;
  align-self: center;
}

/* ── Карточка пользователя ────────────────────────────────────────────── */
.detail {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.facts {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 6px 14px;
  margin: 0;
  font-size: 13px;

  dt {
    color: $text-muted;
  }

  dd {
    margin: 0;
    color: $navy;
    overflow-wrap: anywhere;
  }

  a {
    color: $navy;
    font-weight: 600;
  }
}

.detail-title {
  @include section-title;
  font-size: 15px;
}

.memberships {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.membership {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 14px;
  color: $navy;

  b,
  .meta {
    display: block;
  }
}
</style>
