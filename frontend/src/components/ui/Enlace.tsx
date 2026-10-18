import Link from "next/link";
import type { ComponentProps } from "react";
import { cx } from "./cx";

/** Clase de un enlace de texto: color de enlace, subrayado y área de toque cómoda. */
export const CLASE_ENLACE = "font-semibold text-enlace underline underline-offset-2 transition hover:no-underline";

/** Enlace de texto (Link de Next) con el estilo de la plataforma. */
export default function Enlace({ className, ...resto }: ComponentProps<typeof Link>) {
  return <Link className={cx(CLASE_ENLACE, className)} {...resto} />;
}
