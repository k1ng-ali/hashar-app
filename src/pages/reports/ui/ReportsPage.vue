<template>
  <div class="reports-page">
    <!-- Top Header Card -->
    <div class="reports-top-card">
      <div class="top-row">
        <div class="badge-pill">
          <span class="audit-dot"></span>
          <span>Открытая отчетность ТСЖ</span>
        </div>
      </div>

      <h1 class="page-title">Финансовые отчеты и выгрузка</h1>
      <p class="page-sub">
        Помесячная ведомость, структура расходов и официальные CSV реестры
      </p>

      <!-- CSV Export Action Buttons Grid -->
      <div class="export-buttons-grid">
        <button class="export-btn" @click="exportContributionsCsv">
          <FileExcelOutlined class="icon-income" />
          <div class="export-btn-text">
            <span class="export-btn-title">Реестр взносов</span>
            <span class="export-btn-sub">Формат .CSV</span>
          </div>
        </button>

        <button class="export-btn" @click="exportExpensesCsv">
          <FileExcelOutlined class="icon-expense" />
          <div class="export-btn-text">
            <span class="export-btn-title">Реестр расходов</span>
            <span class="export-btn-sub">Формат .CSV</span>
          </div>
        </button>

        <button class="export-btn" @click="exportDebtorsCsv">
          <FileExcelOutlined class="icon-debt" />
          <div class="export-btn-text">
            <span class="export-btn-title">Ведомость должников</span>
            <span class="export-btn-sub">Формат .CSV</span>
          </div>
        </button>
      </div>
    </div>

    <!-- Monthly Summary Section -->
    <div class="section-card">
      <div class="section-card-header">
        <div class="section-card-title">
          <BarChartOutlined class="icon-indigo" />
          <span>Помесячная ведомость (2026 г.)</span>
        </div>
      </div>

      <div class="monthly-cards-list">
        <div
          v-for="m in monthlyRows"
          :key="m.period"
          class="month-card"
          :class="{ 'month-card--current': m.isCurrent }"
        >
          <div class="month-card-top">
            <span class="month-name">{{ m.title }}</span>
            <span
              class="month-badge"
              :class="m.isCurrent ? 'month-badge--active' : 'month-badge--closed'"
            >
              {{ m.isCurrent ? 'Текущий месяц' : 'Закрыт' }}
            </span>
          </div>

          <div class="month-grid">
            <div class="month-cell">
              <span class="cell-label">Собрано:</span>
              <span class="cell-val text-success font-bold">+{{ m.income.toLocaleString() }} ₽</span>
            </div>

            <div class="month-cell">
              <span class="cell-label">Расходы:</span>
              <span class="cell-val text-danger font-bold">-{{ m.expense.toLocaleString() }} ₽</span>
            </div>

            <div class="month-cell">
              <span class="cell-label">Итог (Сальдо):</span>
              <span
                class="cell-val font-bold"
                :class="m.delta >= 0 ? 'text-success' : 'text-danger'"
              >
                {{ m.delta >= 0 ? '+' : '' }}{{ m.delta.toLocaleString() }} ₽
              </span>
            </div>

            <div class="month-cell">
              <span class="cell-label">Тариф:</span>
              <span class="cell-val">{{ fundStore.billingRate.amount }} ₽/мес</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Category Breakdown & Debtor Overview Grid -->
    <div class="grid-two-blocks">
      <!-- Structure of Expenses -->
      <div class="section-card">
        <div class="section-card-header">
          <div class="section-card-title">
            <PieChartOutlined class="icon-warning" />
            <span>Структура расходов фонда</span>
          </div>
        </div>

        <div class="category-list">
          <div v-for="cat in categoryStats" :key="cat.name" class="cat-stat-item">
            <div class="cat-meta-row">
              <span class="cat-name">{{ cat.name }}</span>
              <span class="cat-amount">{{ cat.total.toLocaleString() }} ₽ ({{ cat.percent }}%)</span>
            </div>
            <!-- Custom Progress Bar -->
            <div class="custom-progress-track">
              <div
                class="custom-progress-fill"
                :style="{ width: `${cat.percent}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Debtors Summary Box -->
      <div class="section-card">
        <div class="section-card-header">
          <div class="section-card-title">
            <WarningOutlined class="icon-danger" />
            <span>Сводка по должникам</span>
          </div>
          <span class="debtors-counter-badge">Должников: {{ debtorsList.length }}</span>
        </div>

        <div v-if="debtorsList.length > 0" class="debtors-list">
          <div
            v-for="d in debtorsList"
            :key="d.user.id"
            class="debtor-item"
          >
            <div class="debtor-main">
              <span class="debtor-unit">кв. {{ d.user.addressUnit }}</span>
              <span class="debtor-name">{{ d.user.fullName }}</span>
            </div>
            <div class="debtor-sum">
              <span class="debtor-amount text-danger font-bold">{{ d.status.debtAmount.toLocaleString() }} ₽</span>
              <span class="debtor-months">за {{ d.status.debtMonthsCount }} мес.</span>
            </div>
          </div>
        </div>

        <div v-else class="empty-debtors">
          <p>Все собственники своевременно оплачивают взносы! 🎉</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import { calculateResidentStatus } from '@/shared/utils/finance';
import { message } from 'ant-design-vue';
import {
  FileExcelOutlined,
  BarChartOutlined,
  PieChartOutlined,
  WarningOutlined,
} from '@ant-design/icons-vue';

const fundStore = useFundStore();

const monthlyRows = computed(() => {
  const approved = fundStore.contributions.filter((c) => c.status === 'APPROVED');
  const expenses = fundStore.expenses;

  // July
  const julyInc = approved
    .filter((c) => c.createdAt.startsWith('2026-07'))
    .reduce((acc, c) => acc + c.amount, 0);
  const julyExp = expenses
    .filter((e) => e.createdAt.startsWith('2026-07'))
    .reduce((acc, e) => acc + e.amount, 0);

  // August
  const augInc = approved
    .filter((c) => c.createdAt.startsWith('2026-08'))
    .reduce((acc, c) => acc + c.amount, 0);
  const augExp = expenses
    .filter((e) => e.createdAt.startsWith('2026-08'))
    .reduce((acc, e) => acc + e.amount, 0);

  // September
  const sepInc = approved
    .filter((c) => c.createdAt.startsWith('2026-09'))
    .reduce((acc, c) => acc + c.amount, 0);
  const sepExp = expenses
    .filter((e) => e.createdAt.startsWith('2026-09'))
    .reduce((acc, e) => acc + e.amount, 0);

  return [
    { period: '2026-09', title: 'Сентябрь 2026', income: sepInc, expense: sepExp, delta: sepInc - sepExp, isCurrent: true },
    { period: '2026-08', title: 'Август 2026', income: augInc, expense: augExp, delta: augInc - augExp, isCurrent: false },
    { period: '2026-07', title: 'Июль 2026', income: julyInc, expense: julyExp, delta: julyInc - julyExp, isCurrent: false },
  ];
});

const categoryStats = computed(() => {
  const total = fundStore.summary.totalExpenses || 1;
  const cats = ['Ремонт', 'Электрика', 'Аварийные работы', 'Хознужды', 'Озеленение', 'Видеонаблюдение'];

  return cats
    .map((name) => {
      const sum = fundStore.expenses
        .filter((e) => e.category === name)
        .reduce((acc, e) => acc + e.amount, 0);
      return {
        name,
        total: sum,
        percent: Math.round((sum / total) * 100),
      };
    })
    .filter((c) => c.total > 0)
    .sort((a, b) => b.total - a.total);
});

const debtorsList = computed(() => {
  return fundStore.users
    .filter((u) => u.role === 'RESIDENT')
    .map((u) => ({
      user: u,
      status: calculateResidentStatus(u.id, fundStore.contributions, fundStore.billingRate),
    }))
    .filter((item) => item.status.statusType === 'DEBT');
});

function downloadCsvFile(content: string, filename: string) {
  const blob = new Blob(['\ufeff' + content], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  message.success(`Файл ${filename} успешно сформирован`);
}

function exportContributionsCsv() {
  let csv = 'ID;Дата;Плательщик;Помещение;Категория;Сумма;Статус\n';
  fundStore.contributions.forEach((c) => {
    csv += `${c.id};"${c.createdAt}";"${c.userName}";"${c.userUnit}";"${c.category}";${c.amount};"${c.status}"\n`;
  });
  downloadCsvFile(csv, `reestr_vznosov_${new Date().toISOString().slice(0, 10)}.csv`);
}

function exportExpensesCsv() {
  let csv = 'ID;Дата;Название;Категория;Сумма;Ответственный;Описание\n';
  fundStore.expenses.forEach((e) => {
    csv += `${e.id};"${e.createdAt}";"${e.title}";"${e.category}";${e.amount};"${e.createdByAdminName}";"${e.description.replace(/"/g, '""')}"\n`;
  });
  downloadCsvFile(csv, `reestr_rashodov_${new Date().toISOString().slice(0, 10)}.csv`);
}

function exportDebtorsCsv() {
  let csv = 'Помещение;Собственник;Телефон;Сумма долга;Кол-во месяцев;Периоды\n';
  debtorsList.value.forEach((d) => {
    csv += `"${d.user.addressUnit}";"${d.user.fullName}";"${d.user.phone}";${d.status.debtAmount};${d.status.debtMonthsCount};"${d.status.unpaidPeriods.join(', ')}"\n`;
  });
  downloadCsvFile(csv, `reestr_dolzhnikov_${new Date().toISOString().slice(0, 10)}.csv`);
}
</script>

<style scoped lang="scss">
.reports-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 680px;
  margin: 0 auto;
}

/* Top Header Card */
.reports-top-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.top-row {
  margin-bottom: 0.5rem;
}

.badge-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: #f1f5f9;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  font-size: 0.725rem;
  font-weight: 700;
  color: #475569;
}

.audit-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #f59e0b;
}

.page-title {
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.page-sub {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 0.15rem;
}

/* Export Buttons */
.export-buttons-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.5rem;
  margin-top: 1.15rem;

  @media (min-width: 480px) {
    grid-template-columns: repeat(3, 1fr);
  }
}

.export-btn {
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 14px;
  padding: 0.75rem 0.85rem;
  display: flex;
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;

  &:hover {
    background: #ffffff;
    border-color: #cbd5e1;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04);
  }
}

.icon-income {
  font-size: 1.25rem;
  color: #10b981;
}

.icon-expense {
  font-size: 1.25rem;
  color: #ef4444;
}

.icon-debt {
  font-size: 1.25rem;
  color: #f59e0b;
}

.icon-indigo {
  color: #4f46e5;
}

.icon-warning {
  color: #f59e0b;
}

.icon-danger {
  color: #ef4444;
}

.export-btn-text {
  display: flex;
  flex-direction: column;
}

.export-btn-title {
  font-size: 0.775rem;
  font-weight: 700;
  color: #0f172a;
}

.export-btn-sub {
  font-size: 0.675rem;
  color: #94a3b8;
}

/* Section Card */
.section-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.section-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.section-card-title {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 1rem;
  font-weight: 800;
  color: #0f172a;
}

/* Monthly Cards List */
.monthly-cards-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.month-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 1rem;
  transition: all 0.15s ease;

  &--current {
    border-color: #c7d2fe;
    background: #fdfefe;
  }
}

.month-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.65rem;
}

.month-name {
  font-size: 0.95rem;
  font-weight: 800;
  color: #0f172a;
}

.month-badge {
  font-size: 0.675rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;

  &--active {
    background: #e0e7ff;
    color: #4338ca;
  }

  &--closed {
    background: #f1f5f9;
    color: #64748b;
  }
}

.month-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.65rem;

  @media (min-width: 480px) {
    grid-template-columns: repeat(4, 1fr);
  }
}

.month-cell {
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.cell-label {
  font-size: 0.7rem;
  color: #64748b;
  font-weight: 600;
}

.cell-val {
  font-size: 0.925rem;
  color: #0f172a;
}

/* Grid Two Blocks */
.grid-two-blocks {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* Category Progress Bars */
.category-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.cat-stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.cat-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.775rem;
}

.cat-name {
  font-weight: 700;
  color: #1e293b;
}

.cat-amount {
  color: #64748b;
  font-weight: 600;
}

.custom-progress-track {
  width: 100%;
  height: 7px;
  background: #f1f5f9;
  border-radius: 9999px;
  overflow: hidden;
}

.custom-progress-fill {
  height: 100%;
  background: #f59e0b;
  border-radius: 9999px;
  transition: width 0.3s ease;
}

/* Debtors List */
.debtors-counter-badge {
  font-size: 0.7rem;
  font-weight: 700;
  background: #fee2e2;
  color: #b91c1c;
  padding: 0.15rem 0.55rem;
  border-radius: 9999px;
}

.debtors-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.debtor-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fef2f2;
  border: 1px solid #fee2e2;
  border-radius: 12px;
  padding: 0.65rem 0.85rem;
}

.debtor-main {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.debtor-unit {
  font-size: 0.775rem;
  font-weight: 800;
  color: #991b1b;
  background: #fee2e2;
  padding: 0.15rem 0.45rem;
  border-radius: 6px;
}

.debtor-name {
  font-size: 0.825rem;
  font-weight: 700;
  color: #1e293b;
}

.debtor-sum {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.debtor-amount {
  font-size: 0.875rem;
}

.debtor-months {
  font-size: 0.675rem;
  color: #94a3b8;
}

.empty-debtors {
  text-align: center;
  padding: 1rem;
  font-size: 0.85rem;
  color: #10b981;
}
</style>
