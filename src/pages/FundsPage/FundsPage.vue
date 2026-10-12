<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { LuSearch } from '@kalimahapps/vue-icons/lu'
import CreateFundForm from '@/features/funds/components/CreateFundForm.vue'
import FundSearchResult from '@/features/funds/components/FundSearchResult.vue'
import JoinForm from '@/features/funds/components/JoinForm.vue'
import MyFundCard from '@/features/funds/components/MyFundCard.vue'
import { useFundsHubFlow } from '@/features/funds/composables/useFundsHubFlow.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import AppLogo from '@/shared/components/AppLogo.vue'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import PillTabs from '@/shared/components/PillTabs.vue'

const store = useFundsStore()
const flow = useFundsHubFlow()

onMounted(() => {
  void flow.initView()
})

onUnmounted(() => {
  flow.dispose()
})
</script>

<template>
  <div class="funds-page">
    <div class="hero">
      <AppLogo :size="52" />
      <p>{{ $t('funds.subtitle') }}</p>
    </div>

    <PillTabs v-model="flow.view.value" :options="flow.tabs.value" />

    <Transition name="slide" mode="out-in">
      <!-- 1. Мои фонды и заявки -->
      <section v-if="flow.view.value === 'list'" key="list" class="section">
        <template v-if="store.isLoading && !store.isLoaded">
          <CardSkeleton v-for="i in 2" :key="i" :lines="2" />
        </template>

        <template v-else-if="store.myFunds.length">
          <div v-if="store.activeFunds.length" class="list">
            <h2 class="section-title">{{ $t('funds.myFunds') }}</h2>
            <MyFundCard
              v-for="fund in store.activeFunds"
              :key="fund.id"
              :fund="fund"
              :is-current="fund.id === store.current?.id"
              @open="flow.openFund"
            />
          </div>

          <div v-if="store.requests.length" class="list">
            <h2 class="section-title">{{ $t('funds.myRequests') }}</h2>
            <MyFundCard
              v-for="fund in store.requests"
              :key="fund.id"
              :fund="fund"
              @cancel="flow.cancelRequest"
              @rejoin="flow.rejoin"
              @leave="flow.leaveBlocked"
            />
          </div>
        </template>

        <EmptyState v-else icon="🏘️" :title="$t('funds.emptyTitle')" :hint="$t('funds.emptyHint')" />
      </section>

      <!-- 2. Найти фонд -->
      <section v-else-if="flow.view.value === 'find'" key="find" class="section">
        <div class="search-box">
          <LuSearch class="search-icon" />
          <input
            :value="flow.query.value"
            :placeholder="$t('funds.search.placeholder')"
            @input="flow.onQueryInput(($event.target as HTMLInputElement).value)"
          />
        </div>
        <p class="hint">{{ $t('funds.search.hint') }}</p>

        <div v-if="store.searchResults.length" class="list">
          <FundSearchResult
            v-for="fund in store.searchResults"
            :key="fund.id"
            :fund="fund"
            @join="flow.joinTarget.value = $event"
          />
        </div>
        <EmptyState
          v-else-if="flow.query.value.trim().length >= 2"
          icon="🔍"
          :title="$t('funds.search.empty')"
          :hint="$t('funds.search.emptyHint')"
        />
      </section>

      <!-- 3. Создать фонд -->
      <section v-else key="create" class="section card">
        <h2 class="section-title">{{ $t('funds.create.title') }}</h2>
        <CreateFundForm :is-submitting="store.isSubmitting" @submit="flow.createFund" />
      </section>
    </Transition>

    <BottomSheet
      :open="!!flow.joinTarget.value"
      :title="$t('funds.join.title')"
      @close="flow.joinTarget.value = null"
    >
      <JoinForm
        v-if="flow.joinTarget.value"
        :fund="flow.joinTarget.value"
        :is-submitting="store.isSubmitting"
        @submit="flow.submitJoin"
      />
    </BottomSheet>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.funds-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  max-width: 640px;
  margin: 0 auto;
  padding: 16px;
}

.hero {
  display: flex;
  align-items: center;
  gap: 14px;

  p {
    margin: 0;
    font-size: 14px;
    color: $text-secondary;
  }
}

.section {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.card {
  @include glass-card(24px);
  padding: 18px;
}

.section-title {
  @include section-title;
  font-size: 16px;
}

.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* ── Поиск ────────────────────────────────────────────────────────────────── */
.search-box {
  position: relative;

  input {
    @include field-input;
    padding-left: 42px;
    border-radius: 30px;
  }
}

.search-icon {
  position: absolute;
  top: 50%;
  left: 16px;
  transform: translateY(-50%);
  color: $text-muted;
  font-size: 18px;
}

.hint {
  margin: -6px 4px 0;
  font-size: 12px;
  color: $text-muted;
}

@media (min-width: 768px) {
  .funds-page {
    padding: 24px;
  }
}
</style>
