import type { ApplicationGenerationStatus, ApplicationType } from '@/api/generated/model'

export type GenerationStatusOption = {
  label: string
  tagType: 'warning' | 'danger'
}

export const applicationTypeOptions: Array<{ label: string; value: ApplicationType }> = [
  { label: 'Inny', value: 'OTHER' },
  { label: 'Przedłużenie terminu złożenia pracy dyplomowej', value: 'DIPLOMA_DEADLINE_EXTENSION' },
]

export const generationStatusOptions: Record<
  Exclude<ApplicationGenerationStatus, 'GENERATED'>,
  GenerationStatusOption
> = {
  IN_PROGRESS: { label: 'Generowanie', tagType: 'warning' },
  FAILED: { label: 'Błąd generowania', tagType: 'danger' },
}
