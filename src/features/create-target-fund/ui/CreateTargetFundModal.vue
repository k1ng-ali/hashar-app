<template>
  <div v-if="isOpen" class="modal-backdrop" @click="handleClose">
    <div class="modal-card" @click.stop>
      <div class="modal-header">
        <div>
          <div class="modal-title">Открытие целевого сбора</div>
          <div class="modal-subtitle">Инициатива на масштабные проекты дома</div>
        </div>
        <button class="modal-close-btn" @click="handleClose">✕</button>
      </div>

      <div class="modal-scroll-body">
        <div class="form-group">
          <label class="form-label">Название проекта / сбора *</label>
          <input
            v-model="form.title"
            type="text"
            placeholder="Например: Автоматический шлагбаум и камеры с распознаванием"
            class="modal-input"
          />
        </div>

        <div class="form-row-two">
          <div class="form-group flex-1">
            <label class="form-label">Категория *</label>
            <select v-model="form.category" class="modal-select">
              <option value="Благоустройство">Благоустройство</option>
              <option value="Безопасность">Безопасность</option>
              <option value="Капремонт">Капремонт</option>
              <option value="Инфраструктура">Инфраструктура</option>
            </select>
          </div>

          <div class="form-group flex-1">
            <label class="form-label">Необходимая сумма (₽) *</label>
            <input
              v-model.number="form.targetAmount"
              type="number"
              min="1000"
              step="5000"
              placeholder="0"
              class="modal-input font-mono"
            />
          </div>
        </div>

        <!-- Quick Amount Presets -->
        <div class="presets-block">
          <span class="presets-label">Быстрый выбор суммы:</span>
          <div class="chips-row">
            <button
              v-for="amt in [50000, 100000, 180000, 280000, 500000]"
              :key="amt"
              type="button"
              class="chip-btn"
              :class="{ 'chip-btn--active': form.targetAmount === amt }"
              @click="form.targetAmount = amt"
            >
              {{ (amt / 1000).toLocaleString() }} тыс. ₽
            </button>
          </div>
        </div>

        <!-- Description -->
        <div class="form-group">
          <label class="form-label">Подробное описание и смета проекта *</label>
          <textarea
            v-model="form.description"
            rows="4"
            class="modal-textarea"
            placeholder="Опишите, какие работы планируются, согласовано ли решение на общем собрании собственников, кто выступает подрядчиком..."
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
          :disabled="!form.title.trim() || !form.targetAmount || !form.description.trim() || isSubmitting"
          @click="handleSubmit"
        >
          <RocketOutlined />
          <span>{{ isSubmitting ? 'Создание...' : 'Открыть сбор средств' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import { TargetFundCategory } from '@/shared/types';
import { message } from 'ant-design-vue';
import { RocketOutlined } from '@ant-design/icons-vue';

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

const isSubmitting = ref(false);

const form = reactive({
  title: '',
  category: 'Благоустройство' as TargetFundCategory,
  targetAmount: 180000,
  description: '',
});

function handleClose() {
  isOpen.value = false;
  resetForm();
}

function resetForm() {
  form.title = '';
  form.category = 'Благоустройство';
  form.targetAmount = 180000;
  form.description = '';
  isSubmitting.value = false;
}

function handleSubmit() {
  if (!form.title.trim()) {
    message.error('Укажите понятное название инициативы');
    return;
  }
  if (!form.targetAmount || form.targetAmount < 1000) {
    message.error('Укажите корректную целевую сумму (от 1 000 ₽)');
    return;
  }
  if (!form.description.trim()) {
    message.error('Опишите цель проекта и ожидаемый результат');
    return;
  }

  isSubmitting.value = true;
  setTimeout(() => {
    fundStore.createTargetFund({
      title: form.title.trim(),
      category: form.category,
      targetAmount: form.targetAmount,
      description: form.description.trim(),
    });

    message.success('Целевой сбор успешно открыт!');
    isSubmitting.value = false;
    handleClose();
  }, 250);
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

.presets-block {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.presets-label {
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
}

.chips-row {
  display: flex;
  gap: 0.4rem;
  flex-wrap: wrap;
}

.chip-btn {
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 9999px;
  padding: 0.35rem 0.75rem;
  font-size: 0.75rem;
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
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
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
