<script setup lang="ts">
import type { Component } from 'vue'

export interface QuickTile {
  key: string
  icon: Component
  title: string
  hint: string
}

/** Плитки быстрых действий 2×2 (на компьютере — в ряд). */
defineProps<{
  tiles: QuickTile[]
}>()

const emit = defineEmits<{
  (e: 'select', key: string): void
}>()
</script>

<template>
  <div class="tiles">
    <button v-for="tile in tiles" :key="tile.key" class="tile" @click="emit('select', tile.key)">
      <span class="icon"><component :is="tile.icon" /></span>
      <span class="title">{{ tile.title }}</span>
      <span class="hint">{{ tile.hint }}</span>
    </button>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.tiles {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.tile {
  @include glass-card(20px);
  @include pressable;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  min-height: 118px;
  padding: 16px;
  text-align: left;
}

.icon {
  margin-bottom: auto;
  padding-bottom: 18px;
  font-size: 22px;
  color: $navy;
}

.title {
  font-size: 15px;
  font-weight: 600;
  color: $navy;
}

.hint {
  margin-top: 2px;
  font-size: 12px;
  color: $text-muted;
}

@media (min-width: 900px) {
  .tiles {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}
</style>
