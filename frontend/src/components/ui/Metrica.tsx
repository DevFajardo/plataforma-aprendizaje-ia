import Icono, { type NombreIcono } from "./Icono";
import Tarjeta from "./Tarjeta";
import { cx } from "./cx";

/** Tarjeta de métrica: icono, etiqueta y valor destacado (vertical en móvil, horizontal desde sm). */
export default function Metrica({ titulo, valor, icono, nota, className }: { titulo: string; valor: string; icono?: NombreIcono; nota?: string; className?: string }) {
  return (
    <Tarjeta className={cx("flex flex-col gap-3 !p-4 sm:flex-row sm:items-center sm:gap-4", className)}>
      {icono && (
        <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border-b-2 border-cul-naranja bg-info-fondo text-info-texto sm:h-12 sm:w-12">
          <Icono nombre={icono} tamano={22} />
        </span>
      )}
      <div className="min-w-0">
        <p className="text-sm leading-snug text-suave">{titulo}</p>
        <p className="text-2xl font-bold leading-tight sm:text-3xl">{valor}</p>
        {nota && <p className="text-xs text-suave">{nota}</p>}
      </div>
    </Tarjeta>
  );
}
