import type {
  RegulationPreparationStatus,
  RegulationRepresentation,
  RegulationType,
} from '@/api/generated/model'

export type RegulationScope = 'user' | 'public'

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

export function isPending(regulation: RegulationRepresentation): boolean {
  return regulation.preparationStatus === 'IN_PROGRESS'
}
