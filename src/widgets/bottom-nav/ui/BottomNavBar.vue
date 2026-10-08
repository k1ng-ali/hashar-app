<template>
  <div class="bottom-nav-wrapper">
    <nav class="bottom-nav-pill" aria-label="Основная навигация">
      <!-- 1. Dashboard Tab -->
      <button
        class="nav-pill-item"
        :class="{ 'nav-pill-item--active': fundStore.activeTab === 'dashboard' }"
        @click="fundStore.activeTab = 'dashboard'"
        title="Главный дашборд"
      >
        <div class="pill-icon-box">
          <HomeOutlined />
        </div>
        <span class="pill-label">Главная</span>
      </button>

      <!-- 2. Target Funds Quick Action / Tab -->
      <button
        class="nav-pill-item"
        :class="{ 'nav-pill-item--active': isTargetFundsActive }"
        @click="goToTargetFunds"
        title="Целевые сборы"
      >
        <div class="pill-icon-box">
          <FireOutlined />
        </div>
        <span class="pill-label">Сборы</span>
      </button>

      <!-- 3. Center Quick Contribution Button -->
      <button
        class="nav-pill-center-btn"
        @click="handleContributeClick"
        title="Внести взнос"
      >
        <PlusOutlined class="center-btn-icon" />
      </button>

      <!-- 4. History / Resident Balance Tab -->
      <button
        class="nav-pill-item"
        :class="{ 'nav-pill-item--active': fundStore.activeTab === 'history' }"
        @click="fundStore.activeTab = 'history'"
        title="Мои взносы и долги"
      >
        <div class="pill-icon-box">
          <CreditCardOutlined />
          <span
            v-if="fundStore.currentUserStatus.statusType === 'DEBT'"
            class="pill-alert-dot"
            title="Есть задолженность"
          />
        </div>
        <span class="pill-label">Взносы</span>
      </button>

      <!-- 5. Announcements Feed Tab -->
      <button
        class="nav-pill-item"
        :class="{ 'nav-pill-item--active': fundStore.activeTab === 'announcements' }"
        @click="fundStore.activeTab = 'announcements'"
        title="Доска объявлений"
      >
        <div class="pill-icon-box">
          <NotificationOutlined />
        </div>
        <span class="pill-label">Новости</span>
      </button>

      <!-- 6. Admin Panel / Management Tab -->
      <button
        class="nav-pill-item"
        :class="{ 'nav-pill-item--active': fundStore.activeTab === 'admin' }"
        @click="fundStore.activeTab = 'admin'"
        title="Управление и аудит"
      >
        <div class="pill-icon-box">
          <SafetyCertificateOutlined v-if="fundStore.permissions.canAccessAdminPanel" />
          <SettingOutlined v-else />
          <span
            v-if="fundStore.pendingContributions.length > 0 && fundStore.permissions.canAccessAdminPanel"
            class="pill-badge-num"
          >
            {{ fundStore.pendingContributions.length }}
          </span>
        </div>
        <span class="pill-label">{{ fundStore.permissions.canAccessAdminPanel ? 'Админ' : 'Кабинет' }}</span>
      </button>
    </nav>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import {
  HomeOutlined,
  FireOutlined,
  CreditCardOutlined,
  NotificationOutlined,
  SafetyCertificateOutlined,
  SettingOutlined,
  PlusOutlined,
} from '@ant-design/icons-vue';

const emit = defineEmits<{
  (e: 'open-contribute'): void;
}>();

const fundStore = useFundStore();

const isTargetFundsActive = computed(() => {
  return false;
});

function goToTargetFunds() {
  fundStore.activeTab = 'dashboard';
  // smooth scroll to target funds section if on dashboard
  setTimeout(() => {
    const el = document.getElementById('target-funds-section');
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }, 100);
}

function handleContributeClick() {
  emit('open-contribute');
}
</script>

<style scoped lang="scss">
@use '@/app/styles/variables' as *;

.bottom-nav-wrapper {
  position: fixed;
  bottom: 1.25rem;
  left: 0;
  right: 0;
  display: flex;
  justify-content: center;
  z-index: 999;
  pointer-events: none;
  padding: 0 1rem;
}

.bottom-nav-pill {
  pointer-events: auto;
  background: #11141a;
  border: 1px solid rgba(255, 255, 255, 0.12);
  box-shadow: 0 16px 36px rgba(0, 0, 0, 0.35), 0 4px 12px rgba(0, 0, 0, 0.2);
  border-radius: 9999px;
  padding: 0.35rem 0.65rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  max-width: 480px;
  width: 100%;
  justify-content: space-between;

  @media (max-width: 380px) {
    padding: 0.3rem 0.45rem;
    gap: 0.2rem;
  }
}

.nav-pill-item {
  background: transparent;
  border: none;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0.35rem 0.6rem;
  border-radius: 9999px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s ease;
  min-width: 52px;
  min-height: 48px;

  @media (max-width: 380px) {
    min-width: 44px;
    padding: 0.25rem 0.4rem;
  }

  &:hover {
    color: #ffffff;
  }

  &--active {
    color: #11141a;

    .pill-icon-box {
      background: #ffffff;
      color: #11141a;
      box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
    }

    .pill-label {
      color: #ffffff;
      font-weight: 700;
    }
  }
}

.pill-icon-box {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.15rem;
  position: relative;
  transition: all 0.2s ease;
}

.pill-label {
  font-size: 0.65rem;
  font-weight: 600;
  margin-top: 0.15rem;
  color: #94a3b8;
  line-height: 1;
}

/* Center Quick Action button (+) */
.nav-pill-center-btn {
  background: linear-gradient(135deg, #4f46e5, #4338ca);
  border: 2px solid #ffffff;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  cursor: pointer;
  margin: 0 0.2rem;
  box-shadow: 0 6px 16px rgba(79, 70, 229, 0.4);
  transition: transform 0.15s ease, background 0.15s ease;
  flex-shrink: 0;

  &:hover {
    transform: scale(1.08);
    background: linear-gradient(135deg, #4338ca, #3730a3);
  }

  &:active {
    transform: scale(0.96);
  }
}

.center-btn-icon {
  font-size: 1.2rem;
  font-weight: 800;
}

.pill-alert-dot {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 8px;
  height: 8px;
  background-color: #ef4444;
  border-radius: 50%;
  border: 1.5px solid #11141a;
}

.pill-badge-num {
  position: absolute;
  top: 0;
  right: -2px;
  background-color: #f43f5e;
  color: #ffffff;
  font-size: 0.65rem;
  font-weight: 800;
  padding: 0.05rem 0.35rem;
  border-radius: 9999px;
  border: 1.5px solid #11141a;
  line-height: 1.1;
}
</style>
