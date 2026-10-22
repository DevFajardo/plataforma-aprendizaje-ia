import type { Semaforo } from "@/lib/tipos";
import { BarraPorcentaje, Insignia, type TonoBarra } from "./ui";

export const pct = (v: number | null) => (v === null ? "—" : `${String(v).replace(".", ",")}%`);

const TONO: Record<Semaforo, TonoBarra> = { verde: "exito", amarillo: "aviso", rojo: "error", sin_datos: "primario" };
const TEXTO: Record<Semaforo, string> = { verde: "Logrado", amarillo: "En desarrollo", rojo: "Crítico", sin_datos: "Sin datos" };
const TONO_INSIGNIA = { verde: "exito", amarillo: "aviso", rojo: "error", sin_datos: "neutro" } as const;

/** Etiqueta del semáforo: el estado va siempre en texto, no solo en color. */
export function InsigniaSemaforo({ semaforo }: { semaforo: Semaforo }) {
  return <Insignia tono={TONO_INSIGNIA[semaforo]}>{TEXTO[semaforo]}</Insignia>;
}

/** Barra de logro con su porcentaje y estado. */
export function FilaLogro({ etiqueta, logro, semaforo, detalle }: { etiqueta: string; logro: number | null; semaforo: Semaforo; detalle?: string }) {
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="min-w-0 text-sm font-semibold">{etiqueta}</span>
        <span className="flex items-center gap-2">
          <span className="text-sm font-bold tabular-nums">{pct(logro)}</span>
          <InsigniaSemaforo semaforo={semaforo} />
        </span>
      </div>
      <BarraPorcentaje valor={logro ?? 0} etiqueta={`Logro de ${etiqueta}`} tono={TONO[semaforo]} />
      {detalle && <span className="text-xs text-suave">{detalle}</span>}
    </div>
  );
}
