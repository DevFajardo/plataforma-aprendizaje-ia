// Formato numérico es-CO: separador de miles con punto, decimales con coma y porcentaje con espacio fino.
const NBSP = " ";

const FORMATOS = new Map<number, Intl.NumberFormat>();
function formato(dec: number): Intl.NumberFormat {
  let f = FORMATOS.get(dec);
  if (!f) {
    f = new Intl.NumberFormat("es-CO", { maximumFractionDigits: dec, minimumFractionDigits: 0 });
    FORMATOS.set(dec, f);
  }
  return f;
}

/** Número con formato es-CO (1.234,5). `null`/`undefined` se muestran como «—». */
export function num(v: number | null | undefined, decimales = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return formato(decimales).format(v);
}

/** Porcentaje es-CO: «87,2 %». `null`/`undefined` se muestran como «—». */
export function pct(v: number | null | undefined, decimales = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${formato(decimales).format(v)}${NBSP}%`;
}

/** Entero con separador de miles (1.234). */
export function entero(v: number | null | undefined): string {
  return num(v, 0);
}

/** Diferencia con signo explícito: «+1,5». */
export function conSigno(v: number | null | undefined, decimales = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${v > 0 ? "+" : ""}${formato(decimales).format(v)}`;
}

/** Plural simple: `plural(3, "intento")` → «3 intentos». */
export function plural(n: number, singular: string, pluralForma = `${singular}s`): string {
  return `${entero(n)} ${n === 1 ? singular : pluralForma}`;
}
