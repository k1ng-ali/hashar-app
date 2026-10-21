<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import PhotosPicker from '@/shared/components/PhotosPicker.vue'
import { formatMoney } from '@/shared/lib/format.ts'
import { TARGET_FUND_CATEGORIES, type TargetFund, type TargetFundCategory } from '@/features/targetFunds/types.ts'
import { type Currency } from '@/shared/lib/currency.ts'
import type { TargetFundCreate, TargetFundUpdate } from '../types.ts'

const PRESETS = [5000, 10000, 50000, 100000, 280000]

/** Без initial — новый сбор (submit), с initial — правка существующего (update). */
const props = defineProps<{
  currencies: Currency[]
  baseCurrency: Currency
  isSubmitting: boolean
  initial?: TargetFund
}>()

const emit = defineEmits<{
  (e: 'submit', payload: TargetFundCreate): void
  (e: 'update', payload: TargetFundUpdate): void
}>()

const { t } = useI18n()

const form = reactive({
  title: props.initial?.title ?? '',
  category: props.initial?.category ?? ('landscaping' as TargetFundCategory),
  target_amount: (props.initial?.target_amount ?? 10000) as number | null,
  currency: props.initial?.currency ?? props.baseCurrency,
  description: props.initial?.description ?? '',
  // Необязательное фото «на что собираем»: ключ загрузки или, при правке, ссылка на прежнее фото
  photos: props.initial?.image ? [props.initial.image] : ([] as string[]),
})
const error = ref('')

function handleSubmit() {
  if (form.title.trim().length < 3 || !form.target_amount || form.target_amount < 1 || form.description.trim().length < 3) {
    error.value = t('admin.funds.validation')
    return
  }
  error.value = ''
  const fields = {
    title: form.title.trim(),
    category: form.category,
    target_amount: form.target_amount,
    description: form.description.trim(),
  }
  if (!props.initial) {
    emit('submit', { ...fields, currency: form.currency, image: form.photos[0] ?? null })
    return
  }
  // Фото передаём, только если его сменили или убрали — прежнее остаётся без поля image
  const image = form.photos[0] ?? null
  emit('update', image === props.initial.image ? fields : { ...fields, image })
}
</script>

<template>
  <form class="form" @submit.prevent="handleSubmit">
    <label>
      <span class="label">{{ $t('admin.funds.titleLabel') }}</span>
      <input v-model="form.title" maxlength="200" :placeholder="$t('admin.funds.titlePlaceholder')" />
    </label>

    <div>
      <span class="label">{{ $t('admin.funds.category') }}</span>
      <div class="chips">
        <button
          v-for="category in TARGET_FUND_CATEGORIES"
          :key="category"
          type="button"
          class="chip"
          :class="{ 'chip--active': form.category === category }"
          @click="form.category = category"
        >
          {{ $t(`targetFundCategory.${category}`) }}
        </button>
      </div>
    </div>

    <div>
      <span class="label">{{ $t('admin.funds.currency') }}</span>
      <div class="chips">
        <button
          v-for="currency in currencies"
          :key="currency"
          type="button"
          class="chip"
          :class="{ 'chip--active': form.currency === currency }"
          :disabled="!!initial && form.currency !== currency"
          @click="form.currency = currency"
        >
          {{ currency.toUpperCase() }}
        </button>
      </div>
      <!-- Взносы уже зачтены в валюте сбора — сменить её нельзя -->
      <p v-if="initial" class="hint">{{ $t('admin.funds.currencyLocked') }}</p>
    </div>

    <label>
      <span class="label">{{ $t('admin.funds.target', { currency: form.currency.toUpperCase() }) }}</span>
      <input v-model.number="form.target_amount" type="number" min="1" inputmode="numeric" />
    </label>
    <div class="chips">
      <button
        v-for="preset in PRESETS"
        :key="preset"
        type="button"
        class="chip"
        :class="{ 'chip--active': form.target_amount === preset }"
        @click="form.target_amount = preset"
      >
        {{ formatMoney(preset, form.currency) }}
      </button>
    </div>

    <label>
      <span class="label">{{ $t('admin.funds.description') }}</span>
      <textarea v-model="form.description" rows="4" :placeholder="$t('admin.funds.descriptionPlaceholder')" />
    </label>

    <div>
      <span class="label">{{ $t('admin.funds.photo') }}</span>
      <PhotosPicker v-model="form.photos" :max="1" :hint="$t('admin.funds.photoHint')" />
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting">
      {{ initial ? $t('admin.funds.saveChanges') : `🚀 ${$t('admin.funds.save')}` }}
    </button>
  </form>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.label {
  @include field-label;
}

input,
textarea {
  @include field-input;
}

textarea {
  resize: vertical;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chip {
  @include ghost-button;
  padding: 7px 12px;
  font-size: 12px;

  &--active {
    border-color: transparent;
    background: $gradient;
    color: #fff;
  }
}

.hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: $text-muted;
}

.error {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
  color: $danger;
}

.submit-btn {
  @include cta-button;
}
</style>
