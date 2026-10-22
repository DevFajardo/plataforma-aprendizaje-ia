"use client";

import { useEffect, useState } from "react";
import { descargarCsvVivo, historialClaseVivo } from "@/lib/api";
import { formatearFecha } from "@/lib/fechas";
import type { HistorialVivo as Historial } from "@/lib/tipos";
import { Alerta, BarraPorcentaje, Boton, EsqueletoPagina, EstadoVacio, Icono, Insignia, Tarjeta, type TonoBarra } from "./ui";

function tono(p: number): TonoBarra {
  if (p < 60) return "error";
  if (p < 80) return "aviso";
  return "exito";
}

/** Pestaña «Sesiones en vivo»: historial de clases en vivo del cuestionario con descarga en CSV. */
export default function HistorialVivo({ cuestionarioId }: { cuestionarioId: number }) {
  const [sesiones, setSesiones] = useState<Historial[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [descargando, setDescargando] = useState(false);

  useEffect(() => {
    historialClaseVivo(cuestionarioId)
      .then(setSesiones)
      .catch((e) => setError(e instanceof Error ? e.message : "No se pudo cargar el historial."));
  }, [cuestionarioId]);

  async function csv() {
    setError(null);
    setDescargando(true);
    try {
      await descargarCsvVivo(cuestionarioId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo descargar el archivo.");
    } finally {
      setDescargando(false);
    }
  }

  if (error && !sesiones) return <Alerta tipo="error">{error}</Alerta>;
  if (!sesiones) return <EsqueletoPagina tarjetas={1} />;
  if (sesiones.length === 0) {
    return (
      <EstadoVacio icono="vivo" titulo="Aún no has hecho clases en vivo con este cuestionario">
        Usa «Iniciar clase en vivo» en el panel del docente. Aquí quedará el historial con la participación y el acierto por pregunta.
      </EstadoVacio>
    );
  }

  return (
    <div className="flex flex-col gap-5">
      {error && <Alerta tipo="error">{error}</Alerta>}
      <div className="flex justify-end">
        <Boton onClick={csv} cargando={descargando}>
          <Icono nombre="descargar" /> Descargar CSV de sesiones
        </Boton>
      </div>
      {sesiones.map((s) => (
        <Tarjeta key={s.id} as="section" aria-label={`Sesión del ${formatearFecha(s.creada_en)}`}>
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h3 className="text-lg font-bold">{formatearFecha(s.creada_en)}</h3>
              <p className="text-sm text-suave">PIN {s.pin}</p>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Insignia tono={s.estado === "finalizada" ? "neutro" : "aviso"}>{s.estado === "finalizada" ? "Finalizada" : "En curso"}</Insignia>
              <Insignia tono="azul">
                {s.participantes} {s.participantes === 1 ? "participante" : "participantes"}
              </Insignia>
              <Insignia tono={s.promedio_acierto === null ? "neutro" : s.promedio_acierto >= 60 ? "exito" : "error"}>
                Acierto promedio: {s.promedio_acierto === null ? "—" : `${s.promedio_acierto}%`}
              </Insignia>
            </div>
          </div>
          <ul className="mt-4 flex flex-col gap-4">
            {s.preguntas.map((p) => (
              <li key={p.pregunta_id}>
                <p className="mb-1.5 text-sm font-semibold">
                  {p.orden + 1}. {p.enunciado}
                </p>
                {p.porcentaje_acierto === null ? (
                  <p className="text-xs text-suave">
                    {p.tipo === "abierta" ? "Pregunta abierta (no puntúa)" : "Sin respuestas"} · {p.respuestas} respuestas
                  </p>
                ) : (
                  <>
                    <div className="flex items-center gap-3">
                      <BarraPorcentaje valor={p.porcentaje_acierto} etiqueta={`Acierto de la pregunta ${p.orden + 1}`} tono={tono(p.porcentaje_acierto)} className="flex-1" />
                      <span className="w-12 shrink-0 text-right text-sm font-bold">{p.porcentaje_acierto}%</span>
                    </div>
                    <p className="mt-1 text-xs text-suave">{p.respuestas} respuestas</p>
                  </>
                )}
              </li>
            ))}
          </ul>
        </Tarjeta>
      ))}
    </div>
  );
}
