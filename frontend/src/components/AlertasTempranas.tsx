"use client";

import { useCallback, useEffect, useState } from "react";
import { atenderAlerta, listarAlertas } from "@/lib/api";
import type { Alerta as AlertaTemprana } from "@/lib/tipos";
import { Alerta, Boton, EstadoVacio, Esqueleto, Insignia, Input, TituloSeccion, cx } from "./ui";

/** Lista de alertas tempranas (explicables) con la acción «Marcar como atendida» y una nota. */
export default function AlertasTempranas() {
  const [alertas, setAlertas] = useState<AlertaTemprana[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [abierta, setAbierta] = useState<string | null>(null);
  const [nota, setNota] = useState("");
  const [guardando, setGuardando] = useState(false);

  const cargar = useCallback(() => {
    listarAlertas()
      .then(setAlertas)
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
  }, []);

  useEffect(cargar, [cargar]);

  async function atender(a: AlertaTemprana) {
    setGuardando(true);
    setError(null);
    try {
      await atenderAlerta(a.grupo_id, a.estudiante_id, nota);
      setAbierta(null);
      setNota("");
      cargar();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <section aria-label="Alertas tempranas" className="flex flex-col gap-4">
      <div>
        <TituloSeccion>Alertas tempranas</TituloSeccion>
        <p className="mt-1 text-sm text-suave">
          Se calculan con reglas simples: 14 días o más sin actividad, promedio inicial menor a 60 %, 2 o más repasos vencidos, o una caída de 20 puntos
          entre los últimos intentos. Con 2 o más motivos el nivel es alto.
        </p>
      </div>
      {error && <Alerta tipo="error">{error}</Alerta>}
      {alertas === null && !error && <Esqueleto className="h-24" />}
      {alertas?.length === 0 && (
        <EstadoVacio icono="check" titulo="Sin alertas pendientes">
          Ningún estudiante matriculado presenta señales de riesgo en este momento.
        </EstadoVacio>
      )}
      <ul className="flex flex-col gap-3">
        {alertas?.map((a) => {
          const clave = `${a.grupo_id}-${a.estudiante_id}`;
          return (
            <li
              key={clave}
              className={cx(
                "flex min-w-0 flex-col gap-3 rounded-2xl border border-borde border-l-[6px] bg-superficie p-4 shadow-tarjeta",
                a.nivel === "alto" ? "border-l-error-solido" : "border-l-aviso-solido",
              )}
            >
              <div className="flex flex-wrap items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="break-words font-bold">{a.nombre}</p>
                  <p className="break-all text-xs text-suave">{a.email}</p>
                  <p className="text-xs text-suave">
                    {a.asignatura} · {a.grupo}
                  </p>
                </div>
                <Insignia tono={a.nivel === "alto" ? "error" : "aviso"}>Nivel {a.nivel}</Insignia>
              </div>
              <ul className="list-disc space-y-1 pl-5 text-sm">
                {a.motivos.map((m) => (
                  <li key={m.codigo}>{m.texto}</li>
                ))}
              </ul>
              {abierta === clave ? (
                <div className="flex flex-col gap-3 rounded-xl bg-superficie-2 p-3">
                  <Input etiqueta="Nota de seguimiento (opcional)" value={nota} onChange={(e) => setNota(e.target.value)} maxLength={1000} placeholder="Ej.: Se habló con el estudiante, acordamos tutoría." />
                  <div className="flex flex-col gap-2 sm:flex-row">
                    <Boton cargando={guardando} onClick={() => atender(a)}>
                      Confirmar atención
                    </Boton>
                    <Boton variante="secundario" disabled={guardando} onClick={() => setAbierta(null)}>
                      Cancelar
                    </Boton>
                  </div>
                </div>
              ) : (
                <Boton
                  variante="secundario"
                  className="self-start"
                  onClick={() => {
                    setAbierta(clave);
                    setNota("");
                  }}
                >
                  Marcar como atendida
                </Boton>
              )}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
