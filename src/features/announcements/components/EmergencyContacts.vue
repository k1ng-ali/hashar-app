<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { LuPhone, LuPlus, LuTrash2 } from '@kalimahapps/vue-icons/lu'
import { formatPhone, formatPhoneInput, isValidPhone, phoneHref } from '@/shared/lib/formatters.ts'
import type { EmergencyContact, EmergencyContactCreate } from '../types.ts'

/** Экстренные телефоны фонда: участники звонят, совет добавляет и удаляет. */
const props = defineProps<{
  contacts: EmergencyContact[]
  canManage: boolean
  isSubmitting: boolean
}>()

const emit = defineEmits<{
  (e: 'add', payload: EmergencyContactCreate): void
  (e: 'delete', id: number): void
}>()

const { t } = useI18n()

const isOpen = ref(false)
const isAdding = ref(false)
const form = reactive({ title: '', phone: '' })
const error = ref('')

const count = computed(() => props.contacts.length)

function onPhoneInput(event: Event) {
  const input = event.target as HTMLInputElement
  form.phone = formatPhoneInput(input.value)
  input.value = form.phone
}

function submit() {
  if (form.title.trim().length < 2) {
    error.value = t('emergency.validationTitle')
    return
  }
  if (!isValidPhone(form.phone)) {
    error.value = t('requisites.phoneInvalid')
    return
  }
  error.value = ''
  emit('add', { title: form.title.trim(), phone: form.phone })
}

/** Родитель сообщает об успешном добавлении — очищаем форму. */
function reset() {
  Object.assign(form, { title: '', phone: '' })
  isAdding.value = false
}

defineExpose({ reset })
</script>

<template>
  <div class="emergency">
    <button class="header" @click="isOpen = !isOpen">
      <span class="title">
        <LuPhone /> {{ $t('announcements.emergencyTitle') }}
        <span v-if="count" class="count">{{ count }}</span>
      </span>
      <span class="toggle">{{ isOpen ? $t('announcements.collapse') : $t('announcements.expand') }}</span>
    </button>

    <div v-if="isOpen" class="list">
      <div v-for="contact in contacts" :key="contact.id" class="contact">
        <div class="info">
          <div class="name">{{ contact.title }}</div>
          <div class="phone">{{ formatPhone(contact.phone) }}</div>
        </div>
        <a :href="phoneHref(contact.phone)" class="call-btn">{{ $t('announcements.call') }}</a>
        <button
          v-if="canManage"
          class="delete-btn"
          :aria-label="$t('common.delete')"
          @click="emit('delete', contact.id)"
        >
          <LuTrash2 />
        </button>
      </div>

      <p v-if="!contacts.length" class="empty">
        {{ canManage ? $t('emergency.emptyCouncil') : $t('emergency.empty') }}
      </p>

      <!-- Совет: новый телефон -->
      <template v-if="canManage">
        <form v-if="isAdding" class="add-form" @submit.prevent="submit">
          <input v-model="form.title" maxlength="100" :placeholder="$t('emergency.titlePlaceholder')" />
          <input
            :value="form.phone"
            type="tel"
            inputmode="tel"
            placeholder="+992 37 221 03 03"
            @input="onPhoneInput"
          />
          <p v-if="error" class="error">{{ error }}</p>
          <div class="form-actions">
            <button type="button" class="ghost-btn" @click="isAdding = false">{{ $t('common.cancel') }}</button>
            <button type="submit" class="save-btn" :disabled="isSubmitting">{{ $t('emergency.save') }}</button>
          </div>
        </form>
        <button v-else class="add-btn" @click="isAdding = true"><LuPlus /> {{ $t('emergency.add') }}</button>
      </template>
    </div>
  </div>
</template>

<style scoped lang="scss">
@use '@/shared/styles/mixins' as *;

.emergency {
  @include glass-card(18px);
  overflow: hidden;
  border-color: rgba(229, 72, 77, 0.2);
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

.count {
  min-width: 20px;
  padding: 0 6px;
  border-radius: 10px;
  background: rgba(229, 72, 77, 0.12);
  font-size: 11px;
  line-height: 20px;
  text-align: center;
}

.toggle {
  font-size: 12px;
  font-weight: 600;
  color: $text-muted;
}

.list {
  display: flex;
  flex-direction: column;
  padding: 0 16px 14px;
}

.contact {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 0;
  border-top: 1px solid $hairline;
}

.info {
  flex: 1;
  min-width: 0;
}

.name {
  overflow: hidden;
  font-size: 13px;
  color: $text-secondary;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.phone {
  font-size: 15px;
  font-weight: 700;
  color: $navy;
}

.call-btn {
  @include ghost-button;
  flex-shrink: 0;
  padding: 6px 14px;
  color: $danger;
  text-decoration: none;
}

.delete-btn {
  @include pressable;
  display: grid;
  place-items: center;
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border: none;
  border-radius: 10px;
  background: rgba(229, 72, 77, 0.08);
  color: $danger;
}

.empty {
  margin: 0;
  padding: 10px 0;
  border-top: 1px solid $hairline;
  font-size: 13px;
  color: $text-muted;
}

.add-btn {
  @include ghost-button;
  align-self: flex-start;
  margin-top: 8px;
}

.add-form {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 10px;
  border-top: 1px solid $hairline;

  input {
    @include field-input;
  }
}

.error {
  margin: 0;
  font-size: 12px;
  font-weight: 600;
  color: $danger;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}

.ghost-btn {
  @include ghost-button;
}

.save-btn {
  @include cta-button;
  padding: 10px 18px;
  font-size: 13px;
}
</style>
