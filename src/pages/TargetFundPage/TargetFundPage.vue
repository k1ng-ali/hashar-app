<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { LuPencil, LuPlus, LuPower, LuShare2, LuTrash2 } from '@kalimahapps/vue-icons/lu'
import { useAdminStore } from '@/features/admin/store.ts'
import FundForm from '@/features/admin/components/FundForm.vue'
import type { TargetFundUpdate } from '@/features/admin/types.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import type { Contribution } from '@/features/contributions/types.ts'
import FundContributionsList from '@/features/targetFunds/components/FundContributionsList.vue'
import FundHistory from '@/features/targetFunds/components/FundHistory.vue'
import MonthlyChart from '@/features/targetFunds/components/MonthlyChart.vue'
import { useTargetFundsStore } from '@/features/targetFunds/store.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import ProgressBar from '@/shared/components/ProgressBar.vue'
import { copyText } from '@/shared/lib/browser.ts'
import { formatMoney } from '@/shared/lib/format.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import { useNavStore } from '@/shared/stores/useNavStore.ts'
import { useReceiptStore } from '@/shared/stores/useReceiptStore.ts'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const fundsStore = useFundsStore()
const store = useTargetFundsStore()
const adminStore = useAdminStore()
const headerStore = useHeaderStore()
const navStore = useNavStore()
const receiptStore = useReceiptStore()

const fundId = computed(() => Number(route.params.id))
const fund = computed(() => store.detail)

onMounted(() => {
  headerStore.setTitle(t('targetFunds.title'))
  headerStore.setLeftAction(() => (window.history.state?.back ? router.back() : router.push('/finance/funds')))
  navStore.hideTabs()
  void store.fetchDetail(fundId.value)
})

// Переход между сборами без размонтирования страницы
watch(fundId, (id) => {
  if (id) void store.fetchDetail(id)
})

onUnmounted(() => {
  headerStore.reset()
  navStore.showTabs()
})

// ── Handlers ─────────────────────────────────────────────────────────────
async function handleShare() {
  if (await copyText(window.location.href)) headerStore.showNotification(t('targetFunds.shared'))
}

async function handleToggle() {
  if (!fund.value) return
  await adminStore.toggleTargetFund(fund.value.id)
  headerStore.showNotification(t('targetFunds.toggled'))
  // Новая строка в истории изменений приходит только с полной карточкой сбора
  void store.fetchDetail(fund.value.id)
}

const isEditing = ref(false)

async function handleUpdate(payload: TargetFundUpdate) {
  if (!fund.value) return
  try {
    await adminStore.updateTargetFund(fund.value.id, payload)
    isEditing.value = false
    headerStore.showNotification(t('targetFunds.updated'))
    void store.fetchDetail(fund.value.id)
  } catch {
    headerStore.showNotification(t('errors.generic'), 'error')
  }
}

async function handleDelete() {
  if (!fund.value || !window.confirm(t('common.confirmDelete'))) return
  try {
    await adminStore.removeTargetFund(fund.value.id)
    headerStore.showNotification(t('targetFunds.deleted'))
    await router.replace('/finance/funds')
  } catch {
    headerStore.showNotification(t('errors.generic'), 'error')
  }
}

function openReceipt(contribution: Contribution) {
  receiptStore.open(contribution.user_name, contribution.receipt_image)
}
</script>

<template>
  <div class="fund-page">
    <!-- Загрузка -->
    <template v-if="store.isDetailLoading && !fund">
      <CardSkeleton :lines="5" :height="260" />
      <CardSkeleton :lines="3" :height="200" />
    </template>

    <!-- Не найден -->
    <EmptyState v-else-if="!fund" icon="🔍" :title="$t('targetFunds.notFound')">
      <button class="ghost-btn" @click="router.push('/')">{{ $t('common.back') }}</button>
    </EmptyState>

    <template v-else>
      <!-- 1. Карточка сбора -->
      <div class="hero-card">
        <button
          v-if="fund.image"
          type="button"
          class="cover"
          :aria-label="$t('targetFunds.photo')"
          @click="receiptStore.open(fund.title, fund.image)"
        >
          <img :src="fund.image" alt="" />
        </button>

        <div class="hero-top">
          <span class="category">{{ $t(`targetFundCategory.${fund.category}`) }}</span>
          <span class="percent-pill">{{ $t('targetFunds.percentCollected', { n: fund.percent }) }}</span>
        </div>

        <h1 class="title">{{ fund.title }}</h1>
        <p class="description">{{ fund.description }}</p>

        <div class="numbers">
          <div>
            <span class="label">{{ $t('targetFunds.collected') }}</span>
            <div class="collected">{{ formatMoney(fund.collected_amount, fund.currency) }}</div>
          </div>
          <div class="right">
            <span class="label">{{ $t('targetFunds.goal') }}</span>
            <div class="goal">{{ formatMoney(fund.target_amount, fund.currency) }}</div>
          </div>
        </div>

        <ProgressBar :percent="fund.percent" />

        <div class="meta">
          <span class="meta-pill">👥 {{ $t('targetFunds.contributors', { n: fund.contributors_count }) }}</span>
          <span class="meta-pill">🎯 {{ $t('targetFunds.remaining', { amount: formatMoney(fund.remaining_amount, fund.currency) }) }}</span>
        </div>

        <div class="hero-actions">
          <button class="ghost-btn" @click="handleShare"><LuShare2 /> {{ $t('targetFunds.share') }}</button>
          <button v-if="fundsStore.permissions.canManageFinance" class="ghost-btn" @click="isEditing = true">
            <LuPencil /> {{ $t('targetFunds.edit') }}
          </button>
          <button v-if="fundsStore.permissions.canManageFinance" class="ghost-btn" @click="handleToggle">
            <LuPower /> {{ fund.is_active ? $t('targetFunds.closeFund') : $t('targetFunds.reopenFund') }}
          </button>
          <!-- Удалить можно только пустой сбор (создан по ошибке); сбор с деньгами — только закрыть -->
          <button
            v-if="fundsStore.permissions.canDeleteRecords && !fund.has_operations"
            class="ghost-btn ghost-btn--danger"
            @click="handleDelete"
          >
            <LuTrash2 /> {{ $t('common.delete') }}
          </button>
        </div>
      </div>

      <!-- 2. Динамика -->
      <div class="card">
        <div class="card-header">
          <div>
            <h2 class="card-title">{{ $t('targetFunds.dynamics') }}</h2>
            <span class="card-sub">{{ $t('targetFunds.dynamicsSub') }}</span>
          </div>
          <span v-if="fund.average_contribution" class="badge">
            {{ $t('targetFunds.average', { amount: formatMoney(fund.average_contribution, fund.currency) }) }}
          </span>
        </div>
        <MonthlyChart :months="fund.monthly" />
      </div>

      <!-- 3. История поступлений -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">{{ $t('targetFunds.history') }}</h2>
          <span class="card-sub">{{ $t('targetFunds.historyCount', { n: fund.contributions.length }) }}</span>
        </div>
        <FundContributionsList
          v-if="fund.contributions.length"
          :contributions="fund.contributions"
          @open-receipt="openReceipt"
        />
        <EmptyState v-else icon="🚀" :title="$t('targetFunds.emptyContrib')" />
      </div>

      <!-- История изменений сбора: правки цели, описания, фото, закрытие -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">{{ $t('targetFunds.changes') }}</h2>
        </div>
        <FundHistory :fund="fund" />
      </div>

      <!-- 4. Плавающая кнопка -->
      <div class="floating">
        <button
          v-if="fund.is_active"
          class="cta-btn"
          @click="router.push({ path: '/contribute', query: { fund: fund.id } })"
        >
          <LuPlus /> {{ $t('targetFunds.support') }}
        </button>
        <div v-else class="closed-banner">✅ {{ $t('targetFunds.closedBanner') }}</div>
      </div>
    </template>

    <!-- Правка сбора: v-if пересоздаёт форму с актуальными данными при каждом открытии -->
    <BottomSheet :open="isEditing" :title="$t('targetFunds.editTitle')" @close="isEditing = false">
      <FundForm
        v-if="isEditing && fund"
        :initial="fund"
        :currencies="[fund.currency]"
        :base-currency="fund.currency"
        :is-submitting="adminStore.isSubmitting"
        @update="handleUpdate"
      />
    </BottomSheet>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.fund-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 720px;
  margin: 0 auto;
  padding: 16px 16px calc(96px + var(--sab));
}

/* ── Hero ─────────────────────────────────────────────────────────────────── */
.hero-card {
  @include glass-card(24px);
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px;
}

// Фото сбора во всю ширину карточки; по нажатию — на весь экран
.cover {
  display: block;
  width: calc(100% + 40px);
  margin: -20px -20px 0;
  padding: 0;
  border: none;
  border-radius: 24px 24px 0 0;
  overflow: hidden;
  background: $surface-muted;
  cursor: zoom-in;

  img {
    display: block;
    width: 100%;
    max-height: 260px;
    object-fit: cover;
  }
}

.hero-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.category {
  font-size: 12px;
  font-weight: 700;
  color: $teal;
  text-transform: uppercase;
  letter-spacing: 0.4px;
}

.percent-pill {
  padding: 4px 12px;
  border-radius: 20px;
  background: $gradient;
  color: #fff;
  font-size: 12px;
  font-weight: 700;
}

.title {
  margin: 0;
  font-size: var(--fs-xl);
  font-weight: 700;
  color: $navy;
}

.description {
  margin: 0;
  font-size: 14px;
  line-height: 1.5;
  color: $text-secondary;
}

.numbers {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;

  .right {
    text-align: right;
  }
}

.label {
  font-size: 12px;
  color: $text-muted;
}

.collected {
  font-size: 26px;
  font-weight: 700;
  color: $navy;
}

.goal {
  font-size: 16px;
  font-weight: 700;
  color: $text-secondary;
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.meta-pill {
  padding: 6px 12px;
  border-radius: 20px;
  background: rgba(17, 24, 39, 0.06);
  font-size: 12px;
  font-weight: 600;
  color: $navy;
}

.hero-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.ghost-btn {
  @include ghost-button;

  &--danger {
    color: $danger;
  }
}

/* ── Cards ────────────────────────────────────────────────────────────────── */
.card {
  @include glass-card;
  padding: 18px;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.card-title {
  @include section-title;
  font-size: 16px;
}

.card-sub {
  font-size: 12px;
  color: $text-muted;
}

.badge {
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: 20px;
  background: rgba(17, 24, 39, 0.14);
  color: #111827;
  font-size: 11px;
  font-weight: 700;
}

/* ── Floating CTA ─────────────────────────────────────────────────────────── */
.floating {
  position: fixed;
  left: 16px;
  right: 16px;
  bottom: calc(16px + var(--sab));
  z-index: 50;
  display: flex;
  justify-content: center;
}

.cta-btn {
  @include cta-button;
  width: 100%;
  max-width: 480px;
  padding: 16px;
}

.closed-banner {
  @include glass-card(30px);
  padding: 14px 20px;
  font-size: 14px;
  font-weight: 700;
  color: $success;
}

@media (min-width: 768px) {
  .fund-page {
    padding: 24px 24px 110px;
  }

  .floating {
    left: calc(var(--nav-width) + 16px);
  }
}
</style>
