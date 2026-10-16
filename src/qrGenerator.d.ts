export function qrcode(typeNumber: number, errorCorrectionLevel: 'L' | 'M' | 'Q' | 'H'): {
  addData(value: string): void
  make(): void
  getModuleCount(): number
  isDark(row: number, col: number): boolean
}
