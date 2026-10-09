<script setup lang="ts">
import { LuCircleCheck, LuUpload, LuZap } from '@kalimahapps/vue-icons/lu'
import { useI18n } from 'vue-i18n'
import { readFileAsDataUrl } from '@/shared/lib/browser.ts'
import { useHeaderStore } from '@/shared/stores/useHeaderStore.ts'

// Ограничение на размер чека — он хранится в БД как data URL
const MAX_FILE_SIZE = 5 * 1024 * 1024

defineProps<{
  modelValue: string
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: string): void
  (e: 'generate'): void
}>()

const { t } = useI18n()
const headerStore = useHeaderStore()
const inputId = `receipt-${Math.random().toString(36).slice(2, 8)}`

async function handleFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  if (file.size > MAX_FILE_SIZE) {
    headerStore.showNotification(t('receipt.tooLarge'), 'error')
    return
  }
  emit('update:modelValue', await readFileAsDataUrl(file))
}
</script>

<template>
  <!-- Чек прикреплён -->
  <div v-if="modelValue" class="receipt-preview">
    <img :src="modelValue" :alt="$t('receipt.viewerTitle')" />
    <div class="preview-info">
      <span class="attached"><LuCircleCheck /> {{ $t('receipt.attached') }}</span>
      <button type="button" class="replace-btn" @click="emit('update:modelValue', '')">
        {{ $t('receipt.replace') }}
      </button>
    </div>
  </div>

  <!-- Выбор файла -->
  <div v-else class="receipt-dropzone">
    <input :id="inputId" type="file" accept="image/*,.pdf" class="file-input" @change="handleFile" />
    <label :for="inputId" class="dropzone-label">
      <span class="upload-icon"><LuUpload /></span>
      <span class="dropzone-title">{{ $t('receipt.pick') }}</span>
      <span class="dropzone-hint">{{ $t('receipt.pickHint') }}</span>
    </label>

    <div class="demo-row">
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
    border: 1px solid rgba(35, 73, 112, 0.1);
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
  border: 2px dashed rgba(78, 190, 194, 0.5);
  border-radius: 18px;
  background: rgba(78, 190, 194, 0.06);
  cursor: pointer;
  text-align: center;
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
