import type { ElementType, HTMLAttributes, ReactNode } from "react";
import { cx } from "./cx";

interface Props extends HTMLAttributes<HTMLElement> {
  as?: ElementType;
  /** Quita el relleno interior (útil para tablas o imágenes a sangre). */
  sinRelleno?: boolean;
  /** Efecto de elevación al pasar el mouse (tarjetas clicables). */
  interactiva?: boolean;
  children: ReactNode;
}

/** Contenedor con borde, fondo de superficie y sombra suave. */
export default function Tarjeta({ as: Etiqueta = "div", sinRelleno, interactiva, className, children, ...resto }: Props) {
  return (
    <Etiqueta
      className={cx(
        "min-w-0 rounded-2xl border border-borde bg-superficie shadow-tarjeta",
        !sinRelleno && "p-4 sm:p-6",
        interactiva && "transition duration-200 hover:-translate-y-0.5 hover:border-borde-fuerte",
        className,
      )}
      {...resto}
    >
      {children}
    </Etiqueta>
  );
}
