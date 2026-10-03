import type { ApplicationType } from '@/api/generated/model'

export const applicationTypeOptions: Array<{ label: string; value: ApplicationType }> = [
  { label: 'Inny', value: 'OTHER' },
  { label: 'Przedłużenie terminu złożenia pracy dyplomowej', value: 'DIPLOMA_DEADLINE_EXTENSION' },
]
