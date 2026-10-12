<script setup lang="ts">
import { computed, type Component } from 'vue'
import { useRouter } from 'vue-router'
import {
  LuArrowLeftRight,
  LuChevronRight,
  LuMegaphone,
  LuReceiptText,
  LuTarget,
  LuWallet,
} from '@kalimahapps/vue-icons/lu'
import { useFundsStore } from '@/features/funds/store.ts'
import BottomSheet from '@/shared/components/BottomSheet.vue'

defineProps<{
  open: boolean
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

interface QuickAction {
  key: string
  icon: Component
  to: string
}

const router = useRouter()
const fundsStore = useFundsStore()

// Создание открывается на экране раздела (?create=1) — там же форма и список
const actions = computed<QuickAction[]>(() => {
  const list: QuickAction[] = [{ key: 'contribute', icon: LuWallet, to: '/contribute' }]
  if (fundsStore.permissions.canManageFinance) {
    list.push(
      { key: 'expense', icon: LuReceiptText, to: '/finance/expenses?create=1' },
      { key: 'fund', icon: LuTarget, to: '/finance/funds?create=1' },
      { key: 'transfer', icon: LuArrowLeftRight, to: '/fund/accounts?create=1' },
    )
  }
  list.push({ key: 'announcement', icon: LuMegaphone, to: '/news?create=1' })
  return list
})

function go(action: QuickAction) {
  emit('close')
  void router.push(action.to)
}
</script>

<template>
  <BottomSheet :open="open" :title="$t('quickActions.title')" @close="emit('close')">
    <div class="actions">
      <button v-for="action in actions" :key="action.key" class="action" @click="go(action)">
        <span class="icon"><component :is="action.icon" /></span>
        <span class="text">
          <span class="title">{{ $t(`quickActions.${action.key}.title`) }}</span>
          <span class="hint">{{ $t(`quickActions.${action.key}.hint`) }}</span>
        </span>
        <LuChevronRight class="chevron" />
      </button>
    </div>
  </BottomSheet>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.action {
  @include pressable;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border: 1px solid $hairline;
  border-radius: 18px;
  background: $surface;
  text-align: left;
}

.icon {
  @include icon-circle(42px);
}

.text {
  display: flex;
  flex-direction: column;
  flex: 1;
  min-width: 0;
}

.title {
  font-size: 15px;
  font-weight: 600;
  color: $navy;
}

.hint {
  font-size: 12px;
  color: $text-muted;
}

.chevron {
  color: $text-muted;
}
</style>
