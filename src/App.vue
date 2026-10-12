<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/features/auth/store.ts'
import { useDashboardStore } from '@/features/dashboard/store.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import Header from '@/features/header/Header.vue'
import Navigator from '@/features/navigator/Navigator.vue'
import AppLogo from '@/shared/components/AppLogo.vue'
import ReceiptViewer from '@/shared/components/ReceiptViewer.vue'
import { useNavStore } from '@/shared/stores/useNavStore.ts'

const route = useRoute()
const authStore = useAuthStore()
const fundsStore = useFundsStore()
const navStore = useNavStore()
const dashboardStore = useDashboardStore()

const isReady = ref(false)

// Шапка — внутри приложения; таб-бар — только когда выбран фонд
const showChrome = computed(() => authStore.isAuthenticated && !route.meta.public)
const showNavigator = computed(() => showChrome.value && !!fundsStore.current && !!route.meta.fund)

// Подразделы «Финансов» меняются внутри своей страницы, без её пересоздания
const pageKey = computed(() => (route.path.startsWith('/finance/') ? '/finance' : route.path))

// Счётчики совета (колокольчик, бейджи в навигации) нужны на любом экране
watch(
  () => [fundsStore.fundId, fundsStore.permissions.isCouncil] as const,
  ([fundId, isCouncil]) => {
    if (fundId && isCouncil) void dashboardStore.fetchSummary().catch(() => undefined)
  },
  { immediate: true },
)

// Тема ant-design-vue под фирменные цвета
const antTheme = {
  token: {
    colorPrimary: '#111827',
    colorLink: '#111827',
    borderRadius: 12,
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  },
}

onMounted(async () => {
  await authStore.bootstrap()
  isReady.value = true
})
</script>

<template>
  <a-config-provider :theme="antTheme">
    <!-- ═══ SPLASH ═══ -->
    <Transition name="fade">
      <div v-if="!isReady" class="splash">
        <AppLogo class="splash-logo" :size="84" />
        <div class="splash-title">{{ $t('app.name') }}</div>
        <div class="splash-sub">{{ $t('app.splash') }}</div>
      </div>
    </Transition>

    <!-- ═══ LAYOUT ═══ -->
    <div
      v-if="isReady"
      class="app-layout"
      :class="{
        'app-layout--chrome': showChrome,
        'app-layout--nav': showNavigator,
        'app-layout--no-tabs': !navStore.isTabsVisible || !showNavigator,
      }"
    >
      <Header v-if="showChrome" :class="{ 'app-header--shifted': showNavigator }" />

      <main class="app-content">
        <router-view v-slot="{ Component }">
          <Transition name="fade" mode="out-in">
            <!-- key по фонду: при переключении фонда страница загружает данные заново -->
            <component :is="Component" :key="`${fundsStore.fundId}-${pageKey}`" />
          </Transition>
        </router-view>
      </main>

      <Navigator v-if="showNavigator" />
    </div>

    <ReceiptViewer />
  </a-config-provider>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

/* ═══ SPLASH ═══ */
.splash {
  position: fixed;
  inset: 0;
  z-index: 2000;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  background: #F6F6F6;
}

.splash-logo {
  margin-bottom: 12px;
  animation: pulse 1.4s ease-in-out infinite;
}

.splash-title {
  font-size: 22px;
  font-weight: 700;
  color: $navy;
}

.splash-sub {
  font-size: 14px;
  color: $text-secondary;
}

@keyframes pulse {
  50% {
    transform: scale(1.06);
  }
}

/* ═══ LAYOUT ═══ */
.app-layout {
  min-height: 100vh;
}

.app-layout--chrome .app-content {
  padding-top: calc(var(--header-height) + var(--sat));
  padding-bottom: calc(var(--nav-height) + 28px + var(--sab));
}

.app-layout--no-tabs .app-content {
  padding-bottom: calc(24px + var(--sab));
}

@media (min-width: 768px) {
  .app-layout--chrome .app-content {
    padding-bottom: 32px;
  }

  .app-layout--nav .app-content {
    padding-left: var(--nav-width);
  }
}
</style>
