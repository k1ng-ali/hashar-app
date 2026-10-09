<script setup lang="ts">
import { LuPlus } from '@kalimahapps/vue-icons/lu'
import BottomSheet from '@/shared/components/BottomSheet.vue'
import MyFundCard from './MyFundCard.vue'
import type { MyFund } from '../types.ts'

defineProps<{
  open: boolean
  funds: MyFund[]
  currentId: number | null
}>()

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'select', fund: MyFund): void
  (e: 'manage'): void
}>()
</script>

<template>
  <BottomSheet :open="open" :title="$t('funds.switcher.title')" @close="emit('close')">
    <div class="list">
      <MyFundCard
        v-for="fund in funds"
        :key="fund.id"
        :fund="fund"
        :is-current="fund.id === currentId"
        @open="emit('select', $event)"
      />
    </div>

    <button class="manage-btn" @click="emit('manage')"><LuPlus /> {{ $t('funds.switcher.manage') }}</button>
  </BottomSheet>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.list {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 14px;
}

.manage-btn {
  @include ghost-button;
  width: 100%;
  padding: 12px;
}
</style>
