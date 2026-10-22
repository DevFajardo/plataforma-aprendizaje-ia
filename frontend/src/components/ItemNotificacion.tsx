"use client";

import Link from "next/link";
import { Icono, cx, type NombreIcono } from "@/components/ui";
import { tiempoRelativo } from "@/lib/fechas";
import type { Notificacion } from "@/lib/tipos";

const ICONO: Record<string, NombreIcono> = {
  publicado: "libro",
  repaso: "repetir",
  alerta: "alerta",
  clase_vivo: "vivo",
};

/** Fila de una notificación: con enlace navega (y se marca como leída); sin enlace solo se marca. */
export default function ItemNotificacion({ n, onAbrir }: { n: Notificacion; onAbrir: (n: Notificacion) => void }) {
  const contenido = (
    <>
      <span
        aria-hidden="true"
        className={cx(
          "mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full",
          n.tipo === "alerta" ? "bg-aviso-fondo text-aviso-texto" : "bg-info-fondo text-info-texto",
        )}
      >
        <Icono nombre={ICONO[n.tipo] ?? "info"} tamano={18} />
      </span>
      <span className="min-w-0 flex-1">
        <span className="flex items-start justify-between gap-2">
          <span className={cx("text-sm leading-snug", n.leida ? "font-semibold" : "font-bold")}>{n.titulo}</span>
          {!n.leida && (
            <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full bg-cul-naranja">
              <span className="sr-only">Sin leer</span>
            </span>
          )}
        </span>
        {n.mensaje && <span className="mt-0.5 block text-sm text-suave">{n.mensaje}</span>}
        <span className="mt-1 block text-xs text-suave">{tiempoRelativo(n.creada_en)}</span>
      </span>
    </>
  );
  const clase = cx("flex w-full items-start gap-3 px-4 py-3 text-left transition hover:bg-superficie-2", !n.leida && "bg-info-fondo/40");
  return n.enlace ? (
    <Link href={n.enlace} onClick={() => onAbrir(n)} className={clase}>
      {contenido}
    </Link>
  ) : (
    <button type="button" onClick={() => onAbrir(n)} className={clase}>
      {contenido}
    </button>
  );
}
