<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { LuPlus } from '@kalimahapps/vue-icons/lu'
import ExpenseForm from '@/features/admin/components/ExpenseForm.vue'
import { useAdminFlow } from '@/features/admin/composables/useAdminFlow.ts'
import { useAdminStore } from '@/features/admin/store.ts'
import { useDashboardStore } from '@/features/dashboard/store.ts'
import ExpenseDetail from '@/features/expenses/components/ExpenseDetail.vue'
import ExpensePost from '@/features/expenses/components/ExpensePost.vue'
import { useExpensesStore } from '@/features/expenses/store.ts'
import { EXPENSE_CATEGORIES, type Expense, type ExpensesFilter } from '@/features/expenses/types.ts'
import { useFundsStore } from '@/features/funds/store.ts'
import { useTargetFundsStore } from '@/features/targetFunds/store.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import CardSkeleton from '@/shared/components/CardSkeleton.vue'
import EmptyState from '@/shared/components/EmptyState.vue'
import PillTabs from '@/shared/components/PillTabs.vue'
import type { Currency } from '@/shared/lib/currency.ts'
import { formatMoney } from '@/shared/lib/format.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'
import { useReceiptStore } from '@/shared/stores/useReceiptStore.ts'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const store = useExpensesStore()
const dashboardStore = useDashboardStore()
const fundsStore = useFundsStore()
const headerStore = useHeaderStore()
const receiptStore = useReceiptStore()
const adminStore = useAdminStore()
const targetFundsStore = useTargetFundsStore()
const flow = useAdminFlow()

const canManage = computed(() => fundsStore.permissions.canManageFinance)
// Остатки счетов — для предупреждения о минусе в форме расхода
const balances = computed(() =>
  Object.fromEntries(fundsStore.current?.accounts.map((a) => [a.currency, a.balance]) ?? []),
)

const filterOptions = computed(() => [
  { value: 'all' as ExpensesFilter, label: t('common.all') },
  ...EXPENSE_CATEGORIES.map((category) => ({
    value: category as ExpensesFilter,
    label: t(`expenseCategory.${category}`),
  })),
])

const currencies = computed<Currency[]>(
  () => fundsStore.current?.accounts.filter((a) => a.is_active).map((a) => a.currency) ?? [],
)
// Сколько потрачено в этом месяце по каждому счёту — из сводки главного экрана
const monthSpent = computed(() => dashboardStore.summary?.accounts ?? [])

onMounted(async () => {
  await Promise.all([store.fetchItems(), dashboardStore.fetchSummary()])
  // «+» → «Добавить расход» ведёт сюда с ?create=1
  if (route.query.create && canManage.value) {
    void router.replace({ query: {} })
    void openForm()
  }
})

onUnmounted(() => {
  store.close()
})

// Ссылка вида /expenses?id=12 (например, из ленты операций) открывает расход
watch(
  () => route.query.id,
  async (id) => {
    if (!id) return store.close()
    try {
      await store.open(Number(id))
    } catch {
      headerStore.showNotification(t('errors.loadFailed'), 'error')
    }
  },
  { immediate: true },
)

// ── Handlers ─────────────────────────────────────────────────────────────
function openExpense(expense: Expense) {
  void router.replace({ query: { ...route.query, id: expense.id } })
}

function closeExpense() {
  const { id: _id, ...query } = route.query
  void router.replace({ query })
}

function openReceipt(expense: Expense, index: number) {
  const total = expense.receipt_images.length
  receiptStore.open(`${expense.title} · ${index + 1}/${total}`, expense.receipt_images[index])
}

function openFund(id: number) {
  void router.push(`/target-funds/${id}`)
}

// ── Совет: добавление и удаление ─────────────────────────────────────────
async function openForm() {
  // Списать можно за счёт сбора — список сборов нужен форме
  if (!targetFundsStore.items.length) await targetFundsStore.fetchList()
  flow.openSheet('expense')
}

async function handleAdd(payload: Parameters<typeof flow.handleAddExpense>[0]) {
  if (await flow.handleAddExpense(payload)) await Promise.all([store.fetchItems(), dashboardStore.fetchSummary()])
}

async function handleDelete(id: number) {
  await flow.handleDeleteExpense(id)
  await store.fetchItems()
}
</script>

<template>
  <div class="expenses-page">
    <div class="toolbar">
      <p class="intro">{{ $t('expenses.subtitle') }}</p>
      <button v-if="canManage" class="add-btn" @click="openForm"><LuPlus /> {{ $t('admin.expenses.add') }}</button>
    </div>

    <!-- Потрачено в этом месяце по каждому счёту -->
    <div v-if="monthSpent.length" class="month">
      <span class="month-label">{{ $t('expenses.thisMonth') }}</span>
      <div class="month-values">
        <span v-for="account in monthSpent" :key="account.currency" class="month-value">
          {{ formatMoney(account.month_spent, account.currency) }}
        </span>
      </div>
    </div>

    <PillTabs :model-value="store.filter" :options="filterOptions" @update:model-value="store.setFilter" />

    <div v-if="currencies.length > 1" class="chips">
      <button class="chip" :class="{ 'chip--active': !store.currency }" @click="store.setCurrency(null)">
        {{ $t('expenses.allAccounts') }}
      </button>
      <button
        v-for="currency in currencies"
        :key="currency"
        class="chip"
        :class="{ 'chip--active': store.currency === currency }"
        @click="store.setCurrency(currency)"
      >
        {{ currency.toUpperCase() }}
      </button>
    </div>

    <!-- Загрузка -->
    <div v-if="store.isLoading && !store.items.length" class="list">
      <CardSkeleton v-for="i in 2" :key="i" :lines="4" />
    </div>

    <EmptyState v-else-if="store.errorMessage" icon="📡" :title="$t(store.errorMessage)">
      <button class="ghost-btn" @click="store.fetchItems()">{{ $t('common.retry') }}</button>
    </EmptyState>

    <!-- Лента -->
    <div v-else-if="store.items.length" class="list">
      <ExpensePost
        v-for="expense in store.items"
        :key="expense.id"
        :expense="expense"
        :can-delete="fundsStore.permissions.canDeleteRecords"
        @open="openExpense"
        @open-receipt="openReceipt"
        @delete="handleDelete"
      />
      <button v-if="store.hasMore" class="ghost-btn more-btn" :disabled="store.isLoading" @click="store.fetchItems(true)">
        {{ $t('admin.history.more') }}
      </button>
    </div>

    <EmptyState v-else icon="🧾" :title="$t('expenses.emptyTitle')" :hint="$t('expenses.emptyHint')" />

    <BottomSheet :open="flow.sheet.value === 'expense'" :title="$t('admin.expenses.sheetTitle')" @close="flow.closeSheet">
      <ExpenseForm
        v-if="fundsStore.current"
        :funds="targetFundsStore.activeItems"
        :fund-name="fundsStore.current.name"
        :currencies="currencies"
        :base-currency="fundsStore.current.base_currency"
        :balances="balances"
        :is-submitting="adminStore.isSubmitting"
        @submit="handleAdd"
      />
    </BottomSheet>

    <BottomSheet :open="!!store.selected" :title="$t('expenses.detailTitle')" @close="closeExpense">
      <ExpenseDetail v-if="store.selected" :expense="store.selected" @open-receipt="openReceipt" @open-fund="openFund" />
    </BottomSheet>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.expenses-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.add-btn {
  @include cta-button;
  flex-shrink: 0;
  padding: 9px 14px;
  font-size: 13px;
}

.intro {
  margin: 0;
  font-size: 13px;
  color: $text-secondary;
}

.month {
  @include glass-card(18px);
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 12px 16px;
}

.month-label {
  font-size: 12px;
  font-weight: 700;
  color: $text-muted;
}

.month-values {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.month-value {
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(239, 68, 68, 0.1);
  color: #B91C1C;
  font-size: 13px;
  font-weight: 700;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.chip {
  @include ghost-button;
  padding: 6px 12px;
  font-size: 12px;

  &--active {
    border-color: transparent;
    background: $gradient;
    color: #fff;
  }
}

.list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ghost-btn {
  @include ghost-button;
}

.more-btn {
  align-self: center;
}

@media (min-width: 768px) {
  .expenses-page {
    padding: 16px 24px 24px;
  }
}
</style>
