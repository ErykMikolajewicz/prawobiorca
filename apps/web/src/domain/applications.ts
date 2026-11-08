import type { ApplicationGenerationStatus } from '@/api/generated/model'

export type GenerationStatusOption = {
  label: string
  tagType: 'warning' | 'danger'
}

export const generationStatusOptions: Record<
  Exclude<ApplicationGenerationStatus, 'GENERATED'>,
  GenerationStatusOption
> = {
  IN_PROGRESS: { label: 'Generowanie', tagType: 'warning' },
  FAILED: { label: 'Błąd generowania', tagType: 'danger' },
}
