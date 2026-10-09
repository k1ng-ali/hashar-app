<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { ANNOUNCEMENT_CATEGORIES, type AnnouncementCreate } from '../types.ts'

defineProps<{
  canPin: boolean
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', payload: AnnouncementCreate): void
}>()

const { t } = useI18n()

const form = reactive<AnnouncementCreate>({ title: '', content: '', category: 'news', is_pinned: false })
const error = ref('')

function handleSubmit() {
  if (form.title.trim().length < 3 || form.content.trim().length < 5) {
    error.value = t('announcements.validation')
    return
  }
  error.value = ''
  emit('submit', { ...form, title: form.title.trim(), content: form.content.trim() })
}

function reset() {
  Object.assign(form, { title: '', content: '', category: 'news', is_pinned: false })
  error.value = ''
}

defineExpose({ reset })
</script>

<template>
  <form class="announcement-form" @submit.prevent="handleSubmit">
    <label class="field">
      <span class="label">{{ $t('announcements.form.titleLabel') }}</span>
      <input v-model="form.title" maxlength="200" :placeholder="$t('announcements.form.titlePlaceholder')" />
    </label>

    <div class="field">
      <span class="label">{{ $t('announcements.form.category') }}</span>
      <div class="categories">
        <button
          v-for="category in ANNOUNCEMENT_CATEGORIES"
          :key="category"
          type="button"
          class="category"
          :class="{ 'category--active': form.category === category }"
          @click="form.category = category"
        >
          {{ $t(`announcementCategory.${category}`) }}
        </button>
      </div>
    </div>

    <label class="field">
      <span class="label">{{ $t('announcements.form.content') }}</span>
      <textarea v-model="form.content" rows="5" :placeholder="$t('announcements.form.contentPlaceholder')" />
    </label>

    <label v-if="canPin" class="switch-row">
      <a-switch v-model:checked="form.is_pinned" />
      <span>{{ $t('announcements.form.pin') }}</span>
    </label>

    <p v-if="error" class="error">{{ error }}</p>

    <button type="submit" class="submit-btn" :disabled="isSubmitting">
      {{ $t('announcements.form.publish') }}
    </button>
  </form>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.announcement-form {
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

.categories {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.category {
  @include ghost-button;
  padding: 7px 12px;
  font-size: 12px;

  &--active {
    border-color: transparent;
    background: $gradient;
    color: #fff;
  }
}

.switch-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: $navy;
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
