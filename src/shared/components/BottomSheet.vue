<script setup lang="ts">
import { onBeforeUnmount, watch } from 'vue'
import { LuX } from '@kalimahapps/vue-icons/lu'

const props = defineProps<{
  open: boolean
  title: string
  subtitle?: string
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

// Блокируем прокрутку страницы под шторкой
watch(
  () => props.open,
  (isOpen) => {
    document.body.style.overflow = isOpen ? 'hidden' : ''
  },
)

onBeforeUnmount(() => {
  document.body.style.overflow = ''
})
</script>

<template>
  <Teleport to="body">
    <Transition name="sheet">
      <div v-if="open" class="sheet-backdrop" @click.self="emit('close')">
        <div class="sheet" role="dialog" :aria-label="title">
          <div class="sheet-handle" />

          <header class="sheet-header">
            <div class="sheet-titles">
              <h2 class="sheet-title">{{ title }}</h2>
              <p v-if="subtitle" class="sheet-subtitle">{{ subtitle }}</p>
            </div>
            <button class="close-btn" :aria-label="$t('common.close')" @click="emit('close')">
              <LuX />
            </button>
          </header>

          <div class="sheet-body">
            <slot />
          </div>

          <footer v-if="$slots.footer" class="sheet-footer">
            <slot name="footer" />
          </footer>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.sheet-backdrop {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  background: rgba(15, 23, 42, 0.4);
  backdrop-filter: blur(4px);
}

.sheet {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-width: 560px;
  max-height: 92vh;
  border-radius: 28px 28px 0 0;
  background: #F6F6F6;
  box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.15);
  padding-bottom: var(--sab, 0px);
}

.sheet-handle {
  width: 40px;
  height: 5px;
  margin: 10px auto 0;
  border-radius: 3px;
  background: rgba(35, 73, 112, 0.18);
}

/* ── Header ───────────────────────────────────────────────────────────────── */
.sheet-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 20px 8px;
}

.sheet-title {
  margin: 0;
  font-size: 19px;
  font-weight: 800;
  color: $navy;
}

.sheet-subtitle {
  margin: 4px 0 0;
  font-size: 13px;
  color: $text-secondary;
}

.close-btn {
  @include pressable;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: rgba(35, 73, 112, 0.08);
  color: $navy;
  font-size: 18px;
}

/* ── Body / footer ────────────────────────────────────────────────────────── */
.sheet-body {
  flex: 1;
  overflow-y: auto;
  padding: 8px 20px 20px;
}

.sheet-footer {
  display: flex;
  gap: 10px;
  padding: 12px 20px 16px;
  border-top: 1px solid rgba(35, 73, 112, 0.06);
}

/* ── Анимация ─────────────────────────────────────────────────────────────── */
.sheet-enter-active,
.sheet-leave-active {
  transition: opacity 0.25s ease;

  .sheet {
    transition: transform 0.3s cubic-bezier(0.32, 0.72, 0, 1);
  }
}

.sheet-enter-from,
.sheet-leave-to {
  opacity: 0;

  .sheet {
    transform: translateY(100%);
  }
}

@media (min-width: 768px) {
  .sheet-backdrop {
    align-items: center;
  }

  .sheet {
    border-radius: 28px;
    max-height: 86vh;
  }

  .sheet-handle {
    display: none;
  }
}
</style>
