/** Compact token counts for display: 1200 → "1.2k", 82000 → "82k". */
export function formatTokens(value: number): string {
  if (value < 1000) {
    return String(value)
  }
  const thousands = value / 1000
  if (thousands < 10) {
    return `${Number.isInteger(thousands) ? thousands : thousands.toFixed(1)}k`
  }
  return `${Math.round(thousands)}k`
}
