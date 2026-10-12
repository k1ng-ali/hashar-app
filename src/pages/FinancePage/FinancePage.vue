<script setup lang="ts">
import { computed, onMounted, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useContributionsStore } from '@/features/contributions/store.ts'
import SegmentedControl from '@/shared/components/SegmentedControl.vue'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'

type FinanceTab = 'my' | 'expenses' | 'funds' | 'reports'

const TABS: FinanceTab[] = ['my', 'expenses', 'funds', 'reports']

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const headerStore = useHeaderStore()
const contributionsStore = useContributionsStore()

// Подраздел — из адреса: /finance/<tab>
const tab = computed<FinanceTab>({
  get: () => {
    const current = route.path.split('/')[2] as FinanceTab
    return TABS.includes(current) ? current : 'my'
  },
  set: (value) => {
    void router.replace(`/finance/${value}`)
  },
})

const options = computed(() =>
  TABS.map((value) => ({
    value,
    label: t(`finance.tabs.${value}`),
    // Долг — красная точка на «Мои взносы»
    dot: value === 'my' && contributionsStore.hasDebt,
  })),
)

onMounted(() => {
  headerStore.setTitle(t('finance.title'))
})

onUnmounted(() => {
  headerStore.reset()
})
</script>

<template>
  <div class="finance-page">
    <div class="tabs">
      <SegmentedControl v-model="tab" :options="options" />
    </div>

    <router-view v-slot="{ Component }">
      <Transition name="fade" mode="out-in">
        <component :is="Component" :key="route.path" />
      </Transition>
    </router-view>
  </div>
</template>

<style scoped lang="scss">
.finance-page {
  max-width: var(--content-max);
  margin: 0 auto;
}

.tabs {
  padding: 8px 16px 0;
}

@media (min-width: 768px) {
  .tabs {
    padding: 16px 24px 0;
  }
}
</style>
