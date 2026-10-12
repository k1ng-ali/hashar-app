<script setup lang="ts">
import { computed, ref } from 'vue'
import { LuCalendarX, LuCircleCheck, LuLock } from '@kalimahapps/vue-icons/lu'
import { formatDate, formatMoney, formatPeriod } from '@/shared/lib/format.ts'
import type { Member } from '../types.ts'

/**
 * Решение совета при возвращении участника или разблокировке:
 * начислять ли взносы за период отсутствия. Долг до ухода остаётся всегда.
 */
const props = defineProps<{
  member: Member
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'confirm', accrue: boolean): void
}>()

const absence = computed(() => props.member.absence!)
const isReturn = computed(() => absence.value.reason === 'left')
const hasPeriod = computed(() => absence.value.months_count > 0)

// Выбор не предзаполнен — совет должен решить осознанно
const choice = ref<'accrue' | 'skip' | null>(null)

const periodLabel = computed(() =>
  absence.value.from_period === absence.value.to_period
    ? formatPeriod(absence.value.from_period)
    : `${formatPeriod(absence.value.from_period)} — ${formatPeriod(absence.value.to_period)}`,
)

function confirm() {
  // Нечего решать (отсутствие меньше месяца) — просто возвращаем
  emit('confirm', hasPeriod.value ? choice.value === 'accrue' : true)
}
</script>

<template>
  <div class="decision">
    <div class="who">
      <span class="avatar">{{ member.full_name.slice(0, 1) }}</span>
      <div>
        <div class="name">{{ member.full_name }}</div>
        <div class="meta">
          {{ member.address_unit ?? '—' }} ·
          {{
            isReturn
              ? $t('absence.leftAt', { date: formatDate(absence.since) })
              : $t('absence.blockedAt', { date: formatDate(absence.since) })
          }}
        </div>
      </div>
    </div>

    <!-- 1. Что сохранится в любом случае -->
    <div class="kept">
      <LuLock class="kept-icon" />
      <div>
        <div class="kept-title">
          {{
            absence.debt_before
              ? $t('absence.debtBefore', { amount: formatMoney(absence.debt_before, absence.currency) })
              : $t('absence.noDebtBefore')
          }}
        </div>
        <div class="kept-hint">{{ $t('absence.debtKept') }}</div>
      </div>
    </div>

    <!-- 2. Решение о периоде отсутствия -->
    <template v-if="hasPeriod">
      <div class="question">
        <span class="question-title">
          {{ isReturn ? $t('absence.questionReturn') : $t('absence.questionUnblock') }}
        </span>
        <span class="period">
          <LuCalendarX />
          {{ periodLabel }} · {{ $t('absence.months', { n: absence.months_count }) }}
        </span>
      </div>

      <div class="options" role="radiogroup">
        <button
          type="button"
          role="radio"
          class="option"
          :class="{ 'option--selected': choice === 'accrue' }"
          :aria-checked="choice === 'accrue'"
          @click="choice = 'accrue'"
        >
          <span class="radio" />
          <span class="option-text">
            <span class="option-title">{{ $t('absence.accrueTitle') }}</span>
            <span class="option-amount option-amount--debt">
              +{{ formatMoney(absence.amount, absence.currency) }}
            </span>
            <span class="option-hint">{{ $t('absence.accrueHint') }}</span>
          </span>
        </button>

        <button
          type="button"
          role="radio"
          class="option"
          :class="{ 'option--selected': choice === 'skip' }"
          :aria-checked="choice === 'skip'"
          @click="choice = 'skip'"
        >
          <span class="radio" />
          <span class="option-text">
            <span class="option-title">{{ $t('absence.skipTitle') }}</span>
            <span class="option-amount">{{ formatMoney(0, absence.currency) }}</span>
            <span class="option-hint">{{ $t('absence.skipHint') }}</span>
          </span>
        </button>
      </div>

      <p class="warning">⚠️ {{ $t('absence.final') }}</p>
    </template>

    <p v-else class="nothing">
      <LuCircleCheck /> {{ $t('absence.nothingToDecide') }}
    </p>

    <button class="confirm-btn" :disabled="isSubmitting || (hasPeriod && !choice)" @click="confirm">
      {{ isReturn ? $t('absence.confirmReturn') : $t('absence.confirmUnblock') }}
    </button>
    <p v-if="hasPeriod && !choice" class="choose-hint">{{ $t('absence.chooseFirst') }}</p>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.decision {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.who {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  @include icon-circle(44px);
  font-size: 17px;
  font-weight: 600;
}

.name {
  font-size: 16px;
  font-weight: 600;
  color: $navy;
}

.meta {
  font-size: 13px;
  color: $text-secondary;
}

.kept {
  display: flex;
  gap: 12px;
  padding: 14px;
  border-radius: 16px;
  background: $surface-muted;
}

.kept-icon {
  flex-shrink: 0;
  margin-top: 2px;
  font-size: 18px;
  color: $navy;
}

.kept-title {
  font-size: 14px;
  font-weight: 600;
  color: $navy;
}

.kept-hint {
  margin-top: 2px;
  font-size: 12px;
  line-height: 1.45;
  color: $text-secondary;
}

.question {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.question-title {
  font-size: 16px;
  font-weight: 600;
  color: $navy;
}

.period {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  align-self: flex-start;
  padding: 6px 10px;
  border-radius: 10px;
  background: #FFFBEB;
  color: #92400E;
  font-size: 13px;
  font-weight: 600;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.option {
  @include pressable;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px;
  border: 1.5px solid rgba(17, 24, 39, 0.1);
  border-radius: 18px;
  background: $surface;
  text-align: left;

  &--selected {
    border-color: #111827;
    box-shadow: 0 0 0 3px rgba(17, 24, 39, 0.08);

    .radio {
      border-color: #111827;

      &::after {
        transform: scale(1);
      }
    }
  }
}

.radio {
  position: relative;
  flex-shrink: 0;
  width: 20px;
  height: 20px;
  margin-top: 2px;
  border: 2px solid rgba(17, 24, 39, 0.25);
  border-radius: 50%;

  &::after {
    content: '';
    position: absolute;
    inset: 3px;
    border-radius: 50%;
    background: #111827;
    transform: scale(0);
    transition: transform 0.15s ease;
  }
}

.option-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.option-title {
  font-size: 15px;
  font-weight: 600;
  color: $navy;
}

.option-amount {
  font-size: 18px;
  font-weight: 700;
  color: $navy;

  &--debt {
    color: $danger;
  }
}

.option-hint {
  font-size: 12px;
  line-height: 1.45;
  color: $text-secondary;
}

.warning {
  margin: 0;
  font-size: 12px;
  color: #92400E;
}

.nothing {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  padding: 12px 14px;
  border-radius: 14px;
  background: rgba(22, 163, 74, 0.08);
  color: #166534;
  font-size: 13px;
}

.confirm-btn {
  @include cta-button;
  width: 100%;
}

.choose-hint {
  margin: -6px 0 0;
  font-size: 12px;
  text-align: center;
  color: $text-muted;
}
</style>
