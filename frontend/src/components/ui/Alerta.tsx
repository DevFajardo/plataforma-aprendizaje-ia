"use client";

import type { ReactNode } from "react";
import { cx } from "./cx";
import Boton from "./Boton";
import Icono, { type NombreIcono } from "./Icono";

export type TipoAlerta = "info" | "exito" | "advertencia" | "error";

const ESTILO: Record<TipoAlerta, { clase: string; icono: NombreIcono }> = {
  info: { clase: "border-info-borde bg-info-fondo text-info-texto", icono: "info" },
  exito: { clase: "border-exito-borde bg-exito-fondo text-exito-texto", icono: "check" },
  advertencia: { clase: "border-aviso-borde bg-aviso-fondo text-aviso-texto", icono: "alerta" },
  error: { clase: "border-error-borde bg-error-fondo text-error-texto", icono: "alerta" },
};

interface Props {
  tipo?: TipoAlerta;
  titulo?: string;
  children: ReactNode;
  /** Botones o enlaces a la derecha (o debajo en móvil). */
  acciones?: ReactNode;
  className?: string;
  /** Muestra un botón «Reintentar»: `true` recarga la página; una función se ejecuta al pulsarlo. */
  reintentar?: boolean | (() => void);
}

/** Mensaje destacado. Los errores usan role="alert"; el resto, role="status". */
export default function Alerta({ tipo = "info", titulo, children, acciones, className, reintentar }: Props) {
  const { clase, icono } = ESTILO[tipo];
  return (
    <div
      role={tipo === "error" ? "alert" : "status"}
      className={cx("flex flex-col gap-3 rounded-xl border p-4 text-sm sm:flex-row sm:items-center sm:justify-between", clase, className)}
    >
      <div className="flex min-w-0 items-start gap-3">
        <Icono nombre={icono} className="mt-0.5" />
        <div className="min-w-0">
          {titulo && <p className="font-bold">{titulo}</p>}
          <div className="leading-relaxed">{children}</div>
        </div>
      </div>
      {(acciones || reintentar) && (
        <div className="flex shrink-0 flex-wrap gap-2">
          {acciones}
          {reintentar && (
            <Boton tamano="sm" variante="secundario" onClick={() => (typeof reintentar === "function" ? reintentar() : window.location.reload())}>
              Reintentar
            </Boton>
          )}
        </div>
      )}
    </div>
  );
}
