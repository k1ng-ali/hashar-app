<script setup lang="ts">
import { LuImagePlus, LuLoader, LuX, LuZap } from '@kalimahapps/vue-icons/lu'
import { useImageUpload } from '@/shared/composables/useImageUpload.ts'
import { IS_DEV_MODE } from '@/shared/lib/env.ts'

/**
 * Несколько фото (чек, фото проблемы, результат работ): modelValue — ключи загрузок для API.
 * Каждое фото загружается сразу после выбора; плитка «+» исчезает, когда набрано max.
 */
const props = withDefaults(
  defineProps<{
    modelValue: string[]
    max?: number
    hint?: string
    /** Кнопка тестового чека (только в демо-режиме) */
    demo?: boolean
  }>(),
  { max: 3, hint: '', demo: false },
)

const emit = defineEmits<{
  (e: 'update:modelValue', value: string[]): void
  (e: 'generate'): void
}>()

const { uploading, upload, previewOf, forget } = useImageUpload()
const inputId = `photos-${Math.random().toString(36).slice(2, 8)}`

async function handleFiles(event: Event) {
  const input = event.target as HTMLInputElement
  const files = Array.from(input.files ?? []).slice(0, props.max - props.modelValue.length)
  input.value = ''
  // По одному: так видно, какое фото не загрузилось, а остальные остаются
  let keys = props.modelValue
  for (const file of files) {
    const key = await upload(file)
    if (key) {
      keys = [...keys, key]
      emit('update:modelValue', keys)
    }
  }
}

function remove(index: number) {
  forget(props.modelValue[index])
  emit('update:modelValue', props.modelValue.filter((_, i) => i !== index))
}
</script>

<template>
  <div class="photos">
    <div class="grid">
      <div v-for="(value, index) in modelValue" :key="value" class="tile">
        <img :src="previewOf(value)" alt="" />
        <button type="button" class="remove" :aria-label="$t('photos.remove')" @click="remove(index)">
          <LuX />
        </button>
      </div>

      <template v-if="modelValue.length < max">
        <input
          :id="inputId"
          type="file"
          accept="image/*"
          :multiple="max - modelValue.length > 1"
          class="file-input"
          :disabled="uploading"
          @change="handleFiles"
        />
        <label :for="inputId" class="tile tile--add" :class="{ uploading }">
          <LuLoader v-if="uploading" class="spin" />
          <LuImagePlus v-else />
          <span>{{ uploading ? $t('photos.uploading') : $t('photos.add') }}</span>
        </label>
      </template>
    </div>

    <!-- Счётчик «1 из 3» — только когда фото может быть несколько -->
    <p v-if="hint || max > 1" class="hint">
      {{ [hint, max > 1 ? $t('photos.count', { n: modelValue.length, max }) : ''].filter(Boolean).join(' · ') }}
    </p>

    <!-- Тестовый чек — только в демо-режиме -->
    <button
      v-if="demo && IS_DEV_MODE && modelValue.length < max"
      type="button"
      class="demo-btn"
      @click="emit('generate')"
    >
      <LuZap /> {{ $t('receipt.generate') }}
    </button>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.photos {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.tile {
  position: relative;
  aspect-ratio: 1;
  overflow: hidden;
  border: 1px solid $field-border;
  border-radius: 14px;
  background: $surface;

  img {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  &--add {
    @include pressable;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    border: 2px dashed rgba(17, 24, 39, 0.3);
    color: $navy;
    font-size: 12px;
    font-weight: 600;
    text-align: center;
    cursor: pointer;

    svg {
      font-size: 22px;
    }

    &.uploading {
      cursor: progress;
      opacity: 0.7;
    }
  }
}

.remove {
  position: absolute;
  top: 6px;
  right: 6px;
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  padding: 0;
  border: none;
  border-radius: 50%;
  background: rgba(17, 24, 39, 0.7);
  color: #fff;
  font-size: 14px;
  cursor: pointer;
}

.file-input {
  display: none;
}

.spin {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.hint {
  margin: 0;
  font-size: 12px;
  color: $text-muted;
}

.demo-btn {
  @include ghost-button;
  align-self: flex-start;
  padding: 7px 12px;
  font-size: 12px;
}
</style>
