<template>
  <header class="mobile-top-bar">
    <div class="top-bar-content">
      <!-- Left side: Back button or Brand -->
      <div class="top-bar-left">
        <button
          v-if="fundStore.activeTab !== 'dashboard'"
          class="back-nav-btn"
          @click="fundStore.activeTab = 'dashboard'"
          aria-label="Вернуться на главную"
        >
          <ArrowLeftOutlined />
          <span class="back-text">Главная</span>
        </button>

        <div v-else class="brand-pill" @click="fundStore.activeTab = 'dashboard'">
          <div class="brand-indicator"></div>
          <span class="brand-name">ЖК «Северная Звезда»</span>
        </div>
      </div>

      <!-- Right side: Quick Requisites + User Chip -->
      <div class="top-bar-right">
        <button
          class="requisites-pill-btn"
          @click="showRequisites = true"
          title="Реквизиты фонда"
        >
          <QrcodeOutlined />
          <span class="btn-text">Счет</span>
        </button>

        <button
          class="user-avatar-chip"
          @click="showUserModal = true"
          title="Сменить жителя / аккаунт"
        >
          <img
            v-if="fundStore.currentUser.avatarUrl"
            :src="fundStore.currentUser.avatarUrl"
            :alt="fundStore.currentUser.fullName"
            class="user-avatar-img"
          />
          <div v-else class="user-avatar-fallback">
            {{ fundStore.currentUser.fullName[0] }}
          </div>
          <span class="user-role-badge">
            {{ fundStore.isSuperAdmin ? 'Председатель' : fundStore.isAdmin ? 'Ревизор' : 'кв. ' + fundStore.currentUser.addressUnit }}
          </span>
          <DownOutlined class="chip-chevron" />
        </button>
      </div>
    </div>

    <!-- User Switcher Modal -->
    <UserSwitcherModal v-model="showUserModal" />

    <!-- Sleek Requisites Sheet Modal -->
    <div v-if="showRequisites" class="req-modal-backdrop" @click="showRequisites = false">
      <div class="req-modal-card" @click.stop>
        <div class="req-modal-header">
          <div>
            <div class="req-modal-title">Реквизиты фонда дома</div>
            <div class="req-modal-sub">Официальные счета для переводов без комиссии</div>
          </div>
          <button class="req-close-btn" @click="showRequisites = false">✕</button>
        </div>

        <div class="req-cards-list">
          <div
            v-for="r in fundStore.paymentRequisites"
            :key="r.id"
            class="req-account-item"
            :class="{ 'is-disabled': !r.isActive }"
          >
            <div class="req-item-top">
              <span class="req-bank-name">{{ r.bankName }}</span>
              <span class="req-active-badge">{{ r.isActive ? 'Активен' : 'Отключен' }}</span>
            </div>
            <div class="req-card-number font-mono">{{ r.cardOrAccountNumber }}</div>
            <div class="req-recipient">Получатель: {{ r.recipientName }}</div>
            <div v-if="r.phoneNumber" class="req-sbp">
              СБП: <strong>{{ r.phoneNumber }}</strong>
            </div>

            <button
              class="req-copy-btn"
              @click="copyNumber(r.cardOrAccountNumber)"
            >
              <CopyOutlined /> Скопировать номер
            </button>
          </div>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import UserSwitcherModal from '@/widgets/user-switcher/ui/UserSwitcherModal.vue';
import {
  ArrowLeftOutlined,
  QrcodeOutlined,
  DownOutlined,
  CopyOutlined,
} from '@ant-design/icons-vue';
import { message } from 'ant-design-vue';

const fundStore = useFundStore();
const showUserModal = ref(false);
const showRequisites = ref(false);

function copyNumber(num: string) {
  navigator.clipboard.writeText(num.replace(/\s+/g, ''));
  message.success('Номер счета скопирован');
}
</script>

<style scoped lang="scss">
.mobile-top-bar {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(226, 232, 240, 0.8);
}

.top-bar-content {
  max-width: 720px;
  margin: 0 auto;
  padding: 0.65rem 1rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.top-bar-left {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.back-nav-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: #f1f5f9;
  border: none;
  padding: 0.4rem 0.85rem;
  border-radius: 9999px;
  font-size: 0.825rem;
  font-weight: 700;
  color: #0f172a;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #e2e8f0;
  }
}

.brand-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  cursor: pointer;
}

.brand-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background-color: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.6);
}

.brand-name {
  font-size: 0.9rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.top-bar-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.requisites-pill-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 0.35rem 0.65rem;
  border-radius: 9999px;
  font-size: 0.775rem;
  font-weight: 700;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #f1f5f9;
    color: #0f172a;
  }
}

.user-avatar-chip {
  display: inline-flex;
  align-items: center;
  gap: 0.45rem;
  background: #ffffff;
  border: 1px solid #e2e8f0;
  padding: 0.25rem 0.65rem 0.25rem 0.3rem;
  border-radius: 9999px;
  cursor: pointer;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  transition: all 0.15s ease;

  &:hover {
    background: #f8fafc;
    border-color: #cbd5e1;
  }
}

.user-avatar-img {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  object-fit: cover;
}

.user-avatar-fallback {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: #4f46e5;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 700;
}

.user-role-badge {
  font-size: 0.75rem;
  font-weight: 700;
  color: #0f172a;
  max-width: 110px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.chip-chevron {
  font-size: 0.65rem;
  color: #94a3b8;
}

/* Requisites Modal */
.req-modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.6);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: center;

  @media (min-width: 640px) {
    align-items: center;
    padding: 1.5rem;
  }
}

.req-modal-card {
  background: #ffffff;
  width: 100%;
  max-width: 480px;
  border-radius: 24px 24px 0 0;
  padding: 1.5rem 1.25rem 2rem 1.25rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
  animation: slideUp 0.2s ease-out;

  @media (min-width: 640px) {
    border-radius: 24px;
    padding: 1.75rem;
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

.req-modal-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.req-modal-title {
  font-size: 1.2rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.req-modal-sub {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 0.15rem;
}

.req-close-btn {
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
  font-weight: 700;

  &:hover {
    background: #e2e8f0;
    color: #0f172a;
  }
}

.req-cards-list {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.req-account-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 1rem 1.15rem;
}

.req-item-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.req-bank-name {
  font-size: 0.9rem;
  font-weight: 700;
  color: #0f172a;
}

.req-active-badge {
  font-size: 0.65rem;
  font-weight: 700;
  background: #dcfce7;
  color: #15803d;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
}

.req-card-number {
  font-size: 1.1rem;
  font-weight: 700;
  color: #1e293b;
  letter-spacing: 0.05em;
  margin: 0.25rem 0;
}

.req-recipient, .req-sbp {
  font-size: 0.775rem;
  color: #64748b;
}

.req-copy-btn {
  margin-top: 0.65rem;
  width: 100%;
  background: #ffffff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
  padding: 0.45rem;
  font-size: 0.8rem;
  font-weight: 700;
  color: #0f172a;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
  transition: all 0.15s ease;

  &:hover {
    background: #f1f5f9;
    border-color: #94a3b8;
  }
}
</style>
