import { cx } from "./cx";

export type TonoBarra = "primario" | "exito" | "aviso" | "error";

const TONOS: Record<TonoBarra, string> = {
  primario: "bg-barra",
  exito: "bg-exito-solido",
  aviso: "bg-aviso-solido",
  error: "bg-error-solido",
};

interface Props {
  valor: number;
  min?: number;
  max?: number;
  etiqueta: string;
  tono?: TonoBarra;
  className?: string;
  alto?: "sm" | "md" | "lg";
}

/** Barra de progreso accesible (role="progressbar"). El valor numérico debe mostrarse como texto junto a ella. */
export default function BarraPorcentaje({ valor, min = 0, max = 100, etiqueta, tono = "primario", className, alto = "md" }: Props) {
  const pct = max === min ? 0 : Math.max(0, Math.min(100, ((valor - min) / (max - min)) * 100));
  return (
    <div
      role="progressbar"
      aria-valuenow={valor}
      aria-valuemin={min}
      aria-valuemax={max}
      aria-label={etiqueta}
      className={cx("w-full overflow-hidden rounded-full bg-pista", alto === "sm" ? "h-2" : alto === "md" ? "h-3" : "h-4", className)}
    >
      <div className={cx("h-full rounded-full transition-[width] duration-500", TONOS[tono])} style={{ width: `${pct}%` }} />
    </div>
  );
}
