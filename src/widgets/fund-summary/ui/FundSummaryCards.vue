<template>
  <div class="fund-summary-section">
    <div class="grid-stats">
      <!-- 1. Total Balance Card -->
      <div class="summary-card summary-card--primary">
        <div class="summary-card__top">
          <span class="summary-card__label">Текущий остаток фонда</span>
          <div class="summary-card__icon summary-card__icon--primary">
            <WalletOutlined />
          </div>
        </div>
        <div class="summary-card__value">
          {{ formatCurrency(fundStore.summary.totalBalance) }}
        </div>
        <div class="summary-card__footer">
          <span class="indicator-dot indicator-dot--green"></span>
          <span>Доступно на балансе дома</span>
        </div>
      </div>

      <!-- 2. Collected in September -->
      <div class="summary-card">
        <div class="summary-card__top">
          <span class="summary-card__label">Собрано в сентябре</span>
          <div class="summary-card__icon summary-card__icon--success">
            <ArrowUpOutlined />
          </div>
        </div>
        <div class="summary-card__value">
          {{ formatCurrency(fundStore.summary.currentMonthCollected) }}
        </div>
        <div class="summary-card__footer">
          <span class="summary-card__rate">Тариф: {{ fundStore.billingRate.amount }} ₽/мес</span>
        </div>
      </div>

      <!-- 3. Expenses this month -->
      <div class="summary-card">
        <div class="summary-card__top">
          <span class="summary-card__label">Израсходовано (Всего)</span>
          <div class="summary-card__icon summary-card__icon--danger">
            <ArrowDownOutlined />
          </div>
        </div>
        <div class="summary-card__value">
          {{ formatCurrency(fundStore.summary.totalExpenses) }}
        </div>
        <div class="summary-card__footer">
          <span>Сентябрь: {{ formatCurrency(fundStore.summary.currentMonthSpent) }}</span>
        </div>
      </div>

      <!-- 4. Debtors & Pending -->
      <div class="summary-card">
        <div class="summary-card__top">
          <span class="summary-card__label">Контроль и дисциплина</span>
          <div class="summary-card__icon summary-card__icon--warning">
            <TeamOutlined />
          </div>
        </div>
        <div class="summary-card__value">
          {{ fundStore.summary.activeResidentsCount - fundStore.summary.debtorsCount }} / {{ fundStore.summary.activeResidentsCount }}
        </div>
        <div class="summary-card__footer">
          <span v-if="fundStore.summary.debtorsCount > 0" class="text-danger">
            {{ fundStore.summary.debtorsCount }} должн.
          </span>
          <span v-else class="text-success">Все оплатили</span>
          <span class="separator">•</span>
          <span>{{ fundStore.pendingContributions.length }} чеков на проверке</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useFundStore } from '@/entities/fund/model/fundStore';
import { formatCurrency } from '@/shared/utils/finance';
import {
  WalletOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  TeamOutlined,
} from '@ant-design/icons-vue';

const fundStore = useFundStore();
</script>

<style scoped lang="scss">
@use '@/app/styles/variables' as *;

.fund-summary-section {
  margin-bottom: 1.5rem;
}

.summary-card {
  background: $bg-surface;
  border: 1px solid $border-color;
  border-radius: $radius-lg;
  padding: 1.25rem;
  box-shadow: $shadow-sm;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  transition: transform 0.15s ease, box-shadow 0.15s ease;

  @media (max-width: $breakpoint-xs) {
    padding: 1rem;
  }

  &:hover {
    box-shadow: $shadow-md;
  }

  &--primary {
    background: linear-gradient(135deg, #ffffff 0%, #f8faff 100%);
    border-color: #c7d2fe;
  }

  &__top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
  }

  &__label {
    font-size: 0.8rem;
    font-weight: 600;
    color: $text-secondary;
    text-transform: uppercase;
    letter-spacing: 0.03em;
  }

  &__icon {
    width: 36px;
    height: 36px;
    border-radius: $radius-md;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;

    &--primary {
      background-color: $primary-light;
      color: $primary-color;
    }

    &--success {
      background-color: $success-light;
      color: $success-dark;
    }

    &--danger {
      background-color: $danger-light;
      color: $danger-dark;
    }

    &--warning {
      background-color: $warning-light;
      color: $warning-dark;
    }
  }

  &__value {
    font-size: 1.6rem;
    font-weight: 800;
    color: $text-main;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;

    @media (max-width: $breakpoint-xs) {
      font-size: 1.35rem;
    }
  }

  &__footer {
    font-size: 0.8rem;
    color: $text-secondary;
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  &__rate {
    font-weight: 600;
    color: $primary-color;
  }
}

.indicator-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;

  &--green {
    background-color: $success-color;
    box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
  }
}

.text-danger {
  color: $danger-color;
  font-weight: 600;
}

.text-success {
  color: $success-color;
  font-weight: 600;
}

.separator {
  color: $text-muted;
}
</style>
