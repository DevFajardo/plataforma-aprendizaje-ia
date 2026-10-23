"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { cx } from "./cx";
import Icono from "./Icono";

export type TipoToast = "ok" | "error" | "info";
interface ToastDatos {
  id: number;
  tipo: TipoToast;
  texto: string;
}

interface ContextoToast {
  /** Muestra una notificación breve. Se anuncia a lectores de pantalla (aria-live). */
  avisar: (texto: string, tipo?: TipoToast) => void;
}

const Contexto = createContext<ContextoToast>({ avisar: () => {} });

/** Hook para confirmar acciones (guardado, copiado, publicado, eliminado…) con una notificación tipo «toast». */
export function useToast(): ContextoToast {
  return useContext(Contexto);
}

const ESTILO: Record<TipoToast, string> = {
  ok: "border-exito-borde bg-exito-fondo text-exito-texto",
  error: "border-error-borde bg-error-fondo text-error-texto",
  info: "border-info-borde bg-info-fondo text-info-texto",
};

function ItemToast({ toast, alCerrar }: { toast: ToastDatos; alCerrar: (id: number) => void }) {
  const pausado = useRef(false);
  useEffect(() => {
    const duracion = toast.tipo === "error" ? 8000 : 4500;
    let restante = duracion;
    let inicio = Date.now();
    const t = setInterval(() => {
      if (pausado.current) {
        inicio = Date.now();
        return;
      }
      restante -= Date.now() - inicio;
      inicio = Date.now();
      if (restante <= 0) alCerrar(toast.id);
    }, 250);
    return () => clearInterval(t);
  }, [toast.id, toast.tipo, alCerrar]);

  return (
    <li
      role={toast.tipo === "error" ? "alert" : "status"}
      onMouseEnter={() => (pausado.current = true)}
      onMouseLeave={() => (pausado.current = false)}
      onFocus={() => (pausado.current = true)}
      onBlur={() => (pausado.current = false)}
      className={cx("anim-aparecer pointer-events-auto flex items-start gap-3 rounded-xl border px-4 py-3 text-sm font-semibold shadow-lg", ESTILO[toast.tipo])}
    >
      <Icono nombre={toast.tipo === "ok" ? "check" : toast.tipo === "error" ? "alerta" : "info"} tamano={18} className="mt-0.5" />
      <span className="min-w-0 flex-1 leading-snug">{toast.texto}</span>
      <button
        type="button"
        onClick={() => alCerrar(toast.id)}
        aria-label="Cerrar notificación"
        className="-mr-1 -mt-1 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg hover:bg-black/10"
      >
        <Icono nombre="cerrar" tamano={16} />
      </button>
    </li>
  );
}

/** Proveedor global: contenedor accesible (aria-live) para las notificaciones. */
export function ProveedorToast({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<ToastDatos[]>([]);
  const contador = useRef(0);

  const cerrar = useCallback((id: number) => setToasts((l) => l.filter((t) => t.id !== id)), []);
  const avisar = useCallback((texto: string, tipo: TipoToast = "ok") => {
    const id = ++contador.current;
    setToasts((l) => [...l.filter((t) => t.texto !== texto).slice(-3), { id, tipo, texto }]);
  }, []);
  const valor = useMemo(() => ({ avisar }), [avisar]);

  return (
    <Contexto.Provider value={valor}>
      {children}
      <ol
        aria-label="Notificaciones"
        aria-live="polite"
        className="pointer-events-none fixed inset-x-0 bottom-0 z-[70] mx-auto flex w-full max-w-md flex-col gap-2 px-4 pb-4 sm:bottom-4 sm:left-auto sm:right-4 sm:mx-0 sm:px-0 sm:pb-0"
      >
        {toasts.map((t) => (
          <ItemToast key={t.id} toast={t} alCerrar={cerrar} />
        ))}
      </ol>
    </Contexto.Provider>
  );
}
