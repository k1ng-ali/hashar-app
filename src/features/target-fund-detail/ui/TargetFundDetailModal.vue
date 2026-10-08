<template>
  <div v-if="isOpen" class="drawer-backdrop" @click="isOpen = false">
    <div v-if="targetFund" class="goal-detail-drawer" @click.stop>
      <!-- Top Mobile App Header (Back < | Title | More ⋮) -->
      <header class="goal-topbar">
        <button class="topbar-btn" @click="isOpen = false" aria-label="Назад">
          <LeftOutlined />
        </button>
        <h2 class="topbar-title">Детали сбора</h2>
        <div class="menu-dropdown-wrapper">
          <button class="topbar-btn" aria-label="Опции" @click="isMenuOpen = !isMenuOpen">
            <MoreOutlined />
          </button>
          <div v-if="isMenuOpen" class="custom-dropdown-menu">
            <button class="custom-menu-item" @click="copyShareLink(); isMenuOpen = false">
              <ShareAltOutlined style="margin-right: 0.5rem;" />
              <span>Поделиться сбором</span>
            </button>
            <button
              v-if="fundStore.permissions.canToggleTargetFund"
              class="custom-menu-item"
              @click="toggleActiveStatus(); isMenuOpen = false"
            >
              <CheckCircleOutlined style="margin-right: 0.5rem;" />
              <span>{{ targetFund.isActive ? 'Завершить сбор' : 'Возобновить сбор' }}</span>
            </button>
          </div>
        </div>
      </header>

      <!-- Scrollable Main Content -->
      <div class="goal-scroll-body">
        <!-- Goal Identity Hero Card -->
        <div class="goal-hero-card">
          <div class="goal-icon-row">
            <div
              class="goal-icon-badge"
              :class="{
                'goal-icon-badge--security': targetFund.category === 'Безопасность',
                'goal-icon-badge--landscaping': targetFund.category === 'Благоустройство',
                'goal-icon-badge--lighting': targetFund.category === 'Энергоэффективность' || targetFund.category === 'Освещение',
              }"
            >
              <CarOutlined v-if="targetFund.category === 'Безопасность' || targetFund.title.toLowerCase().includes('шлагбаум')" />
              <EnvironmentOutlined v-else-if="targetFund.category === 'Благоустройство' || targetFund.title.toLowerCase().includes('двор')" />
              <BulbOutlined v-else-if="targetFund.category === 'Энергоэффективность' || targetFund.title.toLowerCase().includes('освещение')" />
              <RocketOutlined v-else />
            </div>

            <div class="goal-status-pill">
              <span class="status-dot"></span>
              <span>+{{ stats.percent }}% собрано</span>
            </div>
          </div>

          <h1 class="goal-title">{{ targetFund.title }}</h1>
          <p class="goal-description">{{ targetFund.description }}</p>

          <!-- Progress and Numbers -->
          <div class="goal-numbers-row">
            <div>
              <span class="numbers-label">Собрано</span>
              <div class="numbers-collected">{{ stats.collected.toLocaleString() }} ₽</div>
            </div>
            <div class="text-right">
              <span class="numbers-label">Целевая сумма</span>
              <div class="numbers-target">{{ targetFund.targetAmount.toLocaleString() }} ₽</div>
            </div>
          </div>

          <!-- Sleek Pill Progress Bar -->
          <div class="goal-progress-track">
            <div
              class="goal-progress-fill"
              :style="{ width: `${Math.min(stats.percent, 100)}%` }"
              :class="{
                'goal-progress-fill--completed': stats.percent >= 100,
                'goal-progress-fill--orange': stats.percent < 50,
              }"
            ></div>
          </div>

          <div class="goal-sub-meta">
            <div class="meta-pill">
              <TeamOutlined />
              <span>{{ stats.contributorsCount || fundContributions.length }} участников</span>
            </div>
            <div class="meta-pill">
              <CheckOutlined />
              <span>Осталось: {{ Math.max(0, targetFund.targetAmount - stats.collected).toLocaleString() }} ₽</span>
            </div>
          </div>
        </div>

        <!-- Saving Analytics (Bar Chart matching reference image!) -->
        <div class="analytics-card">
          <div class="analytics-header">
            <div>
              <h3 class="analytics-title">Динамика сборов</h3>
              <span class="analytics-subtitle">Помесячные поступления в проект</span>
            </div>
            <div class="analytics-badge">
              <span>Средний взнос: ~{{ averageContribution.toLocaleString() }} ₽</span>
            </div>
          </div>

          <!-- Vertical Bar Chart -->
          <div class="barchart-container">
            <div
              v-for="bar in monthlyAnalytics"
              :key="bar.month"
              class="barchart-col"
            >
              <div class="barchart-bar-wrapper">
                <span v-if="bar.amount > 0" class="barchart-tooltip">
                  {{ (bar.amount / 1000).toFixed(0) }}k
                </span>
                <div
                  class="barchart-bar"
                  :style="{ height: `${Math.max(bar.percentage, 12)}%` }"
                  :class="{ 'barchart-bar--active': bar.isCurrentMonth }"
                ></div>
              </div>
              <span class="barchart-label" :class="{ 'barchart-label--active': bar.isCurrentMonth }">
                {{ bar.month }}
              </span>
            </div>
          </div>
        </div>

        <!-- Transactions Stream (Matching reference mockup!) -->
        <div class="transactions-card">
          <div class="transactions-header">
            <h3 class="transactions-title">История поступлений</h3>
            <span class="transactions-count">{{ fundContributions.length }} взносов</span>
          </div>

          <div v-if="fundContributions.length === 0" class="transactions-empty">
            <RocketOutlined class="empty-icon" />
            <p>Будьте первыми, кто поддержит этот сбор!</p>
          </div>

          <div v-else class="transactions-list">
            <div
              v-for="c in fundContributions"
              :key="c.id"
              class="tx-item"
            >
              <div class="tx-icon-circle">
                <ArrowUpOutlined class="tx-arrow" />
              </div>

              <div class="tx-details">
                <div class="tx-name-row">
                  <span class="tx-name">{{ c.userName }}</span>
                  <span class="tx-amount">+{{ c.amount.toLocaleString() }} ₽</span>
                </div>
                <div class="tx-meta-row">
                  <span class="tx-unit">{{ c.userUnit }}</span>
                  <span class="tx-dot">•</span>
                  <span class="tx-date">{{ formatDate(c.createdAt) }}</span>
                  <span
                    class="status-pill status-pill--small"
                    :class="'status-pill--' + c.status.toLowerCase()"
                    style="margin-left: auto;"
                  >
                    {{ c.status === 'APPROVED' ? 'Одобрен' : 'На проверке' }}
                  </span>
                </div>
              </div>

              <!-- View Receipt Icon if attached -->
              <button
                v-if="c.receiptImagePath"
                class="tx-receipt-btn"
                @click="fundStore.openReceipt(`Чек от ${c.userName}`, c.receiptImagePath)"
                title="Посмотреть чек"
              >
                <FileSearchOutlined />
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Floating Bottom Action Button (Exact match with reference mockup!) -->
      <div class="goal-floating-action">
        <button
          v-if="targetFund.isActive"
          class="goal-action-pill-btn"
          @click="handleContributeClick"
        >
          <PlusOutlined style="font-size: 1.1rem; margin-right: 0.5rem;" />
          <span>Поддержать сбор</span>
        </button>
        <div v-else class="goal-completed-banner">
          <CheckCircleOutlined style="color: #10b981; font-size: 1.25rem;" />
          <span>Сбор успешно закрыт и профинансирован</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import { calculateTargetFundStats, formatDate } from '@/shared/utils/finance';
import { TargetFund } from '@/shared/types';
import { message } from 'ant-design-vue';

const isMenuOpen = ref(false);
import {
  LeftOutlined,
  MoreOutlined,
  CarOutlined,
  EnvironmentOutlined,
  BulbOutlined,
  RocketOutlined,
  TeamOutlined,
  CheckOutlined,
  CheckCircleOutlined,
  ArrowUpOutlined,
  FileSearchOutlined,
  PlusOutlined,
  ShareAltOutlined,
} from '@ant-design/icons-vue';

const props = defineProps<{
  open: boolean;
  targetFund: TargetFund | null;
}>();

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void;
  (e: 'contribute', targetFundId: number): void;
}>();

const fundStore = useFundStore();

const isOpen = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val),
});

// Responsive drawer width (full on mobile, 440px on tablet/desktop)
const windowWidth = ref(window.innerWidth);
function onResize() {
  windowWidth.value = window.innerWidth;
}
onMounted(() => window.addEventListener('resize', onResize));
onUnmounted(() => window.removeEventListener('resize', onResize));

const drawerWidth = computed(() => {
  return windowWidth.value <= 640 ? '100%' : '440px';
});

const stats = computed(() => {
  if (!props.targetFund) return { collected: 0, percent: 0, contributorsCount: 0 };
  return calculateTargetFundStats(props.targetFund, fundStore.contributions);
});

// Contributions specific to this target fund
const fundContributions = computed(() => {
  if (!props.targetFund) return [];
  return fundStore.contributions.filter(
    (c) => c.category === 'TARGET_FUND' && c.targetFundId === props.targetFund?.id
  );
});

const averageContribution = computed(() => {
  if (fundContributions.value.length === 0) return 3000;
  const total = fundContributions.value.reduce((sum, c) => sum + c.amount, 0);
  return Math.round(total / fundContributions.value.length);
});

// Analytics bar chart data (May, Jun, Jul, Aug, Sep)
const monthlyAnalytics = computed(() => {
  const months = [
    { month: 'Май', amount: 25000, percentage: 35, isCurrentMonth: false },
    { month: 'Июн', amount: 45000, percentage: 65, isCurrentMonth: false },
    { month: 'Июл', amount: 60000, percentage: 80, isCurrentMonth: false },
    { month: 'Авг', amount: 85000, percentage: 100, isCurrentMonth: false },
    { month: 'Сен', amount: stats.value.collected > 0 ? stats.value.collected : 30000, percentage: 90, isCurrentMonth: true },
  ];
  return months;
});

function handleContributeClick() {
  if (props.targetFund) {
    emit('contribute', props.targetFund.id);
    isOpen.value = false;
  }
}

function copyShareLink() {
  navigator.clipboard.writeText(window.location.href);
  message.success('Ссылка на сбор скопирована в буфер обмена');
}

function toggleActiveStatus() {
  if (props.targetFund) {
    fundStore.toggleTargetFund(props.targetFund.id);
  }
}
</script>

<style scoped lang="scss">
@use '@/app/styles/variables' as *;

.goal-detail-drawer :deep(.ant-drawer-content) {
  background-color: #f8fafc;
}

.drawer-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(15, 23, 42, 0.65);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  justify-content: flex-end;
}

.goal-detail-drawer {
  width: 100%;
  max-width: 540px;
  height: 100%;
  background: #f8fafc;
  box-shadow: -10px 0 30px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  animation: slideInRight 0.25s ease-out;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.menu-dropdown-wrapper {
  position: relative;
}

.custom-dropdown-menu {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
  min-width: 200px;
  overflow: hidden;
  z-index: 50;
  display: flex;
  flex-direction: column;
}

.custom-menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  background: transparent;
  border: none;
  font-size: 0.825rem;
  font-weight: 600;
  color: #1e293b;
  text-align: left;
  cursor: pointer;

  &:hover {
    background: #f1f5f9;
  }
}

.goal-detail-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #f8fafc;
  position: relative;
}

/* Top bar matching mobile app navbar */
.goal-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.85rem 1.15rem;
  background: #ffffff;
  border-bottom: 1px solid #e2e8f0;
  position: sticky;
  top: 0;
  z-index: 20;
}

.topbar-btn {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f1f5f9;
  color: #0f172a;
  border: none;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #e2e8f0;
  }
}

.topbar-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

/* Scrollable Container */
.goal-scroll-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem 1.15rem 6.5rem 1.15rem;
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

/* Goal Hero Card */
.goal-hero-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 1.5rem;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
}

.goal-icon-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.goal-icon-badge {
  width: 52px;
  height: 52px;
  border-radius: 18px;
  background: #eef2ff;
  color: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;

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

.goal-status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: #dcfce7;
  color: #15803d;
  font-size: 0.8rem;
  font-weight: 700;
  padding: 0.35rem 0.75rem;
  border-radius: 9999px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #16a34a;
}

.goal-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
  line-height: 1.3;
  margin-bottom: 0.5rem;
}

.goal-description {
  font-size: 0.875rem;
  color: #64748b;
  line-height: 1.5;
  margin-bottom: 1.25rem;
}

.goal-numbers-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.numbers-label {
  font-size: 0.75rem;
  color: #94a3b8;
  text-transform: uppercase;
  font-weight: 600;
  letter-spacing: 0.03em;
  display: block;
}

.numbers-collected {
  font-size: 1.5rem;
  font-weight: 800;
  color: #0f172a;
}

.numbers-target {
  font-size: 1.15rem;
  font-weight: 700;
  color: #64748b;
}

/* Pill Progress Bar */
.goal-progress-track {
  width: 100%;
  height: 12px;
  background: #f1f5f9;
  border-radius: 9999px;
  overflow: hidden;
  margin-bottom: 1.25rem;
}

.goal-progress-fill {
  height: 100%;
  background: #10b981;
  border-radius: 9999px;
  transition: width 0.4s ease;

  &--orange {
    background: #f59e0b;
  }

  &--completed {
    background: #4f46e5;
  }
}

.goal-sub-meta {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.meta-pill {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 0.35rem 0.65rem;
  border-radius: 8px;
  font-size: 0.775rem;
  font-weight: 600;
  color: #475569;
}

/* Saving Analytics Card */
.analytics-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 1.25rem 1.5rem;
}

.analytics-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.analytics-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.analytics-subtitle {
  font-size: 0.775rem;
  color: #94a3b8;
}

.analytics-badge {
  font-size: 0.75rem;
  font-weight: 600;
  color: #4f46e5;
  background: #eef2ff;
  padding: 0.25rem 0.5rem;
  border-radius: 6px;
}

/* Bar chart styles */
.barchart-container {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  height: 140px;
  padding-top: 1.5rem;
  gap: 0.5rem;
}

.barchart-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
}

.barchart-bar-wrapper {
  flex: 1;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  position: relative;
}

.barchart-tooltip {
  font-size: 0.65rem;
  font-weight: 700;
  color: #0f172a;
  margin-bottom: 0.25rem;
}

.barchart-bar {
  width: 24px;
  background: #e2e8f0;
  border-radius: 8px 8px 4px 4px;
  transition: all 0.3s ease;

  &--active {
    background: #11141a;
  }
}

.barchart-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #94a3b8;
  margin-top: 0.5rem;

  &--active {
    color: #0f172a;
    font-weight: 700;
  }
}

/* Transactions Card */
.transactions-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 1.25rem 1.5rem;
}

.transactions-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1rem;
}

.transactions-title {
  font-size: 1.05rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.transactions-count {
  font-size: 0.8rem;
  font-weight: 600;
  color: #64748b;
}

.transactions-empty {
  text-align: center;
  padding: 2rem 1rem;
  color: #94a3b8;
  font-size: 0.875rem;

  .empty-icon {
    font-size: 2rem;
    color: #cbd5e1;
    margin-bottom: 0.5rem;
    display: block;
  }
}

.transactions-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.tx-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.65rem 0.5rem;
  border-radius: 12px;
  transition: background 0.15s ease;

  &:hover {
    background: #f8fafc;
  }
}

.tx-icon-circle {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #f1f5f9;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.tx-arrow {
  color: #10b981;
  font-size: 1rem;
}

.tx-details {
  flex: 1;
  min-width: 0;
}

.tx-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.tx-name {
  font-size: 0.875rem;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.tx-amount {
  font-size: 0.95rem;
  font-weight: 800;
  color: #10b981;
  white-space: nowrap;
}

.tx-meta-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.status-pill--small {
  font-size: 0.65rem;
  padding: 0.1rem 0.4rem;
}

.tx-receipt-btn {
  background: #f1f5f9;
  border: none;
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  color: #475569;
  transition: all 0.15s ease;

  &:hover {
    background: #e2e8f0;
    color: #0f172a;
  }
}

/* Floating Bottom Action Button (Pinned Black Pill) */
.goal-floating-action {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 1rem 1.25rem 1.25rem 1.25rem;
  background: linear-gradient(180deg, rgba(248, 250, 252, 0) 0%, rgba(248, 250, 252, 0.95) 30%, #f8fafc 100%);
  display: flex;
  justify-content: center;
  z-index: 10;
}

.goal-action-pill-btn {
  width: 100%;
  max-width: 380px;
  height: 52px;
  background: #11141a;
  color: #ffffff;
  border: none;
  border-radius: 9999px;
  font-size: 1rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 10px 25px rgba(17, 20, 26, 0.25);
  transition: transform 0.15s ease, background-color 0.15s ease;

  &:hover {
    background: #232834;
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(1px);
  }
}

.goal-completed-banner {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  padding: 0.85rem 1.25rem;
  border-radius: 9999px;
  font-size: 0.875rem;
  font-weight: 600;
  color: #065f46;
}
</style>
