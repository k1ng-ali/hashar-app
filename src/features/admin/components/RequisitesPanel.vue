<script setup lang="ts">
import { LuPlus, LuTrash2 } from '@kalimahapps/vue-icons/lu'
import type { Requisite } from '@/features/dashboard/types.ts'

defineProps<{
  requisites: Requisite[]
  canManage: boolean
}>()

const emit = defineEmits<{
  (e: 'add'): void
  (e: 'toggle', id: number): void
  (e: 'delete', id: number): void
}>()
</script>

<template>
  <section class="card">
    <div class="card-header">
      <div>
        <h3 class="card-title">{{ $t('admin.settings.requisitesTitle') }}</h3>
        <p class="card-sub">{{ $t('admin.settings.requisitesSubtitle') }}</p>
      </div>
      <button v-if="canManage" class="ghost-btn" @click="emit('add')">
        <LuPlus /> {{ $t('admin.settings.addRequisite') }}
      </button>
    </div>

    <div class="requisites">
      <div v-for="requisite in requisites" :key="requisite.id" class="requisite">
        <div class="requisite-top">
          <b>
            {{ requisite.bank_name }}
            <span class="currency">{{ requisite.currency.toUpperCase() }}</span>
            <span class="kind">{{ $t(`requisites.kind.${requisite.kind}`) }}</span>
          </b>
          <div class="requisite-actions">
            <a-switch
              :checked="requisite.is_active"
              :disabled="!canManage"
              size="small"
              @change="emit('toggle', requisite.id)"
            />
            <button v-if="canManage" class="icon-btn" :aria-label="$t('common.delete')" @click="emit('delete', requisite.id)">
              <LuTrash2 />
            </button>
          </div>
        </div>
        <span class="number">{{ requisite.card_or_account_number }}</span>
        <span class="recipient">{{ requisite.recipient_name }}</span>
      </div>
      <p v-if="!requisites.length" class="hint">{{ $t('requisites.empty') }}</p>
    </div>
  </section>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.card {
  @include glass-card;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 16px;
}

.card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.card-title {
  margin: 0;
  font-size: 15px;
  font-weight: 700;
  color: $navy;
}

.card-sub {
  margin: 2px 0 0;
  font-size: 12px;
  color: $text-muted;
}

.hint {
  margin: 0;
  font-size: 12px;
  color: $text-muted;
}

.ghost-btn {
  @include ghost-button;
  flex-shrink: 0;
}

.requisites {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.requisite {
  display: flex;
  flex-direction: column;
  gap: 2px;
  padding: 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.7);
}

.requisite-top {
  display: flex;
  align-items: center;
  justify-content: space-between;

  b {
    color: $navy;
  }
}

.currency {
  margin-left: 6px;
  padding: 1px 8px;
  border-radius: 10px;
  background: rgba(17, 24, 39, 0.14);
  color: #111827;
  font-size: 11px;
}

.requisite-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.number {
  font-family: 'SF Mono', 'Consolas', monospace;
  font-size: 14px;
  font-weight: 700;
  color: #111827;
}

.recipient {
  font-size: 12px;
  color: $text-secondary;
}

.icon-btn {
  @include pressable;
  display: grid;
  place-items: center;
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.08);
  color: $danger;
}

.kind {
  margin-left: 6px;
  font-size: 11px;
  font-weight: 500;
  color: $text-muted;
}
</style>
