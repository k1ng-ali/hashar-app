<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { LuChevronDown, LuChevronLeft } from '@kalimahapps/vue-icons/lu'
import { useAuthStore } from '@/features/auth/store.ts'
import FundSwitcherSheet from '@/features/funds/components/FundSwitcherSheet.vue'
import { useFundsStore } from '@/features/funds/store.ts'
import type { MyFund } from '@/features/funds/types.ts'
import ProfileSheet from '@/features/header/ProfileSheet.vue'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'

const router = useRouter()
const headerStore = useHeaderStore()
const authStore = useAuthStore()
const fundsStore = useFundsStore()

const isProfileOpen = ref(false)
const isSwitcherOpen = ref(false)

const initials = computed(() => authStore.user?.full_name.slice(0, 1) ?? '?')

// ── Handlers ─────────────────────────────────────────────────────────────
async function selectFund(fund: MyFund) {
  isSwitcherOpen.value = false
  if (fund.id !== fundsStore.current?.id) await fundsStore.select(fund.id)
  await router.push('/')
}

function manageFunds() {
  isSwitcherOpen.value = false
  void router.push('/funds')
}
</script>

<template>
  <header class="app-header">
    <div class="header-inner">
      <!-- Слева: «назад» или логотип -->
      <button
        v-if="headerStore.leftAction"
        class="back-btn"
        :aria-label="$t('common.back')"
        @click="headerStore.leftAction()"
      >
        <LuChevronLeft />
      </button>
      <div v-else class="brand-logo">🏠</div>

      <div class="titles">
        <h1 class="header-title">{{ headerStore.title || $t('app.name') }}</h1>
        <!-- Переключатель фондов -->
        <button v-if="fundsStore.current" class="fund-switch" @click="isSwitcherOpen = true">
          {{ fundsStore.current.name }}
          <LuChevronDown />
        </button>
      </div>

      <!-- Справа: профиль -->
      <button v-if="authStore.user" class="user-chip" :aria-label="$t('header.profile')" @click="isProfileOpen = true">
        <img v-if="authStore.user.avatar_url" :src="authStore.user.avatar_url" alt="" class="avatar" />
        <span v-else class="avatar avatar--fallback">{{ initials }}</span>
        <span v-if="fundsStore.current" class="role">{{ $t(`roles.${fundsStore.current.my_role}`) }}</span>
      </button>
    </div>

    <!-- Уведомление -->
    <Transition name="toast">
      <div v-if="headerStore.notification" class="toast" :class="`toast--${headerStore.notification.type}`">
        {{ headerStore.notification.message }}
      </div>
    </Transition>

    <ProfileSheet :open="isProfileOpen" @close="isProfileOpen = false" />
    <FundSwitcherSheet
      :open="isSwitcherOpen"
      :funds="fundsStore.activeFunds"
      :current-id="fundsStore.current?.id ?? null"
      @close="isSwitcherOpen = false"
      @select="selectFund"
      @manage="manageFunds"
    />
  </header>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.app-header {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding-top: var(--sat);
  background: rgba(246, 246, 246, 0.82);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(35, 73, 112, 0.05);
}

.header-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  height: var(--header-height);
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 0 16px;
}

/* ── Left ─────────────────────────────────────────────────────────────────── */
.back-btn {
  @include pressable;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border: none;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.9);
  color: $navy;
  font-size: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.brand-logo {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 38px;
  height: 38px;
  border-radius: 12px;
  background: $gradient;
  font-size: 18px;
}

.titles {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.header-title {
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: var(--fs-lg);
  font-weight: 800;
  line-height: 1.2;
  color: $navy;
}

.fund-switch {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  max-width: 100%;
  padding: 0;
  overflow: hidden;
  border: none;
  background: none;
  color: $teal;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
  text-overflow: ellipsis;
}

/* ── User chip ────────────────────────────────────────────────────────────── */
.user-chip {
  @include pressable;
  display: flex;
  align-items: center;
  gap: 6px;
  flex-shrink: 0;
  padding: 4px 10px 4px 4px;
  border: 1px solid rgba(35, 73, 112, 0.08);
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.9);
}

.avatar {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  object-fit: cover;

  &--fallback {
    display: grid;
    place-items: center;
    background: $gradient;
    color: #fff;
    font-size: 13px;
    font-weight: 700;
  }
}

.role {
  font-size: 12px;
  font-weight: 700;
  color: $navy;
}

/* ── Toast ────────────────────────────────────────────────────────────────── */
.toast {
  position: absolute;
  top: calc(var(--header-height) + var(--sat) + 8px);
  left: 50%;
  transform: translateX(-50%);
  max-width: calc(100% - 32px);
  padding: 10px 18px;
  border-radius: 30px;
  font-size: 14px;
  font-weight: 600;
  color: #fff;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);

  &--success {
    background: linear-gradient(135deg, #34D399, #10B981);
  }

  &--error {
    background: linear-gradient(135deg, #F87171, #EF4444);
  }
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -8px);
}

// Модификатор ставит App.vue, когда слева есть сайдбар
@media (min-width: 768px) {
  .app-header--shifted {
    left: var(--nav-width);
  }
}
</style>
