<script setup lang="ts">
import { LuCircleCheck, LuLoader, LuUpload, LuZap } from '@kalimahapps/vue-icons/lu'
import { useImageUpload } from '@/shared/composables/useImageUpload.ts'
import { IS_DEV_MODE } from '@/shared/lib/env.ts'

/**
 * modelValue — то, что уходит в API: ключ загруженного чека или демо-чек (SVG data URL).
 * Фото загружается сразу после выбора; превью — локальная blob-ссылка на сжатый файл.
 */
const props = defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'generate'): void
}>()

const { uploading, upload, previewOf, forget } = useImageUpload()
const inputId = `receipt-${Math.random().toString(36).slice(2, 8)}`

async function handleFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file || uploading.value) return
  const key = await upload(file)
  if (key) emit('update:modelValue', key)
}

function replace() {
  forget(props.modelValue)
  emit('update:modelValue', '')
}
</script>

<template>
  <!-- Чек прикреплён -->
  <div v-if="modelValue" class="receipt-preview">
    <img :src="previewOf(modelValue)" :alt="$t('receipt.viewerTitle')" />
    <div class="preview-info">
      <span class="attached"><LuCircleCheck /> {{ $t('receipt.attached') }}</span>
      <button type="button" class="replace-btn" @click="replace">
        {{ $t('receipt.replace') }}
      </button>
    </div>
  </div>

  <!-- Выбор файла -->
  <div v-else class="receipt-dropzone">
    <input
      :id="inputId"
      type="file"
      accept="image/*"
      class="file-input"
      :disabled="uploading"
      @change="handleFile"
    />
    <label :for="inputId" class="dropzone-label" :class="{ uploading }">
      <span class="upload-icon"><LuLoader v-if="uploading" class="spin" /><LuUpload v-else /></span>
      <span class="dropzone-title">{{ uploading ? $t('receipt.uploading') : $t('receipt.pick') }}</span>
      <span v-if="!uploading" class="dropzone-hint">{{ $t('receipt.pickHint') }}</span>
    </label>

    <!-- Тестовый чек — только в демо-режиме: в проде это был бы генератор поддельных чеков -->
    <div v-if="IS_DEV_MODE" class="demo-row">
      <span>{{ $t('receipt.or') }}</span>
      <button type="button" class="demo-btn" @click="emit('generate')">
        <LuZap /> {{ $t('receipt.generate') }}
      </button>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

/* ── Preview ──────────────────────────────────────────────────────────────── */
.receipt-preview {
  @include glass-card(16px);
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 10px;

  img {
    width: 64px;
    height: 84px;
    object-fit: cover;
    border-radius: 10px;
    border: 1px solid rgba(17, 24, 39, 0.1);
    background: #fff;
  }
}

.preview-info {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 8px;
}

.attached {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: $success;
  font-size: 14px;
  font-weight: 700;
}

.replace-btn {
  @include ghost-button;
  padding: 6px 12px;
  font-size: 12px;
}

/* ── Dropzone ─────────────────────────────────────────────────────────────── */
.receipt-dropzone {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.file-input {
  display: none;
}

.dropzone-label {
  @include pressable;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 20px 16px;
  border: 2px dashed rgba(17, 24, 39, 0.5);
  border-radius: 18px;
  background: rgba(17, 24, 39, 0.06);
  cursor: pointer;
  text-align: center;

  &.uploading {
    cursor: progress;
    opacity: 0.7;
  }
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.upload-icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  margin-bottom: 4px;
  border-radius: 50%;
  background: $gradient;
  color: #fff;
  font-size: 20px;
}

.dropzone-title {
  font-size: 14px;
  font-weight: 700;
  color: $navy;
}

.dropzone-hint {
  font-size: 12px;
  color: $text-muted;
}

.demo-row {
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 12px;
  color: $text-muted;
}

.demo-btn {
  @include ghost-button;
  padding: 7px 12px;
  font-size: 12px;
  color: $teal;
}
</style>
