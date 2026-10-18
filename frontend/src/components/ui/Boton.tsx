import Link from "next/link";
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { cx } from "./cx";
import Spinner from "./Spinner";

export type VarianteBoton = "primario" | "secundario" | "fantasma" | "peligro" | "peligroSuave";
export type TamanoBoton = "sm" | "md" | "lg";

const BASE =
  "inline-flex items-center justify-center gap-2 rounded-lg border font-semibold leading-tight transition " +
  "duration-150 active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-55 disabled:active:scale-100";

const VARIANTES: Record<VarianteBoton, string> = {
  primario: "border-transparent bg-primario text-sobre-primario shadow-sm hover:bg-primario-hover",
  secundario: "border-borde-fuerte bg-superficie text-texto hover:bg-superficie-2",
  fantasma: "border-transparent bg-transparent text-enlace hover:bg-superficie-2",
  peligro: "border-transparent bg-error-boton text-white shadow-sm hover:brightness-90",
  peligroSuave: "border-error-borde bg-error-fondo text-error-texto hover:brightness-95 dark:hover:brightness-110",
};

const TAMANOS: Record<TamanoBoton, string> = {
  sm: "min-h-10 px-3.5 py-2 text-sm",
  md: "min-h-11 px-5 py-2.5 text-sm",
  lg: "min-h-12 px-6 py-3 text-base",
};

/** Clases de un botón, reutilizables en enlaces. */
export function claseBoton(variante: VarianteBoton = "primario", tamano: TamanoBoton = "md", bloque = false, extra?: string) {
  return cx(BASE, VARIANTES[variante], TAMANOS[tamano], bloque && "w-full", extra);
}

interface PropsComunes {
  variante?: VarianteBoton;
  tamano?: TamanoBoton;
  bloque?: boolean;
  children: ReactNode;
  className?: string;
}

interface PropsBoton extends PropsComunes, Omit<ButtonHTMLAttributes<HTMLButtonElement>, "className" | "children"> {
  cargando?: boolean;
}

/** Botón. `cargando` lo deshabilita y muestra un spinner. */
export default function Boton({
  variante = "primario",
  tamano = "md",
  bloque = false,
  className,
  children,
  cargando,
  disabled,
  type = "button",
  ...resto
}: PropsBoton) {
  return (
    <button
      type={type}
      disabled={disabled || cargando}
      aria-busy={cargando || undefined}
      className={claseBoton(variante, tamano, bloque, className)}
      {...resto}
    >
      {cargando && <Spinner tamano={16} />}
      {children}
    </button>
  );
}

interface PropsEnlace extends PropsComunes {
  href: string;
  target?: string;
  onClick?: () => void;
}

/** Enlace de Next con el aspecto de un botón. */
export function BotonEnlace({ href, target, onClick, variante = "primario", tamano = "md", bloque = false, className, children }: PropsEnlace) {
  return (
    <Link href={href} target={target} onClick={onClick} className={claseBoton(variante, tamano, bloque, className)}>
      {children}
    </Link>
  );
}
