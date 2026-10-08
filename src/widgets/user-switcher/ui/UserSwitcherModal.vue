<template>
  <div v-if="modelValue" class="user-modal-backdrop" @click="close">
    <div class="user-modal-card" @click.stop>
      <div class="user-modal-header">
        <div class="user-modal-title">Переключить аккаунт</div>
        <button class="user-modal-close" @click="close">✕</button>
      </div>
      <div class="user-modal-sub">
        Выберите жителя или администратора для проверки работы фонда
      </div>

      <div class="user-modal-list">
        <button
          v-for="u in fundStore.users"
          :key="u.id"
          class="user-item-btn"
          :class="{ 'user-item-btn--active': u.id === fundStore.currentUser.id }"
          @click="selectUser(u.id)"
        >
          <div class="user-avatar">
            <img v-if="u.avatarUrl" :src="u.avatarUrl" :alt="u.fullName" class="avatar-img" />
            <span v-else class="avatar-letter">{{ u.fullName[0] }}</span>
          </div>

          <div class="user-info">
            <div class="user-name-row">
              <span class="user-name">{{ u.fullName }}</span>
              <span v-if="u.id === fundStore.currentUser.id" class="user-current-badge">Текущий</span>
            </div>
            <div class="user-unit-row">
              <span class="user-unit">Квартира {{ u.addressUnit }}</span>
              <span class="user-dot">•</span>
              <span
                class="user-role-tag"
                :class="{
                  'role--superadmin': u.role === 'SUPERADMIN',
                  'role--admin': u.role === 'ADMIN',
                  'role--resident': u.role === 'RESIDENT',
                }"
              >
                {{ u.role === 'SUPERADMIN' ? 'Председатель' : u.role === 'ADMIN' ? 'Ревизор' : 'Житель' }}
              </span>
            </div>
          </div>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useFundStore } from '@/entities/fund/model/fundStore';

defineProps<{
  modelValue: boolean;
}>();

const emit = defineEmits<{
  (e: 'update:modelValue', val: boolean): void;
}>();

const fundStore = useFundStore();

function close() {
  emit('update:modelValue', false);
}

function selectUser(userId: string) {
  fundStore.switchUser(userId);
  close();
}
</script>

<style scoped lang="scss">
.user-modal-backdrop {
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

.user-modal-card {
  background: #ffffff;
  width: 100%;
  max-width: 460px;
  border-radius: 24px 24px 0 0;
  padding: 1.5rem 1.25rem 2rem 1.25rem;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.25);
  animation: slideUp 0.2s ease-out;

  @media (min-width: 640px) {
    border-radius: 24px;
    padding: 1.75rem;
    animation: fadeInScale 0.2s ease-out;
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

@keyframes fadeInScale {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.user-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.35rem;
}

.user-modal-title {
  font-size: 1.25rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.user-modal-close {
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
  font-size: 0.9rem;
  font-weight: 700;
  transition: all 0.15s ease;

  &:hover {
    background: #e2e8f0;
    color: #0f172a;
  }
}

.user-modal-sub {
  font-size: 0.8rem;
  color: #64748b;
  margin-bottom: 1.25rem;
}

.user-modal-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 55vh;
  overflow-y: auto;
  padding-right: 0.25rem;
}

.user-item-btn {
  background: #f8fafc;
  border: 1.5px solid #e2e8f0;
  border-radius: 16px;
  padding: 0.75rem 1rem;
  display: flex;
  align-items: center;
  gap: 0.85rem;
  cursor: pointer;
  text-align: left;
  transition: all 0.15s ease;
  width: 100%;

  &:hover {
    background: #f1f5f9;
    border-color: #cbd5e1;
  }

  &--active {
    background: #eef2ff;
    border-color: #6366f1;
  }
}

.user-avatar {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  background: #4f46e5;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.1rem;
  font-weight: 700;
  flex-shrink: 0;
  overflow: hidden;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.user-info {
  flex: 1;
  min-width: 0;
}

.user-name-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
}

.user-name {
  font-size: 0.925rem;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-current-badge {
  font-size: 0.65rem;
  font-weight: 700;
  color: #4f46e5;
  background: #e0e7ff;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
  white-space: nowrap;
}

.user-unit-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  margin-top: 0.2rem;
  font-size: 0.75rem;
  color: #64748b;
}

.user-dot {
  color: #cbd5e1;
}

.user-role-tag {
  font-weight: 600;
  padding: 0.1rem 0.45rem;
  border-radius: 6px;

  &.role--superadmin {
    background: #f3e8ff;
    color: #7e22ce;
  }

  &.role--admin {
    background: #e0f2fe;
    color: #0284c7;
  }

  &.role--resident {
    background: #f1f5f9;
    color: #475569;
  }
}
</style>
