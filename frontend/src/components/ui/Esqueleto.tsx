import { cx } from "./cx";

/** Bloque gris pulsante para indicar carga (la animación se desactiva con prefers-reduced-motion). */
export default function Esqueleto({ className }: { className?: string }) {
  return <div aria-hidden="true" className={cx("animate-pulse rounded-lg bg-superficie-2", className)} />;
}

/** Esqueleto genérico de una página (título + tarjetas). Anuncia «Cargando» a lectores de pantalla. */
export function EsqueletoPagina({ tarjetas = 3 }: { tarjetas?: number }) {
  return (
    <div role="status" aria-live="polite" className="flex flex-col gap-6">
      <span className="sr-only">Cargando…</span>
      <div className="flex flex-col gap-3">
        <Esqueleto className="h-8 w-2/3 max-w-sm" />
        <Esqueleto className="h-4 w-full max-w-md" />
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: tarjetas }, (_, i) => (
          <Esqueleto key={i} className="h-28 rounded-2xl" />
        ))}
      </div>
    </div>
  );
}
