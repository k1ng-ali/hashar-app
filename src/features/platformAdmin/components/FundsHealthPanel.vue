<script setup lang="ts">
import { computed, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { LuSearch } from '@kalimahapps/vue-icons/lu'
import EmptyState from '@/shared/components/EmptyState.vue'
import { formatDate } from '@/shared/lib/format.ts'
import { formatPhone, phoneHref } from '@/shared/lib/formatters.ts'
import type { Plan } from '@/features/funds/types.ts'
import type { FundCouncilMember, FundHealth, FundHealthFilters, FundSort } from '../types.ts'

const SEARCH_DELAY = 350
const PLANS: Plan[] = ['free', 'pro', 'max', 'individual']
const SORTS: FundSort[] = ['created', 'activity', 'members', 'pending']

defineProps<{
  funds: FundHealth[]
  total: number
  councils: Record<number, FundCouncilMember[]>
  isLoadingMore: boolean
}>()

const filters = defineModel<FundHealthFilters>('filters', { required: true })

const emit = defineEmits<{
  (e: 'change'): void
  (e: 'more'): void
  (e: 'audit', fund: FundHealth): void
}>()

const { t } = useI18n()

const sortOptions = computed(() => SORTS.map((s) => ({ value: s, label: t(`platform.funds.sort.${s}`) })))
const planOptions = computed(() => PLANS.map((p) => ({ value: p, label: t(`plans.${p}`) })))

function update(patch: Partial<FundHealthFilters>) {
  filters.value = { ...filters.value, ...patch }
  emit('change')
}

let searchTimer: ReturnType<typeof setTimeout> | undefined
function onSearch(event: Event) {
  filters.value = { ...filters.value, q: (event.target as HTMLInputElement).value }
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => emit('change'), SEARCH_DELAY)
}
onUnmounted(() => clearTimeout(searchTimer))

// Совет с контактами — по раскрытию карточки
const expanded = ref<number | null>(null)
const toggle = (id: number) => (expanded.value = expanded.value === id ? null : id)
</script>

<template>
  <div class="funds">
    <div class="filters">
      <label class="search">
        <LuSearch />
        <input :value="filters.q" type="search" :placeholder="$t('platform.funds.search')" @input="onSearch" />
      </label>
      <div class="selects">
        <a-select
          :value="filters.sort"
          class="select"
          :options="sortOptions"
          @update:value="(value: unknown) => update({ sort: value as FundSort })"
        />
        <a-select
          :value="filters.plan ?? undefined"
          allow-clear
          class="select"
          :placeholder="$t('platform.funds.allPlans')"
          :options="planOptions"
          @update:value="(value: unknown) => update({ plan: typeof value === 'string' ? (value as Plan) : null })"
        />
      </div>
      <button
        type="button"
        class="chip"
        :class="{ 'chip--active': filters.inactive }"
        @click="update({ inactive: !filters.inactive })"
      >
        {{ $t('platform.funds.inactiveOnly') }}
      </button>
    </div>

    <span class="found">{{ $t('platform.funds.found', { n: total }) }}</span>

    <div v-if="funds.length" class="list">
      <article v-for="fund in funds" :key="fund.id" class="fund">
        <div class="fund-top">
          <div class="fund-name">
            <b>{{ fund.name }}</b>
            <span class="meta">{{ fund.code }}<template v-if="fund.address"> · {{ fund.address }}</template></span>
          </div>
          <div class="plan">
            <span class="badge">{{ $t(`plans.${fund.effective_plan}`) }}</span>
            <span v-if="fund.plan_expires_at" class="meta">
              {{ $t('plans.until', { date: formatDate(fund.plan_expires_at) }) }}
            </span>
          </div>
        </div>

        <div class="stats">
          <span class="stat">
            <b>{{ fund.members_active }}<template v-if="fund.member_limit">/{{ fund.member_limit }}</template></b>
            {{ $t('platform.funds.members') }}
          </span>
          <span class="stat"><b>{{ fund.contributions_30d }}</b> {{ $t('platform.funds.contributions30') }}</span>
          <span class="stat" :class="{ 'stat--warn': fund.stale_contributions }">
            <b>{{ fund.pending_contributions }}</b> {{ $t('platform.funds.pendingReceipts') }}
          </span>
          <span class="stat"><b>{{ fund.pending_members }}</b> {{ $t('platform.funds.pendingMembers') }}</span>
        </div>

        <div class="flags">
          <span v-if="fund.inactive" class="flag flag--warn">⚠️ {{ $t('platform.funds.inactive') }}</span>
          <span v-if="fund.stale_contributions" class="flag flag--warn">
            ⏳ {{ $t('platform.funds.stale', { n: fund.stale_contributions }) }}
          </span>
          <span class="flag">
            {{
              fund.last_activity_at
                ? $t('platform.funds.lastActivity', { date: formatDate(fund.last_activity_at) })
                : $t('platform.funds.noActivity')
            }}
          </span>
        </div>

        <div class="actions">
          <button type="button" class="link" @click="toggle(fund.id)">
            {{ expanded === fund.id ? $t('platform.funds.hideCouncil') : $t('platform.council') }}
          </button>
          <button type="button" class="link" @click="emit('audit', fund)">{{ $t('platform.funds.openAudit') }}</button>
        </div>

        <!-- Председатель и администраторы с контактами -->
        <div v-if="expanded === fund.id" class="council">
          <div v-for="member in councils[fund.id] ?? []" :key="member.user_id" class="council-row">
            <div class="who">
              <span>{{ member.role === 'chairman' ? '👑' : '🛡️' }} {{ member.full_name }}</span>
              <span class="meta">
                {{ $t(`roles.${member.role}`) }}<template v-if="member.address_unit"> · {{ member.address_unit }}</template>
              </span>
            </div>
            <div class="contacts">
              <a v-if="member.phone" :href="phoneHref(member.phone)">{{ formatPhone(member.phone) }}</a>
              <a v-if="member.email" :href="`mailto:${member.email}`">{{ member.email }}</a>
              <span v-if="!member.phone && !member.email" class="meta">—</span>
            </div>
          </div>
          <span v-if="!councils[fund.id]?.length" class="meta">—</span>
        </div>
      </article>

      <button v-if="funds.length < total" type="button" class="more-btn" :disabled="isLoadingMore" @click="emit('more')">
        {{ $t('platform.loadMore') }}
      </button>
    </div>
    <EmptyState v-else icon="🏠" :title="$t('platform.funds.empty')" />
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.funds {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* ── Фильтры ──────────────────────────────────────────────────────────── */
.filters {
  @include glass-card(18px);
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 10px;
  padding: 12px;
}

.search {
  display: flex;
  align-self: stretch;
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

.selects {
  display: grid;
  align-self: stretch;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.select {
  width: 100%;
  min-width: 0;
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

/* ── Карточка фонда ───────────────────────────────────────────────────── */
.list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.fund {
  @include glass-card(16px);
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 12px 14px;
}

.fund-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.fund-name {
  min-width: 0;

  b,
  .meta {
    display: block;
  }

  b {
    color: $navy;
  }
}

.plan {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 2px;
  flex-shrink: 0;
}

.badge {
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(17, 24, 39, 0.16);
  color: #111827;
  font-size: 12px;
  font-weight: 700;
}

.stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 4px 12px;

  @media (min-width: 560px) {
    grid-template-columns: repeat(4, 1fr);
  }
}

.stat {
  font-size: 12px;
  color: $text-secondary;

  b {
    font-size: 15px;
    color: $navy;
  }

  &--warn b {
    color: $warning;
  }
}

.flags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.flag {
  padding: 3px 10px;
  border-radius: 20px;
  background: $surface-muted;
  font-size: 11px;
  color: $text-secondary;

  &--warn {
    background: rgba(217, 119, 6, 0.12);
    color: #92400e;
  }
}

.actions {
  display: flex;
  gap: 16px;
}

.link {
  padding: 0;
  border: none;
  background: none;
  color: $navy;
  font-size: 13px;
  font-weight: 600;
  text-decoration: underline;
  cursor: pointer;
}

/* ── Совет ────────────────────────────────────────────────────────────── */
.council {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 10px;
  border-top: 1px solid rgba(17, 24, 39, 0.08);
}

.council-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 4px 12px;
  font-size: 13px;
  color: $navy;
}

.who {
  display: flex;
  flex-direction: column;
}

.contacts {
  display: flex;
  flex-direction: column;
  align-items: flex-end;

  a {
    color: $teal;
    font-weight: 600;
    word-break: break-all;
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
</style>
