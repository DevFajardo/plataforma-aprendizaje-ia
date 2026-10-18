/** Une clases condicionales (ignora valores falsos). */
export function cx(...partes: (string | false | null | undefined)[]): string {
  return partes.filter(Boolean).join(" ");
}
