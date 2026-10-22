// El backend entrega las fechas en ISO 8601 con zona (UTC, "Z"); aquí se muestran en la hora local del navegador.

const FORMATOS = {
  corta: new Intl.DateTimeFormat("es-CO", { day: "2-digit", month: "short", year: "numeric" }),
  larga: new Intl.DateTimeFormat("es-CO", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }),
};

/** Formatea una fecha ISO en hora local. `corta` = solo fecha; `larga` = fecha y hora. */
export function formatearFecha(iso: string, estilo: keyof typeof FORMATOS = "larga"): string {
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return "—";
  return FORMATOS[estilo].format(fecha);
}

const RELATIVO = new Intl.RelativeTimeFormat("es-CO", { numeric: "auto" });

/** «hace 5 minutos», «ayer»… para fechas recientes; para las antiguas, la fecha corta. */
export function tiempoRelativo(iso: string): string {
  const fecha = new Date(iso).getTime();
  if (Number.isNaN(fecha)) return "—";
  const seg = Math.round((fecha - Date.now()) / 1000);
  const abs = Math.abs(seg);
  if (abs < 60) return "hace un momento";
  if (abs < 3600) return RELATIVO.format(Math.round(seg / 60), "minute");
  if (abs < 86400) return RELATIVO.format(Math.round(seg / 3600), "hour");
  if (abs < 7 * 86400) return RELATIVO.format(Math.round(seg / 86400), "day");
  return formatearFecha(iso, "corta");
}
