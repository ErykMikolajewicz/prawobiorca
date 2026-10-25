import type {
  RegulationDescriptionStatus,
  RegulationPreparationStatus,
  RegulationType,
} from '@/api/generated/model'

export type { RegulationScope } from '@/api/generated/model'

export type PreparationStatusOption = {
  label: string
  tagType: 'info' | 'warning' | 'danger'
}

export const regulationTypeOptions: Array<{ label: string; value: RegulationType }> = [
  { label: 'Ustawa', value: 'ACT' },
  { label: 'Rozporządzenie', value: 'DECREE' },
  { label: 'Regulamin', value: 'STATUTE' },
]

export const preparationStatusOptions: Record<
  Exclude<RegulationPreparationStatus, 'PREPARED'>,
  PreparationStatusOption
> = {
  NOT_STARTED: { label: 'Oczekuje', tagType: 'info' },
  IN_PROGRESS: { label: 'Przetwarzanie', tagType: 'warning' },
  FAILED: { label: 'Błąd przetwarzania', tagType: 'danger' },
}

export const descriptionStatusOptions: Record<
  Extract<RegulationDescriptionStatus, 'IN_PROGRESS' | 'FAILED'>,
  PreparationStatusOption
> = {
  IN_PROGRESS: { label: 'Generowanie opisu', tagType: 'warning' },
  FAILED: { label: 'Błąd generowania opisu', tagType: 'danger' },
}
