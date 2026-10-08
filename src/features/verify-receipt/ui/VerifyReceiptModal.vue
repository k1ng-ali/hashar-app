<template>
  <div v-if="isOpen && contribution" class="modal-backdrop" @click="handleClose">
    <div class="modal-card" @click.stop>
      <div class="modal-header">
        <div>
          <div class="modal-title">Верификация платежа и чека</div>
          <div class="modal-subtitle">Проверка подлинности и зачисление на баланс</div>
        </div>
        <button class="modal-close-btn" @click="handleClose">✕</button>
      </div>

      <div class="modal-scroll-body">
        <div class="verify-details-grid">
          <div class="verify-info-col">
            <div class="info-row">
              <span class="info-label">Отправитель:</span>
              <span class="info-val"><strong>{{ contribution.userName }}</strong> ({{ contribution.userUnit }})</span>
            </div>

            <div class="info-row">
              <span class="info-label">Сумма взноса:</span>
              <span class="info-val info-amount">{{ contribution.amount.toLocaleString() }} ₽</span>
            </div>

            <div class="info-row">
              <span class="info-label">Назначение:</span>
              <span class="info-val">
                {{ contribution.category === 'MONTHLY_FEE' ? 'Ежемесячный сбор' : contribution.targetFundTitle || 'Целевой сбор' }}
              </span>
            </div>

            <div class="info-row">
              <span class="info-label">Дата отправки:</span>
              <span class="info-val">{{ formatDate(contribution.createdAt) }}</span>
            </div>

            <div v-if="contribution.commentUser" class="info-comment-box">
              <span class="comment-label">Комментарий жильца:</span>
              <p class="comment-text">«{{ contribution.commentUser }}»</p>
            </div>
          </div>

          <div class="verify-receipt-col">
            <span class="receipt-label">Прикрепленный чек:</span>
            <div class="receipt-thumb-wrapper" @click="openFullReceipt">
              <img :src="contribution.receiptImagePath" alt="Чек" class="receipt-thumb-img" />
              <div class="receipt-zoom-hint">
                <EyeOutlined />
                <span>Увеличить</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Rejection reason form if Reject clicked -->
        <div v-if="showRejectReasonInput" class="reject-reason-box">
          <div class="reject-alert-header">
            <span>Укажите причину отклонения:</span>
          </div>
          <textarea
            v-model="rejectReason"
            rows="3"
            placeholder="Например: Не сходится сумма перевода, либо чек обрезан..."
            class="reject-textarea"
          ></textarea>
          <div class="reject-actions-row">
            <button type="button" class="btn-secondary-sm" @click="showRejectReasonInput = false">
              Назад
            </button>
            <button
              type="button"
              class="btn-danger-sm"
              :disabled="!rejectReason.trim()"
              @click="confirmReject"
            >
              Подтвердить отклонение
            </button>
          </div>
        </div>
      </div>

      <!-- Standard Footer Actions -->
      <div v-if="!showRejectReasonInput" class="modal-footer">
        <button type="button" class="btn-reject" @click="showRejectReasonInput = true">
          <CloseCircleOutlined />
          <span>Отклонить чек</span>
        </button>
        <div class="footer-right-actions">
          <button type="button" class="btn-cancel" @click="handleClose">
            Отмена
          </button>
          <button type="button" class="btn-approve" @click="confirmApprove">
            <CheckCircleOutlined />
            <span>Одобрить и зачислить</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { Contribution } from '@/shared/types';
import { useFundStore } from '@/entities/fund/model/fundStore';
import { formatDate } from '@/shared/utils/finance';
import {
  EyeOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
} from '@ant-design/icons-vue';

const props = defineProps<{
  open: boolean;
  contribution: Contribution | null;
}>();

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void;
}>();

const fundStore = useFundStore();

const isOpen = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val),
});

const showRejectReasonInput = ref(false);
const rejectReason = ref('');

function openFullReceipt() {
  if (props.contribution) {
    fundStore.openReceipt(
      `Чек от ${props.contribution.userName} (${props.contribution.amount} ₽)`,
      props.contribution.receiptImagePath
    );
  }
}

function confirmApprove() {
  if (props.contribution) {
    fundStore.approveContribution(props.contribution.id);
    handleClose();
  }
}

function confirmReject() {
  if (props.contribution && rejectReason.value.trim()) {
    fundStore.rejectContribution(props.contribution.id, rejectReason.value.trim());
    handleClose();
  }
}

function handleClose() {
  isOpen.value = false;
  showRejectReasonInput.value = false;
  rejectReason.value = '';
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
  max-width: 580px;
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
  font-size: 1.1rem;
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

.verify-details-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1.25rem;

  @media (min-width: 540px) {
    grid-template-columns: 1.3fr 1fr;
  }
}

.verify-info-col {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.info-row {
  display: flex;
  justify-content: space-between;
  padding: 0.4rem 0;
  border-bottom: 1px dashed #e2e8f0;
  font-size: 0.8rem;
}

.info-label {
  color: #64748b;
}

.info-val {
  color: #0f172a;
  text-align: right;
}

.info-amount {
  font-size: 1.15rem;
  font-weight: 800;
  color: #10b981;
}

.info-comment-box {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 0.65rem 0.85rem;
  margin-top: 0.5rem;
}

.comment-label {
  font-size: 0.7rem;
  font-weight: 700;
  color: #64748b;
}

.comment-text {
  font-size: 0.775rem;
  color: #0f172a;
  margin-top: 0.2rem;
  font-style: italic;
}

.verify-receipt-col {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.receipt-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
}

.receipt-thumb-wrapper {
  position: relative;
  border-radius: 16px;
  overflow: hidden;
  border: 1.5px solid #cbd5e1;
  background: #f8fafc;
  cursor: pointer;
  aspect-ratio: 3 / 4;
  display: flex;
  align-items: center;
  justify-content: center;

  &:hover .receipt-zoom-hint {
    opacity: 1;
  }
}

.receipt-thumb-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.receipt-zoom-hint {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  color: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.25rem;
  font-size: 0.75rem;
  font-weight: 700;
  opacity: 0.85;
  transition: opacity 0.2s;
}

.reject-reason-box {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 16px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.reject-alert-header {
  font-size: 0.8rem;
  font-weight: 800;
  color: #991b1b;
}

.reject-textarea {
  width: 100%;
  padding: 0.65rem 0.85rem;
  border: 1.5px solid #fca5a5;
  border-radius: 12px;
  background: #ffffff;
  font-size: 0.8rem;
  outline: none;

  &:focus {
    border-color: #ef4444;
  }
}

.reject-actions-row {
  display: flex;
  justify-content: flex-end;
  gap: 0.65rem;
}

.btn-secondary-sm {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 0.5rem 0.85rem;
  font-size: 0.775rem;
  font-weight: 700;
  cursor: pointer;

  &:hover {
    background: #f1f5f9;
  }
}

.btn-danger-sm {
  background: #dc2626;
  color: #ffffff;
  border: none;
  border-radius: 10px;
  padding: 0.5rem 0.85rem;
  font-size: 0.775rem;
  font-weight: 700;
  cursor: pointer;

  &:hover:not(:disabled) {
    background: #b91c1c;
  }

  &:disabled {
    opacity: 0.45;
    cursor: not-allowed;
  }
}

.modal-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.5rem;
  border-top: 1px solid #f1f5f9;
  background: #ffffff;
  gap: 0.75rem;
}

.footer-right-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-reject {
  background: #fee2e2;
  color: #b91c1c;
  border: none;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  font-size: 0.8rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;

  &:hover {
    background: #fecaca;
  }
}

.btn-cancel {
  background: #f1f5f9;
  border: none;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: #475569;
  cursor: pointer;

  &:hover {
    background: #e2e8f0;
    color: #0f172a;
  }
}

.btn-approve {
  background: #10b981;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  padding: 0.75rem 1.15rem;
  font-size: 0.8rem;
  font-weight: 800;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.4rem;

  &:hover {
    background: #059669;
  }
}
</style>
