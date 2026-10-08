<template>
  <div class="access-denied-container">
    <div class="access-denied-card surface-card">
      <div class="lock-icon-circle">
        <LockOutlined />
      </div>

      <h2 class="access-title">Раздел доступен только администрации дома</h2>
      
      <p class="access-desc">
        Управление сборами, верификация банковских чеков, учет расходов и изменение тарифов
        требуют прав Председателя ТСЖ или члена Ревизионной комиссии.
      </p>

      <div class="current-user-badge">
        <span class="text-secondary text-xs">Ваш текущий аккаунт:</span>
        <div class="user-pill">
          <strong>{{ fundStore.currentUser.fullName }}</strong> ({{ fundStore.currentUser.addressUnit }})
          <span class="resident-tag">Житель</span>
        </div>
      </div>

      <div class="role-switch-demo-box">
        <p class="demo-box-title">
          <SwapOutlined />
          Переключить роль для тестирования функционала:
        </p>
        <div class="demo-role-buttons">
          <button class="btn-role-action btn-role-primary" @click="switchToChairman">
            <CrownOutlined />
            <span>Войти как Председатель (Полный доступ)</span>
          </button>
          <button class="btn-role-action btn-role-secondary" @click="switchToRevisor">
            <AuditOutlined />
            <span>Войти как Ревизор (Совет дома)</span>
          </button>
        </div>
      </div>

      <div class="back-link">
        <button class="btn-back-link" @click="fundStore.activeTab = 'dashboard'">
          Вернуться на главную страницу
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useFundStore } from '@/entities/fund/model/fundStore';
import {
  LockOutlined,
  CrownOutlined,
  AuditOutlined,
  SwapOutlined,
} from '@ant-design/icons-vue';

const fundStore = useFundStore();

function switchToChairman() {
  fundStore.switchUser('user-1'); // Алексей Николаев (SUPERADMIN)
}

function switchToRevisor() {
  fundStore.switchUser('user-2'); // Марат Каримов (ADMIN)
}
</script>

<style scoped lang="scss">
@use '@/app/styles/variables' as *;

.access-denied-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 55vh;
  padding: 1rem 0;
}

.access-denied-card {
  max-width: 580px;
  width: 100%;
  text-align: center;
  padding: 2.5rem 1.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;

  @media (min-width: $breakpoint-sm) {
    padding: 3rem 2.5rem;
  }
}

.lock-icon-circle {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background-color: #fee2e2;
  color: #ef4444;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.75rem;
  margin-bottom: 1.25rem;
}

.access-title {
  font-size: 1.25rem;
  font-weight: 700;
  color: $text-main;
  margin-bottom: 0.75rem;

  @media (min-width: $breakpoint-sm) {
    font-size: 1.45rem;
  }
}

.access-desc {
  font-size: 0.9rem;
  color: $text-secondary;
  line-height: 1.6;
  max-width: 440px;
  margin-bottom: 1.5rem;
}

.current-user-badge {
  background-color: $bg-surface-secondary;
  border-radius: $radius-md;
  padding: 0.75rem 1.25rem;
  border: 1px solid $border-color;
  margin-bottom: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.user-pill {
  font-size: 0.9rem;
  color: $text-main;
}

.role-switch-demo-box {
  width: 100%;
  background-color: #f8fafc;
  border: 1px dashed #cbd5e1;
  border-radius: $radius-md;
  padding: 1.25rem;
  margin-bottom: 1.5rem;
}

.demo-box-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: $text-secondary;
  margin-bottom: 0.85rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.35rem;
}

.demo-role-buttons {
  display: flex;
  flex-direction: column;
  gap: 0.65rem;
}

.btn-role-action {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  font-weight: 700;
  padding: 0.8rem 1rem;
  border-radius: 12px;
  border: none;
  cursor: pointer;
  transition: all 0.15s ease;

  &.btn-role-primary {
    background: #4f46e5;
    color: #ffffff;
    &:hover {
      background: #4338ca;
    }
  }

  &.btn-role-secondary {
    background: #ffffff;
    color: #0f172a;
    border: 1px solid #cbd5e1;
    &:hover {
      background: #f1f5f9;
    }
  }
}

.resident-tag {
  font-size: 0.7rem;
  font-weight: 700;
  background: #f1f5f9;
  color: #475569;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
  margin-left: 0.5rem;
}

.back-link {
  margin-top: 0.5rem;
}

.btn-back-link {
  background: none;
  border: none;
  color: #4f46e5;
  font-size: 0.85rem;
  font-weight: 700;
  cursor: pointer;
  text-decoration: underline;
}
</style>
