<script setup lang="ts">
import { computed, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  LuChartPie,
  LuHouse,
  LuMegaphone,
  LuPlus,
  LuReceipt,
  LuShieldCheck,
} from '@kalimahapps/vue-icons/lu'
import { useContributionsStore } from '@/features/contributions/store.ts'
import { useDashboardStore } from '@/features/dashboard/store.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import { useNavStore } from '@/shared/stores/useNavStore.ts'

interface NavItem {
  path: string
  label: string
  icon: Component
  dot?: boolean
  badge?: number
}

const route = useRoute()
const router = useRouter()
const navStore = useNavStore()
const dashboardStore = useDashboardStore()
const fundsStore = useFundsStore()
const contributionsStore = useContributionsStore()

const items = computed<NavItem[]>(() => {
  const list: NavItem[] = [
    { path: '/', label: 'nav.home', icon: LuHouse },
    { path: '/history', label: 'nav.history', icon: LuReceipt, dot: contributionsStore.hasDebt },
    { path: '/news', label: 'nav.news', icon: LuMegaphone },
    { path: '/reports', label: 'nav.reports', icon: LuChartPie },
  ]
  if (fundsStore.permissions.isCouncil) {
    list.push({
      path: '/admin',
      label: 'nav.admin',
      icon: LuShieldCheck,
      badge: dashboardStore.summary?.pending_count ?? 0,
    })
  }
  return list
})

// На мобильном кнопка «+» стоит по центру панели
const leftItems = computed(() => items.value.slice(0, 2))
const rightItems = computed(() => items.value.slice(2))

function isActive(path: string) {
  return path === '/' ? route.path === '/' : route.path.startsWith(path)
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
          <span v-if="item.badge" class="tab-badge">{{ item.badge }}</span>
        </span>
        <span class="tab-label">{{ $t(item.label) }}</span>
      </router-link>

      <button class="center-btn" :aria-label="$t('nav.contribute')" @click="router.push('/contribute')">
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
          <span v-if="item.dot" class="tab-dot" />
          <span v-if="item.badge" class="tab-badge">{{ item.badge }}</span>
        </span>
        <span class="tab-label">{{ $t(item.label) }}</span>
      </router-link>
    </nav>
  </Transition>

  <!-- ═══ Десктоп: боковая панель ═══ -->
  <aside class="sidebar">
    <div class="sidebar-brand">
      <span class="brand-logo">🏠</span>
      <div>
        <div class="brand-name">{{ $t('app.name') }}</div>
        <div class="brand-sub">{{ fundsStore.current?.name }}</div>
      </div>
    </div>

    <button class="sidebar-cta" @click="router.push('/contribute')">
      <LuPlus /> {{ $t('nav.contribute') }}
    </button>

    <router-link
      v-for="item in items"
      :key="item.path"
      :to="item.path"
      class="side-link"
      :class="{ 'side-link--active': isActive(item.path) }"
    >
      <component :is="item.icon" class="side-icon" />
      <span>{{ $t(item.label) }}</span>
      <span v-if="item.dot" class="tab-dot tab-dot--inline" />
      <span v-if="item.badge" class="tab-badge tab-badge--inline">{{ item.badge }}</span>
    </router-link>

    <div class="sidebar-footer">{{ $t('app.footer') }}</div>
  </aside>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

/* ═══ TABBAR ═══ */
.tabbar {
  @include glass-card(30px);
  position: fixed;
  left: 12px;
  right: 12px;
  bottom: calc(12px + var(--sab));
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: space-around;
  height: var(--nav-height);
  padding: 0 6px;
  background: rgba(255, 255, 255, 0.88);
}

.tab {
  @include pressable;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 3px;
  flex: 1;
  min-width: 0;
  padding: 6px 0;
  color: $text-muted;
  text-decoration: none;

  &--active {
    color: $navy;

    .tab-icon {
      background: rgba(78, 190, 194, 0.16);
      color: $teal;
    }
  }
}

.tab-icon {
  position: relative;
  display: grid;
  place-items: center;
  width: 40px;
  height: 30px;
  border-radius: 15px;
  font-size: 20px;
  transition: all 0.2s ease;
}

.tab-label {
  font-size: 10px;
  font-weight: 700;
}

.tab-dot {
  position: absolute;
  top: 2px;
  right: 6px;
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
  top: -4px;
  right: 0;
  min-width: 18px;
  padding: 1px 5px;
  border: 2px solid #fff;
  border-radius: 10px;
  background: $danger;
  color: #fff;
  font-size: 10px;
  font-weight: 800;
  line-height: 1.2;

  &--inline {
    position: static;
    margin-left: auto;
    border: none;
  }
}

.center-btn {
  @include pressable;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  margin: 0 4px;
  border: none;
  border-radius: 50%;
  background: $gradient;
  color: #fff;
  font-size: 26px;
  box-shadow: 0 6px 18px rgba(78, 190, 194, 0.45);
  transform: translateY(-12px);

  &:active {
    transform: translateY(-12px) scale(0.94);
  }
}

/* ═══ SIDEBAR ═══ */
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
    z-index: 110;
    display: flex;
    flex-direction: column;
    gap: 6px;
    width: var(--nav-width);
    padding: 20px 14px;
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(16px);
    border-right: 1px solid rgba(35, 73, 112, 0.06);
  }

  .sidebar-brand {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 6px 18px;
  }

  .brand-logo {
    display: grid;
    place-items: center;
    width: 42px;
    height: 42px;
    border-radius: 14px;
    background: $gradient;
    font-size: 20px;
  }

  .brand-name {
    font-size: 15px;
    font-weight: 800;
    color: $navy;
  }

  .brand-sub {
    font-size: 11px;
    color: $text-muted;
  }

  .sidebar-cta {
    @include cta-button;
    margin-bottom: 14px;
    padding: 12px;
  }

  .side-link {
    @include pressable;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 11px 14px;
    border-radius: 14px;
    color: $text-secondary;
    font-size: 14px;
    font-weight: 600;
    text-decoration: none;

    &:hover {
      background: rgba(78, 190, 194, 0.08);
    }

    &--active {
      background: rgba(78, 190, 194, 0.16);
      color: $navy;

      .side-icon {
        color: $teal;
      }
    }
  }

  .side-icon {
    font-size: 19px;
  }

  .sidebar-footer {
    margin-top: auto;
    padding: 0 8px;
    font-size: 11px;
    color: $text-muted;
  }
}
</style>
