<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { LuX } from '@kalimahapps/vue-icons/lu'
import EmptyState from '@/shared/components/EmptyState.vue'
import { formatDateTime } from '@/shared/lib/format.ts'
import type { AuditEventAdmin, AuditFilters } from '../types.ts'

// Типы записей журнала (AuditEvent.entity на бэкенде)
const ENTITIES = [
  'fund',
  'member',
  'contribution',
  'expense',
  'target_fund',
  'announcement',
  'account',
  'requisite',
  'transfer',
  'user',
]
// Сколько полей снимка показывать в карточке
const MAX_DETAILS = 6

defineProps<{
  events: AuditEventAdmin[]
  hasMore: boolean
  isLoadingMore: boolean
}>()

const filters = defineModel<AuditFilters>('filters', { required: true })

const emit = defineEmits<{
  (e: 'change'): void
  (e: 'more'): void
}>()

const { t, te } = useI18n()

function update(patch: Partial<AuditFilters>) {
  filters.value = { ...filters.value, ...patch }
  emit('change')
}

const actionLabel = (action: string) => {
  const key = `platform.audit.actions.${action}`
  return te(key) ? t(key) : action
}

function show(value: unknown): string {
  if (value === null || value === undefined || value === '') return '—'
  if (typeof value === 'object') return JSON.stringify(value)
  return String(value)
}

/** Снимок действия в строки «поле: значение»; изменения [было, стало] — «было → стало». */
function detailLines(details: Record<string, unknown>): string[] {
  const lines: string[] = []
  for (const [key, value] of Object.entries(details)) {
    if (key === 'changes' && value && typeof value === 'object' && !Array.isArray(value)) {
      for (const [field, change] of Object.entries(value as Record<string, unknown>)) {
        lines.push(
          Array.isArray(change) && change.length === 2
            ? `${field}: ${show(change[0])} → ${show(change[1])}`
            : `${field}: ${show(change)}`,
        )
      }
    } else {
      lines.push(`${key}: ${show(value)}`)
    }
  }
  return lines.slice(0, MAX_DETAILS)
}
</script>

<template>
  <div class="audit">
    <div class="filters">
      <div class="chips">
        <button
          type="button"
          class="chip"
          :class="{ 'chip--active': !filters.entity }"
          @click="update({ entity: null })"
        >
          {{ $t('platform.audit.all') }}
        </button>
        <button
          v-for="entity in ENTITIES"
          :key="entity"
          type="button"
          class="chip"
          :class="{ 'chip--active': filters.entity === entity }"
          @click="update({ entity })"
        >
          {{ $t(`platform.audit.entities.${entity}`) }}
        </button>
      </div>
      <button
        v-if="filters.fund_id"
        type="button"
        class="fund-filter"
        @click="update({ fund_id: null, fund_name: null })"
      >
        🏠 {{ filters.fund_name }} <LuX />
      </button>
    </div>

    <div v-if="events.length" class="list">
      <article v-for="event in events" :key="event.id" class="event">
        <div class="event-top">
          <b>{{ actionLabel(event.action) }}</b>
          <span class="meta">{{ formatDateTime(event.created_at) }}</span>
        </div>
        <span class="meta">
          {{ event.actor_name ?? $t('platform.audit.system') }}
          <template v-if="event.fund_name">
            ·
            <button
              type="button"
              class="link"
              @click="update({ fund_id: event.fund_id, fund_name: event.fund_name })"
            >
              {{ event.fund_name }}
            </button>
          </template>
        </span>
        <ul v-if="Object.keys(event.details).length" class="details">
          <li v-for="(line, i) in detailLines(event.details)" :key="i">{{ line }}</li>
        </ul>
      </article>

      <button v-if="hasMore" type="button" class="more-btn" :disabled="isLoadingMore" @click="emit('more')">
        {{ $t('platform.loadMore') }}
      </button>
    </div>
    <EmptyState v-else icon="📜" :title="$t('platform.audit.empty')" />
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.audit {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.filters {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
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

.fund-filter {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 12px;
  border: none;
  border-radius: 20px;
  background: $surface-muted;
  color: $navy;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.event {
  @include glass-card(14px);
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 10px 14px;
}

.event-top {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;

  b {
    font-size: 14px;
    color: $navy;
  }

  .meta {
    flex-shrink: 0;
  }
}

.meta {
  font-size: 12px;
  color: $text-muted;
}

.link {
  padding: 0;
  border: none;
  background: none;
  color: $text-secondary;
  font-size: 12px;
  font-weight: 600;
  text-decoration: underline;
  cursor: pointer;
}

.details {
  margin: 2px 0 0;
  padding: 6px 10px;
  border-radius: 10px;
  background: $surface-muted;
  list-style: none;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px;
  color: $text-secondary;
  overflow-wrap: anywhere;
}

.more-btn {
  @include ghost-button;
  align-self: center;
}
</style>
