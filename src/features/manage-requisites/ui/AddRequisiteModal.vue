<template>
  <div v-if="isOpen" class="modal-backdrop" @click="handleClose">
    <div class="modal-card" @click.stop>
      <div class="modal-header">
        <div>
          <div class="modal-title">Добавление счета или карты фонда</div>
          <div class="modal-subtitle">Реквизиты будут доступны всем жителям для оплат</div>
        </div>
        <button class="modal-close-btn" @click="handleClose">✕</button>
      </div>

      <div class="modal-scroll-body">
        <div class="form-group">
          <label class="form-label">Банк / Тип счета *</label>
          <select v-model="bankName" class="modal-select">
            <option value="" disabled>Выберите банк</option>
            <option value="Сбербанк">Сбербанк</option>
            <option value="Т-Банк (Тинькофф)">Т-Банк (Тинькофф)</option>
            <option value="Альфа-Банк">Альфа-Банк</option>
            <option value="ВТБ">ВТБ</option>
            <option value="Расчетный счет ТСЖ">Расчетный счет ТСЖ</option>
          </select>
        </div>

        <div class="form-group">
          <label class="form-label">Номер карты или р/с *</label>
          <input
            v-model="cardOrAccountNumber"
            type="text"
            placeholder="2202 2034 5678 9101 или 40702810..."
            class="modal-input font-mono"
          />
        </div>

        <div class="form-group">
          <label class="form-label">ФИО получателя *</label>
          <input
            v-model="recipientName"
            type="text"
            placeholder="Иван Иванович И. (Председатель)"
            class="modal-input"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Телефон для переводов через СБП</label>
          <input
            v-model="phoneNumber"
            type="text"
            placeholder="+7 (999) 000-00-00"
            class="modal-input"
          />
        </div>

        <div class="form-group">
          <label class="form-label">Инструкция / Комментарий для жителей</label>
          <textarea
            v-model="note"
            rows="2"
            placeholder="Например: В назначении платежа обязательно укажите номер квартиры"
            class="modal-textarea"
          ></textarea>
        </div>
      </div>

      <div class="modal-footer">
        <button type="button" class="btn-cancel" @click="handleClose">
          Отмена
        </button>
        <button
          type="button"
          class="btn-submit"
          :disabled="!bankName || !cardOrAccountNumber || !recipientName"
          @click="handleSubmit"
        >
          Сохранить реквизит
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import { message } from 'ant-design-vue';

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

const bankName = ref('Сбербанк');
const cardOrAccountNumber = ref('');
const recipientName = ref('');
const phoneNumber = ref('');
const note = ref('');

function handleClose() {
  isOpen.value = false;
  resetForm();
}

function resetForm() {
  bankName.value = 'Сбербанк';
  cardOrAccountNumber.value = '';
  recipientName.value = '';
  phoneNumber.value = '';
  note.value = '';
}

function handleSubmit() {
  if (!bankName.value || !cardOrAccountNumber.value.trim() || !recipientName.value.trim()) {
    message.error('Заполните обязательные поля');
    return;
  }

  fundStore.addPaymentRequisite({
    bankName: bankName.value,
    cardOrAccountNumber: cardOrAccountNumber.value.trim(),
    recipientName: recipientName.value.trim(),
    phoneNumber: phoneNumber.value.trim() || undefined,
    note: note.value.trim() || undefined,
  });

  message.success('Реквизит успешно сохранен');
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
  max-width: 500px;
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
