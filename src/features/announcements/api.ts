import { http } from '@/shared/api/http.ts'
import type {
  Announcement,
  AnnouncementCategory,
  AnnouncementComment,
  AnnouncementCreate,
  EmergencyContact,
  EmergencyContactCreate,
} from './types.ts'

const base = (fundId: number) => `/funds/${fundId}/announcements`

export const listAnnouncements = (fundId: number, category?: AnnouncementCategory) =>
  http.get<Announcement[]>(`${base(fundId)}/`, { params: { category } })

export const createAnnouncement = (fundId: number, payload: AnnouncementCreate) =>
  http.post<Announcement>(`${base(fundId)}/`, payload)

export const toggleLike = (fundId: number, id: number) => http.post<Announcement>(`${base(fundId)}/${id}/like`)

export const addComment = (fundId: number, id: number, text: string) =>
  http.post<AnnouncementComment>(`${base(fundId)}/${id}/comments`, { text })

// Закрепить / открепить — только совет
export const setPinned = (fundId: number, id: number, isPinned: boolean) =>
  http.put<Announcement>(`/council/funds/${fundId}/announcements/${id}/pin`, { is_pinned: isPinned })

export const deleteAnnouncement = (fundId: number, id: number) => http.delete<void>(`${base(fundId)}/${id}`)

// ── Экстренные телефоны: смотрят все, ведёт совет ──
export const listEmergencyContacts = (fundId: number) =>
  http.get<EmergencyContact[]>(`/funds/${fundId}/emergency-contacts/`)

export const createEmergencyContact = (fundId: number, payload: EmergencyContactCreate) =>
  http.post<EmergencyContact>(`/council/funds/${fundId}/emergency-contacts/`, payload)

export const deleteEmergencyContact = (fundId: number, id: number) =>
  http.delete<void>(`/council/funds/${fundId}/emergency-contacts/${id}`)
