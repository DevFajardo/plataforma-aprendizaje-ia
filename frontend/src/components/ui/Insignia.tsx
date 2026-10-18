import type { ReactNode } from "react";
import { cx } from "./cx";

export type TonoInsignia = "neutro" | "azul" | "exito" | "aviso" | "error" | "acento";

const TONOS: Record<TonoInsignia, string> = {
  neutro: "bg-superficie-2 text-texto border-borde",
  azul: "bg-info-fondo text-info-texto border-info-borde",
  exito: "bg-exito-fondo text-exito-texto border-exito-borde",
  aviso: "bg-aviso-fondo text-aviso-texto border-aviso-borde",
  error: "bg-error-fondo text-error-texto border-error-borde",
  // Acento de marca: amarillo institucional con texto marino oscuro (contraste 8,3:1)
  acento: "bg-cul-amarillo text-cul-azul-oscuro border-cul-naranja",
};

/** Etiqueta corta de estado. El significado siempre va en el texto, no solo en el color. */
export default function Insignia({ tono = "neutro", children, className }: { tono?: TonoInsignia; children: ReactNode; className?: string }) {
  return (
    <span className={cx("inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold", TONOS[tono], className)}>
      {children}
    </span>
  );
}
