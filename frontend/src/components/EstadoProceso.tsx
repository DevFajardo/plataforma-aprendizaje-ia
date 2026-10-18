import type { EstadoTarea } from "@/lib/tipos";
import { Icono, Spinner, cx } from "./ui";

const TEXTOS: Partial<Record<EstadoTarea, string>> = {
  pendiente: "Preparando la solicitud…",
  transcribiendo: "Obteniendo transcripción…",
  generando: "Generando resumen y cuestionario con IA…",
};

const PASOS: { estado: EstadoTarea; texto: string }[] = [
  { estado: "pendiente", texto: "Preparando" },
  { estado: "transcribiendo", texto: "Transcribiendo" },
  { estado: "generando", texto: "Generando" },
];

export default function EstadoProceso({ estado }: { estado: EstadoTarea }) {
  const actual = Math.max(0, PASOS.findIndex((p) => p.estado === estado));
  return (
    <div role="status" className="rounded-2xl border border-info-borde bg-info-fondo p-4 text-info-texto sm:p-5">
      <div className="flex items-center gap-3 font-semibold">
        <Spinner />
        <span>{TEXTOS[estado] ?? "Procesando…"}</span>
      </div>
      <ol className="mt-4 grid grid-cols-3 gap-2 text-center text-xs font-semibold sm:text-sm">
        {PASOS.map((p, i) => {
          const hecho = i < actual;
          const enCurso = i === actual;
          return (
            <li key={p.estado} className="flex flex-col items-center gap-1.5">
              <span
                className={cx(
                  "flex h-8 w-8 items-center justify-center rounded-full border-2 text-sm",
                  hecho && "border-exito-solido bg-exito-solido text-white",
                  enCurso && "border-info-texto bg-superficie text-info-texto",
                  !hecho && !enCurso && "border-info-borde text-info-texto/70",
                )}
              >
                {hecho ? <Icono nombre="check" tamano={16} /> : i + 1}
              </span>
              <span className={cx(!hecho && !enCurso && "opacity-75")}>
                {p.texto}
                {hecho && <span className="sr-only"> (completado)</span>}
                {enCurso && <span className="sr-only"> (en curso)</span>}
              </span>
            </li>
          );
        })}
      </ol>
      <p className="mt-4 text-xs opacity-90">Esto puede tardar uno o dos minutos según la duración del video. Puedes dejar esta pestaña abierta.</p>
    </div>
  );
}
