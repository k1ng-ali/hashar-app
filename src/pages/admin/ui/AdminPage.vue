<template>
  <!-- 1. RBAC Guard: If resident attempts to access admin panel, show AccessDenied -->
  <AccessDenied v-if="!fundStore.permissions.canAccessAdminPanel" />

  <div v-else class="admin-page">
    <!-- Top Header Card -->
    <div class="admin-top-card">
      <div class="top-row">
        <div class="role-badge" :class="fundStore.isSuperAdmin ? 'role-badge--super' : 'role-badge--audit'">
          <CrownOutlined v-if="fundStore.isSuperAdmin" />
          <AuditOutlined v-else />
          <span>{{ fundStore.isSuperAdmin ? 'Председатель ТСЖ' : 'Ревизор фонда' }}</span>
        </div>
        <span class="access-pill">
          {{ fundStore.isSuperAdmin ? 'Полный доступ' : 'Аудит и проверка' }}
        </span>
      </div>

      <h1 class="page-title">Управление фондом дома</h1>
      <p class="page-sub">
        Верификация поступлений, учет расходов, жильцы и реквизиты счетов
      </p>

      <!-- Segmented Sub-navigation Tabs -->
      <div class="subnav-scroll">
        <button
          type="button"
          class="subnav-tab"
          :class="{ 'subnav-tab--active': activeSubTab === 'verification' }"
          @click="activeSubTab = 'verification'"
        >
          <span>Верификация</span>
          <span
            v-if="fundStore.pendingContributions.length > 0"
            class="tab-badge"
          >
            {{ fundStore.pendingContributions.length }}
          </span>
        </button>

        <button
          type="button"
          class="subnav-tab"
          :class="{ 'subnav-tab--active': activeSubTab === 'expenses' }"
          @click="activeSubTab = 'expenses'"
        >
          <span>Расходы</span>
        </button>

        <button
          type="button"
          class="subnav-tab"
          :class="{ 'subnav-tab--active': activeSubTab === 'residents' }"
          @click="activeSubTab = 'residents'"
        >
          <span>Жильцы</span>
          <span v-if="debtorsCount > 0" class="tab-badge tab-badge--danger">
            {{ debtorsCount }}
          </span>
        </button>

        <button
          type="button"
          class="subnav-tab"
          :class="{ 'subnav-tab--active': activeSubTab === 'target-funds' }"
          @click="activeSubTab = 'target-funds'"
        >
          <span>Целевые сборы</span>
        </button>

        <button
          type="button"
          class="subnav-tab"
          :class="{ 'subnav-tab--active': activeSubTab === 'settings' }"
          @click="activeSubTab = 'settings'"
        >
          <span>Настройки</span>
        </button>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- 1. TAB: VERIFICATION QUEUE -->
    <!-- ========================================================================= -->
    <div v-if="activeSubTab === 'verification'" class="subtab-container">
      <div class="section-card">
        <div class="section-header">
          <div>
            <h2 class="section-heading">Очередь проверки чеков</h2>
            <p class="section-subheading">
              Сверьте подлинность чека перед зачислением средств на баланс
            </p>
          </div>
          <span class="count-pill">{{ fundStore.pendingContributions.length }} на проверке</span>
        </div>

        <div v-if="fundStore.pendingContributions.length > 0" class="verify-cards-list">
          <div
            v-for="c in fundStore.pendingContributions"
            :key="c.id"
            class="verify-card"
          >
            <div class="verify-main-row">
              <div
                class="receipt-thumb"
                title="Нажмите для просмотра чека"
                @click="fundStore.openReceipt(`Чек от ${c.userName}`, c.receiptImagePath)"
              >
                <img :src="c.receiptImagePath" alt="Чек" />
                <div class="thumb-zoom-icon">
                  <EyeOutlined />
                </div>
              </div>

              <div class="verify-details">
                <div class="resident-title">
                  <span class="res-name">{{ c.userName }}</span>
                  <span class="res-unit">кв. {{ c.userUnit }}</span>
                </div>

                <div class="verify-purpose-tag">
                  {{ c.category === 'MONTHLY_FEE' ? 'Ежемесячный сбор' : c.targetFundTitle || 'Целевой сбор' }}
                </div>

                <div class="verify-meta-line">
                  <span class="verify-date">{{ formatDate(c.createdAt) }}</span>
                </div>

                <div v-if="c.commentUser" class="verify-comment">
                  «{{ c.commentUser }}»
                </div>
              </div>

              <div class="verify-right">
                <div class="verify-sum font-bold text-success">
                  +{{ c.amount.toLocaleString() }} ₽
                </div>
                <button
                  class="verify-action-btn"
                  @click="handleOpenVerifyModal(c)"
                >
                  <SafetyCertificateOutlined />
                  <span>Проверить</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="empty-tab-box">
          <div class="empty-icon text-success">✓</div>
          <div class="empty-title">Все чеки проверены!</div>
          <div class="empty-sub">Новых платежей, ожидающих проверки, сейчас нет.</div>
        </div>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- 2. TAB: EXPENSES -->
    <!-- ========================================================================= -->
    <div v-if="activeSubTab === 'expenses'" class="subtab-container">
      <div class="section-card">
        <div class="section-header">
          <div>
            <h2 class="section-heading">Реестр расходов фонда</h2>
            <p class="section-subheading">
              Все траты с подтверждающими чеками и накладными
            </p>
          </div>

          <button
            class="action-add-btn"
            @click="isAddExpenseOpen = true"
          >
            <PlusOutlined />
            <span>Внести расход</span>
          </button>
        </div>

        <div v-if="fundStore.expenses.length > 0" class="expenses-cards-list">
          <div
            v-for="e in fundStore.expenses"
            :key="e.id"
            class="expense-card"
          >
            <div class="expense-card-top">
              <div class="expense-cat-badge">{{ e.category }}</div>
              <div class="expense-amount font-bold text-danger">
                -{{ e.amount.toLocaleString() }} ₽
              </div>
            </div>

            <div class="expense-title">{{ e.title }}</div>
            <p class="expense-desc">{{ e.description }}</p>

            <div class="expense-footer">
              <span class="expense-by">Внес: <strong>{{ e.createdByAdminName }}</strong> • {{ formatDate(e.createdAt) }}</span>

              <button
                v-if="e.receiptImagePaths.length > 0"
                class="receipt-link-btn"
                @click="fundStore.openReceipt(`Чек: ${e.title}`, e.receiptImagePaths[0])"
              >
                <EyeOutlined />
                <span>Чек ({{ e.receiptImagePaths.length }})</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- 3. TAB: RESIDENTS -->
    <!-- ========================================================================= -->
    <div v-if="activeSubTab === 'residents'" class="subtab-container">
      <div class="section-card">
        <div class="section-header">
          <div>
            <h2 class="section-heading">Реестр собственников</h2>
            <p class="section-subheading">
              Баланс лицевых счетов и контактные телефоны
            </p>
          </div>

          <button
            v-if="fundStore.permissions.canRegisterResidents"
            class="action-add-btn"
            @click="isRegisterResidentOpen = true"
          >
            <PlusOutlined />
            <span>Добавить</span>
          </button>
        </div>

        <!-- Filter toggles -->
        <div class="filter-switch-row">
          <label class="custom-toggle-label">
            <input
              type="checkbox"
              v-model="onlyDebtors"
              class="custom-toggle"
            />
            <span>Показать только должников ({{ debtorsCount }})</span>
          </label>
        </div>

        <div class="residents-cards-list">
          <div
            v-for="r in filteredResidents"
            :key="r.id"
            class="resident-card"
          >
            <div class="res-card-top">
              <div class="res-unit-pill">кв. {{ r.addressUnit }}</div>
              <div
                class="res-status-chip"
                :class="{
                  'res-status--debt': getResidentStatus(r.id).statusType === 'DEBT',
                  'res-status--advance': getResidentStatus(r.id).statusType === 'ADVANCE',
                  'res-status--ok': getResidentStatus(r.id).statusType === 'OK',
                }"
              >
                {{
                  getResidentStatus(r.id).statusType === 'DEBT'
                    ? `Долг ${getResidentStatus(r.id).debtAmount} ₽`
                    : getResidentStatus(r.id).statusType === 'ADVANCE'
                    ? `Аванс +${getResidentStatus(r.id).balance} ₽`
                    : 'Оплачено'
                }}
              </div>
            </div>

            <div class="res-card-name">{{ r.fullName }}</div>
            <div class="res-card-phone">{{ r.phone }}</div>

            <div class="res-calc-row">
              <span class="text-secondary text-xs">Всего внесено:</span>
              <span class="font-semibold text-xs">{{ getResidentStatus(r.id).totalPaid.toLocaleString() }} ₽</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- 4. TAB: TARGET FUNDS -->
    <!-- ========================================================================= -->
    <div v-if="activeSubTab === 'target-funds'" class="subtab-container">
      <div class="section-card">
        <div class="section-header">
          <div>
            <h2 class="section-heading">Целевые сборы</h2>
            <p class="section-subheading">
              Спецпроекты дома (шлагбаумы, видеонаблюдение, благоустройство)
            </p>
          </div>

          <button
            v-if="fundStore.permissions.canManageSettings"
            class="action-add-btn"
            @click="isCreateTargetFundOpen = true"
          >
            <PlusOutlined />
            <span>Создать сбор</span>
          </button>
        </div>

        <div class="target-funds-cards-list">
          <div
            v-for="f in fundStore.targetFunds"
            :key="f.id"
            class="target-fund-card"
          >
            <div class="tf-card-top">
              <span class="tf-title">{{ f.title }}</span>
              <label class="switch-control">
                <input
                  type="checkbox"
                  :checked="f.isActive"
                  @change="fundStore.toggleTargetFundActive(f.id)"
                />
                <span class="slider"></span>
              </label>
            </div>

            <p class="tf-desc">{{ f.description }}</p>

            <div class="tf-meta-row">
              <span class="tf-collected font-bold text-success">
                {{ getTargetFundCollected(f.id).toLocaleString() }} ₽
              </span>
              <span class="tf-target text-secondary text-xs">
                из {{ f.targetAmount.toLocaleString() }} ₽
              </span>
              <span class="tf-percent font-bold">
                {{ getTargetFundPercent(f.id, f.targetAmount) }}%
              </span>
            </div>

            <div class="tf-progress-track">
              <div
                class="tf-progress-fill"
                :style="{ width: `${getTargetFundPercent(f.id, f.targetAmount)}%` }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ========================================================================= -->
    <!-- 5. TAB: SETTINGS & REQUISITES -->
    <!-- ========================================================================= -->
    <div v-if="activeSubTab === 'settings'" class="subtab-container">
      <!-- Billing Rate Config -->
      <div class="section-card">
        <h2 class="section-heading">Ежемесячный тариф взноса</h2>
        <p class="section-subheading">
          Устанавливается решением общего собрания собственников
        </p>

        <div class="rate-config-box">
          <div class="rate-input-wrap">
            <input
              v-model.number="newBillingRate"
              type="number"
              min="100"
              step="50"
              class="rate-input"
              :disabled="!fundStore.permissions.canManageSettings"
            />
            <span class="rate-unit">₽ / месяц с квартиры</span>
          </div>

          <button
            class="rate-save-btn"
            :disabled="!fundStore.permissions.canManageSettings"
            @click="handleSaveRate"
          >
            Сохранить тариф
          </button>
        </div>
      </div>

      <!-- Payment Requisites Section -->
      <div class="section-card">
        <div class="section-header">
          <div>
            <h2 class="section-heading">Счета и банковские карты фонда</h2>
            <p class="section-subheading">
              Отображаются жителям при оплате взносов
            </p>
          </div>

          <button
            v-if="fundStore.permissions.canManageSettings"
            class="action-add-btn"
            @click="isAddRequisiteOpen = true"
          >
            <PlusOutlined />
            <span>Добавить счет</span>
          </button>
        </div>

        <div class="req-cards-list">
          <div
            v-for="r in fundStore.paymentRequisites"
            :key="r.id"
            class="requisite-card"
          >
            <div class="req-card-top">
              <span class="req-bank-name">{{ r.bankName }}</span>
              <div class="req-card-actions">
                <label class="switch-control">
                  <input
                    type="checkbox"
                    :checked="r.isActive"
                    :disabled="!fundStore.permissions.canManageSettings"
                    @change="fundStore.toggleRequisiteActive(r.id)"
                  />
                  <span class="slider"></span>
                </label>

                <button
                  v-if="fundStore.permissions.canManageSettings"
                  class="req-delete-btn"
                  @click="handleDeleteRequisite(r.id)"
                >
                  <DeleteOutlined />
                </button>
              </div>
            </div>

            <div class="req-card-num font-mono">{{ r.cardOrAccountNumber }}</div>
            <div class="req-card-holder">{{ r.recipientName }}</div>
            <div v-if="r.phoneNumber" class="req-card-sbp">
              СБП телефон: <strong>{{ r.phoneNumber }}</strong>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <VerifyReceiptModal
      v-model:open="isVerifyModalOpen"
      :contribution="selectedContribution"
    />
    <AddExpenseModal v-model:open="isAddExpenseOpen" />
    <AddRequisiteModal v-model:open="isAddRequisiteOpen" />
    <RegisterResidentModal v-model:open="isRegisterResidentOpen" />
    <CreateTargetFundModal v-model:open="isCreateTargetFundOpen" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import { formatDate, calculateResidentStatus } from '@/shared/utils/finance';
import { Contribution } from '@/shared/types';
import AccessDenied from '@/widgets/access-denied/ui/AccessDenied.vue';
import VerifyReceiptModal from '@/features/verify-receipt/ui/VerifyReceiptModal.vue';
import AddExpenseModal from '@/features/manage-expenses/ui/AddExpenseModal.vue';
import AddRequisiteModal from '@/features/manage-requisites/ui/AddRequisiteModal.vue';
import RegisterResidentModal from '@/features/register-resident/ui/RegisterResidentModal.vue';
import CreateTargetFundModal from '@/features/create-target-fund/ui/CreateTargetFundModal.vue';
import { message } from 'ant-design-vue';
import {
  CrownOutlined,
  AuditOutlined,
  SafetyCertificateOutlined,
  PlusOutlined,
  EyeOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue';

const fundStore = useFundStore();

const activeSubTab = ref<'verification' | 'expenses' | 'residents' | 'target-funds' | 'settings'>('verification');

const isVerifyModalOpen = ref(false);
const selectedContribution = ref<Contribution | null>(null);

const isAddExpenseOpen = ref(false);
const isAddRequisiteOpen = ref(false);
const isRegisterResidentOpen = ref(false);
const isCreateTargetFundOpen = ref(false);

const onlyDebtors = ref(false);
const newBillingRate = ref(fundStore.billingRate.amount);

function handleOpenVerifyModal(c: Contribution) {
  selectedContribution.value = c;
  isVerifyModalOpen.value = true;
}

function getResidentStatus(userId: string) {
  return calculateResidentStatus(userId, fundStore.contributions, fundStore.billingRate);
}

const debtorsCount = computed(() => {
  return fundStore.users
    .filter((u) => u.role === 'RESIDENT')
    .filter((u) => getResidentStatus(u.id).statusType === 'DEBT').length;
});

const filteredResidents = computed(() => {
  const residents = fundStore.users.filter((u) => u.role === 'RESIDENT');
  if (!onlyDebtors.value) return residents;
  return residents.filter((u) => getResidentStatus(u.id).statusType === 'DEBT');
});

function getTargetFundCollected(targetFundId: number): number {
  return fundStore.contributions
    .filter((c) => c.category === 'TARGET_FUND' && c.targetFundId === targetFundId && c.status === 'APPROVED')
    .reduce((sum, c) => sum + c.amount, 0);
}

function getTargetFundPercent(targetFundId: number, targetAmount: number): number {
  const collected = getTargetFundCollected(targetFundId);
  return Math.min(100, Math.round((collected / (targetAmount || 1)) * 100));
}

function handleSaveRate() {
  fundStore.updateBillingRate(newBillingRate.value);
  message.success('Тариф фонда успешно обновлен');
}

function handleDeleteRequisite(id: number) {
  fundStore.deletePaymentRequisite(id);
  message.success('Реквизит удален');
}
</script>

<style scoped lang="scss">
.admin-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 680px;
  margin: 0 auto;
}

/* Top Header Card */
.admin-top-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.65rem;
}

.role-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.75rem;
  font-weight: 700;
  padding: 0.25rem 0.65rem;
  border-radius: 9999px;

  &--super {
    background: #f3e8ff;
    color: #7e22ce;
  }

  &--audit {
    background: #e0e7ff;
    color: #4338ca;
  }
}

.access-pill {
  font-size: 0.725rem;
  color: #64748b;
  background: #f1f5f9;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  font-weight: 600;
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

/* Subnav Scroll */
.subnav-scroll {
  display: flex;
  gap: 0.4rem;
  overflow-x: auto;
  margin-top: 1.15rem;
  padding-bottom: 0.2rem;
}

.subnav-tab {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 9999px;
  padding: 0.4rem 0.85rem;
  font-size: 0.775rem;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #f1f5f9;
  }

  &--active {
    background: #0f172a;
    border-color: #0f172a;
    color: #ffffff;
  }
}

.tab-badge {
  background: #6366f1;
  color: #ffffff;
  font-size: 0.65rem;
  font-weight: 800;
  padding: 0.05rem 0.4rem;
  border-radius: 9999px;

  &--danger {
    background: #ef4444;
  }
}

/* Subtab Container */
.subtab-container {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.section-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.section-heading {
  font-size: 1.1rem;
  font-weight: 800;
  color: #0f172a;
}

.section-subheading {
  font-size: 0.775rem;
  color: #64748b;
  margin-top: 0.1rem;
}

.count-pill {
  background: #fef3c7;
  color: #b45309;
  font-size: 0.725rem;
  font-weight: 700;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  white-space: nowrap;
}

.action-add-btn {
  background: #0f172a;
  color: #ffffff;
  border: none;
  border-radius: 9999px;
  padding: 0.4rem 0.85rem;
  font-size: 0.775rem;
  font-weight: 700;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  white-space: nowrap;

  &:hover {
    background: #1e293b;
  }
}

/* Verification Cards */
.verify-cards-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.verify-card {
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 18px;
  padding: 0.85rem 1rem;
  transition: all 0.15s ease;

  &:hover {
    border-color: #cbd5e1;
    background: #ffffff;
  }
}

.verify-main-row {
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.receipt-thumb {
  position: relative;
  width: 58px;
  height: 58px;
  border-radius: 12px;
  overflow: hidden;
  border: 1.5px solid #cbd5e1;
  flex-shrink: 0;
  cursor: pointer;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .thumb-zoom-icon {
    position: absolute;
    inset: 0;
    background: rgba(15, 23, 42, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    opacity: 0;
    transition: opacity 0.15s ease;
  }

  &:hover .thumb-zoom-icon {
    opacity: 1;
  }
}

.verify-details {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0.15rem;
}

.resident-title {
  display: flex;
  align-items: center;
  gap: 0.4rem;
}

.res-name {
  font-size: 0.875rem;
  font-weight: 800;
  color: #0f172a;
}

.res-unit {
  font-size: 0.725rem;
  background: #e2e8f0;
  color: #334155;
  font-weight: 700;
  padding: 0.1rem 0.45rem;
  border-radius: 6px;
}

.verify-purpose-tag {
  font-size: 0.725rem;
  color: #6366f1;
  font-weight: 700;
}

.verify-meta-line {
  font-size: 0.7rem;
  color: #94a3b8;
}

.verify-comment {
  font-size: 0.725rem;
  color: #64748b;
  font-style: italic;
}

.verify-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.4rem;
}

.verify-sum {
  font-size: 1rem;
}

.verify-action-btn {
  background: #0f172a;
  color: #ffffff;
  border: none;
  border-radius: 10px;
  padding: 0.4rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.35rem;

  &:hover {
    background: #1e293b;
  }
}

/* Empty Tab Box */
.empty-tab-box {
  text-align: center;
  padding: 2.5rem 1rem;
}

.empty-icon {
  font-size: 2.25rem;
  margin-bottom: 0.5rem;
}

.empty-title {
  font-size: 1.1rem;
  font-weight: 800;
  color: #0f172a;
}

.empty-sub {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 0.25rem;
}

/* Expenses Cards List */
.expenses-cards-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.expense-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 0.85rem 1rem;
}

.expense-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.expense-cat-badge {
  font-size: 0.675rem;
  font-weight: 700;
  background: #ffedd5;
  color: #c2410c;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
}

.expense-amount {
  font-size: 1rem;
}

.expense-title {
  font-size: 0.95rem;
  font-weight: 800;
  color: #0f172a;
}

.expense-desc {
  font-size: 0.8rem;
  color: #475569;
  margin: 0.25rem 0 0.65rem 0;
}

.expense-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.5rem;
  border-top: 1px solid #e2e8f0;
}

.expense-by {
  font-size: 0.7rem;
  color: #94a3b8;
}

.receipt-link-btn {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 0.25rem 0.55rem;
  font-size: 0.725rem;
  font-weight: 700;
  color: #334155;
  display: flex;
  align-items: center;
  gap: 0.3rem;
  cursor: pointer;

  &:hover {
    background: #f1f5f9;
  }
}

/* Residents Registry */
.filter-switch-row {
  margin-bottom: 0.85rem;
}

.custom-toggle-label {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: #334155;
  cursor: pointer;
}

.custom-toggle {
  width: 16px;
  height: 16px;
  accent-color: #4f46e5;
}

.residents-cards-list {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.65rem;

  @media (min-width: 500px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.resident-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 0.85rem;
}

.res-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.res-unit-pill {
  font-size: 0.725rem;
  font-weight: 800;
  background: #0f172a;
  color: #ffffff;
  padding: 0.15rem 0.5rem;
  border-radius: 6px;
}

.res-status-chip {
  font-size: 0.675rem;
  font-weight: 700;
  padding: 0.1rem 0.45rem;
  border-radius: 9999px;

  &.res-status--debt {
    background: #fee2e2;
    color: #b91c1c;
  }

  &.res-status--advance {
    background: #dcfce7;
    color: #15803d;
  }

  &.res-status--ok {
    background: #e0e7ff;
    color: #4338ca;
  }
}

.res-card-name {
  font-size: 0.875rem;
  font-weight: 800;
  color: #0f172a;
}

.res-card-phone {
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 0.5rem;
}

.res-calc-row {
  display: flex;
  justify-content: space-between;
  padding-top: 0.35rem;
  border-top: 1px dashed #cbd5e1;
}

/* Target Funds Cards */
.target-funds-cards-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.target-fund-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 1rem;
}

.tf-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.tf-title {
  font-size: 1rem;
  font-weight: 800;
  color: #0f172a;
}

.tf-desc {
  font-size: 0.8rem;
  color: #475569;
  margin-bottom: 0.75rem;
}

.tf-meta-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.tf-collected {
  font-size: 0.95rem;
}

.tf-progress-track {
  width: 100%;
  height: 8px;
  background: #e2e8f0;
  border-radius: 9999px;
  overflow: hidden;
}

.tf-progress-fill {
  height: 100%;
  background: #10b981;
  border-radius: 9999px;
  transition: width 0.3s ease;
}

/* Switch Control */
.switch-control {
  position: relative;
  display: inline-block;
  width: 36px;
  height: 20px;

  input {
    opacity: 0;
    width: 0;
    height: 0;
  }

  .slider {
    position: absolute;
    cursor: pointer;
    inset: 0;
    background-color: #cbd5e1;
    transition: 0.2s;
    border-radius: 20px;

    &:before {
      position: absolute;
      content: "";
      height: 14px;
      width: 14px;
      left: 3px;
      bottom: 3px;
      background-color: white;
      transition: 0.2s;
      border-radius: 50%;
    }
  }

  input:checked + .slider {
    background-color: #10b981;
  }

  input:checked + .slider:before {
    transform: translateX(16px);
  }
}

/* Settings Tab */
.rate-config-box {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.75rem;

  @media (min-width: 480px) {
    flex-direction: row;
    align-items: center;
  }
}

.rate-input-wrap {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.4rem 0.85rem;
}

.rate-input {
  width: 90px;
  border: none;
  background: transparent;
  font-size: 1.1rem;
  font-weight: 800;
  outline: none;
  color: #0f172a;
}

.rate-unit {
  font-size: 0.8rem;
  color: #64748b;
  font-weight: 600;
}

.rate-save-btn {
  background: #0f172a;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  padding: 0.65rem 1.15rem;
  font-size: 0.825rem;
  font-weight: 800;
  cursor: pointer;

  &:hover {
    background: #1e293b;
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

/* Requisites Cards */
.req-cards-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.requisite-card {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 0.85rem 1rem;
}

.req-card-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.req-bank-name {
  font-size: 0.9rem;
  font-weight: 800;
  color: #0f172a;
}

.req-card-actions {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.req-delete-btn {
  background: transparent;
  border: none;
  color: #ef4444;
  cursor: pointer;
  padding: 0.2rem;
  font-size: 0.85rem;

  &:hover {
    color: #b91c1c;
  }
}

.req-card-num {
  font-size: 0.875rem;
  color: #1e293b;
  font-weight: 700;
  letter-spacing: 0.03em;
}

.req-card-holder {
  font-size: 0.75rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.req-card-sbp {
  font-size: 0.725rem;
  color: #4338ca;
  margin-top: 0.25rem;
}
</style>
