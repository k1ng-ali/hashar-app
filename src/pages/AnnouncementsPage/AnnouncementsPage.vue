<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { LuPlus } from '@kalimahapps/vue-icons/lu'
import AnnouncementCard from '@/features/announcements/components/AnnouncementCard.vue'
import AnnouncementForm from '@/features/announcements/components/AnnouncementForm.vue'
import EmergencyContacts from '@/features/announcements/components/EmergencyContacts.vue'
import { useAnnouncementsStore, type AnnouncementsFilter } from '@/features/announcements/store.ts'
import { ANNOUNCEMENT_FILTERS, type Announcement, type AnnouncementCreate } from '@/features/announcements/types.ts'
import { useAuthStore } from '@/features/auth/store.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import PillTabs from '@/shared/components/PillTabs.vue'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'

const { t } = useI18n()
const store = useAnnouncementsStore()
const authStore = useAuthStore()
const fundsStore = useFundsStore()
const headerStore = useHeaderStore()

const isFormOpen = ref(false)
const formRef = ref<InstanceType<typeof AnnouncementForm> | null>(null)

const filterOptions = computed(() => [
  { value: 'all' as AnnouncementsFilter, label: t('common.all') },
  ...ANNOUNCEMENT_FILTERS.map((category) => ({
    value: category as AnnouncementsFilter,
    label: t(`announcementCategory.${category}`),
  })),
])

onMounted(async () => {
  headerStore.setTitle(t('announcements.title'))
  await store.fetchItems('all')
})

onUnmounted(() => {
  headerStore.reset()
})

// ── Handlers ─────────────────────────────────────────────────────────────
function canDelete(announcement: Announcement) {
  // Объявления о движении по счетам не удаляются — это след для прозрачности
  if (announcement.transfer) return false
  return fundsStore.permissions.isChairman || announcement.author_id === authStore.user?.id
}

async function handleCreate(payload: AnnouncementCreate) {
  try {
    await store.create(payload)
    formRef.value?.reset()
    isFormOpen.value = false
    headerStore.showNotification(t('announcements.published'))
  } catch {
    headerStore.showNotification(t('errors.generic'), 'error')
  }
}

async function handleComment(id: number, text: string) {
  try {
    await store.comment(id, text)
  } catch {
    headerStore.showNotification(t('errors.generic'), 'error')
  }
}

async function handleDelete(id: number) {
  if (!window.confirm(t('common.confirmDelete'))) return
  try {
    await store.remove(id)
    headerStore.showNotification(t('announcements.deleted'))
  } catch {
    headerStore.showNotification(t('errors.generic'), 'error')
  }
}
</script>

<template>
  <div class="announcements-page">
    <div class="intro">
      <p>{{ $t('announcements.subtitle') }}</p>
      <button class="create-btn" @click="isFormOpen = true"><LuPlus /> {{ $t('announcements.create') }}</button>
    </div>

    <EmergencyContacts />

    <PillTabs :model-value="store.filter" :options="filterOptions" @update:model-value="store.fetchItems" />

    <!-- Загрузка -->
    <div v-if="store.isLoading && !store.items.length" class="list">
      <CardSkeleton v-for="i in 2" :key="i" :lines="4" />
    </div>

    <!-- Лента -->
    <div v-else-if="store.items.length" class="list">
      <AnnouncementCard
        v-for="announcement in store.items"
        :key="announcement.id"
        :announcement="announcement"
        :can-delete="canDelete(announcement)"
        :is-submitting="store.isSubmitting"
        @like="store.like"
        @comment="handleComment"
        @delete="handleDelete"
      />
    </div>

    <!-- Пусто -->
    <EmptyState v-else icon="📢" :title="$t('announcements.emptyTitle')" :hint="$t('announcements.emptyHint')" />

    <BottomSheet :open="isFormOpen" :title="$t('announcements.form.title')" @close="isFormOpen = false">
      <AnnouncementForm
        ref="formRef"
        :can-pin="fundsStore.permissions.canPinAnnouncements"
        :is-submitting="store.isSubmitting"
        @submit="handleCreate"
      />
    </BottomSheet>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.announcements-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  max-width: var(--content-max);
  margin: 0 auto;
  padding: 16px;
}

.intro {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;

  p {
    margin: 0;
    font-size: 13px;
    color: $text-secondary;
  }
}

.create-btn {
  @include cta-button;
  flex-shrink: 0;
  padding: 10px 16px;
  font-size: 13px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

@media (min-width: 768px) {
  .announcements-page {
    padding: 24px;
  }
}
</style>
