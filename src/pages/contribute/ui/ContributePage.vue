<template>
  <div class="contribute-page">
    <!-- Header -->
    <div class="page-top-card">
      <div class="page-badge">
        <span class="pulse-dot"></span>
        <span>Официальный фонд дома</span>
      </div>
      <h1 class="page-title">Внесение взноса</h1>
      <p class="page-desc">
        Переведите средства по реквизитам фонда и прикрепите электронный чек или скриншот.
      </p>
    </div>

    <!-- 3-step Quick Flow (compact mobile pills) -->
    <div class="quick-steps-row">
      <div class="quick-step-pill">
        <span class="step-num">1</span>
        <span class="step-text">Скопируйте счет</span>
      </div>
      <div class="quick-step-divider">→</div>
      <div class="quick-step-pill">
        <span class="step-num">2</span>
        <span class="step-text">Переведите в банке</span>
      </div>
      <div class="quick-step-divider">→</div>
      <div class="quick-step-pill">
        <span class="step-num">3</span>
        <span class="step-text">Загрузите чек</span>
      </div>
    </div>

    <!-- Active Requisites Cards (Swipeable / Stacked) -->
    <div class="requisites-section">
      <div class="section-label-row">
        <span class="section-label">Реквизиты для оплаты</span>
        <span class="section-sub">Без комиссии через СБП</span>
      </div>

      <div class="req-cards-grid">
        <div
          v-for="r in fundStore.paymentRequisites"
          :key="r.id"
          class="req-fintech-card"
          :class="{ 'is-disabled': !r.isActive }"
        >
          <div class="req-fintech-top">
            <div class="req-bank-tag">{{ r.bankName }}</div>
            <span class="req-status-dot" :class="{ 'is-active': r.isActive }">
              {{ r.isActive ? 'Активен' : 'Отключен' }}
            </span>
          </div>

          <div class="req-number-wrap font-mono">
            {{ r.cardOrAccountNumber }}
          </div>

          <div class="req-meta-details">
            <div class="req-meta-row">
              <span class="req-meta-label">Получатель:</span>
              <span class="req-meta-val">{{ r.recipientName }}</span>
            </div>
            <div v-if="r.phoneNumber" class="req-meta-row">
              <span class="req-meta-label">СБП:</span>
              <span class="req-meta-val font-semibold">{{ r.phoneNumber }}</span>
            </div>
          </div>

          <button
            class="copy-account-btn"
            :disabled="!r.isActive"
            @click="copyCard(r.cardOrAccountNumber)"
          >
            <CopyOutlined />
            <span>Скопировать счет</span>
          </button>
        </div>
      </div>
    </div>

    <!-- Contribution Form Card -->
    <div class="contribute-form-card">
      <div class="form-header">
        <h2 class="form-title">Параметры взноса</h2>
        <span class="form-subtitle">Заполните поля и прикрепите подтверждение</span>
      </div>

      <!-- Category Segmented Buttons -->
      <div class="form-field-group">
        <label class="field-label">Назначение платежа</label>
        <div class="segmented-control">
          <button
            type="button"
            class="segmented-btn"
            :class="{ 'segmented-btn--active': category === 'MONTHLY_FEE' }"
            @click="category = 'MONTHLY_FEE'"
          >
            Ежемесячный сбор ({{ fundStore.billingRate.amount }} ₽)
          </button>
          <button
            type="button"
            class="segmented-btn"
            :class="{ 'segmented-btn--active': category === 'TARGET_FUND' }"
            @click="category = 'TARGET_FUND'"
          >
            Целевой сбор
          </button>
        </div>
      </div>

      <!-- Target Fund Selector if category is TARGET_FUND -->
      <div v-if="category === 'TARGET_FUND'" class="form-field-group">
        <label class="field-label">Выберите проект сбора</label>
        <select v-model="selectedTargetFundId" class="custom-select">
          <option :value="undefined" disabled>-- Выберите сбор --</option>
          <option
            v-for="tf in activeTargetFunds"
            :key="tf.id"
            :value="tf.id"
          >
            {{ tf.title }} (Цель: {{ tf.targetAmount.toLocaleString() }} ₽)
          </option>
        </select>
      </div>

      <!-- Amount Input + Quick Chips -->
      <div class="form-field-group">
        <label class="field-label">Сумма взноса (₽)</label>
        <div class="amount-input-box">
          <input
            v-model.number="amount"
            type="number"
            min="100"
            max="1000000"
            step="100"
            class="custom-amount-input font-mono"
            placeholder="0"
          />
          <span class="currency-symbol">₽</span>
        </div>

        <!-- Quick Amount Chips -->
        <div class="amount-chips-row">
          <button
            v-for="val in [1500, 3000, 4500, 9000]"
            :key="val"
            type="button"
            class="amount-chip"
            :class="{ 'amount-chip--active': amount === val }"
            @click="amount = val"
          >
            {{ val.toLocaleString() }} ₽
          </button>
        </div>
      </div>

      <!-- Receipt Upload Box -->
      <div class="form-field-group">
        <label class="field-label">Квитанция или скриншот платежа</label>

        <div v-if="receiptPreview" class="uploaded-receipt-preview">
          <img :src="receiptPreview" alt="Чек" class="receipt-preview-img" />
          <div class="receipt-preview-info">
            <div class="receipt-ok-badge">
              <CheckCircleOutlined /> Документ прикреплен
            </div>
            <button
              type="button"
              class="receipt-replace-btn"
              @click="receiptPreview = ''"
            >
              Заменить документ
            </button>
          </div>
        </div>

        <div v-else class="receipt-upload-box">
          <input
            type="file"
            accept="image/*,.pdf"
            id="page-file-upload"
            class="hidden-file-input"
            @change="handleFileUpload"
          />
          <label for="page-file-upload" class="upload-area-label">
            <div class="upload-icon-circle">
              <UploadOutlined />
            </div>
            <span class="upload-main-text">Нажмите для выбора фото или чека</span>
            <span class="upload-sub-text">PNG, JPG или скриншот банковского приложения</span>
          </label>

          <div class="demo-generator-row">
            <span class="demo-sep">или для быстрого тестирования:</span>
            <button
              type="button"
              class="demo-gen-btn"
              @click="generateDemo"
            >
              <ThunderboltOutlined />
              <span>Сформировать тестовый чек</span>
            </button>
          </div>
        </div>
      </div>

      <!-- Comment Field -->
      <div class="form-field-group">
        <label class="field-label">Комментарий (необязательно)</label>
        <textarea
          v-model="commentUser"
          rows="2"
          class="custom-textarea"
          placeholder="Например: Оплата за сентябрь и октябрь..."
        ></textarea>
      </div>

      <!-- Submit Action Button -->
      <button
        type="button"
        class="submit-contribution-btn"
        :disabled="!amount || !receiptPreview"
        @click="handleSubmit"
      >
        <SendOutlined />
        <span>Отправить чек на подтверждение</span>
      </button>

      <p class="form-guarantee-note">
        После отправки квитанция попадет на верификацию ревизору. Баланс обновится автоматически.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import { generateReceiptSvg } from '@/shared/utils/receiptGenerator';
import { message } from 'ant-design-vue';
import {
  SendOutlined,
  UploadOutlined,
  ThunderboltOutlined,
  CopyOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons-vue';

const fundStore = useFundStore();

const category = ref<'MONTHLY_FEE' | 'TARGET_FUND'>('MONTHLY_FEE');
const selectedTargetFundId = ref<number | undefined>(undefined);
const amount = ref<number>(1500);
const receiptPreview = ref<string>('');
const commentUser = ref<string>('');

const activeTargetFunds = computed(() => {
  return fundStore.targetFunds.filter((tf) => tf.isActive);
});

function copyCard(num: string) {
  navigator.clipboard.writeText(num.replace(/\s+/g, ''));
  message.success('Номер счета скопирован');
}

function handleFileUpload(e: Event) {
  const target = e.target as HTMLInputElement;
  if (target.files && target.files[0]) {
    const file = target.files[0];
    const reader = new FileReader();
    reader.onload = (event) => {
      receiptPreview.value = event.target?.result as string;
    };
    reader.readAsDataURL(file);
  }
}

function generateDemo() {
  const bank = fundStore.paymentRequisites[0]?.bankName || 'СберБанк Онлайн';
  const recipient = fundStore.paymentRequisites[0]?.recipientName || 'Фонд Дома';

  const svg = generateReceiptSvg({
    bankName: bank,
    amount: amount.value,
    date: new Date().toLocaleString('ru-RU'),
    senderName: fundStore.currentUser.fullName,
    recipientName: recipient,
    purpose:
      category.value === 'MONTHLY_FEE'
        ? `Взнос за ЖКУ (${fundStore.currentUser.addressUnit})`
        : 'Целевой взнос',
  });

  receiptPreview.value = svg;
  message.success('Тестовый чек успешно сгенерирован');
}

function handleSubmit() {
  if (!amount.value || amount.value <= 0) {
    message.error('Укажите сумму платежа');
    return;
  }
  if (!receiptPreview.value) {
    message.error('Прикрепите квитанцию или чек');
    return;
  }

  fundStore.submitContribution({
    amount: amount.value,
    category: category.value,
    targetFundId: selectedTargetFundId.value,
    billingPeriod: category.value === 'MONTHLY_FEE' ? '2026-09' : undefined,
    receiptImagePath: receiptPreview.value,
    commentUser: commentUser.value.trim() || undefined,
  });

  receiptPreview.value = '';
  commentUser.value = '';
  message.success('Взнос отправлен на верификацию');
  fundStore.activeTab = 'history';
}
</script>

<style scoped lang="scss">
.contribute-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 680px;
  margin: 0 auto;
}

/* Page Top Header */
.page-top-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.page-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: #f1f5f9;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  font-size: 0.725rem;
  font-weight: 700;
  color: #475569;
  margin-bottom: 0.5rem;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #10b981;
}

.page-title {
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.page-desc {
  font-size: 0.825rem;
  color: #64748b;
  margin-top: 0.25rem;
  line-height: 1.4;
}

/* Quick Steps */
.quick-steps-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.4rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 16px;
  padding: 0.65rem 0.85rem;
  overflow-x: auto;
}

.quick-step-pill {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  white-space: nowrap;
}

.step-num {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: #4f46e5;
  color: #ffffff;
  font-size: 0.7rem;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.step-text {
  font-size: 0.75rem;
  font-weight: 700;
  color: #1e293b;
}

.quick-step-divider {
  color: #94a3b8;
  font-size: 0.8rem;
}

/* Requisites Section */
.requisites-section {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.section-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 0.25rem;
}

.section-label {
  font-size: 0.85rem;
  font-weight: 800;
  color: #0f172a;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.section-sub {
  font-size: 0.75rem;
  color: #10b981;
  font-weight: 700;
}

.req-cards-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 0.75rem;

  @media (min-width: 600px) {
    grid-template-columns: repeat(2, 1fr);
  }
}

.req-fintech-card {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 18px;
  padding: 1.15rem;
  color: #ffffff;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.15);

  &.is-disabled {
    opacity: 0.6;
    filter: grayscale(0.8);
  }
}

.req-fintech-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.req-bank-tag {
  font-size: 0.825rem;
  font-weight: 800;
  letter-spacing: 0.02em;
  color: #e2e8f0;
}

.req-status-dot {
  font-size: 0.65rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.15);
  color: #94a3b8;

  &.is-active {
    background: rgba(16, 185, 129, 0.25);
    color: #34d399;
  }
}

.req-number-wrap {
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #ffffff;
  margin: 0.4rem 0;
}

.req-meta-details {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  margin-bottom: 0.85rem;
}

.req-meta-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.75rem;
}

.req-meta-label {
  color: #94a3b8;
}

.req-meta-val {
  color: #f1f5f9;
}

.copy-account-btn {
  width: 100%;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  color: #ffffff;
  padding: 0.5rem;
  font-size: 0.775rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.4rem;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.2);
  }
}

/* Contribute Form Card */
.contribute-form-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 1.25rem;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
}

.form-header {
  margin-bottom: 1.25rem;
}

.form-title {
  font-size: 1.15rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.01em;
}

.form-subtitle {
  font-size: 0.775rem;
  color: #64748b;
}

.form-field-group {
  margin-bottom: 1.15rem;
}

.field-label {
  display: block;
  font-size: 0.8rem;
  font-weight: 700;
  color: #334155;
  margin-bottom: 0.45rem;
}

/* Segmented Control */
.segmented-control {
  display: flex;
  background: #f1f5f9;
  padding: 0.25rem;
  border-radius: 14px;
  gap: 0.25rem;
}

.segmented-btn {
  flex: 1;
  padding: 0.65rem 0.5rem;
  border-radius: 11px;
  border: none;
  background: transparent;
  font-size: 0.8rem;
  font-weight: 700;
  color: #64748b;
  cursor: pointer;
  transition: all 0.15s ease;

  &--active {
    background: #ffffff;
    color: #0f172a;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);
  }
}

/* Custom Select */
.custom-select {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 14px;
  border: 1.5px solid #e2e8f0;
  background: #f8fafc;
  font-size: 0.875rem;
  font-weight: 600;
  color: #0f172a;
  outline: none;

  &:focus {
    border-color: #6366f1;
    background: #ffffff;
  }
}

/* Amount Input */
.amount-input-box {
  position: relative;
  display: flex;
  align-items: center;
}

.custom-amount-input {
  width: 100%;
  padding: 0.85rem 2.5rem 0.85rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  background: #f8fafc;
  font-size: 1.5rem;
  font-weight: 800;
  color: #0f172a;
  outline: none;
  transition: all 0.15s ease;

  &:focus {
    border-color: #6366f1;
    background: #ffffff;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
  }
}

.currency-symbol {
  position: absolute;
  right: 1.15rem;
  font-size: 1.25rem;
  font-weight: 800;
  color: #94a3b8;
}

.amount-chips-row {
  display: flex;
  gap: 0.45rem;
  margin-top: 0.6rem;
  flex-wrap: wrap;
}

.amount-chip {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 9999px;
  padding: 0.35rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #e2e8f0;
  }

  &--active {
    background: #eef2ff;
    border-color: #6366f1;
    color: #4f46e5;
  }
}

/* Receipt Upload Box */
.receipt-upload-box {
  border: 2px dashed #cbd5e1;
  border-radius: 18px;
  padding: 1.25rem 1rem;
  text-align: center;
  background: #f8fafc;
  transition: all 0.15s ease;

  &:hover {
    border-color: #94a3b8;
    background: #f1f5f9;
  }
}

.hidden-file-input {
  display: none;
}

.upload-area-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.upload-icon-circle {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: #eef2ff;
  color: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.25rem;
  margin-bottom: 0.5rem;
}

.upload-main-text {
  font-size: 0.85rem;
  font-weight: 700;
  color: #1e293b;
}

.upload-sub-text {
  font-size: 0.725rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.demo-generator-row {
  margin-top: 1rem;
  padding-top: 0.85rem;
  border-top: 1px dashed #e2e8f0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
}

.demo-sep {
  font-size: 0.7rem;
  color: #94a3b8;
}

.demo-gen-btn {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 0.45rem 0.85rem;
  font-size: 0.775rem;
  font-weight: 700;
  color: #0f172a;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  transition: all 0.15s ease;

  &:hover {
    background: #f8fafc;
    border-color: #94a3b8;
  }
}

.uploaded-receipt-preview {
  border: 1.5px solid #10b981;
  background: #f0fdf4;
  border-radius: 16px;
  padding: 0.85rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.receipt-preview-img {
  width: 56px;
  height: 72px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
}

.receipt-preview-info {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.receipt-ok-badge {
  font-size: 0.8rem;
  font-weight: 700;
  color: #15803d;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.receipt-replace-btn {
  background: #fee2e2;
  border: none;
  color: #b91c1c;
  padding: 0.3rem 0.65rem;
  border-radius: 8px;
  font-size: 0.725rem;
  font-weight: 700;
  cursor: pointer;
  width: fit-content;

  &:hover {
    background: #fecaca;
  }
}

.custom-textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border: 1.5px solid #e2e8f0;
  border-radius: 14px;
  background: #f8fafc;
  font-size: 0.825rem;
  outline: none;
  resize: vertical;

  &:focus {
    border-color: #6366f1;
    background: #ffffff;
  }
}

.submit-contribution-btn {
  width: 100%;
  background: #0f172a;
  border: none;
  border-radius: 16px;
  padding: 0.95rem;
  color: #ffffff;
  font-size: 0.95rem;
  font-weight: 800;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.2);
  transition: all 0.15s ease;

  &:hover:not(:disabled) {
    background: #1e293b;
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.form-guarantee-note {
  font-size: 0.7rem;
  color: #94a3b8;
  text-align: center;
  margin-top: 0.75rem;
  line-height: 1.4;
}
</style>
