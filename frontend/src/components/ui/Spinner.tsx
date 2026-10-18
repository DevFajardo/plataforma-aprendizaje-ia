import { cx } from "./cx";

/** Indicador de carga circular. Decorativo: el texto vecino debe explicar la espera. */
export default function Spinner({ className, tamano = 20 }: { className?: string; tamano?: number }) {
  return (
    <span
      aria-hidden="true"
      style={{ width: tamano, height: tamano }}
      className={cx("inline-block shrink-0 animate-spin rounded-full border-2 border-current border-t-transparent", className)}
    />
  );
}
