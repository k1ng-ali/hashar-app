<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import {
  LuBuilding2,
  LuCreditCard,
  LuLandmark,
  LuLayers,
  LuLogOut,
  LuReceipt,
  LuSettings,
  LuShare2,
  LuUsers,
} from '@kalimahapps/vue-icons/lu'
import RequisitesSheet from '@/features/dashboard/components/RequisitesSheet.vue'
import { useDashboardStore } from '@/features/dashboard/store.ts'
import FundCodeCard from '@/features/funds/components/FundCodeCard.vue'
import { useFundsStore } from '@/features/funds/store.ts'
import { errorDetail } from '@/shared/api/http.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import MenuRow from '@/shared/components/MenuRow.vue'
import { copyText } from '@/shared/lib/browser.ts'
import { formatDate, formatMoney } from '@/shared/lib/format.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'

const { t } = useI18n()
const router = useRouter()
const fundsStore = useFundsStore()
const dashboardStore = useDashboardStore()
const headerStore = useHeaderStore()

const isInviteOpen = ref(false)
const isRequisitesOpen = ref(false)

const fund = computed(() => fundsStore.current)
const summary = computed(() => dashboardStore.summary)
const baseAccount = computed(() => fund.value?.accounts.find((a) => a.currency === fund.value?.base_currency) ?? null)

onMounted(async () => {
  headerStore.setTitle(t('nav.fund'))
  await Promise.all([dashboardStore.fetchSummary(), dashboardStore.fetchRequisites(), fundsStore.fetchCurrent()])
})

onUnmounted(() => {
  headerStore.reset()
})

// ── Handlers ─────────────────────────────────────────────────────────────
async function handleCopy(value: string) {
  if (await copyText(value)) headerStore.showNotification(t('common.copied'))
}

async function handleLeave() {
  if (!fund.value || !window.confirm(t('funds.leaveConfirm', { name: fund.value.name }))) return
  try {
    await fundsStore.leave()
    await router.push(fundsStore.current ? '/' : '/funds')
  } catch (error) {
    // Председатель не может выйти, пока не передал права
    const transferFirst = errorDetail(error) === 'Transfer chairman rights first'
    headerStore.showNotification(transferFirst ? t('funds.leaveChairman') : t('errors.generic'), 'error', 3500)
  }
}
</script>

<template>
  <div v-if="fund" class="fund-page">
    <!-- 1. Карточка фонда -->
    <section class="hero">
      <span class="hero-icon"><LuBuilding2 /></span>
      <div class="hero-text">
        <h2 class="hero-name">{{ fund.name }}</h2>
        <span v-if="fund.address" class="hero-address">{{ fund.address }}</span>
      </div>
      <div class="chips">
        <button class="chip" @click="handleCopy(fund.code)">{{ $t('fundMenu.code', { code: fund.code }) }}</button>
        <span class="chip">{{ $t(`plans.${fund.plan.effective_plan}`) }}</span>
        <span class="chip">{{ $t('funds.membersCount', { n: fund.plan.members_count }) }}</span>
        <span class="chip chip--role">{{ $t(`roles.${fund.my_role}`) }}</span>
      </div>
    </section>

    <!-- 2. Управление — совет фонда -->
    <template v-if="fundsStore.permissions.isCouncil">
      <h3 class="group-title">{{ $t('fundMenu.manage') }}</h3>
      <div class="group">
        <MenuRow
          :title="$t('fundMenu.receipts')"
          :hint="$t('fundMenu.receiptsHint', { n: summary?.pending_count ?? 0 })"
          :badge="summary?.pending_count"
          @click="router.push('/fund/receipts')"
        >
          <template #icon><LuReceipt /></template>
        </MenuRow>
        <MenuRow
          :title="$t('fundMenu.members')"
          :hint="$t('fundMenu.membersHint', { n: fund.plan.members_count, requests: summary?.pending_members_count ?? 0 })"
          :badge="summary?.pending_members_count"
          @click="router.push('/fund/members')"
        >
          <template #icon><LuUsers /></template>
        </MenuRow>
        <MenuRow
          :title="$t('fundMenu.accounts')"
          :hint="baseAccount ? formatMoney(baseAccount.balance, baseAccount.currency) : undefined"
          @click="router.push('/fund/accounts')"
        >
          <template #icon><LuLandmark /></template>
        </MenuRow>
        <MenuRow
          :title="$t('fundMenu.settings')"
          :hint="
            fund.plan.expires_at && fund.plan.effective_plan !== 'free'
              ? $t('fundMenu.settingsHintUntil', { plan: $t(`plans.${fund.plan.effective_plan}`), date: formatDate(fund.plan.expires_at) })
              : $t(`plans.${fund.plan.effective_plan}`)
          "
          @click="router.push('/fund/settings')"
        >
          <template #icon><LuSettings /></template>
        </MenuRow>
      </div>
    </template>

    <!-- 3. Для всех участников -->
    <h3 class="group-title">{{ $t('fundMenu.general') }}</h3>
    <div class="group">
      <MenuRow :title="$t('fundMenu.invite')" :hint="$t('fundMenu.inviteHint')" @click="isInviteOpen = true">
        <template #icon><LuShare2 /></template>
      </MenuRow>
      <MenuRow :title="$t('requisites.title')" :hint="$t('requisites.subtitle')" @click="isRequisitesOpen = true">
        <template #icon><LuCreditCard /></template>
      </MenuRow>
      <MenuRow :title="$t('header.myFunds')" :hint="$t('fundMenu.myFundsHint')" @click="router.push('/funds')">
        <template #icon><LuLayers /></template>
      </MenuRow>
    </div>

    <div class="group">
      <MenuRow :title="$t('funds.leave')" danger @click="handleLeave">
        <template #icon><LuLogOut /></template>
      </MenuRow>
    </div>

    <BottomSheet :open="isInviteOpen" :title="$t('fundMenu.invite')" @close="isInviteOpen = false">
      <FundCodeCard :code="fund.code" @copy="handleCopy" />
    </BottomSheet>
    <RequisitesSheet :open="isRequisitesOpen" :requisites="dashboardStore.requisites" @close="isRequisitesOpen = false" />
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.fund-page {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 720px;
  margin: 0 auto;
  padding: 16px;
}

.hero {
  @include glass-card(24px);
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 12px 14px;
  align-items: center;
  padding: 18px;
}

.hero-icon {
  @include icon-circle(52px);
  border-radius: 16px;
  font-size: 24px;
}

.hero-text {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.hero-name {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: $navy;
}

.hero-address {
  font-size: 13px;
  color: $text-secondary;
}

.chips {
  grid-column: 1 / -1;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  padding: 5px 10px;
  border: none;
  border-radius: 10px;
  background: $surface-muted;
  color: $navy;
  font-size: 12px;
  font-weight: 500;

  &--role {
    background: #111827;
    color: #fff;
  }
}

button.chip {
  @include pressable;
  font-family: 'SF Mono', 'Consolas', monospace;
  letter-spacing: 0.04em;
}

.group-title {
  margin: 8px 4px 0;
  font-size: 13px;
  font-weight: 500;
  color: $text-secondary;
}

.group {
  @include glass-card(20px);
  overflow: hidden;
}

@media (min-width: 768px) {
  .fund-page {
    padding: 24px;
  }
}
</style>
