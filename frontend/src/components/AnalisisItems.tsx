"use client";

import { pct } from "@/lib/formato";
import type { ItemAnalisis } from "@/lib/tipos";
import { BarraPorcentaje, Icono, Insignia, Tarjeta, TituloSeccion, type TonoBarra } from "./ui";
const num = (v: number | null, dec = 2) => (v === null ? "—" : v.toFixed(dec).replace(".", ","));

function tonoDificultad(texto: string): "exito" | "aviso" | "error" | "azul" {
  if (texto === "Dificultad adecuada") return "exito";
  if (texto === "Muy fácil" || texto === "Fácil") return "azul";
  return "aviso";
}

function tonoDiscriminacion(d: number | null): "exito" | "aviso" | "error" {
  if (d === null) return "aviso";
  if (d >= 0.3) return "exito";
  return d < 0 ? "error" : "aviso";
}

function Distractores({ item }: { item: ItemAnalisis }) {
  return (
    <details className="group rounded-xl border border-borde bg-superficie-2/60 text-sm">
      <summary className="flex min-h-10 cursor-pointer list-none items-center justify-between gap-3 px-3 py-1.5 font-semibold [&::-webkit-details-marker]:hidden">
        Análisis de distractores
        <Icono nombre="chevron" tamano={16} className="transition group-open:rotate-180" />
      </summary>
      <ul className="flex flex-col gap-3 border-t border-borde px-3 py-3">
        {item.distractores.map((d) => {
          const tono: TonoBarra = d.correcta ? "exito" : d.funcional === false ? "aviso" : "error";
          return (
            <li key={d.letra}>
              <div className="mb-1 flex flex-wrap items-center gap-2">
                <span className="font-bold">{d.letra}.</span>
                <span className="min-w-0 flex-1 break-words">{d.opcion}</span>
                {d.correcta && (
                  <Insignia tono="exito">
                    <Icono nombre="check" tamano={12} /> Correcta
                  </Insignia>
                )}
                {d.funcional === false && <Insignia tono="aviso">No funcional (&lt; 5 %)</Insignia>}
                {d.confunde_mejores && (
                  <Insignia tono="error">
                    <Icono nombre="alerta" tamano={12} /> Confunde a los mejores
                  </Insignia>
                )}
              </div>
              <div className="flex items-center gap-3">
                <BarraPorcentaje valor={d.porcentaje} etiqueta={`Porcentaje que eligió la opción ${d.letra}`} tono={tono} className="flex-1" />
                <span className="w-14 shrink-0 text-right font-bold">{pct(d.porcentaje)}</span>
              </div>
              {d.porcentaje_superior !== null && d.porcentaje_inferior !== null && (
                <p className="mt-1 text-xs text-suave">
                  Grupo superior: {pct(d.porcentaje_superior)} · grupo inferior: {pct(d.porcentaje_inferior)}
                </p>
              )}
            </li>
          );
        })}
      </ul>
    </details>
  );
}

function Lectura({ item }: { item: ItemAnalisis }) {
  return (
    <div className="flex flex-wrap items-center gap-1.5">
      {item.dificultad && <Insignia tono={tonoDificultad(item.dificultad)}>{item.dificultad}</Insignia>}
      {item.discriminacion && <Insignia tono={tonoDiscriminacion(item.d)}>{item.discriminacion}</Insignia>}
      {item.revisar && (
        <Insignia tono="error">
          <Icono nombre="alerta" tamano={12} /> Revisar
        </Insignia>
      )}
    </div>
  );
}

/** Análisis de ítems (psicometría clásica): dificultad, discriminación, punto-biserial y distractores. */
export default function AnalisisItems({ items, minimo, intentos }: { items: ItemAnalisis[]; minimo: number; intentos: number }) {
  if (items.length === 0) return null;
  return (
    <section className="flex flex-col gap-4" aria-label="Análisis de ítems">
      <TituloSeccion>Análisis de ítems</TituloSeccion>
      <Tarjeta className="flex flex-col gap-4">
        <p className="text-sm text-suave">
          Calculado con los <strong className="text-texto">{intentos}</strong> {intentos === 1 ? "intento inicial finalizado" : "intentos iniciales finalizados"}. <strong className="text-texto">p</strong> = proporción de
          aciertos (dificultad) · <strong className="text-texto">D</strong> = diferencia de aciertos entre el 27 % de mayor y de menor puntaje (discriminación) ·{" "}
          <strong className="text-texto">r<sub>pb</sub></strong> = correlación punto-biserial con el puntaje total. Se muestran los índices con al menos {minimo}{" "}
          respuestas por pregunta.
        </p>

        {/* Móvil: tarjetas */}
        <ul className="flex flex-col gap-3 md:hidden">
          {items.map((it) => (
            <li key={it.pregunta_id} className="flex flex-col gap-2 rounded-xl border border-borde p-3">
              <p className="text-sm font-semibold">
                {it.orden + 1}. {it.enunciado}
              </p>
              {it.suficiente ? (
                <>
                  <dl className="grid grid-cols-3 gap-2 text-center text-sm">
                    <div className="rounded-lg bg-superficie-2 p-2">
                      <dt className="text-xs text-suave">p</dt>
                      <dd className="font-bold">{num(it.p)}</dd>
                    </div>
                    <div className="rounded-lg bg-superficie-2 p-2">
                      <dt className="text-xs text-suave">D</dt>
                      <dd className="font-bold">{num(it.d)}</dd>
                    </div>
                    <div className="rounded-lg bg-superficie-2 p-2">
                      <dt className="text-xs text-suave">r pb</dt>
                      <dd className="font-bold">{num(it.r_pb)}</dd>
                    </div>
                  </dl>
                  <Lectura item={it} />
                  <ul className="list-disc space-y-1 pl-5 text-sm">
                    {it.observaciones.map((o, i) => (
                      <li key={i}>{o}</li>
                    ))}
                  </ul>
                  <Distractores item={it} />
                </>
              ) : (
                <p className="text-sm text-suave">Datos insuficientes ({it.n} de {minimo} respuestas necesarias).</p>
              )}
            </li>
          ))}
        </ul>

        {/* Tablet y escritorio: tabla */}
        <div tabIndex={0} role="region" aria-label="Análisis de ítems" className="hidden overflow-x-auto rounded-xl border border-borde md:block">
          <table className="w-full text-left text-sm">
            <thead className="bg-superficie-2">
              <tr>
                <th scope="col" className="px-3 py-2.5">#</th>
                <th scope="col" className="px-3 py-2.5">Pregunta</th>
                <th scope="col" className="px-3 py-2.5 text-right">n</th>
                <th scope="col" className="px-3 py-2.5 text-right">p</th>
                <th scope="col" className="px-3 py-2.5 text-right">D</th>
                <th scope="col" className="px-3 py-2.5 text-right">r<sub>pb</sub></th>
                <th scope="col" className="px-3 py-2.5">Interpretación</th>
              </tr>
            </thead>
            <tbody>
              {items.map((it) => (
                <tr key={it.pregunta_id} className="border-t border-borde align-top">
                  <td className="px-3 py-2.5 font-bold">{it.orden + 1}</td>
                  <td className="max-w-xs px-3 py-2.5">{it.enunciado}</td>
                  <td className="px-3 py-2.5 text-right">{it.n}</td>
                  {it.suficiente ? (
                    <>
                      <td className="px-3 py-2.5 text-right font-bold">{num(it.p)}</td>
                      <td className="px-3 py-2.5 text-right font-bold">{num(it.d)}</td>
                      <td className="px-3 py-2.5 text-right font-bold">{num(it.r_pb)}</td>
                      <td className="flex min-w-72 flex-col gap-2 px-3 py-2.5">
                        <Lectura item={it} />
                        <ul className="list-disc space-y-1 pl-5">
                          {it.observaciones.map((o, i) => (
                            <li key={i}>{o}</li>
                          ))}
                        </ul>
                        <Distractores item={it} />
                      </td>
                    </>
                  ) : (
                    <td colSpan={4} className="px-3 py-2.5 text-suave">
                      Datos insuficientes: se necesitan al menos {minimo} respuestas.
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Tarjeta>
    </section>
  );
}
