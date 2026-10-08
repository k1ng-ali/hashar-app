<template>
  <div class="app-layout">
    <!-- Mobile Top Bar for sub-pages -->
    <AppTopBar v-if="fundStore.activeTab !== 'dashboard'" />

    <!-- Main Application Pages Container -->
    <main class="main-content">
      <transition name="fade-page" mode="out-in">
        <DashboardPage v-if="fundStore.activeTab === 'dashboard'" />
        <ContributePage v-else-if="fundStore.activeTab === 'contribute'" />
        <HistoryPage v-else-if="fundStore.activeTab === 'history'" />
        <AnnouncementsPage v-else-if="fundStore.activeTab === 'announcements'" />
        <AdminPage v-else-if="fundStore.activeTab === 'admin'" />
        <ReportsPage v-else-if="fundStore.activeTab === 'reports'" />
      </transition>
    </main>

    <!-- Bottom Navigation Floating Pill (Mobile-First) -->
    <BottomNavBar @open-contribute="isGlobalContributeOpen = true" />

    <!-- Global Contribution Modal -->
    <MakeContributionModal v-model:open="isGlobalContributeOpen" />

    <!-- Full-screen Receipt Modal -->
    <ReceiptModal />

    <!-- Minimalist Footer -->
    <footer class="app-footer">
      <div class="footer-inner">
        <div class="footer-brand">
          <strong>Фонд Района • ЖК «Северная Звезда»</strong>
          <p class="text-secondary text-xs">
            Прозрачная система сбора и целевого расходования средств собственников дома.
          </p>
        </div>
        <div class="footer-meta">
          <span class="text-muted text-xs">Vue 3 • Feature-Sliced Design • Чистый мобильный интерфейс</span>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useFundStore } from '@/entities/fund/model/fundStore';
import AppTopBar from '@/widgets/top-bar/ui/AppTopBar.vue';
import BottomNavBar from '@/widgets/bottom-nav/ui/BottomNavBar.vue';
import MakeContributionModal from '@/features/make-contribution/ui/MakeContributionModal.vue';
import ReceiptModal from '@/widgets/receipt-modal/ui/ReceiptModal.vue';
import DashboardPage from '@/pages/dashboard/ui/DashboardPage.vue';
import ContributePage from '@/pages/contribute/ui/ContributePage.vue';
import HistoryPage from '@/pages/history/ui/HistoryPage.vue';
import AnnouncementsPage from '@/pages/announcements/ui/AnnouncementsPage.vue';
import AdminPage from '@/pages/admin/ui/AdminPage.vue';
import ReportsPage from '@/pages/reports/ui/ReportsPage.vue';

const fundStore = useFundStore();
const isGlobalContributeOpen = ref(false);
</script>

<style scoped lang="scss">
@use '@/app/styles/variables' as *;

.fade-page-enter-active,
.fade-page-leave-active {
  transition: opacity 0.15s ease, transform 0.15s ease;
}

.fade-page-enter-from {
  opacity: 0;
  transform: translateY(4px);
}

.fade-page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

.app-footer {
  border-top: 1px solid $border-color;
  background: $bg-surface;
  padding: 1.5rem 1rem 6.5rem 1rem;
  margin-top: auto;
}

.footer-inner {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
}

.footer-brand {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}
</style>
