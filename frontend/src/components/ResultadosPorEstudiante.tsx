"use client";

import { Fragment, useEffect, useMemo, useState } from "react";
import { obtenerDetalleIntento } from "@/lib/api";
import { formatearFecha } from "@/lib/fechas";
import { pct, plural } from "@/lib/formato";
import type { IntentoDetalle, IntentoResultado } from "@/lib/tipos";
import { Alerta, Boton, Icono, Insignia, Spinner, Tarjeta } from "./ui";

interface Estudiante {
  email: string;
  nombre: string;
  intentos: IntentoResultado[]; // en orden cronológico
  primero: number;
  ultimo: number;
  mejor: number;
}

const etiquetaTipo = (t: string) => (t === "practica" ? "Práctica" : t.charAt(0).toUpperCase() + t.slice(1));

function agrupar(intentos: IntentoResultado[]): Estudiante[] {
  const mapa = new Map<string, IntentoResultado[]>();
  for (const i of intentos) mapa.set(i.email, [...(mapa.get(i.email) ?? []), i]);
  return [...mapa.entries()]
    .map(([email, lista]) => {
      const orden = [...lista].sort((a, b) => a.fecha.localeCompare(b.fecha) || a.intento_id - b.intento_id);
      return {
        email,
        nombre: orden[0].nombre,
        intentos: orden,
        primero: orden[0].porcentaje,
        ultimo: orden[orden.length - 1].porcentaje,
        mejor: Math.max(...orden.map((x) => x.porcentaje)),
      };
    })
    .sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));
}

function DetalleIntento({ cuestionarioId, intentoId }: { cuestionarioId: number; intentoId: number }) {
  const [res, setRes] = useState<{ id: number; datos?: IntentoDetalle; error?: string } | null>(null);

  useEffect(() => {
    let activo = true;
    obtenerDetalleIntento(cuestionarioId, intentoId)
      .then((datos) => activo && setRes({ id: intentoId, datos }))
      .catch((e) => activo && setRes({ id: intentoId, error: e instanceof Error ? e.message : "Error desconocido" }));
    return () => {
      activo = false;
    };
  }, [cuestionarioId, intentoId]);

  if (!res || res.id !== intentoId) {
    return (
      <p className="flex items-center gap-2 text-sm text-suave" role="status">
        <Spinner /> Cargando respuestas…
      </p>
    );
  }
  if (res.error || !res.datos) return <Alerta tipo="error">{res.error}</Alerta>;

  return (
    <ol className="flex flex-col gap-3">
      {res.datos.preguntas.map((p, i) => (
        <li key={p.pregunta_id} className="rounded-lg border border-borde bg-superficie p-3 text-sm">
          <p className="flex items-start justify-between gap-3 font-bold">
            <span className="min-w-0 flex-1">
              {i + 1}. {p.enunciado}
            </span>
            {p.correcta === true && (
              <Insignia tono="exito" className="shrink-0">
                <Icono nombre="check" tamano={12} /> Correcta
              </Insignia>
            )}
            {p.correcta === false && (
              <Insignia tono="error" className="shrink-0">
                <Icono nombre="x" tamano={12} /> Incorrecta
              </Insignia>
            )}
            {p.tipo === "abierta" && <Insignia tono="azul" className="shrink-0">Abierta</Insignia>}
          </p>
          <p className="mt-2 break-words">
            <strong>Respondió:</strong> {p.respuesta || <em>(sin respuesta)</em>}
          </p>
          {p.tipo !== "abierta" ? (
            <p className="mt-1 break-words">
              <strong>Respuesta correcta:</strong> {p.respuesta_correcta}
            </p>
          ) : (
            <div className="mt-2 flex flex-col gap-1 rounded-lg bg-superficie-2 p-2.5">
              {p.respuesta_correcta && (
                <p className="break-words text-suave">
                  <strong>Respuesta de referencia:</strong> {p.respuesta_correcta}
                </p>
              )}
              <p>
                <strong>Nota sugerida por la IA:</strong> {p.sugerida ? `${p.sugerida.puntaje}/100` : "sin sugerencia"}
                {p.sugerida?.retroalimentacion && <span className="text-suave"> — {p.sugerida.retroalimentacion}</span>}
              </p>
              <p>
                <strong>Nota del docente:</strong> {p.nota_final !== null ? `${p.nota_final}/100` : "pendiente"}
              </p>
            </div>
          )}
        </li>
      ))}
    </ol>
  );
}

function PanelEstudiante({ cuestionarioId, est }: { cuestionarioId: number; est: Estudiante }) {
  const [sel, setSel] = useState(est.intentos[est.intentos.length - 1].intento_id);
  return (
    <div className="flex flex-col gap-3">
      <div role="group" aria-label={`Intentos de ${est.nombre}`} className="flex flex-wrap gap-2">
        {est.intentos.map((i, n) => (
          <button
            key={i.intento_id}
            type="button"
            aria-pressed={sel === i.intento_id}
            onClick={() => setSel(i.intento_id)}
            className={`min-h-10 rounded-lg border px-3 text-left text-sm font-semibold transition ${
              sel === i.intento_id ? "border-cul-naranja bg-cul-naranja/15 text-texto" : "border-borde bg-superficie text-suave hover:bg-superficie-2"
            }`}
          >
            Intento {n + 1} · {pct(i.porcentaje)}
            <span className="ml-1 font-normal">
              ({etiquetaTipo(i.tipo)}, {formatearFecha(i.fecha)})
            </span>
          </button>
        ))}
      </div>
      <DetalleIntento cuestionarioId={cuestionarioId} intentoId={sel} />
    </div>
  );
}

export default function ResultadosPorEstudiante({ cuestionarioId, intentos }: { cuestionarioId: number; intentos: IntentoResultado[] }) {
  const estudiantes = useMemo(() => agrupar(intentos), [intentos]);
  const [abierto, setAbierto] = useState<string | null>(null);
  const alternar = (email: string) => setAbierto((a) => (a === email ? null : email));

  if (estudiantes.length === 0) return <Alerta tipo="info">Aún no hay estudiantes con intentos finalizados.</Alerta>;

  return (
    <section className="flex flex-col gap-4" aria-label="Resultados por estudiante">
      <p className="text-sm text-suave">
        {plural(estudiantes.length, "estudiante")}. Abre un estudiante para ver, intento por intento, qué respondió y cuál era la respuesta
        correcta. Tus pruebas como docente no aparecen aquí.
      </p>

      {/* Móvil: tarjetas */}
      <ul className="flex flex-col gap-3 md:hidden">
        {estudiantes.map((e) => {
          const abierta = abierto === e.email;
          return (
            <li key={e.email}>
              <Tarjeta className="flex flex-col gap-3 !p-4">
                <div className="min-w-0">
                  <p className="font-bold">{e.nombre}</p>
                  <p className="break-words text-xs text-suave">{e.email}</p>
                </div>
                <dl className="grid grid-cols-3 gap-2 text-center text-xs text-suave">
                  <div>
                    <dt>Primero</dt>
                    <dd className="text-base font-extrabold text-texto">{pct(e.primero)}</dd>
                  </div>
                  <div>
                    <dt>Último</dt>
                    <dd className="text-base font-extrabold text-texto">{pct(e.ultimo)}</dd>
                  </div>
                  <div>
                    <dt>Mejor</dt>
                    <dd className="text-base font-extrabold text-texto">{pct(e.mejor)}</dd>
                  </div>
                </dl>
                <p className="text-sm text-suave">{plural(e.intentos.length, "intento")}</p>
                <Boton variante="secundario" tamano="sm" aria-expanded={abierta} onClick={() => alternar(e.email)} className="self-start">
                  {abierta ? "Ocultar respuestas" : "Ver respuestas"}
                  <Icono nombre="chevron" tamano={16} className={abierta ? "rotate-180" : ""} />
                </Boton>
                {abierta && <PanelEstudiante cuestionarioId={cuestionarioId} est={e} />}
              </Tarjeta>
            </li>
          );
        })}
      </ul>

      {/* Tablet y escritorio: tabla */}
      <div tabIndex={0} role="region" aria-label="Resultados por estudiante" className="hidden overflow-x-auto rounded-2xl border border-borde bg-superficie shadow-tarjeta md:block">
        <table className="w-full text-left text-sm">
          <thead className="bg-superficie-2">
            <tr>
              <th scope="col" className="px-3 py-2.5">Estudiante</th>
              <th scope="col" className="px-3 py-2.5">Intentos</th>
              <th scope="col" className="px-3 py-2.5">Primero</th>
              <th scope="col" className="px-3 py-2.5">Último</th>
              <th scope="col" className="px-3 py-2.5">Mejor</th>
              <th scope="col" className="px-3 py-2.5">
                <span className="sr-only">Acciones</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {estudiantes.map((e) => {
              const abierta = abierto === e.email;
              return (
                <Fragment key={e.email}>
                  <tr className="border-t border-borde transition hover:bg-superficie-2/60">
                    <td className="px-3 py-2.5">
                      <p className="font-semibold">{e.nombre}</p>
                      <p className="whitespace-nowrap text-xs text-suave">{e.email}</p>
                    </td>
                    <td className="px-3 py-2.5">{e.intentos.length}</td>
                    <td className="px-3 py-2.5 font-bold">{pct(e.primero)}</td>
                    <td className="px-3 py-2.5 font-bold">{pct(e.ultimo)}</td>
                    <td className="px-3 py-2.5 font-bold">{pct(e.mejor)}</td>
                    <td className="w-px whitespace-nowrap px-3 py-2.5 text-right">
                      <Boton variante="secundario" tamano="sm" aria-expanded={abierta} onClick={() => alternar(e.email)} className="whitespace-nowrap">
                        {abierta ? "Ocultar" : "Ver respuestas"}
                        <Icono nombre="chevron" tamano={16} className={abierta ? "rotate-180" : ""} />
                      </Boton>
                    </td>
                  </tr>
                  {abierta && (
                    <tr className="border-t border-borde bg-superficie-2/40">
                      <td colSpan={6} className="px-4 py-4">
                        <PanelEstudiante cuestionarioId={cuestionarioId} est={e} />
                      </td>
                    </tr>
                  )}
                </Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
}
