<template>
  <div class="dashboard-page">
    <!-- Top Mobile Greeting Header -->
    <div class="mobile-greeting-bar">
      <div class="greeting-user">
        <h1 class="greeting-title">
          Привет, {{ fundStore.currentUser.fullName.split(' ')[0] }} 👋
        </h1>
        <div class="greeting-subtitle">
          ЖК «Северная Звезда» • {{ fundStore.currentUser.addressUnit }}
        </div>
      </div>

      <div class="greeting-controls">
        <button
          class="requisites-pill-btn"
          title="Реквизиты фонда"
          @click="isRequisitesSheetOpen = true"
        >
          <QrcodeOutlined />
          <span class="btn-text">Счет</span>
        </button>

        <button
          class="user-chip-btn"
          aria-label="Сменить пользователя"
          @click="isUserSwitcherOpen = true"
        >
          <img
            v-if="fundStore.currentUser.avatarUrl"
            :src="fundStore.currentUser.avatarUrl"
            :alt="fundStore.currentUser.fullName"
            class="user-chip-avatar"
          />
          <div v-else class="user-chip-avatar-fallback">
            {{ fundStore.currentUser.fullName.slice(0, 1) }}
          </div>
          <span class="user-chip-role">
            {{ fundStore.isSuperAdmin ? 'Председатель' : fundStore.isAdmin ? 'Ревизор' : 'Житель' }}
          </span>
          <DownOutlined class="user-chip-chevron" />
        </button>
      </div>
    </div>

    <!-- HERO CARD: The Dark Wallet Card (Exact match with reference Screen 1!) -->
    <div class="hero-wallet-card">
      <div class="hero-card-glow"></div>

      <!-- Top Row: Card pill & Eye toggle -->
      <div class="hero-top-row">
        <div class="hero-status-pill">
          <span class="pill-green-dot"></span>
          <span>кв. {{ fundStore.currentUser.addressUnit }} • {{ fundStore.isSuperAdmin ? 'Председатель' : fundStore.isAdmin ? 'Ревизор' : 'Житель' }}</span>
        </div>

        <button
          class="hero-eye-toggle"
          @click="isBalanceVisible = !isBalanceVisible"
          :title="isBalanceVisible ? 'Скрыть баланс' : 'Показать баланс'"
        >
          <EyeOutlined v-if="isBalanceVisible" />
          <EyeInvisibleOutlined v-else />
        </button>
      </div>

      <!-- Middle: Balance Title & Sum -->
      <div class="hero-balance-section">
        <div class="hero-balance-label">Общий баланс фонда дома</div>
        <div class="hero-balance-value">
          {{ isBalanceVisible ? formatCurrency(fundStore.summary.totalBalance) : '•••••••• ₽' }}
        </div>
        <div class="hero-balance-caption">
          <span class="pulse-indicator"></span>
          <span>Доступно на расчетных счетах ЖК</span>
        </div>
      </div>

      <!-- Bottom: 4 Circular Action Buttons (Matching reference image!) -->
      <div class="hero-actions-grid">
        <!-- 1. Top Up / Contribute -->
        <div class="hero-action-item" @click="openContribute(undefined)">
          <div class="hero-action-circle hero-action-circle--primary">
            <PlusOutlined />
          </div>
          <span class="hero-action-label">Внести взнос</span>
        </div>

        <!-- 2. Expense -->
        <div class="hero-action-item" @click="handleExpenseClick">
          <div class="hero-action-circle">
            <ArrowUpOutlined style="transform: rotate(45deg);" />
          </div>
          <span class="hero-action-label">Расход</span>
        </div>

        <!-- 3. Receipts / History -->
        <div class="hero-action-item" @click="fundStore.activeTab = 'history'">
          <div class="hero-action-circle">
            <FileTextOutlined />
          </div>
          <span class="hero-action-label">Чеки</span>
        </div>

        <!-- 4. Goals / Target Funds -->
        <div class="hero-action-item" @click="scrollToTargetFunds">
          <div class="hero-action-circle">
            <FireOutlined />
          </div>
          <span class="hero-action-label">Сборы</span>
        </div>
      </div>
    </div>

    <!-- Personal Debt / Advance Notice if Resident (Transferred BELOW Fund Card) -->
    <div
      v-if="fundStore.currentUserStatus.statusType === 'DEBT'"
      class="debt-banner-card"
    >
      <div class="debt-banner-left">
        <div class="debt-banner-icon">
          <ExclamationCircleOutlined />
        </div>
        <div>
          <div class="debt-banner-title">
            Неоплаченные взносы: {{ fundStore.currentUserStatus.debtAmount.toLocaleString() }} ₽
          </div>
          <div class="debt-banner-sub">
            Задолженность за {{ fundStore.currentUserStatus.debtMonthsCount }} мес. ({{ fundStore.currentUserStatus.unpaidPeriods.join(', ') }})
          </div>
        </div>
      </div>
      <button class="debt-pay-btn" @click="isContributeModalOpen = true">
        Погасить
      </button>
    </div>

    <div
      v-else-if="fundStore.currentUserStatus.statusType === 'ADVANCE'"
      class="advance-banner-card"
    >
      <div class="advance-banner-icon">
        <CheckCircleOutlined />
      </div>
      <div class="advance-banner-text">
        <span class="advance-banner-title">Взносы оплачены наперед!</span>
        <span class="advance-banner-sub">
          Аванс: {{ fundStore.currentUserStatus.advanceAmount.toLocaleString() }} ₽ • Следующий платеж в ноябре 2026 г.
        </span>
      </div>
    </div>

    <!-- Quick Metrics Ticker (Compact & modern) -->
    <div class="metrics-ticker">
      <div class="metric-pill-item">
        <div class="metric-icon-wrap metric-icon--in">
          <ArrowUpOutlined />
        </div>
        <div class="metric-text-wrap">
          <span class="metric-name">Собрано в сентябре</span>
          <span class="metric-val text-success font-bold">+{{ formatCurrency(fundStore.summary.currentMonthCollected) }}</span>
        </div>
      </div>

      <div class="metric-pill-item">
        <div class="metric-icon-wrap metric-icon--out">
          <ArrowDownOutlined />
        </div>
        <div class="metric-text-wrap">
          <span class="metric-name">Расходы фонда</span>
          <span class="metric-val text-danger font-bold">-{{ formatCurrency(fundStore.summary.totalExpenses) }}</span>
        </div>
      </div>

      <div class="metric-pill-item">
        <div class="metric-icon-wrap metric-icon--audit">
          <TeamOutlined />
        </div>
        <div class="metric-text-wrap">
          <span class="metric-name">Дисциплина оплат</span>
          <span class="metric-val font-bold">
            {{ fundStore.summary.activeResidentsCount - fundStore.summary.debtorsCount }} / {{ fundStore.summary.activeResidentsCount }}
          </span>
        </div>
      </div>
    </div>

    <!-- SECTION: Целевые сборы (Your goals) — Direct match with reference Screen 1! -->
    <section id="target-funds-section" class="goals-section">
      <div class="section-header">
        <div class="section-title-group">
          <h2 class="section-title">Целевые сборы</h2>
          <span class="section-subtitle">Проекты благоустройства и модернизации</span>
        </div>

        <div class="section-header-actions">
          <button
            v-if="fundStore.permissions.canCreateTargetFund"
            class="section-create-btn"
            @click="isCreateTargetFundOpen = true"
          >
            <PlusOutlined />
            <span>Создать сбор</span>
          </button>
          <button class="section-viewall-btn" @click="scrollToTargetFunds">
            Все ({{ fundStore.targetFunds.length }}) <RightOutlined style="font-size: 0.75rem;" />
          </button>
        </div>
      </div>

      <!-- Goals List (Matching reference cards) -->
      <div class="goals-grid">
        <div
          v-for="tf in fundStore.targetFunds"
          :key="tf.id"
          class="goal-card-item"
          :class="{ 'goal-card-item--completed': !tf.isActive }"
          @click="openGoalDetail(tf)"
        >
          <!-- Top Row: Icon + Title + Chevron Right -->
          <div class="goal-card-top">
            <div
              class="goal-card-icon"
              :class="{
                'goal-card-icon--security': tf.category === 'Безопасность',
                'goal-card-icon--landscaping': tf.category === 'Благоустройство',
                'goal-card-icon--lighting': tf.category === 'Энергоэффективность' || tf.category === 'Освещение',
              }"
            >
              <CarOutlined v-if="tf.category === 'Безопасность' || tf.title.toLowerCase().includes('шлагбаум')" />
              <EnvironmentOutlined v-else-if="tf.category === 'Благоустройство' || tf.title.toLowerCase().includes('двор')" />
              <BulbOutlined v-else-if="tf.category === 'Энергоэффективность' || tf.title.toLowerCase().includes('освещение')" />
              <RocketOutlined v-else />
            </div>

            <div class="goal-card-title-wrap">
              <h3 class="goal-card-title">{{ tf.title }}</h3>
              <span class="goal-card-category">{{ tf.category }}</span>
            </div>

            <div class="goal-card-chevron">
              <RightOutlined />
            </div>
          </div>

          <!-- Middle: Collected / Target numbers -->
          <div class="goal-card-numbers">
            <div class="numbers-left">
              <span class="numbers-sub">Собрано</span>
              <span class="numbers-main">{{ getTargetStats(tf).collected.toLocaleString() }} ₽</span>
            </div>
            <div class="numbers-right">
              <span class="numbers-sub">Цель: {{ tf.targetAmount.toLocaleString() }} ₽</span>
              <span class="numbers-percent">{{ getTargetStats(tf).percent }}%</span>
            </div>
          </div>

          <!-- Sleek Pill Progress Bar -->
          <div class="goal-card-progress">
            <div
              class="goal-card-progress-bar"
              :style="{ width: `${Math.min(getTargetStats(tf).percent, 100)}%` }"
              :class="{
                'goal-card-progress-bar--complete': getTargetStats(tf).percent >= 100,
                'goal-card-progress-bar--orange': getTargetStats(tf).percent < 50,
              }"
            ></div>
          </div>

          <!-- Bottom Footer Row -->
          <div class="goal-card-footer">
            <span class="goal-footer-tag" v-if="tf.isActive">
              Осталось: {{ Math.max(0, tf.targetAmount - getTargetStats(tf).collected).toLocaleString() }} ₽
            </span>
            <span class="goal-footer-tag goal-footer-tag--completed" v-else>
              Сбор завершен
            </span>

            <button
              v-if="tf.isActive"
              class="goal-card-quick-contribute-btn"
              @click.stop="openContribute(tf.id)"
            >
              + Внести
            </button>
          </div>
        </div>
      </div>
    </section>

    <!-- SECTION: Последние операции (Transactions stream with tabs) -->
    <section class="operations-section">
      <div class="section-header">
        <div>
          <h2 class="section-title">История операций</h2>
          <span class="section-subtitle">Прозрачные поступления и расходы дома</span>
        </div>

        <div class="tx-filter-pills">
          <button
            class="tx-filter-pill"
            :class="{ active: operationFilter === 'all' }"
            @click="operationFilter = 'all'"
          >
            Все
          </button>
          <button
            class="tx-filter-pill"
            :class="{ active: operationFilter === 'contributions' }"
            @click="operationFilter = 'contributions'"
          >
            Взносы
          </button>
          <button
            class="tx-filter-pill"
            :class="{ active: operationFilter === 'expenses' }"
            @click="operationFilter = 'expenses'"
          >
            Расходы
          </button>
        </div>
      </div>

      <!-- Transactions List -->
      <div class="operations-list">
        <div
          v-for="op in filteredOperations"
          :key="op.id"
          class="op-card-item"
        >
          <div
            class="op-icon-badge"
            :class="op.type === 'CONTRIBUTION' ? 'op-icon-badge--in' : 'op-icon-badge--out'"
          >
            <ArrowUpOutlined v-if="op.type === 'CONTRIBUTION'" />
            <ArrowDownOutlined v-else />
          </div>

          <div class="op-main-content">
            <div class="op-title-row">
              <span class="op-title">{{ op.title }}</span>
              <span
                class="op-amount font-bold"
                :class="op.type === 'CONTRIBUTION' ? 'text-success' : 'text-danger'"
              >
                {{ op.type === 'CONTRIBUTION' ? '+' : '-' }}{{ op.amount.toLocaleString() }} ₽
              </span>
            </div>

            <div class="op-meta-row">
              <span class="op-meta-cat">{{ op.subtitle }}</span>
              <span class="op-dot">•</span>
              <span class="op-date">{{ formatDate(op.date) }}</span>
              <span
                v-if="op.status"
                class="status-pill status-pill--mini"
                :class="'status-pill--' + op.status.toLowerCase()"
              >
                {{ op.status === 'APPROVED' ? 'Одобрен' : op.status === 'PENDING' ? 'Проверяется' : 'Отклонен' }}
              </span>
            </div>
          </div>

          <!-- Receipt Thumbnail if attached -->
          <div v-if="op.receiptImage" class="op-receipt-action">
            <img
              :src="op.receiptImage"
              alt="Чек"
              class="op-receipt-thumb"
              @click="fundStore.openReceipt(op.title, op.receiptImage)"
              title="Нажмите, чтобы просмотреть чек"
            />
          </div>
        </div>
      </div>
    </section>

    <!-- Modals & Drawers -->
    <TargetFundDetailModal
      v-model:open="isGoalDetailOpen"
      :target-fund="selectedGoal"
      @contribute="openContribute"
    />

    <MakeContributionModal
      v-model:open="isContributeModalOpen"
      :target-fund-id="contributeTargetFundId"
    />

    <AddExpenseModal
      v-model:open="isAddExpenseModalOpen"
    />

    <CreateTargetFundModal
      v-model:open="isCreateTargetFundOpen"
    />

    <!-- User Switcher Modal -->
    <UserSwitcherModal
      v-model="isUserSwitcherOpen"
    />

    <!-- Sleek Requisites Sheet Modal -->
    <div v-if="isRequisitesSheetOpen" class="req-modal-backdrop" @click="isRequisitesSheetOpen = false">
      <div class="req-modal-card" @click.stop>
        <div class="req-modal-header">
          <div>
            <div class="req-modal-title">Реквизиты фонда дома</div>
            <div class="req-modal-sub">Официальные счета для переводов без комиссии</div>
          </div>
          <button class="req-close-btn" @click="isRequisitesSheetOpen = false">✕</button>
        </div>

        <div class="req-cards-list">
          <div
            v-for="r in fundStore.paymentRequisites"
            :key="r.id"
            class="req-account-item"
            :class="{ 'is-disabled': !r.isActive }"
          >
            <div class="req-item-top">
              <span class="req-bank-name">{{ r.bankName }}</span>
              <span class="req-active-badge">{{ r.isActive ? 'Активен' : 'Отключен' }}</span>
            </div>
            <div class="req-card-number font-mono">{{ r.cardOrAccountNumber }}</div>
            <div class="req-recipient">Получатель: {{ r.recipientName }}</div>
            <div v-if="r.phoneNumber" class="req-sbp">
              СБП: <strong>{{ r.phoneNumber }}</strong>
            </div>

            <button
              class="req-copy-btn"
              @click="copyReqNumber(r.cardOrAccountNumber)"
            >
              <CopyOutlined /> Скопировать реквизиты
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import { calculateTargetFundStats, formatCurrency, formatDate } from '@/shared/utils/finance';
import { TargetFund } from '@/shared/types';
import MakeContributionModal from '@/features/make-contribution/ui/MakeContributionModal.vue';
import AddExpenseModal from '@/features/manage-expenses/ui/AddExpenseModal.vue';
import CreateTargetFundModal from '@/features/create-target-fund/ui/CreateTargetFundModal.vue';
import TargetFundDetailModal from '@/features/target-fund-detail/ui/TargetFundDetailModal.vue';
import UserSwitcherModal from '@/widgets/user-switcher/ui/UserSwitcherModal.vue';
import { message } from 'ant-design-vue';
import {
  PlusOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  FireOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  FileTextOutlined,
  TeamOutlined,
  RightOutlined,
  DownOutlined,
  CarOutlined,
  EnvironmentOutlined,
  BulbOutlined,
  RocketOutlined,
  QrcodeOutlined,
  CopyOutlined,
} from '@ant-design/icons-vue';

const fundStore = useFundStore();

const isBalanceVisible = ref(true);
const isContributeModalOpen = ref(false);
const isAddExpenseModalOpen = ref(false);
const isCreateTargetFundOpen = ref(false);
const isUserSwitcherOpen = ref(false);
const isRequisitesSheetOpen = ref(false);
const contributeTargetFundId = ref<number | undefined>(undefined);

function copyReqNumber(text: string) {
  navigator.clipboard.writeText(text);
  message.success('Номер реквизитов скопирован');
}

// Goal Detail Modal State (Reference Screen 2)
const isGoalDetailOpen = ref(false);
const selectedGoal = ref<TargetFund | null>(null);

// Operation Stream Filter ('all' | 'contributions' | 'expenses')
const operationFilter = ref<'all' | 'contributions' | 'expenses'>('all');

function getTargetStats(tf: TargetFund) {
  return calculateTargetFundStats(tf, fundStore.contributions);
}

function openGoalDetail(tf: TargetFund) {
  selectedGoal.value = tf;
  isGoalDetailOpen.value = true;
}

function openContribute(targetFundId?: number) {
  contributeTargetFundId.value = targetFundId;
  isContributeModalOpen.value = true;
}

function handleExpenseClick() {
  if (fundStore.permissions.canAddExpense) {
    isAddExpenseModalOpen.value = true;
  } else {
    // For regular resident, switch filter to expenses so they can audit
    operationFilter.value = 'expenses';
    message.info('Просмотр расходов фонда. Вносить расходы могут Председатель и Ревизоры.');
  }
}

function scrollToTargetFunds() {
  const el = document.getElementById('target-funds-section');
  if (el) {
    el.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

// Combined unified operations stream
interface UnifiedOperation {
  id: string;
  type: 'CONTRIBUTION' | 'EXPENSE';
  title: string;
  subtitle: string;
  amount: number;
  date: string;
  status?: string;
  receiptImage?: string;
}

const filteredOperations = computed<UnifiedOperation[]>(() => {
  const contribs: UnifiedOperation[] = fundStore.contributions.map((c) => ({
    id: `c-${c.id}`,
    type: 'CONTRIBUTION',
    title: `${c.userName} (${c.userUnit})`,
    subtitle: c.category === 'MONTHLY_FEE' ? 'Ежемесячный взнос' : c.targetFundTitle || 'Целевой сбор',
    amount: c.amount,
    date: c.createdAt,
    status: c.status,
    receiptImage: c.receiptImagePath,
  }));

  const exps: UnifiedOperation[] = fundStore.expenses.map((e) => ({
    id: `e-${e.id}`,
    type: 'EXPENSE',
    title: e.title,
    subtitle: `${e.category} • ${e.createdByAdminName}`,
    amount: e.amount,
    date: e.createdAt,
    receiptImage: e.receiptImagePaths[0],
  }));

  let combined: UnifiedOperation[] = [];
  if (operationFilter.value === 'all') {
    combined = [...contribs, ...exps];
  } else if (operationFilter.value === 'contributions') {
    combined = contribs;
  } else {
    combined = exps;
  }

  // Sort descending by date
  return combined.sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime()).slice(0, 10);
});
</script>

<style scoped lang="scss">
@use '@/app/styles/variables' as *;

.dashboard-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 720px;
  margin: 0 auto;
}

/* Mobile Greeting Header */
.mobile-greeting-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.greeting-title {
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
  line-height: 1.2;
}

.greeting-subtitle {
  font-size: 0.825rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.user-chip-btn {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  padding: 0.25rem 0.65rem 0.25rem 0.3rem;
  border-radius: 9999px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.15s ease;

  &:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
  }
}

.user-chip-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  object-fit: cover;
}

.user-chip-avatar-fallback {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #4f46e5;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
}

.user-chip-role {
  font-size: 0.775rem;
  font-weight: 700;
  color: #0f172a;
}

.user-chip-chevron {
  font-size: 0.65rem;
  color: #94a3b8;
}

.user-quick-menu {
  max-width: 320px;
  border-radius: 16px;
  padding: 0.5rem;
}

.user-menu-title {
  font-size: 0.7rem;
  text-transform: uppercase;
  font-weight: 700;
  color: #94a3b8;
  padding: 0.4rem 0.75rem;
}

.user-menu-item-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.user-menu-unit {
  font-size: 0.775rem;
  color: #64748b;
  margin-left: 0.25rem;
}

.is-selected {
  background-color: #eef2ff;
}

/* Debt & Advance Notice Banners */
.debt-banner-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
  border: 1px solid #fca5a5;
  border-radius: 20px;
  padding: 1rem 1.25rem;
  gap: 1rem;
}

.debt-banner-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.debt-banner-icon {
  font-size: 1.35rem;
  color: #ef4444;
}

.debt-banner-title {
  font-size: 0.925rem;
  font-weight: 800;
  color: #991b1b;
}

.debt-banner-sub {
  font-size: 0.775rem;
  color: #b91c1c;
}

.debt-pay-btn {
  background: #dc2626;
  color: #ffffff;
  border: none;
  font-size: 0.85rem;
  font-weight: 700;
  padding: 0.5rem 1rem;
  border-radius: 9999px;
  cursor: pointer;
  flex-shrink: 0;
  transition: background 0.15s ease;

  &:hover {
    background: #b91c1c;
  }
}

.advance-banner-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  border: 1px solid #6ee7b7;
  border-radius: 20px;
  padding: 0.85rem 1.15rem;
}

.advance-banner-icon {
  font-size: 1.25rem;
  color: #10b981;
}

.advance-banner-title {
  font-size: 0.875rem;
  font-weight: 700;
  color: #065f46;
  display: block;
}

.advance-banner-sub {
  font-size: 0.775rem;
  color: #047857;
}

/* HERO WALLET CARD: Deep Obsidian Finish (Reference Screen 1) */
.hero-wallet-card {
  background: linear-gradient(145deg, #11141a 0%, #171b24 100%);
  border-radius: 28px;
  padding: 1.65rem 1.5rem 1.5rem 1.5rem;
  color: #ffffff;
  box-shadow: 0 16px 36px rgba(17, 20, 26, 0.25), 0 4px 12px rgba(0, 0, 0, 0.15);
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.hero-card-glow {
  position: absolute;
  top: -40px;
  right: -40px;
  width: 160px;
  height: 160px;
  background: radial-gradient(circle, rgba(79, 70, 229, 0.2) 0%, transparent 70%);
  pointer-events: none;
}

.hero-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.hero-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: rgba(255, 255, 255, 0.1);
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.775rem;
  font-weight: 600;
  color: #e2e8f0;
  backdrop-filter: blur(8px);
}

.pill-green-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background-color: #10b981;
  box-shadow: 0 0 8px #10b981;
}

.hero-eye-toggle {
  background: rgba(255, 255, 255, 0.08);
  border: none;
  width: 34px;
  height: 34px;
  border-radius: 50%;
  color: #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: rgba(255, 255, 255, 0.16);
    color: #ffffff;
  }
}

.hero-balance-section {
  text-align: left;
  margin-bottom: 1.75rem;
}

.hero-balance-label {
  font-size: 0.825rem;
  font-weight: 600;
  color: #94a3b8;
  letter-spacing: 0.02em;
}

.hero-balance-value {
  font-size: 2.35rem;
  font-weight: 800;
  letter-spacing: -0.03em;
  line-height: 1.15;
  margin: 0.35rem 0;
  color: #ffffff;

  @media (max-width: 480px) {
    font-size: 2rem;
  }
}

.hero-balance-caption {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.775rem;
  color: #64748b;
}

.pulse-indicator {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #10b981;
}

/* 4 Circular Action Buttons */
.hero-actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.hero-action-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.45rem;
  cursor: pointer;
  user-select: none;
  transition: transform 0.15s ease;

  &:hover {
    transform: translateY(-2px);

    .hero-action-circle {
      background: #ffffff;
      color: #11141a;
      box-shadow: 0 6px 16px rgba(255, 255, 255, 0.2);
    }
  }

  &:active {
    transform: translateY(1px);
  }
}

.hero-action-circle {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  transition: all 0.2s ease;

  &--primary {
    background: #ffffff;
    color: #11141a;
  }
}

.hero-action-label {
  font-size: 0.725rem;
  font-weight: 600;
  color: #cbd5e1;
  text-align: center;
  white-space: nowrap;
}

/* Quick Metrics Ticker */
.metrics-ticker {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.75rem;

  @media (max-width: 480px) {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }
}

.metric-pill-item {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 0.85rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
}

.metric-icon-wrap {
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;

  &--in {
    background: #dcfce7;
    color: #15803d;
  }

  &--out {
    background: #fee2e2;
    color: #b91c1c;
  }

  &--audit {
    background: #eef2ff;
    color: #4f46e5;
  }
}

.metric-text-wrap {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.metric-name {
  font-size: 0.7rem;
  font-weight: 600;
  color: #94a3b8;
  text-transform: uppercase;
}

.metric-val {
  font-size: 0.95rem;
  color: #0f172a;
}

/* Goals Section (Reference Screen 1) */
.goals-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.section-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
  margin: 0;
}

.section-subtitle {
  font-size: 0.8rem;
  color: #64748b;
}

.section-header-actions {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-create-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: #eef2ff;
  color: #4f46e5;
  border: none;
  border-radius: 9999px;
  font-size: 0.775rem;
  font-weight: 700;
  padding: 0.35rem 0.75rem;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #e0e7ff;
  }
}

.section-viewall-btn {
  background: transparent;
  border: none;
  font-size: 0.85rem;
  font-weight: 700;
  color: #4f46e5;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.25rem;

  &:hover {
    text-decoration: underline;
  }
}

.goals-grid {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.goal-card-item {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 22px;
  padding: 1.15rem 1.25rem;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
  transition: all 0.2s ease;

  &:hover {
    border-color: #cbd5e1;
    transform: translateY(-1px);
    box-shadow: 0 6px 16px rgba(0, 0, 0, 0.05);
  }

  &--completed {
    opacity: 0.8;
    background: #f8fafc;
  }
}

.goal-card-top {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.85rem;
}

.goal-card-icon {
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: #eef2ff;
  color: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  flex-shrink: 0;

  &--security {
    background: #dcfce7;
    color: #16a34a;
  }

  &--landscaping {
    background: #ffedd5;
    color: #ea580c;
  }

  &--lighting {
    background: #e0f2fe;
    color: #0284c7;
  }
}

.goal-card-title-wrap {
  flex: 1;
  min-width: 0;
}

.goal-card-title {
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.goal-card-category {
  font-size: 0.75rem;
  color: #64748b;
}

.goal-card-chevron {
  color: #94a3b8;
  font-size: 0.85rem;
}

.goal-card-numbers {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.numbers-sub {
  font-size: 0.725rem;
  color: #94a3b8;
  display: block;
}

.numbers-main {
  font-size: 1.15rem;
  font-weight: 800;
  color: #0f172a;
}

.numbers-percent {
  font-size: 0.95rem;
  font-weight: 800;
  color: #10b981;
}

.goal-card-progress {
  width: 100%;
  height: 8px;
  background: #f1f5f9;
  border-radius: 9999px;
  overflow: hidden;
  margin-bottom: 0.75rem;
}

.goal-card-progress-bar {
  height: 100%;
  background: #10b981;
  border-radius: 9999px;
  transition: width 0.3s ease;

  &--orange {
    background: #f59e0b;
  }

  &--complete {
    background: #4f46e5;
  }
}

.goal-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.775rem;
}

.goal-footer-tag {
  color: #64748b;
  font-weight: 600;

  &--completed {
    color: #4f46e5;
  }
}

.goal-card-quick-contribute-btn {
  background: #f1f5f9;
  border: none;
  padding: 0.25rem 0.65rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 700;
  color: #0f172a;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #11141a;
    color: #ffffff;
  }
}

/* Operations Stream Section */
.operations-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.tx-filter-pills {
  display: flex;
  align-items: center;
  background: #f1f5f9;
  padding: 0.25rem;
  border-radius: 9999px;
  gap: 0.2rem;
}

.tx-filter-pill {
  border: none;
  background: transparent;
  font-size: 0.75rem;
  font-weight: 600;
  color: #64748b;
  padding: 0.25rem 0.65rem;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.15s ease;

  &.active {
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);
  }
}

.operations-list {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.op-card-item {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 0.85rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.02);
  transition: background 0.15s ease;

  &:hover {
    background: #f8fafc;
  }
}

.op-icon-badge {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1rem;
  flex-shrink: 0;

  &--in {
    background: #dcfce7;
    color: #15803d;
  }

  &--out {
    background: #fee2e2;
    color: #b91c1c;
  }
}

.op-main-content {
  flex: 1;
  min-width: 0;
}

.op-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.op-title {
  font-size: 0.875rem;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.op-amount {
  font-size: 0.95rem;
  white-space: nowrap;
}

.op-meta-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.op-receipt-action {
  margin-left: 0.35rem;
}

.op-receipt-thumb {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
  object-fit: cover;
  cursor: pointer;
  transition: transform 0.15s ease;

  &:hover {
    transform: scale(1.1);
  }
}

.status-pill--mini {
  font-size: 0.65rem;
  padding: 0.05rem 0.4rem;
}

/* Requisites Pill Button in Greeting Controls */
.requisites-pill-btn {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.775rem;
  font-weight: 700;
  color: #0f172a;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.15s ease;

  &:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
  }
}

/* Requisites Sheet Modal */
.req-modal-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: flex-end;
  justify-content: center;

  @media (min-width: 640px) {
    align-items: center;
    padding: 1.5rem;
  }
}

.req-modal-card {
  background: #ffffff;
  width: 100%;
  max-width: 480px;
  max-height: 90vh;
  border-radius: 28px 28px 0 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: slideUp 0.2s ease-out;

  @media (min-width: 640px) {
    border-radius: 28px;
  }
}

.req-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1.25rem 1.5rem 1rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.req-modal-title {
  font-size: 1.1rem;
  font-weight: 800;
  color: #0f172a;
}

.req-modal-sub {
  font-size: 0.775rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.req-close-btn {
  background: #f1f5f9;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  color: #64748b;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.85rem;

  &:hover {
    background: #e2e8f0;
    color: #0f172a;
  }
}

.req-cards-list {
  padding: 1.25rem 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.req-account-item {
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 18px;
  padding: 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;

  &.is-disabled {
    opacity: 0.6;
  }
}

.req-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.req-bank-name {
  font-weight: 800;
  font-size: 0.95rem;
  color: #0f172a;
}

.req-active-badge {
  font-size: 0.7rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
  background: #dcfce7;
  color: #15803d;
}

.req-card-number {
  font-size: 1.1rem;
  font-weight: 700;
  color: #4f46e5;
  letter-spacing: 0.05em;
  margin: 0.25rem 0;
}

.req-recipient,
.req-sbp {
  font-size: 0.8rem;
  color: #475569;
}

.req-copy-btn {
  margin-top: 0.65rem;
  width: 100%;
  padding: 0.65rem;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 12px;
  font-size: 0.8rem;
  font-weight: 700;
  color: #0f172a;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  transition: all 0.15s ease;

  &:hover {
    background: #0f172a;
    color: #ffffff;
    border-color: #0f172a;
  }
}
</style>
