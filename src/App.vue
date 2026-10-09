<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/features/auth/store.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import Header from '@/features/header/Header.vue'
import Navigator from '@/features/navigator/Navigator.vue'
import ReceiptViewer from '@/shared/components/ReceiptViewer.vue'
import { useNavStore } from '@/shared/stores/useNavStore.ts'

const route = useRoute()
const authStore = useAuthStore()
const fundsStore = useFundsStore()
const navStore = useNavStore()

const isReady = ref(false)

// Шапка — внутри приложения; таб-бар — только когда выбран фонд
const showChrome = computed(() => authStore.isAuthenticated && !route.meta.public)
const showNavigator = computed(() => showChrome.value && !!fundsStore.current && !!route.meta.fund)

// Тема ant-design-vue под фирменные цвета
const antTheme = {
  token: {
    colorPrimary: '#4EBEC2',
    colorLink: '#234970',
    borderRadius: 12,
    fontFamily: "'Manrope', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
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
        <div class="splash-logo">🏠</div>
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
            <component :is="Component" :key="`${fundsStore.fundId}-${route.path}`" />
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
  display: grid;
  place-items: center;
  width: 84px;
  height: 84px;
  margin-bottom: 12px;
  border-radius: 26px;
  background: $gradient;
  font-size: 40px;
  box-shadow: 0 10px 30px rgba(78, 190, 194, 0.4);
  animation: pulse 1.4s ease-in-out infinite;
}

.splash-title {
  font-size: 22px;
  font-weight: 800;
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
