<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { PlanInfo } from '@/features/funds/types.ts'
import { formatDate } from '@/shared/lib/format.ts'

/**
 * Плашка после окончания платного тарифа (core/plans.py на бэкенде).
 * Совету: льготный срок — «продлите, иначе с даты взносы заблокируются»; после — «взносы жителей заблокированы».
 * Жителю (и члену совета сверх 10): «фонд не продлил подписку — внести взнос нельзя».
 */
const props = defineProps<{
  plan: PlanInfo
  isCouncil: boolean
  canRenew: boolean
}>()

const emit = defineEmits<{
  (e: 'renew'): void
}>()

const { t } = useI18n()

const banner = computed<{ tone: 'warn' | 'danger'; title: string; text: string } | null>(() => {
  const plan = props.plan
  const expired = plan.expires_at ? formatDate(plan.expires_at) : ''
  const blockDate = plan.blocks_at ? formatDate(plan.blocks_at) : ''

  if (props.isCouncil && plan.lapse === 'grace') {
    return {
      tone: 'warn',
      title: t('planStatus.expiredTitle', { date: expired }),
      text: plan.over_free_limit
        ? t('planStatus.graceBlock', { date: blockDate })
        : t('planStatus.graceFree', { date: blockDate }),
    }
  }
  if (!plan.can_contribute) {
    return props.isCouncil
      ? { tone: 'danger', title: t('planStatus.blockedTitle'), text: t('planStatus.blockedCouncilOver') }
      : { tone: 'danger', title: t('planStatus.blockedTitle'), text: t('planStatus.blockedResident') }
  }
  if (props.isCouncil && plan.contributions_blocked) {
    return { tone: 'danger', title: t('planStatus.blockedTitle'), text: t('planStatus.blockedCouncil', { date: blockDate }) }
  }
  return null
})
</script>

<template>
  <section v-if="banner" class="banner" :class="`banner--${banner.tone}`" role="status">
    <b class="title">{{ banner.title }}</b>
    <p class="text">{{ banner.text }}</p>
    <button v-if="isCouncil && canRenew" type="button" class="renew" @click="emit('renew')">
      {{ $t('planStatus.renew') }}
    </button>
  </section>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.banner {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  padding: 14px 16px;
  border-radius: 20px;

  &--warn {
    border: 1px solid rgba(217, 119, 6, 0.25);
    background: #fffbeb;
    color: #92400e;
  }

  &--danger {
    border: 1px solid rgba(229, 72, 77, 0.25);
    background: #fef2f2;
    color: #991b1b;
  }
}

.title {
  font-size: 14px;
}

.text {
  margin: 0;
  font-size: 13px;
  line-height: 1.45;
}

.renew {
  @include pressable;
  margin-top: 4px;
  padding: 8px 14px;
  border: none;
  border-radius: 12px;
  background: #111827;
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
}
</style>
