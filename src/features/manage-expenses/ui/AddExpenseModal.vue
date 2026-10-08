<template>
  <div v-if="isOpen" class="modal-backdrop" @click="handleClose">
    <div class="modal-card" @click.stop>
      <div class="modal-header">
        <div>
          <div class="modal-title">Внесение расхода средств фонда</div>
          <div class="modal-subtitle">Списание с баланса ЖК с обязательным обоснованием</div>
        </div>
        <button class="modal-close-btn" @click="handleClose">✕</button>
      </div>

      <div class="modal-scroll-body">
        <!-- Title Input -->
        <div class="form-group">
          <label class="form-label">Название расхода / Работы *</label>
          <input
            v-model="title"
            type="text"
            placeholder="Например: Покупка LED-светильников для МОП"
            class="modal-input"
          />
        </div>

        <div class="form-row-two">
          <!-- Category -->
          <div class="form-group flex-1">
            <label class="form-label">Категория *</label>
            <select v-model="category" class="modal-select">
              <option value="Ремонт">Ремонт</option>
              <option value="Электрика">Электрика</option>
              <option value="Аварийные работы">Аварийные работы</option>
              <option value="Хознужды">Хознужды</option>
              <option value="Озеленение">Озеленение</option>
              <option value="Видеонаблюдение">Видеонаблюдение</option>
            </select>
          </div>

          <!-- Amount -->
          <div class="form-group flex-1">
            <label class="form-label">Сумма (₽) *</label>
            <input
              v-model.number="amount"
              type="number"
              min="1"
              max="10000000"
              placeholder="0"
              class="modal-input font-mono"
            />
          </div>
        </div>

        <!-- Target Fund Deduction -->
        <div class="form-group">
          <label class="form-label">Списать за счет целевого сбора (необязательно)</label>
          <select v-model="targetFundId" class="modal-select">
            <option :value="undefined">Общий баланс дома</option>
            <option
              v-for="tf in fundStore.targetFunds"
              :key="tf.id"
              :value="tf.id"
            >
              {{ tf.title }}
            </option>
          </select>
        </div>

        <!-- Description -->
        <div class="form-group">
          <label class="form-label">Подробное описание и обоснование *</label>
          <textarea
            v-model="description"
            rows="3"
            class="modal-textarea"
            placeholder="Укажите количество купленного материала, подрядчика, номер договора или акта выполненных работ..."
          ></textarea>
        </div>

        <!-- Receipt / Act -->
        <div class="form-group">
          <label class="form-label">Подтверждающий чек или акт выполненных работ</label>
          <div v-if="receiptPreview" class="receipt-preview-box">
            <img :src="receiptPreview" alt="Чек" class="receipt-preview-thumb" />
            <div class="receipt-preview-actions">
              <span class="text-success-bold">Чек прикреплен</span>
              <button type="button" class="btn-remove-sm" @click="receiptPreview = ''">
                Удалить
              </button>
            </div>
          </div>
          <div v-else class="empty-receipt-box">
            <button type="button" class="btn-demo-receipt" @click="generateExpenseDemoReceipt">
              <FileDoneOutlined />
              <span>Сформировать товарный чек онлайн</span>
            </button>
          </div>
        </div>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn-cancel" @click="handleClose">
          Отмена
        </button>
        <button
          type="button"
          class="btn-submit"
          :disabled="!title || !amount || !description"
          @click="handleSubmit"
        >
          Зафиксировать расход
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import { ExpenseCategory } from '@/shared/types';
import { generateReceiptSvg } from '@/shared/utils/receiptGenerator';
import { message } from 'ant-design-vue';
import { FileDoneOutlined } from '@ant-design/icons-vue';

const props = defineProps<{
  open: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void;
}>();

const fundStore = useFundStore();

const isOpen = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val),
});

const title = ref('');
const category = ref<ExpenseCategory>('Хознужды');
const amount = ref<number | undefined>(undefined);
const targetFundId = ref<number | undefined>(undefined);
const description = ref('');
const receiptPreview = ref('');

function handleClose() {
  isOpen.value = false;
  resetForm();
}

function resetForm() {
  title.value = '';
  category.value = 'Хознужды';
  amount.value = undefined;
  targetFundId.value = undefined;
  description.value = '';
  receiptPreview.value = '';
}

function generateExpenseDemoReceipt() {
  const currentCategory = category.value;
  const currentAmount = amount.value || 8500;
  const currentTitle = title.value || 'Хозяйственные материалы и инструмент';

  const svg = generateReceiptSvg({
    bankName: 'ООО Леруа Мерлен Восток',
    amount: currentAmount,
    date: new Date().toLocaleString('ru-RU'),
    senderName: 'ТСЖ Северная Звезда',
    recipientName: 'ООО Леруа Мерлен',
    purpose: `Оплата по счету №${Math.floor(Math.random() * 90000) + 10000}: ${currentTitle} (${currentCategory})`,
  });

  receiptPreview.value = svg;
  if (!amount.value) {
    amount.value = currentAmount;
  }
  message.success('Тестовый чек расхода сгенерирован');
}

function handleSubmit() {
  if (!title.value.trim()) {
    message.error('Укажите название расхода');
    return;
  }
  if (!amount.value || amount.value <= 0) {
    message.error('Укажите корректную сумму расхода');
    return;
  }
  if (!description.value.trim()) {
    message.error('Заполните подробное обоснование расхода');
    return;
  }

  fundStore.addExpense({
    title: title.value.trim(),
    category: category.value,
    amount: amount.value,
    targetFundId: targetFundId.value,
    description: description.value.trim(),
    receiptImagePath: receiptPreview.value || undefined,
  });

  message.success('Расход успешно зафиксирован в отчете дома');
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
  max-width: 540px;
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
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.45rem;
}

.form-row-two {
  display: flex;
  gap: 0.75rem;
}

.flex-1 {
  flex: 1;
}

.form-label {
  font-size: 0.8rem;
  font-weight: 700;
  color: #334155;
}

.modal-input,
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

.modal-textarea {
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

.receipt-preview-actions {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.text-success-bold {
  font-size: 0.8rem;
  font-weight: 700;
  color: #15803d;
}

.btn-remove-sm {
  background: #fee2e2;
  border: none;
  color: #b91c1c;
  padding: 0.25rem 0.6rem;
  border-radius: 6px;
  font-size: 0.7rem;
  font-weight: 700;
  cursor: pointer;
  align-self: flex-start;

  &:hover {
    background: #fecaca;
  }
}

.empty-receipt-box {
  border: 1.5px dashed #cbd5e1;
  border-radius: 14px;
  padding: 0.75rem;
  text-align: center;
  background: #f8fafc;
}

.btn-demo-receipt {
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: #0f172a;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;

  &:hover {
    background: #f1f5f9;
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
