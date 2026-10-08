<template>
  <div v-if="fundStore.receiptModal.isOpen" class="receipt-backdrop" @click="fundStore.closeReceipt">
    <div class="receipt-card" @click.stop>
      <div class="receipt-header">
        <div class="receipt-title">{{ fundStore.receiptModal.title || 'Квитанция об оплате' }}</div>
        <button class="receipt-close-btn" @click="fundStore.closeReceipt">✕</button>
      </div>

      <div class="receipt-body">
        <div class="receipt-image-wrapper">
          <img
            :src="fundStore.receiptModal.imagePath"
            alt="Квитанция"
            class="receipt-image"
          />
        </div>
      </div>

      <div class="receipt-footer">
        <button class="btn-download" @click="downloadReceipt">
          Скачать документ
        </button>
        <button class="btn-close" @click="fundStore.closeReceipt">
          Закрыть
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useFundStore } from '@/entities/fund/model/fundStore';

const fundStore = useFundStore();

function downloadReceipt() {
  const link = document.createElement('a');
  link.href = fundStore.receiptModal.imagePath;
  link.download = `receipt_${Date.now()}.svg`;
  link.click();
}
</script>

<style scoped lang="scss">
.receipt-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.receipt-card {
  background: #ffffff;
  border-radius: 24px;
  width: 100%;
  max-width: 460px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
  animation: popIn 0.2s ease-out;
}

@keyframes popIn {
  from {
    opacity: 0;
    transform: scale(0.96);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.receipt-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid #f1f5f9;
}

.receipt-title {
  font-size: 1rem;
  font-weight: 800;
  color: #0f172a;
}

.receipt-close-btn {
  background: #f1f5f9;
  border: none;
  width: 30px;
  height: 30px;
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

.receipt-body {
  padding: 1rem 1.25rem;
  overflow-y: auto;
  display: flex;
  justify-content: center;
  background: #f8fafc;
}

.receipt-image-wrapper {
  width: 100%;
  max-width: 380px;
  background: #ffffff;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.06);
  border: 1px solid #e2e8f0;
}

.receipt-image {
  width: 100%;
  height: auto;
  display: block;
}

.receipt-footer {
  display: flex;
  gap: 0.75rem;
  padding: 1rem 1.25rem;
  border-top: 1px solid #f1f5f9;
  background: #ffffff;
}

.btn-download {
  flex: 1;
  background: #0f172a;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s ease;

  &:hover {
    background: #1e293b;
  }
}

.btn-close {
  background: #f1f5f9;
  color: #475569;
  border: none;
  border-radius: 12px;
  padding: 0.75rem 1rem;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;

  &:hover {
    background: #e2e8f0;
    color: #0f172a;
  }
}
</style>
