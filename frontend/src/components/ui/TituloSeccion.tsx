import type { ReactNode } from "react";
import { cx } from "./cx";

/** Título de sección con barra naranja de marca. */
export default function TituloSeccion({ children, nivel = 2, visual, className }: { children: ReactNode; nivel?: 2 | 3; /** Tamaño visual si difiere del nivel semántico. */ visual?: 2 | 3; className?: string }) {
  const Etiqueta = nivel === 2 ? "h2" : "h3";
  return (
    <Etiqueta className={cx("flex items-center gap-3 font-bold tracking-tight", (visual ?? nivel) === 2 ? "text-xl" : "text-lg", className)}>
      <span aria-hidden="true" className="h-6 w-1.5 shrink-0 rounded-full bg-cul-naranja" />
      <span className="min-w-0">{children}</span>
    </Etiqueta>
  );
}
