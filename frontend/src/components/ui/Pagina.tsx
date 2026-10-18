import type { ReactNode } from "react";
import { cx } from "./cx";

const ANCHOS = {
  sm: "max-w-md",
  md: "max-w-2xl",
  lg: "max-w-4xl",
  xl: "max-w-6xl",
  completo: "max-w-7xl",
} as const;

/** Contenedor principal de cada página: ancho máximo, márgenes responsivos y ancla para «saltar al contenido». */
export default function Pagina({ ancho = "xl", children, className }: { ancho?: keyof typeof ANCHOS; children: ReactNode; className?: string }) {
  return (
    <main
      id="contenido"
      tabIndex={-1}
      className={cx("mx-auto w-full flex-1 px-4 py-6 outline-none sm:px-6 sm:py-10 lg:px-8", ANCHOS[ancho], className)}
    >
      {children}
    </main>
  );
}
