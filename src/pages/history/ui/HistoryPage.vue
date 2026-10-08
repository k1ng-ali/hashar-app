<template>
  <div class="history-page">
    <!-- Top Header Card -->
    <div class="history-top-card">
      <div class="top-meta-row">
        <div class="account-pill">
          Лицевой счет: <strong>кв. {{ fundStore.currentUser.addressUnit }}</strong>
        </div>
        <button class="top-pay-btn" @click="isContributeOpen = true">
          <PlusOutlined />
          <span>Внести платеж</span>
        </button>
      </div>

      <h1 class="history-title">История и статус взносов</h1>
      <p class="history-sub">
        Собственник: {{ fundStore.currentUser.fullName }}
      </p>

      <!-- Financial Status Widget -->
      <div class="account-status-grid">
        <div class="status-box">
          <span class="status-box-label">Статус оплаты:</span>
          <div
            class="status-indicator-chip"
            :class="{
              'status-chip--debt': status.statusType === 'DEBT',
              'status-chip--advance': status.statusType === 'ADVANCE',
              'status-chip--ok': status.statusType === 'OK',
            }"
          >
            <span class="dot"></span>
            <span>
              {{
                status.statusType === 'DEBT'
                  ? 'Задолженность'
                  : status.statusType === 'ADVANCE'
                  ? 'Оплачено авансом'
                  : 'Все оплачено'
              }}
            </span>
          </div>
        </div>

        <div class="status-box">
          <span class="status-box-label">Баланс счета:</span>
          <div
            class="status-box-val font-semibold"
            :class="{
              'text-danger': status.balance < 0,
              'text-success': status.balance > 0,
            }"
          >
            {{ status.balance > 0 ? '+' : '' }}{{ status.balance.toLocaleString() }} ₽
          </div>
        </div>

        <div class="status-box">
          <span class="status-box-label">Всего начислено:</span>
          <div class="status-box-val">{{ status.totalDue.toLocaleString() }} ₽</div>
        </div>

        <div class="status-box">
          <span class="status-box-label">Всего оплачено:</span>
          <div class="status-box-val font-semibold">{{ status.totalPaid.toLocaleString() }} ₽</div>
        </div>
      </div>

      <!-- Debt banner if debtor -->
      <div v-if="status.statusType === 'DEBT'" class="debt-warning-box">
        <div class="debt-warning-left">
          <ExclamationCircleOutlined class="debt-warning-icon" />
          <div>
            <div class="debt-warning-title">
              Задолженность: {{ status.debtAmount.toLocaleString() }} ₽
            </div>
            <div class="debt-warning-sub">
              Не оплачены периоды: {{ status.unpaidPeriods.join(', ') }}
            </div>
          </div>
        </div>
        <button class="debt-warning-btn" @click="isContributeOpen = true">
          Оплатить долг
        </button>
      </div>
    </div>

    <!-- Payments Section -->
    <div class="history-list-section">
      <div class="history-list-header">
        <div class="section-title-wrap">
          <h2 class="section-title">Отправленные платежи</h2>
          <span class="section-counter">{{ filteredContributions.length }} платежей</span>
        </div>

        <!-- Filter Pill Tabs -->
        <div class="history-filters-row">
          <button
            type="button"
            class="filter-pill"
            :class="{ 'filter-pill--active': activeFilter === 'ALL' }"
            @click="activeFilter = 'ALL'"
          >
            Все
          </button>
          <button
            type="button"
            class="filter-pill"
            :class="{ 'filter-pill--active': activeFilter === 'APPROVED' }"
            @click="activeFilter = 'APPROVED'"
          >
            Одобренные
          </button>
          <button
            type="button"
            class="filter-pill"
            :class="{ 'filter-pill--active': activeFilter === 'PENDING' }"
            @click="activeFilter = 'PENDING'"
          >
            На проверке
          </button>
        </div>
      </div>

      <!-- List of Transaction Cards -->
      <div v-if="filteredContributions.length > 0" class="transactions-cards-list">
        <div
          v-for="c in filteredContributions"
          :key="c.id"
          class="tx-card"
        >
          <div class="tx-card-top">
            <div class="tx-date">{{ formatDate(c.createdAt) }}</div>
            <span
              class="tx-status-badge"
              :class="{
                'tx-status--approved': c.status === 'APPROVED',
                'tx-status--pending': c.status === 'PENDING',
                'tx-status--rejected': c.status === 'REJECTED',
              }"
            >
              {{ c.status === 'APPROVED' ? 'Одобрен' : c.status === 'PENDING' ? 'На проверке' : 'Отклонен' }}
            </span>
          </div>

          <div class="tx-card-body">
            <div class="tx-info">
              <div class="tx-category-tag">
                {{ c.category === 'MONTHLY_FEE' ? 'Ежемесячный сбор' : 'Целевой сбор' }}
              </div>
              <div class="tx-purpose">
                {{ c.category === 'MONTHLY_FEE' ? formatPeriodName(c.billingPeriod) : c.targetFundTitle }}
              </div>
              <div v-if="c.commentUser" class="tx-comment">
                «{{ c.commentUser }}»
              </div>
            </div>

            <div class="tx-amount font-bold">
              +{{ c.amount.toLocaleString() }} ₽
            </div>
          </div>

          <!-- Card Footer: Receipt view & Rejection reason -->
          <div class="tx-card-footer">
            <button
              class="tx-receipt-btn"
              @click="fundStore.openReceipt(`Квитанция (${c.amount} ₽)`, c.receiptImagePath)"
            >
              <EyeOutlined />
              <span>Посмотреть чек</span>
            </button>

            <span v-if="c.verifiedAt" class="tx-verified-note">
              Проверено: {{ formatDate(c.verifiedAt) }}
            </span>
          </div>

          <div v-if="c.status === 'REJECTED' && c.commentAdmin" class="tx-rejection-alert">
            <ExclamationCircleOutlined />
            <span>Причина отклонения: {{ c.commentAdmin }}</span>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else class="empty-state-card">
        <div class="empty-state-icon">
          <HistoryOutlined />
        </div>
        <div class="empty-state-title">Платежей не найдено</div>
        <div class="empty-state-desc">
          В выбранной категории пока нет записей о взносах
        </div>
        <button class="empty-state-btn" @click="isContributeOpen = true">
          Внести взнос
        </button>
      </div>
    </div>

    <!-- Make Contribution Modal -->
    <MakeContributionModal v-model:open="isContributeOpen" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import { formatDate, formatPeriodName } from '@/shared/utils/finance';
import MakeContributionModal from '@/features/make-contribution/ui/MakeContributionModal.vue';
import {
  PlusOutlined,
  HistoryOutlined,
  ExclamationCircleOutlined,
  EyeOutlined,
} from '@ant-design/icons-vue';

const fundStore = useFundStore();
const isContributeOpen = ref(false);
const activeFilter = ref<'ALL' | 'APPROVED' | 'PENDING'>('ALL');

const status = computed(() => fundStore.currentUserStatus);

const myContributions = computed(() => {
  return fundStore.contributions.filter((c) => c.userId === fundStore.currentUser.id);
});

const filteredContributions = computed(() => {
  if (activeFilter.value === 'ALL') return myContributions.value;
  return myContributions.value.filter((c) => c.status === activeFilter.value);
});
</script>

<style scoped lang="scss">
.history-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 680px;
  margin: 0 auto;
}

/* History Top Card */
.history-top-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.top-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.account-pill {
  font-size: 0.75rem;
  color: #475569;
  background: #f1f5f9;
  padding: 0.25rem 0.65rem;
  border-radius: 9999px;
}

.top-pay-btn {
  background: #0f172a;
  border: none;
  border-radius: 9999px;
  color: #ffffff;
  font-size: 0.775rem;
  font-weight: 700;
  padding: 0.35rem 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #1e293b;
  }
}

.history-title {
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.history-sub {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.account-status-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-top: 1.15rem;

  @media (min-width: 540px) {
    grid-template-columns: repeat(4, 1fr);
  }
}

.status-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.status-box-label {
  font-size: 0.7rem;
  color: #64748b;
  font-weight: 600;
}

.status-box-val {
  font-size: 1.05rem;
  color: #0f172a;
  font-weight: 700;
}

.status-indicator-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
  width: fit-content;

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }

  &.status-chip--debt {
    background: #fee2e2;
    color: #b91c1c;
    .dot {
      background: #ef4444;
    }
  }

  &.status-chip--advance {
    background: #dcfce7;
    color: #15803d;
    .dot {
      background: #10b981;
    }
  }

  &.status-chip--ok {
    background: #e0e7ff;
    color: #4338ca;
    .dot {
      background: #6366f1;
    }
  }
}

.debt-warning-box {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 16px;
  padding: 0.85rem 1rem;
  margin-top: 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.debt-warning-left {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.debt-warning-icon {
  font-size: 1.25rem;
  color: #ef4444;
}

.debt-warning-title {
  font-size: 0.85rem;
  font-weight: 700;
  color: #991b1b;
}

.debt-warning-sub {
  font-size: 0.75rem;
  color: #b91c1c;
}

.debt-warning-btn {
  background: #ef4444;
  color: #ffffff;
  border: none;
  border-radius: 10px;
  font-size: 0.775rem;
  font-weight: 700;
  padding: 0.45rem 0.85rem;
  cursor: pointer;
  white-space: nowrap;

  &:hover {
    background: #dc2626;
  }
}

/* History List Section */
.history-list-section {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.history-list-header {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;

  @media (min-width: 480px) {
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
  }
}

.section-title-wrap {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.section-title {
  font-size: 1.15rem;
  font-weight: 800;
  color: #0f172a;
}

.section-counter {
  font-size: 0.75rem;
  color: #64748b;
  background: #f1f5f9;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
  font-weight: 600;
}

.history-filters-row {
  display: flex;
  gap: 0.35rem;
}

.filter-pill {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 9999px;
  padding: 0.3rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #f8fafc;
  }

  &--active {
    background: #0f172a;
    border-color: #0f172a;
    color: #ffffff;
  }
}

/* Transaction Cards */
.transactions-cards-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.tx-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 1rem 1.15rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
  transition: all 0.15s ease;

  &:hover {
    border-color: #cbd5e1;
  }
}

.tx-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.tx-date {
  font-size: 0.75rem;
  color: #94a3b8;
  font-weight: 600;
}

.tx-status-badge {
  font-size: 0.675rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;

  &.tx-status--approved {
    background: #dcfce7;
    color: #15803d;
  }

  &.tx-status--pending {
    background: #fef3c7;
    color: #b45309;
  }

  &.tx-status--rejected {
    background: #fee2e2;
    color: #b91c1c;
  }
}

.tx-card-body {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.tx-info {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
}

.tx-category-tag {
  font-size: 0.7rem;
  font-weight: 700;
  color: #6366f1;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.tx-purpose {
  font-size: 0.95rem;
  font-weight: 700;
  color: #0f172a;
}

.tx-comment {
  font-size: 0.775rem;
  color: #64748b;
  font-style: italic;
}

.tx-amount {
  font-size: 1.15rem;
  color: #10b981;
  letter-spacing: -0.01em;
  white-space: nowrap;
}

.tx-card-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.65rem;
  border-top: 1px solid #f1f5f9;
}

.tx-receipt-btn {
  background: #f1f5f9;
  border: none;
  border-radius: 8px;
  padding: 0.35rem 0.7rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: #334155;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #e2e8f0;
    color: #0f172a;
  }
}

.tx-verified-note {
  font-size: 0.7rem;
  color: #94a3b8;
}

.tx-rejection-alert {
  margin-top: 0.65rem;
  background: #fee2e2;
  border-radius: 8px;
  padding: 0.45rem 0.65rem;
  font-size: 0.75rem;
  color: #991b1b;
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

/* Empty State */
.empty-state-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 2.5rem 1.5rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-state-icon {
  font-size: 2.5rem;
  color: #cbd5e1;
  margin-bottom: 0.75rem;
}

.empty-state-title {
  font-size: 1.1rem;
  font-weight: 800;
  color: #0f172a;
}

.empty-state-desc {
  font-size: 0.8rem;
  color: #64748b;
  margin: 0.25rem 0 1.25rem 0;
}

.empty-state-btn {
  background: #0f172a;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  padding: 0.65rem 1.25rem;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
}
</style>
