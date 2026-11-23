import type {
  RegulationPreparationFailureReason,
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

export const preparationFailureReasonLabels: Record<RegulationPreparationFailureReason, string> = {
  INCOMPLETE_DOCUMENT:
    'Nie udało się odczytać całego dokumentu, więc nie został udostępniony do wyszukiwania. Wgraj inną wersję pliku.',
  UNREADABLE_DOCUMENT:
    'Nie udało się odczytać pliku. Upewnij się, że to poprawny plik PDF bez hasła.',
  PROCESSING_ERROR: 'Wystąpił błąd techniczny podczas przetwarzania. Ponów przetwarzanie.',
}

export type RegulationsOrder = 'name' | 'score'

export type RegulationsSearchParams = {
  query: string
  threshold: number
  orderBy: RegulationsOrder
}
