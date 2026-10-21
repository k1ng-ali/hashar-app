<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { LuBell, LuChevronDown, LuChevronLeft } from '@kalimahapps/vue-icons/lu'
import { useAuthStore } from '@/features/auth/store.ts'
import { useCouncilAttention } from '@/features/dashboard/composables/useCouncilAttention.ts'
import FundSwitcherSheet from '@/features/funds/components/FundSwitcherSheet.vue'
import { useFundsStore } from '@/features/funds/store.ts'
import type { MyFund } from '@/features/funds/types.ts'
import ProfileSheet from '@/features/header/ProfileSheet.vue'
import NoticesSheet from '@/features/notices/components/NoticesSheet.vue'
import { useNoticesStore } from '@/features/notices/store.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'

const router = useRouter()
const headerStore = useHeaderStore()
const authStore = useAuthStore()
const fundsStore = useFundsStore()
const noticesStore = useNoticesStore()
const attention = useCouncilAttention()

const isProfileOpen = ref(false)
const isSwitcherOpen = ref(false)

const initials = computed(() => authStore.user?.full_name.slice(0, 1) ?? '?')

// Колокольчик — у совета: дела фонда (чеки, заявки) и уведомления от платформы
const attentionCount = computed(() => attention.value.length + noticesStore.unread)

// Уведомления платформы видит только совет — грузим при смене фонда или роли
watch(
  () => [fundsStore.current?.id, fundsStore.permissions.isCouncil] as const,
  ([fundId, isCouncil]) => {
    if (fundId && isCouncil) void noticesStore.fetch(fundId).catch(() => undefined)
    else noticesStore.reset()
  },
  { immediate: true },
)

// Открыли окно — уведомления прочитаны
watch(
  () => noticesStore.isOpen,
  (open) => {
    if (open) void noticesStore.markRead().catch(() => undefined)
  },
)

function goFromNotices(to: string) {
  noticesStore.isOpen = false
  void router.push(to)
}

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
      <!-- Слева: «назад» на вложенных экранах, иначе — профиль -->
      <button
        v-if="headerStore.leftAction"
        class="circle-btn"
        :aria-label="$t('common.back')"
        @click="headerStore.leftAction()"
      >
        <LuChevronLeft />
      </button>
      <button
        v-else-if="authStore.user"
        class="avatar-btn"
        :aria-label="$t('header.profile')"
        @click="isProfileOpen = true"
      >
        <img v-if="authStore.user.avatar_url" :src="authStore.user.avatar_url" alt="" class="avatar" />
        <span v-else class="avatar avatar--fallback">{{ initials }}</span>
      </button>

      <div class="titles">
        <!-- Переключатель фондов — мелкой строкой над заголовком -->
        <button v-if="fundsStore.current" class="fund-switch" @click="isSwitcherOpen = true">
          <span>{{ fundsStore.current.name }}</span>
          <LuChevronDown />
        </button>
        <h1 class="header-title">{{ headerStore.title || $t('app.name') }}</h1>
      </div>

      <button
        v-if="fundsStore.permissions.isCouncil"
        class="circle-btn"
        :aria-label="$t('attention.title')"
        @click="noticesStore.isOpen = true"
      >
        <LuBell />
        <span v-if="attentionCount" class="bell-dot" />
      </button>
    </div>

    <!-- Уведомление -->
    <Transition name="toast">
      <div v-if="headerStore.notification" class="toast" :class="`toast--${headerStore.notification.type}`">
        {{ headerStore.notification.message }}
      </div>
    </Transition>

    <ProfileSheet :open="isProfileOpen" @close="isProfileOpen = false" />
    <NoticesSheet
      :open="noticesStore.isOpen"
      :notices="noticesStore.items"
      :attention="attention"
      :can-renew="fundsStore.permissions.isChairman"
      @close="noticesStore.isOpen = false"
      @go="goFromNotices"
    />
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
  z-index: 90;
  padding-top: var(--sat);
  background: rgba(242, 242, 243, 0.9);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.header-inner {
  display: flex;
  align-items: center;
  gap: 12px;
  max-width: var(--content-max);
  height: var(--header-height);
  margin: 0 auto;
  padding: 0 16px;
}

.avatar-btn {
  @include pressable;
  flex-shrink: 0;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: none;
}

.avatar {
  display: block;
  width: 42px;
  height: 42px;
  border-radius: 50%;
  object-fit: cover;

  &--fallback {
    display: grid;
    place-items: center;
    background: #E5E7EB;
    color: $navy;
    font-size: 16px;
    font-weight: 600;
  }
}

.circle-btn {
  @include pressable;
  position: relative;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 42px;
  height: 42px;
  border: 1px solid $hairline;
  border-radius: 50%;
  background: $surface;
  color: $navy;
  font-size: 19px;
}

.bell-dot {
  position: absolute;
  top: 9px;
  right: 10px;
  width: 8px;
  height: 8px;
  border: 2px solid #fff;
  border-radius: 50%;
  background: $danger;
}

.titles {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.fund-switch {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  align-self: flex-start;
  max-width: 100%;
  padding: 0;
  border: none;
  background: none;
  color: $text-secondary;
  font-size: 12px;
  font-weight: 500;

  span {
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
}

.header-title {
  margin: 0;
  overflow: hidden;
  font-size: 18px;
  font-weight: 600;
  line-height: 1.25;
  color: $navy;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.toast {
  position: absolute;
  top: calc(var(--header-height) + var(--sat) + 8px);
  left: 50%;
  transform: translateX(-50%);
  max-width: calc(100% - 32px);
  padding: 10px 18px;
  border-radius: 16px;
  font-size: 14px;
  font-weight: 500;
  color: #fff;
  box-shadow: 0 8px 24px rgba(17, 24, 39, 0.18);

  &--success {
    background: #111827;
  }

  &--error {
    background: $danger;
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

// Модификатор ставит App.vue, когда слева есть боковое меню
@media (min-width: 768px) {
  .app-header--shifted {
    left: var(--nav-width);
  }
}
</style>
