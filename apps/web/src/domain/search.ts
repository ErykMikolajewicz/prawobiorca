export const defaultThreshold = 0.5

export const thresholdPresets: Array<{ label: string; value: number }> = [
  { label: 'Szeroki', value: defaultThreshold },
  { label: 'Średni', value: 0.6 },
  { label: 'Ścisły', value: 0.7 },
  { label: 'Bardzo ścisły', value: 0.8 },
]

export function isPresetThreshold(threshold: number) {
  return thresholdPresets.some((preset) => preset.value === threshold)
}
