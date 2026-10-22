"use client";

import { cx } from "@/components/ui";
import type { PuestoVivo } from "@/lib/tipos";

/** Cuatro opciones con color, forma y letra distintos: la información nunca depende solo del color. */
export const ESTILOS_OPCION = [
  { letra: "A", forma: "triangulo", fondo: "bg-[#c93a2e] text-white", barra: "bg-[#e5564a]" },
  { letra: "B", forma: "rombo", fondo: "bg-[#1b5fb4] text-white", barra: "bg-[#4a8fe0]" },
  { letra: "C", forma: "circulo", fondo: "bg-cul-amarillo text-cul-azul-oscuro", barra: "bg-cul-amarillo" },
  { letra: "D", forma: "cuadrado", fondo: "bg-[#1e8a4c] text-white", barra: "bg-[#3fb56e]" },
] as const;

export function estiloOpcion(i: number) {
  return ESTILOS_OPCION[i % ESTILOS_OPCION.length];
}

export function Forma({ forma, tamano = 28, className }: { forma: string; tamano?: number; className?: string }) {
  return (
    <svg width={tamano} height={tamano} viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" className={cx("shrink-0", className)}>
      {forma === "triangulo" && <path d="M12 3l10 18H2L12 3z" />}
      {forma === "rombo" && <path d="M12 2l10 10-10 10L2 12 12 2z" />}
      {forma === "circulo" && <circle cx="12" cy="12" r="10" />}
      {forma === "cuadrado" && <rect x="3" y="3" width="18" height="18" rx="2" />}
    </svg>
  );
}

/** Temporizador circular. Cambia de color y muestra los segundos restantes en el centro. */
export function AroTemporizador({ restanteMs, totalMs, tamano = 120 }: { restanteMs: number; totalMs: number; tamano?: number }) {
  const r = 52;
  const circunferencia = 2 * Math.PI * r;
  const fraccion = totalMs > 0 ? Math.min(1, Math.max(0, restanteMs / totalMs)) : 0;
  const segundos = Math.ceil(restanteMs / 1000);
  const color = segundos <= 5 ? "#ff7a66" : segundos <= 10 ? "#ffe24b" : "#e88a37";
  return (
    <div
      role="timer"
      aria-label={`${segundos} segundos restantes`}
      className="relative shrink-0"
      style={{ width: tamano, height: tamano }}
    >
      <svg viewBox="0 0 120 120" width={tamano} height={tamano} className="-rotate-90" aria-hidden="true">
        <circle cx="60" cy="60" r={r} fill="none" stroke="currentColor" strokeOpacity="0.2" strokeWidth="10" />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circunferencia}
          strokeDashoffset={circunferencia * (1 - fraccion)}
          style={{ transition: "stroke-dashoffset 0.15s linear, stroke 0.3s" }}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-4xl font-extrabold tabular-nums" aria-hidden="true">
        {segundos}
      </span>
    </div>
  );
}

const MEDALLAS = ["#f6b70b", "#c7d0df", "#cd8a52"];

/** Podio animado: 1.º al centro, 2.º a la izquierda y 3.º a la derecha. Si hay menos de 3, se adapta. */
export function Podio({ ranking, grande = false, resaltar }: { ranking: PuestoVivo[]; grande?: boolean; resaltar?: string }) {
  const top = ranking.slice(0, 3);
  // Orden visual: 2.º, 1.º, 3.º
  const orden = [top[1], top[0], top[2]].map((p, i) => (p ? { p, puesto: [2, 1, 3][i] } : null)).filter(Boolean) as { p: PuestoVivo; puesto: number }[];
  const altura = (puesto: number) => (puesto === 1 ? (grande ? "h-72" : "h-32") : puesto === 2 ? (grande ? "h-52" : "h-24") : grande ? "h-36" : "h-16");
  const retraso = (puesto: number) => (puesto === 3 ? "0s" : puesto === 2 ? "0.5s" : "1s");
  return (
    <ol className={cx("mx-auto flex w-full items-end justify-center gap-2 sm:gap-4", grande && "max-w-5xl")} aria-label="Podio">
      {orden.map(({ p, puesto }) => (
        <li key={p.apodo} className={cx("flex w-1/3 min-w-0 flex-col items-center", grande ? "max-w-80" : "max-w-52")}>
          <span
            className={cx("anim-rebote mb-2 max-w-full break-words px-1 text-center font-extrabold leading-tight", !grande && "truncate", grande ? "text-2xl sm:text-4xl" : "text-base sm:text-lg", resaltar === p.apodo && "underline decoration-cul-naranja decoration-4 underline-offset-4")}
            style={{ animationDelay: `calc(${retraso(puesto)} + 0.6s)` }}
          >
            {p.apodo}
          </span>
          <div
            className={cx("anim-podio flex w-full flex-col items-center justify-start rounded-t-xl pt-2 text-cul-azul-oscuro", altura(puesto))}
            style={{ backgroundColor: MEDALLAS[puesto - 1], animationDelay: retraso(puesto) }}
          >
            <span className={cx("font-extrabold", grande ? "text-7xl" : "text-3xl")}>{puesto}</span>
            <span className={cx("font-bold tabular-nums", grande ? "text-2xl sm:text-4xl" : "text-sm")}>{p.puntos}</span>
          </div>
        </li>
      ))}
    </ol>
  );
}
