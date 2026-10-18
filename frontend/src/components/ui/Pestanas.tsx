"use client";

import { useId, useRef, type KeyboardEvent, type ReactNode } from "react";
import { cx } from "./cx";

interface Item<T extends string> {
  id: T;
  texto: string;
}

interface Props<T extends string> {
  etiqueta: string;
  items: readonly Item<T>[];
  activa: T;
  onCambiar: (id: T) => void;
  /** Contenido del panel de la pestaña activa. */
  children: ReactNode;
}

/** Pestañas accesibles (patrón WAI-ARIA): flechas, Inicio y Fin cambian de pestaña. */
export default function Pestanas<T extends string>({ etiqueta, items, activa, onCambiar, children }: Props<T>) {
  const base = useId();
  const refs = useRef<(HTMLButtonElement | null)[]>([]);

  function alTeclear(e: KeyboardEvent, indice: number) {
    let destino = -1;
    if (e.key === "ArrowRight") destino = (indice + 1) % items.length;
    else if (e.key === "ArrowLeft") destino = (indice - 1 + items.length) % items.length;
    else if (e.key === "Home") destino = 0;
    else if (e.key === "End") destino = items.length - 1;
    if (destino < 0) return;
    e.preventDefault();
    onCambiar(items[destino].id);
    refs.current[destino]?.focus();
  }

  return (
    <div>
      <div
        role="tablist"
        aria-label={etiqueta}
        className="mb-5 grid gap-1 rounded-xl border border-borde bg-superficie-2 p-1 sm:grid-flow-col sm:auto-cols-fr"
      >
        {items.map((it, i) => {
          const seleccionada = it.id === activa;
          return (
            <button
              key={it.id}
              ref={(el) => {
                refs.current[i] = el;
              }}
              type="button"
              role="tab"
              id={`${base}-t-${it.id}`}
              aria-selected={seleccionada}
              aria-controls={`${base}-p`}
              tabIndex={seleccionada ? 0 : -1}
              onClick={() => onCambiar(it.id)}
              onKeyDown={(e) => alTeclear(e, i)}
              className={cx(
                "min-h-11 rounded-lg px-4 py-2 text-sm font-semibold transition duration-150",
                seleccionada
                  ? "bg-superficie text-enlace shadow-tarjeta ring-1 ring-borde"
                  : "text-suave hover:bg-superficie/60 hover:text-texto",
              )}
            >
              {it.texto}
            </button>
          );
        })}
      </div>
      <div role="tabpanel" id={`${base}-p`} aria-labelledby={`${base}-t-${activa}`}>
        {children}
      </div>
    </div>
  );
}
