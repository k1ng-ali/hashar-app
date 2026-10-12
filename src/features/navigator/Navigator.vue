<script setup lang="ts">
import { computed, ref, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  LuBuilding2,
  LuHouse,
  LuMegaphone,
  LuPlus,
  LuWallet,
} from '@kalimahapps/vue-icons/lu'
import { useContributionsStore } from '@/features/contributions/store.ts'
import { useDashboardStore } from '@/features/dashboard/store.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import { useNavStore } from '@/shared/stores/useNavStore.ts'
import QuickActionsSheet from './QuickActionsSheet.vue'

interface NavLink {
  path: string
  label: string
  badge?: number
}

interface NavItem extends NavLink {
  icon: Component
  dot?: boolean
  // Подразделы — в боковом меню на компьютере
  children?: NavLink[]
}

const route = useRoute()
const router = useRouter()
const navStore = useNavStore()
const dashboardStore = useDashboardStore()
const fundsStore = useFundsStore()
const contributionsStore = useContributionsStore()

const isActionsOpen = ref(false)

// Что ждёт решения совета: чеки и заявки на вступление
const pendingReceipts = computed(() => dashboardStore.summary?.pending_count ?? 0)
const pendingMembers = computed(() => dashboardStore.summary?.pending_members_count ?? 0)
const attentionCount = computed(() =>
  fundsStore.permissions.isCouncil ? pendingReceipts.value + pendingMembers.value : 0,
)

const finance: NavItem = {
  path: '/finance',
  label: 'nav.finance',
  icon: LuWallet,
  children: [
    { path: '/finance/my', label: 'finance.tabs.my' },
    { path: '/finance/expenses', label: 'finance.tabs.expenses' },
    { path: '/finance/funds', label: 'finance.tabs.funds' },
    { path: '/finance/reports', label: 'finance.tabs.reports' },
  ],
}

const fund = computed<NavItem>(() => ({
  path: '/fund',
  label: 'nav.fund',
  icon: LuBuilding2,
  badge: attentionCount.value,
  children: fundsStore.permissions.isCouncil
    ? [
        { path: '/fund/receipts', label: 'fundMenu.receipts', badge: pendingReceipts.value },
        { path: '/fund/members', label: 'fundMenu.members', badge: pendingMembers.value },
        { path: '/fund/accounts', label: 'fundMenu.accounts' },
        { path: '/fund/settings', label: 'fundMenu.settings' },
      ]
    : [],
}))

// Мобильная панель: две вкладки, «+», две вкладки
const leftItems = computed<NavItem[]>(() => [
  { path: '/', label: 'nav.home', icon: LuHouse },
  { ...finance, dot: contributionsStore.hasDebt },
])
const rightItems = computed<NavItem[]>(() => [
  { path: '/news', label: 'nav.news', icon: LuMegaphone },
  fund.value,
])
const allItems = computed(() => [...leftItems.value, ...rightItems.value])

function isActive(path: string) {
  return path === '/' ? route.path === '/' : route.path === path || route.path.startsWith(`${path}/`)
}

// У жителя «+» сразу ведёт к взносу, у совета — меню действий
function handlePlus() {
  if (fundsStore.permissions.canManageFinance) isActionsOpen.value = true
  else void router.push('/contribute')
}
</script>

<template>
  <!-- ═══ Мобильная панель ═══ -->
  <Transition name="fade">
    <nav v-if="navStore.isTabsVisible" class="tabbar" :aria-label="$t('app.name')">
      <router-link
        v-for="item in leftItems"
        :key="item.path"
        :to="item.path"
        class="tab"
        :class="{ 'tab--active': isActive(item.path) }"
      >
        <span class="tab-icon">
          <component :is="item.icon" />
          <span v-if="item.dot" class="tab-dot" />
        </span>
        <span class="tab-label">{{ $t(item.label) }}</span>
      </router-link>

      <button class="plus-btn" :aria-label="$t('quickActions.title')" @click="handlePlus">
        <LuPlus />
      </button>

      <router-link
        v-for="item in rightItems"
        :key="item.path"
        :to="item.path"
        class="tab"
        :class="{ 'tab--active': isActive(item.path) }"
      >
        <span class="tab-icon">
          <component :is="item.icon" />
          <span v-if="item.badge" class="tab-badge">{{ item.badge }}</span>
        </span>
        <span class="tab-label">{{ $t(item.label) }}</span>
      </router-link>
    </nav>
  </Transition>

  <!-- ═══ Компьютер: боковое меню ═══ -->
  <aside class="sidebar">
    <div class="sidebar-brand">
      <span class="brand-logo">🏠</span>
      <div class="brand-text">
        <div class="brand-name">{{ $t('app.name') }}</div>
        <div class="brand-sub">{{ fundsStore.current?.name }}</div>
      </div>
    </div>

    <button class="sidebar-cta" @click="handlePlus">
      <LuPlus />
      {{ fundsStore.permissions.canManageFinance ? $t('quickActions.title') : $t('nav.contribute') }}
    </button>

    <nav class="side-nav">
      <template v-for="item in allItems" :key="item.path">
        <router-link :to="item.path" class="side-link" :class="{ 'side-link--active': isActive(item.path) }">
          <component :is="item.icon" class="side-icon" />
          <span>{{ $t(item.label) }}</span>
          <span v-if="item.dot" class="tab-dot tab-dot--inline" />
          <span v-if="item.badge" class="side-badge">{{ item.badge }}</span>
        </router-link>

        <div v-if="item.children?.length && isActive(item.path)" class="side-children">
          <router-link
            v-for="child in item.children"
            :key="child.path"
            :to="child.path"
            class="side-child"
            :class="{ 'side-child--active': isActive(child.path) }"
          >
            {{ $t(child.label) }}
            <span v-if="child.badge" class="side-badge">{{ child.badge }}</span>
          </router-link>
        </div>
      </template>
    </nav>

    <div class="sidebar-footer">{{ $t('app.footer') }}</div>
  </aside>

  <QuickActionsSheet :open="isActionsOpen" @close="isActionsOpen = false" />
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

/* ═══ Мобильная панель ═══ */
.tabbar {
  position: fixed;
  left: 12px;
  right: 12px;
  bottom: calc(12px + var(--sab));
  z-index: 100;
  display: flex;
  align-items: center;
  gap: 2px;
  height: var(--nav-height);
  padding: 6px;
  border: 1px solid $hairline;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  box-shadow: 0 8px 30px rgba(17, 24, 39, 0.08);
}

.tab {
  @include pressable;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  flex: 1;
  min-width: 0;
  height: 100%;
  border-radius: 999px;
  color: $text-muted;
  text-decoration: none;

  &--active {
    background: $surface-muted;
    color: $navy;

    .tab-label {
      font-weight: 600;
    }
  }
}

.tab-icon {
  position: relative;
  display: grid;
  place-items: center;
  font-size: 21px;
}

.tab-label {
  overflow: hidden;
  max-width: 100%;
  font-size: 11px;
  font-weight: 500;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.plus-btn {
  @include pressable;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  margin: 0 6px;
  border: none;
  border-radius: 50%;
  background: #111827;
  color: #fff;
  font-size: 20px;
}

.tab-dot {
  position: absolute;
  top: -1px;
  right: -4px;
  width: 8px;
  height: 8px;
  border: 2px solid #fff;
  border-radius: 50%;
  background: $danger;

  &--inline {
    position: static;
    margin-left: auto;
    border: none;
  }
}

.tab-badge {
  position: absolute;
  top: -6px;
  right: -10px;
  min-width: 17px;
  padding: 0 4px;
  border: 2px solid #fff;
  border-radius: 9px;
  background: $danger;
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 13px;
  text-align: center;
}

/* ═══ Боковое меню ═══ */
.sidebar {
  display: none;
}

@media (min-width: 768px) {
  .tabbar {
    display: none;
  }

  .sidebar {
    position: fixed;
    top: 0;
    bottom: 0;
    left: 0;
    z-index: 100;
    display: flex;
    flex-direction: column;
    gap: 6px;
    width: var(--nav-width);
    padding: 20px 14px;
    border-right: 1px solid $hairline;
    background: $surface;
  }

  .sidebar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 4px 6px 14px;
  }

  .brand-logo {
    @include icon-circle(40px);
    border-radius: 12px;
    font-size: 20px;
  }

  .brand-text {
    min-width: 0;
  }

  .brand-name {
    font-size: 15px;
    font-weight: 700;
    color: $navy;
  }

  .brand-sub {
    overflow: hidden;
    font-size: 12px;
    color: $text-muted;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .sidebar-cta {
    @include cta-button;
    margin-bottom: 12px;
    padding: 12px 16px;
    font-size: 14px;
  }

  .side-nav {
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .side-link {
    @include pressable;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 11px 12px;
    border-radius: 14px;
    color: $text-secondary;
    font-size: 14px;
    font-weight: 500;
    text-decoration: none;

    &:hover {
      background: $surface-muted;
    }

    &--active {
      background: $surface-muted;
      color: $navy;
      font-weight: 600;
    }
  }

  .side-icon {
    font-size: 19px;
  }

  .side-children {
    display: flex;
    flex-direction: column;
    gap: 2px;
    margin: 2px 0 6px 31px;
    padding-left: 12px;
    border-left: 1px solid $hairline;
  }

  .side-child {
    display: flex;
    align-items: center;
    padding: 8px 10px;
    border-radius: 10px;
    color: $text-secondary;
    font-size: 13px;
    text-decoration: none;

    &:hover {
      background: $surface-muted;
    }

    &--active {
      color: $navy;
      font-weight: 600;
    }
  }

  .side-badge {
    min-width: 20px;
    margin-left: auto;
    padding: 0 6px;
    border-radius: 10px;
    background: $danger;
    color: #fff;
    font-size: 11px;
    font-weight: 700;
    line-height: 20px;
    text-align: center;
  }

  .sidebar-footer {
    margin-top: auto;
    padding: 0 6px;
    font-size: 11px;
    color: $text-muted;
  }
}
</style>
