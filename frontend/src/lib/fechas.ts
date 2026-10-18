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
