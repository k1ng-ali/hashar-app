<template>
  <div v-if="isOpen" class="modal-backdrop" @click="handleClose">
    <div class="modal-card" @click.stop>
      <!-- Sheet Header -->
      <div class="modal-header">
        <div>
          <div class="modal-title">Внесение взноса в фонд</div>
          <div class="modal-subtitle">ЖК «Северная Звезда» • кв. {{ fundStore.currentUser.addressUnit }}</div>
        </div>
        <button class="modal-close-btn" @click="handleClose">✕</button>
      </div>

      <!-- Sheet Scrollable Body -->
      <div class="modal-scroll-body">
        <!-- Debt status warning box if user owes money -->
        <div v-if="residentStatus.statusType === 'DEBT'" class="debt-alert-box">
          <div class="debt-alert-content">
            <div class="debt-alert-title">
              Задолженность: {{ residentStatus.debtAmount.toLocaleString() }} ₽
            </div>
            <div class="debt-alert-desc">
              Не оплачено {{ residentStatus.debtMonthsCount }} мес. ({{ residentStatus.unpaidPeriods.join(', ') }})
            </div>
          </div>
          <button
            type="button"
            class="debt-fill-btn"
            @click="amount = residentStatus.debtAmount"
          >
            Погасить весь долг
          </button>
        </div>

        <!-- 1. Category Switcher (Segmented Pill) -->
        <div class="form-group">
          <label class="form-label">Тип взноса</label>
          <div class="segmented-pills">
            <button
              type="button"
              class="seg-pill"
              :class="{ 'seg-pill--active': category === 'MONTHLY_FEE' }"
              @click="category = 'MONTHLY_FEE'"
            >
              Ежемесячный сбор ({{ fundStore.billingRate.amount }} ₽)
            </button>
            <button
              type="button"
              class="seg-pill"
              :class="{ 'seg-pill--active': category === 'TARGET_FUND' }"
              @click="category = 'TARGET_FUND'"
            >
              Целевой сбор
            </button>
          </div>
        </div>

        <!-- If Target Fund Selected -->
        <div v-if="category === 'TARGET_FUND'" class="form-group">
          <label class="form-label">Целевой проект сбора</label>
          <select v-model="selectedTargetFundId" class="modal-select">
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

        <!-- 2. Amount Input + Quick Presets -->
        <div class="form-group">
          <label class="form-label">Сумма взноса (₽)</label>
          <div class="amount-input-wrap">
            <input
              v-model.number="amount"
              type="number"
              min="100"
              max="1000000"
              step="100"
              placeholder="0"
              class="modal-num-input font-mono"
            />
            <span class="currency-label">₽</span>
          </div>

          <div class="chips-row">
            <button
              v-for="val in [1500, 3000, 4500, 9000]"
              :key="val"
              type="button"
              class="chip-btn"
              :class="{ 'chip-btn--active': amount === val }"
              @click="amount = val"
            >
              {{ val.toLocaleString() }} ₽
            </button>
          </div>
        </div>

        <!-- 3. Active Bank Requisites Details -->
        <div class="requisites-wrap">
          <div class="req-header-row">
            <span class="req-section-title">Реквизиты фонда для перевода</span>
            <span class="req-tag-sbp">СБП без комиссии</span>
          </div>

          <div v-if="activeRequisites.length > 0" class="req-cards-column">
            <div
              v-for="req in activeRequisites"
              :key="req.id"
              class="mini-req-card"
            >
              <div class="mini-req-top">
                <span class="mini-req-bank">{{ req.bankName }}</span>
                <span class="mini-req-recipient">{{ req.recipientName }}</span>
              </div>
              <div class="mini-req-num font-mono">{{ req.cardOrAccountNumber }}</div>
              <div v-if="req.phoneNumber" class="mini-req-phone">
                СБП: <strong>{{ req.phoneNumber }}</strong>
              </div>

              <button
                type="button"
                class="mini-req-copy-btn"
                @click="copyCard(req.cardOrAccountNumber)"
              >
                <CopyOutlined /> Скопировать номер
              </button>
            </div>
          </div>
        </div>

        <!-- 4. Receipt Upload / Demo Generator -->
        <div class="form-group">
          <label class="form-label">Чек или квитанция платежа</label>

          <div v-if="receiptPreview" class="receipt-preview-box">
            <img :src="receiptPreview" alt="Чек" class="receipt-preview-thumb" />
            <div class="receipt-preview-details">
              <div class="receipt-success-text">
                <CheckCircleOutlined /> Документ прикреплен
              </div>
              <button
                type="button"
                class="receipt-remove-btn"
                @click="receiptPreview = ''"
              >
                Удалить чек
              </button>
            </div>
          </div>

          <div v-else class="receipt-dropzone">
            <input
              type="file"
              accept="image/*,.pdf"
              id="modal-file-upload"
              class="hidden-file-input"
              @change="handleFileUpload"
            />
            <label for="modal-file-upload" class="dropzone-label">
              <div class="dropzone-icon">
                <UploadOutlined />
              </div>
              <div class="dropzone-text">Нажмите для выбора фото или чека</div>
              <div class="dropzone-sub">Скриншот из банковского приложения (PNG, JPG, PDF)</div>
            </label>

            <div class="demo-gen-box">
              <span class="demo-gen-text">или для мгновенного теста:</span>
              <button
                type="button"
                class="demo-gen-action"
                @click="handleGenerateDemoReceipt"
              >
                <ThunderboltOutlined />
                <span>Сформировать электронный чек</span>
              </button>
            </div>
          </div>
        </div>

        <!-- 5. Optional Comment -->
        <div class="form-group">
          <label class="form-label">Комментарий для ревизора (необязательно)</label>
          <textarea
            v-model="commentUser"
            rows="2"
            class="modal-textarea"
            placeholder="Например: Взнос за сентябрь и октябрь..."
          ></textarea>
        </div>
      </div>

      <!-- Sheet Footer Actions -->
      <div class="modal-footer">
        <button type="button" class="btn-cancel" @click="handleClose">
          Отмена
        </button>
        <button
          type="button"
          class="btn-submit"
          :disabled="!amount || !receiptPreview"
          @click="handleSubmit"
        >
          <span>Отправить на проверку</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import { generateReceiptSvg } from '@/shared/utils/receiptGenerator';
import { message } from 'ant-design-vue';
import {
  UploadOutlined,
  ThunderboltOutlined,
  CopyOutlined,
  CheckCircleOutlined,
} from '@ant-design/icons-vue';

const props = defineProps<{
  open: boolean;
  targetFundId?: number;
}>();

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void;
}>();

const fundStore = useFundStore();

const isOpen = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val),
});

const category = ref<'MONTHLY_FEE' | 'TARGET_FUND'>('MONTHLY_FEE');
const selectedTargetFundId = ref<number | undefined>(undefined);
const amount = ref<number>(1500);
const receiptPreview = ref<string>('');
const commentUser = ref<string>('');

watch(
  () => props.open,
  (newOpen) => {
    if (newOpen) {
      if (props.targetFundId) {
        category.value = 'TARGET_FUND';
        selectedTargetFundId.value = props.targetFundId;
      } else if (residentStatus.value.statusType === 'DEBT' && residentStatus.value.debtAmount > 0) {
        category.value = 'MONTHLY_FEE';
        amount.value = residentStatus.value.debtAmount;
      }
    }
  }
);

const residentStatus = computed(() => fundStore.currentUserStatus);

const activeTargetFunds = computed(() => {
  return fundStore.targetFunds.filter((tf) => tf.isActive);
});

const activeRequisites = computed(() => {
  return fundStore.paymentRequisites.filter((r) => r.isActive);
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

function handleGenerateDemoReceipt() {
  const bank = activeRequisites.value[0]?.bankName || 'СберБанк Онлайн';
  const recipient = activeRequisites.value[0]?.recipientName || 'Фонд Дома';

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
  message.success('Тестовый чек успешно прикреплен');
}

function handleClose() {
  isOpen.value = false;
}

function handleSubmit() {
  if (!amount.value || amount.value <= 0) {
    message.error('Укажите корректную сумму');
    return;
  }
  if (!receiptPreview.value) {
    message.error('Прикрепите подтверждающий чек');
    return;
  }
  if (category.value === 'TARGET_FUND' && !selectedTargetFundId.value) {
    message.error('Выберите целевой сбор');
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

  message.success('Платеж отправлен на проверку');
  receiptPreview.value = '';
  commentUser.value = '';
  handleClose();
}
</script>

<style scoped lang="scss">
.modal-backdrop {
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

.modal-card {
  background: #ffffff;
  width: 100%;
  max-width: 560px;
  max-height: 92vh;
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

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }
  to {
    transform: translateY(0);
  }
}

.modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  padding: 1.25rem 1.5rem 1rem 1.5rem;
  border-bottom: 1px solid #f1f5f9;
}

.modal-title {
  font-size: 1.15rem;
  font-weight: 800;
  color: #0f172a;
}

.modal-subtitle {
  font-size: 0.775rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.modal-close-btn {
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

.modal-scroll-body {
  padding: 1.25rem 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 1.15rem;
}

.debt-alert-box {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 16px;
  padding: 0.85rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.debt-alert-title {
  font-size: 0.85rem;
  font-weight: 800;
  color: #991b1b;
}

.debt-alert-desc {
  font-size: 0.75rem;
  color: #b91c1c;
}

.debt-fill-btn {
  background: #dc2626;
  color: #ffffff;
  border: none;
  border-radius: 9999px;
  padding: 0.4rem 0.85rem;
  font-size: 0.75rem;
  font-weight: 700;
  cursor: pointer;
  white-space: nowrap;

  &:hover {
    background: #b91c1c;
  }
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.form-label {
  font-size: 0.8rem;
  font-weight: 700;
  color: #334155;
}

.segmented-pills {
  display: flex;
  background: #f1f5f9;
  padding: 0.25rem;
  border-radius: 14px;
  gap: 0.25rem;
}

.seg-pill {
  flex: 1;
  padding: 0.6rem 0.5rem;
  border-radius: 11px;
  border: none;
  background: transparent;
  font-size: 0.775rem;
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

.modal-select {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 14px;
  border: 1.5px solid #e2e8f0;
  background: #f8fafc;
  font-size: 0.85rem;
  font-weight: 600;
  color: #0f172a;
  outline: none;

  &:focus {
    border-color: #6366f1;
    background: #ffffff;
  }
}

.amount-input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.modal-num-input {
  width: 100%;
  padding: 0.75rem 2.5rem 0.75rem 1rem;
  border: 2px solid #e2e8f0;
  border-radius: 16px;
  background: #f8fafc;
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f172a;
  outline: none;

  &:focus {
    border-color: #6366f1;
    background: #ffffff;
    box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1);
  }
}

.currency-label {
  position: absolute;
  right: 1.15rem;
  font-size: 1.2rem;
  font-weight: 800;
  color: #94a3b8;
}

.chips-row {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
  margin-top: 0.4rem;
}

.chip-btn {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 9999px;
  padding: 0.3rem 0.65rem;
  font-size: 0.725rem;
  font-weight: 700;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s ease;

  &--active {
    background: #eef2ff;
    border-color: #6366f1;
    color: #4f46e5;
  }
}

.requisites-wrap {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 0.85rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.req-header-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.req-section-title {
  font-size: 0.775rem;
  font-weight: 800;
  color: #334155;
  text-transform: uppercase;
  letter-spacing: 0.03em;
}

.req-tag-sbp {
  font-size: 0.675rem;
  font-weight: 700;
  color: #15803d;
  background: #dcfce7;
  padding: 0.15rem 0.45rem;
  border-radius: 9999px;
}

.req-cards-column {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.mini-req-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 0.75rem;
}

.mini-req-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-size: 0.75rem;
}

.mini-req-bank {
  font-weight: 800;
  color: #0f172a;
}

.mini-req-recipient {
  color: #64748b;
}

.mini-req-num {
  font-size: 0.95rem;
  font-weight: 800;
  color: #1e293b;
  margin: 0.25rem 0;
  letter-spacing: 0.04em;
}

.mini-req-phone {
  font-size: 0.725rem;
  color: #64748b;
}

.mini-req-copy-btn {
  margin-top: 0.5rem;
  width: 100%;
  background: #f1f5f9;
  border: none;
  border-radius: 8px;
  padding: 0.35rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: #0f172a;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;

  &:hover {
    background: #e2e8f0;
  }
}

.receipt-dropzone {
  border: 2px dashed #cbd5e1;
  border-radius: 16px;
  padding: 1rem;
  text-align: center;
  background: #f8fafc;
}

.hidden-file-input {
  display: none;
}

.dropzone-label {
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
}

.dropzone-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: #eef2ff;
  color: #4f46e5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
  margin-bottom: 0.4rem;
}

.dropzone-text {
  font-size: 0.825rem;
  font-weight: 700;
  color: #1e293b;
}

.dropzone-sub {
  font-size: 0.7rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.demo-gen-box {
  margin-top: 0.75rem;
  padding-top: 0.65rem;
  border-top: 1px dashed #e2e8f0;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.35rem;
}

.demo-gen-text {
  font-size: 0.675rem;
  color: #94a3b8;
}

.demo-gen-action {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 8px;
  padding: 0.35rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: #0f172a;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;

  &:hover {
    background: #f8fafc;
    border-color: #94a3b8;
  }
}

.receipt-preview-box {
  border: 1.5px solid #10b981;
  background: #f0fdf4;
  border-radius: 14px;
  padding: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.85rem;
}

.receipt-preview-thumb {
  width: 50px;
  height: 64px;
  object-fit: cover;
  border-radius: 8px;
  border: 1px solid #cbd5e1;
}

.receipt-success-text {
  font-size: 0.8rem;
  font-weight: 700;
  color: #15803d;
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.receipt-remove-btn {
  margin-top: 0.35rem;
  background: #fee2e2;
  border: none;
  color: #b91c1c;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  cursor: pointer;

  &:hover {
    background: #fecaca;
  }
}

.modal-textarea {
  width: 100%;
  padding: 0.65rem 0.85rem;
  border: 1.5px solid #e2e8f0;
  border-radius: 14px;
  background: #f8fafc;
  font-size: 0.8rem;
  outline: none;
  resize: vertical;

  &:focus {
    border-color: #6366f1;
    background: #ffffff;
  }
}

.modal-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid #f1f5f9;
  background: #ffffff;
}

.btn-cancel {
  background: #f1f5f9;
  border: none;
  border-radius: 14px;
  padding: 0.85rem 1.25rem;
  font-size: 0.85rem;
  font-weight: 700;
  color: #475569;
  cursor: pointer;

  &:hover {
    background: #e2e8f0;
    color: #0f172a;
  }
}

.btn-submit {
  flex: 1;
  background: #0f172a;
  border: none;
  border-radius: 14px;
  padding: 0.85rem 1.25rem;
  font-size: 0.85rem;
  font-weight: 800;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover:not(:disabled) {
    background: #1e293b;
  }

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
}
</style>
