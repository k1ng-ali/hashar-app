<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { LuCirclePlay, LuCircleStop, LuPencil, LuSparkles } from '@kalimahapps/vue-icons/lu'
import { formatDateTime, formatMoney } from '@/shared/lib/format.ts'
import type { TargetFund, TargetFundCategory, TargetFundHistoryItem } from '../types.ts'

/**
 * История сбора для всех участников: кто и когда менял цель, описание, фото,
 * закрывал или возобновлял сбор. Последняя строка — открытие сбора (дата создания).
 */
const props = defineProps<{
  fund: TargetFund & { history: TargetFundHistoryItem[] }
}>()

const { t } = useI18n()

const ICONS = { update: LuPencil, close: LuCircleStop, open: LuCirclePlay }

/** Правка → строки «что изменилось»; деньги и категорию показываем «было → стало». */
function describe(item: TargetFundHistoryItem): string[] {
  if (item.action !== 'update') return [t(`targetFunds.log.${item.action}`)]
  return Object.entries(item.changes).map(([field, change]) => {
    if (field === 'image') return t(change === 'removed' ? 'targetFunds.log.imageRemoved' : 'targetFunds.log.imageReplaced')
    if (!Array.isArray(change)) return t(`targetFunds.log.${field}`)
    const [from, to] = change
    if (field === 'target_amount') {
      return t('targetFunds.log.targetAmount', {
        from: formatMoney(Number(from), props.fund.currency),
        to: formatMoney(Number(to), props.fund.currency),
      })
    }
    if (field === 'category') {
      return t('targetFunds.log.categoryChanged', {
        from: t(`targetFundCategory.${from as TargetFundCategory}`),
        to: t(`targetFundCategory.${to as TargetFundCategory}`),
      })
    }
    return t(`targetFunds.log.${field}`)
  })
}

const rows = computed(() => props.fund.history.map((item) => ({ ...item, lines: describe(item) })))
</script>

<template>
  <ul class="history">
    <li v-for="(row, index) in rows" :key="index" class="row">
      <span class="icon"><component :is="ICONS[row.action]" /></span>
      <div class="body">
        <span v-for="line in row.lines" :key="line" class="line">{{ line }}</span>
        <span class="meta">{{ [row.actor_name, formatDateTime(row.created_at)].filter(Boolean).join(' · ') }}</span>
      </div>
    </li>
    <li class="row">
      <span class="icon"><LuSparkles /></span>
      <div class="body">
        <span class="line">{{ $t('targetFunds.log.created') }}</span>
        <span class="meta">{{ formatDateTime(fund.created_at) }}</span>
      </div>
    </li>
  </ul>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.history {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.row {
  display: flex;
  gap: 12px;
}

.icon {
  @include icon-circle(32px);
  font-size: 15px;
}

.body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.line {
  font-size: 14px;
  font-weight: 500;
  color: $navy;
}

.meta {
  font-size: 12px;
  color: $text-muted;
}
</style>
