<script setup lang="ts">
import { LuChevronRight } from '@kalimahapps/vue-icons/lu'
import ProgressBar from '@/shared/components/ProgressBar.vue'
import { formatMoney } from '@/shared/lib/format.ts'
import type { TargetFund, TargetFundCategory } from '../types.ts'

defineProps<{
  fund: TargetFund
}>()

const emit = defineEmits<{
  (e: 'open', fund: TargetFund): void
  (e: 'contribute', fund: TargetFund): void
}>()

const CATEGORY_EMOJI: Record<TargetFundCategory, string> = {
  security: '🚧',
  landscaping: '🌳',
  major_repair: '🏗️',
  infrastructure: '💡',
}
</script>

<template>
  <div class="fund-card" :class="{ 'fund-card--closed': !fund.is_active }" @click="emit('open', fund)">
    <img v-if="fund.image" :src="fund.image" alt="" class="cover" loading="lazy" />

    <div class="top">
      <span class="icon">{{ CATEGORY_EMOJI[fund.category] }}</span>
      <div class="titles">
        <h3 class="title">{{ fund.title }}</h3>
        <span class="category">{{ $t(`targetFundCategory.${fund.category}`) }}</span>
      </div>
      <LuChevronRight class="chevron" />
    </div>

    <div class="numbers">
      <div>
        <span class="sub">{{ $t('targetFunds.collected') }}</span>
        <span class="collected">{{ formatMoney(fund.collected_amount, fund.currency) }}</span>
      </div>
      <div class="right">
        <span class="sub">{{ $t('targetFunds.target', { amount: formatMoney(fund.target_amount, fund.currency) }) }}</span>
        <span class="percent">{{ fund.percent }}%</span>
      </div>
    </div>

    <ProgressBar :percent="fund.percent" />

    <div class="footer">
      <span v-if="fund.is_active" class="tag">
        {{ $t('targetFunds.remaining', { amount: formatMoney(fund.remaining_amount, fund.currency) }) }}
      </span>
      <span v-else class="tag tag--closed">{{ $t('targetFunds.closed') }}</span>

      <button v-if="fund.is_active" class="contribute-btn" @click.stop="emit('contribute', fund)">
        {{ $t('targetFunds.contribute') }}
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.fund-card {
  @include glass-card;
  @include pressable;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  cursor: pointer;

  &--closed {
    opacity: 0.7;
  }
}

// Фото «на что собираем» — во всю ширину карточки
.cover {
  width: calc(100% + 32px);
  height: 150px;
  margin: -16px -16px 0;
  object-fit: cover;
  border-radius: 20px 20px 0 0;
  background: $surface-muted;
}

.top {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon {
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 44px;
  height: 44px;
  border-radius: 14px;
  background: rgba(17, 24, 39, 0.14);
  font-size: 22px;
}

.titles {
  flex: 1;
  min-width: 0;
}

.title {
  margin: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  font-size: 15px;
  font-weight: 700;
  color: $navy;
}

.category {
  font-size: 12px;
  color: $text-muted;
}

.chevron {
  flex-shrink: 0;
  color: $text-muted;
}

.numbers {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;

  > div {
    display: flex;
    flex-direction: column;
  }

  .right {
    align-items: flex-end;
  }
}

.sub {
  font-size: 11px;
  color: $text-muted;
}

.collected {
  font-size: 18px;
  font-weight: 700;
  color: $navy;
}

.percent {
  font-size: 16px;
  font-weight: 700;
  color: $teal;
}

.footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.tag {
  font-size: 12px;
  font-weight: 600;
  color: $text-secondary;

  &--closed {
    color: $success;
  }
}

.contribute-btn {
  @include cta-button;
  padding: 7px 14px;
  font-size: 12px;
}
</style>
