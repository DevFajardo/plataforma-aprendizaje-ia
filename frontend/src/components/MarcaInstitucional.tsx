"use client";

import { createContext, useContext, type ReactNode } from "react";
import { cx } from "./ui/cx";

/**
 * El layout (servidor) comprueba si existe `public/logo-cul.png` y lo informa aquí,
 * para no pedir una imagen inexistente (evita errores 404 en la consola).
 */
const ContextoLogo = createContext(false);

export function ProveedorLogo({ hayLogo, children }: { hayLogo: boolean; children: ReactNode }) {
  return <ContextoLogo.Provider value={hayLogo}>{children}</ContextoLogo.Provider>;
}

export const NOMBRE_PROGRAMA = "Ingeniería de Sistemas y Computación";

type Variante = "barra" | "panel" | "pie";

interface Props {
  variante?: Variante;
  /** Nombre de la aplicación que acompaña a la marca (en la barra superior). */
  titulo?: string;
  className?: string;
  /** Clases extra para el subtítulo (p. ej. ocultarlo en anchos donde la barra de navegación está llena). */
  subtituloClase?: string;
}

/**
 * Marca institucional. Si existe `public/logo-cul.png` lo muestra sobre una placa blanca;
 * si no, usa un monograma neutro de texto («CUL»). No reproduce el escudo oficial.
 */
export default function MarcaInstitucional({ variante = "barra", titulo, className, subtituloClase }: Props) {
  const hayLogo = useContext(ContextoLogo);
  const grande = variante === "panel";
  const sobreOscuro = variante !== "pie";

  const placa = hayLogo ? (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src="/logo-cul.png"
      alt="Logo de la Corporación Universitaria Latinoamericana"
      className={cx("w-auto rounded-md bg-white object-contain p-1", grande ? "h-14" : "h-10")}
    />
  ) : (
    <span
      aria-hidden="true"
      className={cx(
        "flex shrink-0 items-center justify-center rounded-md border-b-[3px] border-cul-naranja bg-white font-extrabold tracking-wide text-cul-azul",
        grande ? "h-14 w-14 text-lg" : "h-10 w-10 text-sm",
      )}
    >
      CUL
    </span>
  );

  return (
    <span className={cx("flex min-w-0 items-center gap-3", className)}>
      {placa}
      <span className="flex min-w-0 flex-col leading-tight">
        <span className={cx("truncate font-bold", grande ? "text-lg" : "text-sm sm:text-base", sobreOscuro ? "text-white" : "text-texto")}>
          {titulo ?? "Corporación Universitaria Latinoamericana"}
        </span>
        <span className={cx("truncate text-[11px] sm:text-xs", sobreOscuro ? "text-white/85" : "text-suave", subtituloClase)}>{NOMBRE_PROGRAMA}</span>
      </span>
    </span>
  );
}
