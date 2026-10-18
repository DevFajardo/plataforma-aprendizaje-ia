import type { ReactNode } from "react";
import Icono, { type NombreIcono } from "./Icono";

/** Mensaje amigable cuando no hay datos, con un llamado a la acción opcional. */
export default function EstadoVacio({
  titulo,
  children,
  icono = "libro",
  accion,
}: {
  titulo: string;
  children?: ReactNode;
  icono?: NombreIcono;
  accion?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-borde-fuerte bg-superficie px-5 py-8 text-center sm:py-10">
      <span className="flex h-12 w-12 items-center justify-center rounded-full bg-info-fondo text-info-texto">
        <Icono nombre={icono} tamano={24} />
      </span>
      <p className="text-lg font-bold">{titulo}</p>
      {children && <div className="max-w-md text-sm text-suave">{children}</div>}
      {accion}
    </div>
  );
}
