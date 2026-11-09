import type { DescriptionStatus } from '@/api/generated/model'

export type DescriptionStatusOption = {
  label: string
  tagType: 'warning' | 'danger'
}

export const descriptionStatusOptions: Record<
  Extract<DescriptionStatus, 'IN_PROGRESS' | 'FAILED'>,
  DescriptionStatusOption
> = {
  IN_PROGRESS: { label: 'Generowanie opisu', tagType: 'warning' },
  FAILED: { label: 'Błąd generowania opisu', tagType: 'danger' },
}
