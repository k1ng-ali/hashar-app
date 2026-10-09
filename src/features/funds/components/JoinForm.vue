<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import type { FundPublic, JoinPayload } from '../types.ts'

defineProps<{
  fund: FundPublic
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', payload: JoinPayload): void
}>()

const { t } = useI18n()

const form = reactive({ address_unit: '', message: '' })
const error = ref('')

function handleSubmit() {
  if (!form.address_unit.trim()) {
    error.value = t('funds.join.validation')
    return
  }
  error.value = ''
  emit('submit', { address_unit: form.address_unit.trim(), message: form.message.trim() || null })
}
</script>

<template>
  <form class="form" @submit.prevent="handleSubmit">
    <div class="fund">
      <b>{{ fund.name }}</b>
      <span>{{ fund.address ?? fund.code }}</span>
    </div>

    <label>
      <span class="label">{{ $t('funds.join.unit') }}</span>
      <input v-model="form.address_unit" maxlength="50" :placeholder="$t('funds.join.unitPlaceholder')" />
    </label>

    <label>
      <span class="label">{{ $t('funds.join.message') }} · {{ $t('common.optional') }}</span>
      <textarea v-model="form.message" rows="2" maxlength="500" :placeholder="$t('funds.join.messagePlaceholder')" />
    </label>

    <p v-if="error" class="error">{{ error }}</p>
    <p class="hint">{{ $t('funds.join.hint') }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting">{{ $t('funds.join.submit') }}</button>
  </form>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.fund {
  @include glass-card(16px);
  display: flex;
  flex-direction: column;
  padding: 12px 14px;

  b {
    color: $navy;
  }

  span {
    font-size: 12px;
    color: $text-muted;
  }
}

.label {
  @include field-label;
}

input,
textarea {
  @include field-input;
}

.hint {
  margin: 0;
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
