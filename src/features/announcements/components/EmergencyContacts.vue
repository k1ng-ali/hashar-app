<script setup lang="ts">
import { ref } from 'vue'
import { LuPhone } from '@kalimahapps/vue-icons/lu'

// Телефоны дома — справочные, редактируются здесь
const CONTACTS = [
  { key: 'dispatcher', phone: '+7 (812) 345-67-89' },
  { key: 'lift', phone: '+7 (812) 998-11-22' },
  { key: 'chairman', phone: '+7 (916) 123-45-67' },
]

const isOpen = ref(false)
</script>

<template>
  <div class="emergency">
    <button class="header" @click="isOpen = !isOpen">
      <span class="title"><LuPhone /> {{ $t('announcements.emergencyTitle') }}</span>
      <span class="toggle">{{ isOpen ? $t('announcements.collapse') : $t('announcements.expand') }}</span>
    </button>

    <div v-if="isOpen" class="list">
      <div v-for="contact in CONTACTS" :key="contact.key" class="contact">
        <div>
          <div class="name">{{ $t(`announcements.contacts.${contact.key}`) }}</div>
          <div class="phone">{{ contact.phone }}</div>
        </div>
        <a :href="`tel:${contact.phone.replace(/[^\d+]/g, '')}`" class="call-btn">
          {{ $t('announcements.call') }}
        </a>
      </div>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.emergency {
  @include glass-card(18px);
  overflow: hidden;
  border-color: rgba(239, 68, 68, 0.2);
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding: 14px 16px;
  border: none;
  background: transparent;
}

.title {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 700;
  color: #B91C1C;
}

.toggle {
  font-size: 12px;
  font-weight: 600;
  color: $text-muted;
}

.list {
  display: flex;
  flex-direction: column;
  padding: 0 16px 12px;
}

.contact {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 0;
  border-top: 1px solid rgba(35, 73, 112, 0.06);
}

.name {
  font-size: 13px;
  color: $text-secondary;
}

.phone {
  font-size: 15px;
  font-weight: 700;
  color: $navy;
}

.call-btn {
  @include ghost-button;
  padding: 6px 14px;
  color: $danger;
  text-decoration: none;
}
</style>
