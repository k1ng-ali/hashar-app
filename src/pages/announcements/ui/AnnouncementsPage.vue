<template>
  <div class="announcements-page">
    <!-- Top Header -->
    <div class="announcements-top-card">
      <div class="top-row">
        <div class="badge-pill">
          <span class="live-dot"></span>
          <span>Официальный канал ЖК</span>
        </div>
        <button
          class="create-announcement-btn"
          @click="showAddDialog = true"
        >
          <PlusOutlined />
          <span>Создать</span>
        </button>
      </div>

      <h1 class="page-title">Доска объявлений и собрания</h1>
      <p class="page-sub">
        Официальные уведомления совета дома, аварийные контакты и графики
      </p>

      <!-- Category Filter Tabs -->
      <div class="category-tabs-scroll">
        <button
          v-for="cat in ['Все', 'Новости', 'Собрание', 'Аварийные работы', 'Субботник']"
          :key="cat"
          type="button"
          class="cat-filter-chip"
          :class="{ 'cat-filter-chip--active': activeCategoryFilter === cat }"
          @click="activeCategoryFilter = cat"
        >
          {{ cat }}
        </button>
      </div>
    </div>

    <!-- Emergency Contacts Mobile Bar (Accordion / Quick Cards) -->
    <div class="emergency-quick-box">
      <div class="emergency-header" @click="isEmergencyOpen = !isEmergencyOpen">
        <div class="emergency-title">
          <PhoneOutlined class="emergency-icon" />
          <span>Аварийные и важные телефоны ЖК</span>
        </div>
        <span class="emergency-toggle">{{ isEmergencyOpen ? 'Свернуть' : 'Развернуть' }}</span>
      </div>

      <div v-show="isEmergencyOpen" class="emergency-contacts-list">
        <div class="emergency-contact-card">
          <div class="contact-info">
            <span class="contact-title">Диспетчерская (круглосуточно)</span>
            <a href="tel:+78123456789" class="contact-phone font-mono">+7 (812) 345-67-89</a>
          </div>
          <a href="tel:+78123456789" class="contact-call-btn">Позвонить</a>
        </div>

        <div class="emergency-contact-card">
          <div class="contact-info">
            <span class="contact-title">Аварийная служба лифтов</span>
            <a href="tel:+78129981122" class="contact-phone font-mono">+7 (812) 998-11-22</a>
          </div>
          <a href="tel:+78129981122" class="contact-call-btn">Позвонить</a>
        </div>

        <div class="emergency-contact-card">
          <div class="contact-info">
            <span class="contact-title">Председатель ТСЖ (Алексей)</span>
            <a href="tel:+79211112233" class="contact-phone font-mono">+7 (921) 111-22-33</a>
          </div>
          <a href="tel:+79211112233" class="contact-call-btn">Позвонить</a>
        </div>
      </div>
    </div>

    <!-- Announcements Feed -->
    <div class="announcements-feed">
      <div
        v-for="item in filteredAnnouncements"
        :key="item.id"
        class="announcement-item-card"
        :class="{ 'announcement-item-card--pinned': item.isPinned }"
      >
        <div class="item-top-row">
          <div class="item-tags-row">
            <span v-if="item.isPinned" class="pinned-badge">
              <PushpinOutlined /> Закреплено
            </span>
            <span
              class="cat-badge"
              :class="{
                'cat-badge--meeting': item.category === 'Собрание',
                'cat-badge--emergency': item.category === 'Аварийные работы',
                'cat-badge--news': item.category === 'Новости',
              }"
            >
              {{ item.category }}
            </span>
          </div>

          <div class="item-meta-right">
            <span class="item-date">{{ formatDate(item.createdAt) }}</span>
            <button
              v-if="fundStore.permissions.canDeleteAnnouncements"
              class="delete-item-btn"
              title="Удалить объявление"
              @click="confirmDelete(item.id)"
            >
              <DeleteOutlined />
            </button>
          </div>
        </div>

        <h2 class="announcement-title">{{ item.title }}</h2>
        <p class="announcement-body-text">{{ item.content }}</p>

        <div class="item-footer">
          <div class="author-row">
            <UserOutlined />
            <span>{{ item.authorName }}</span>
          </div>

          <button
            class="like-btn"
            @click="fundStore.likeAnnouncement(item.id)"
          >
            <LikeOutlined />
            <span class="like-counter">{{ item.likesCount }}</span>
          </button>
        </div>
      </div>

      <div v-if="filteredAnnouncements.length === 0" class="empty-feed-card">
        <p>В этой категории пока нет объявлений</p>
      </div>
    </div>

    <!-- Create Announcement Custom Modal -->
    <div v-if="showAddDialog" class="modal-backdrop" @click="showAddDialog = false">
      <div class="modal-card" @click.stop>
        <div class="modal-header">
          <h2 class="modal-title">Новое объявление</h2>
          <button class="modal-close" @click="showAddDialog = false">✕</button>
        </div>

        <form @submit.prevent="handleCreateAnnouncement" class="modal-form">
          <div class="field-item">
            <label class="field-label">Заголовок</label>
            <input
              v-model="newTitle"
              type="text"
              required
              class="custom-input"
              placeholder="Например: Плановое собрание жильцов"
            />
          </div>

          <div class="field-item">
            <label class="field-label">Категория</label>
            <select v-model="newCategory" class="custom-select">
              <option value="Новости">Новости</option>
              <option value="Собрание">Собрание</option>
              <option value="Аварийные работы">Аварийные работы</option>
              <option value="Субботник">Субботник</option>
            </select>
          </div>

          <div class="field-item">
            <label class="field-label">Текст объявления</label>
            <textarea
              v-model="newContent"
              required
              rows="4"
              class="custom-textarea"
              placeholder="Подробная информация для жильцов дома..."
            ></textarea>
          </div>

          <div v-if="fundStore.permissions.canPinAnnouncements" class="checkbox-row">
            <label class="custom-checkbox-label">
              <input v-model="newIsPinned" type="checkbox" class="custom-checkbox" />
              <span>Закрепить объявление вверху ленты</span>
            </label>
          </div>

          <div class="modal-actions">
            <button
              type="button"
              class="cancel-btn"
              @click="showAddDialog = false"
            >
              Отмена
            </button>
            <button
              type="submit"
              class="publish-btn"
            >
              Опубликовать
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import { formatDate } from '@/shared/utils/finance';
import { Announcement } from '@/shared/types';
import { message } from 'ant-design-vue';
import {
  PlusOutlined,
  PushpinOutlined,
  UserOutlined,
  LikeOutlined,
  PhoneOutlined,
  DeleteOutlined,
} from '@ant-design/icons-vue';

const fundStore = useFundStore();

const showAddDialog = ref(false);
const isEmergencyOpen = ref(true);
const activeCategoryFilter = ref('Все');

const newTitle = ref('');
const newCategory = ref<Announcement['category']>('Новости');
const newContent = ref('');
const newIsPinned = ref(false);

const filteredAnnouncements = computed(() => {
  if (activeCategoryFilter.value === 'Все') {
    return fundStore.announcements;
  }
  return fundStore.announcements.filter((a) => a.category === activeCategoryFilter.value);
});

function confirmDelete(id: number) {
  fundStore.deleteAnnouncement(id);
  message.success('Объявление удалено');
}

function handleCreateAnnouncement() {
  if (!newTitle.value.trim() || !newContent.value.trim()) {
    message.error('Заполните все обязательные поля');
    return;
  }

  fundStore.addAnnouncement({
    title: newTitle.value.trim(),
    category: newCategory.value,
    content: newContent.value.trim(),
    isPinned: newIsPinned.value,
  });

  newTitle.value = '';
  newContent.value = '';
  newIsPinned.value = false;
  showAddDialog.value = false;
  message.success('Объявление опубликовано');
}
</script>

<style scoped lang="scss">
.announcements-page {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
  max-width: 680px;
  margin: 0 auto;
}

/* Top Header Card */
.announcements-top-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 24px;
  padding: 1.25rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.02);
}

.top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.65rem;
}

.badge-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  background: #f1f5f9;
  padding: 0.2rem 0.6rem;
  border-radius: 9999px;
  font-size: 0.725rem;
  font-weight: 700;
  color: #475569;
}

.live-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background-color: #3b82f6;
}

.create-announcement-btn {
  background: #0f172a;
  color: #ffffff;
  border: none;
  border-radius: 9999px;
  padding: 0.35rem 0.85rem;
  font-size: 0.775rem;
  font-weight: 700;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  transition: all 0.15s ease;

  &:hover {
    background: #1e293b;
  }
}

.page-title {
  font-size: 1.35rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.02em;
}

.page-sub {
  font-size: 0.8rem;
  color: #64748b;
  margin-top: 0.15rem;
}

/* Category Filter Chips */
.category-tabs-scroll {
  display: flex;
  gap: 0.4rem;
  overflow-x: auto;
  margin-top: 1rem;
  padding-bottom: 0.2rem;
}

.cat-filter-chip {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 9999px;
  padding: 0.35rem 0.75rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: #64748b;
  white-space: nowrap;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #f1f5f9;
  }

  &--active {
    background: #0f172a;
    border-color: #0f172a;
    color: #ffffff;
  }
}

/* Emergency Quick Box */
.emergency-quick-box {
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 18px;
  padding: 0.85rem 1rem;
}

.emergency-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  cursor: pointer;
}

.emergency-title {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  font-size: 0.825rem;
  font-weight: 800;
  color: #991b1b;
}

.emergency-icon {
  color: #ef4444;
}

.emergency-toggle {
  font-size: 0.725rem;
  font-weight: 700;
  color: #dc2626;
}

.emergency-contacts-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px dashed #fca5a5;
}

.emergency-contact-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #ffffff;
  border-radius: 12px;
  padding: 0.6rem 0.85rem;
  border: 1px solid #fee2e2;
}

.contact-title {
  display: block;
  font-size: 0.75rem;
  color: #475569;
  font-weight: 600;
}

.contact-phone {
  display: block;
  font-size: 0.875rem;
  font-weight: 800;
  color: #0f172a;
}

.contact-call-btn {
  background: #fee2e2;
  color: #991b1b;
  padding: 0.3rem 0.65rem;
  border-radius: 8px;
  font-size: 0.725rem;
  font-weight: 700;
  text-decoration: none;

  &:hover {
    background: #fecaca;
  }
}

/* Feed */
.announcements-feed {
  display: flex;
  flex-direction: column;
  gap: 0.85rem;
}

.announcement-item-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 20px;
  padding: 1.15rem;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.02);
  transition: all 0.15s ease;

  &--pinned {
    border-color: #fed7aa;
    background: #fffdfa;
  }
}

.item-top-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.item-tags-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
}

.pinned-badge {
  background: #fee2e2;
  color: #b91c1c;
  font-size: 0.675rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
  display: inline-flex;
  align-items: center;
  gap: 0.25rem;
}

.cat-badge {
  font-size: 0.675rem;
  font-weight: 700;
  padding: 0.15rem 0.5rem;
  border-radius: 9999px;
  background: #f1f5f9;
  color: #475569;

  &--meeting {
    background: #f3e8ff;
    color: #7e22ce;
  }

  &--emergency {
    background: #ffedd5;
    color: #c2410c;
  }

  &--news {
    background: #e0e7ff;
    color: #4338ca;
  }
}

.item-meta-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.item-date {
  font-size: 0.725rem;
  color: #94a3b8;
}

.delete-item-btn {
  background: transparent;
  border: none;
  color: #ef4444;
  cursor: pointer;
  padding: 0.2rem;
  font-size: 0.85rem;

  &:hover {
    color: #b91c1c;
  }
}

.announcement-title {
  font-size: 1.1rem;
  font-weight: 800;
  color: #0f172a;
  letter-spacing: -0.01em;
  line-height: 1.3;
  margin-bottom: 0.35rem;
}

.announcement-body-text {
  font-size: 0.85rem;
  color: #334155;
  line-height: 1.5;
  margin-bottom: 0.85rem;
}

.item-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 0.65rem;
  border-top: 1px solid #f1f5f9;
}

.author-row {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: #64748b;
}

.like-btn {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 9999px;
  padding: 0.25rem 0.65rem;
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  font-weight: 700;
  color: #475569;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: #eef2ff;
    color: #4f46e5;
    border-color: #c7d2fe;
  }
}

.like-counter {
  font-weight: 800;
}

.empty-feed-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 18px;
  padding: 2rem;
  text-align: center;
  font-size: 0.85rem;
  color: #64748b;
}

/* Custom Modal */
.modal-backdrop {
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

.modal-card {
  background: #ffffff;
  width: 100%;
  max-width: 500px;
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

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 1.25rem;
}

.modal-title {
  font-size: 1.2rem;
  font-weight: 800;
  color: #0f172a;
}

.modal-close {
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

.modal-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.field-item {
  display: flex;
  flex-direction: column;
  gap: 0.35rem;
}

.field-label {
  font-size: 0.8rem;
  font-weight: 700;
  color: #334155;
}

.custom-input, .custom-select, .custom-textarea {
  width: 100%;
  padding: 0.75rem 1rem;
  border-radius: 14px;
  border: 1.5px solid #e2e8f0;
  background: #f8fafc;
  font-size: 0.875rem;
  outline: none;

  &:focus {
    border-color: #6366f1;
    background: #ffffff;
  }
}

.checkbox-row {
  display: flex;
  align-items: center;
}

.custom-checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.825rem;
  font-weight: 600;
  color: #1e293b;
  cursor: pointer;
}

.custom-checkbox {
  width: 18px;
  height: 18px;
  accent-color: #4f46e5;
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.cancel-btn {
  flex: 1;
  background: #f1f5f9;
  border: none;
  border-radius: 12px;
  padding: 0.75rem;
  font-size: 0.85rem;
  font-weight: 700;
  color: #475569;
  cursor: pointer;

  &:hover {
    background: #e2e8f0;
  }
}

.publish-btn {
  flex: 2;
  background: #0f172a;
  border: none;
  border-radius: 12px;
  padding: 0.75rem;
  font-size: 0.85rem;
  font-weight: 800;
  color: #ffffff;
  cursor: pointer;

  &:hover {
    background: #1e293b;
  }
}
</style>
