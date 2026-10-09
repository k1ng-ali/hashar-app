<script setup lang="ts">
defineProps<{
  status: 'pending' | 'approved' | 'rejected'
}>()
</script>

<template>
  <span class="status-badge" :class="`status-badge--${status}`">
    {{ $t(`contributionStatus.${status}`) }}
  </span>
</template>

<style scoped lang="scss">
.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 3px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 700;
  white-space: nowrap;

  &--pending {
    background: rgba(245, 158, 11, 0.14);
    color: #B45309;
  }

  &--approved {
    background: rgba(16, 185, 129, 0.14);
    color: #047857;
  }

  &--rejected {
    background: rgba(239, 68, 68, 0.12);
    color: #B91C1C;
  }
}
</style>
