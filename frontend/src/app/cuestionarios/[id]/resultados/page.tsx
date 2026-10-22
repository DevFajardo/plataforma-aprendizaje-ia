"use client";

import { useParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import {
  Alerta,
  BarraPorcentaje,
  Boton,
  EncabezadoPagina,
  EsqueletoPagina,
  EstadoVacio,
  Icono,
  Insignia,
  Metrica,
  Pagina,
  Tarjeta,
  TituloSeccion,
  type TonoBarra,
} from "@/components/ui";
import { descargarCsv, descargarPdfCuestionario, obtenerResultados } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import { formatearFecha } from "@/lib/fechas";
import type { GananciaAprendizaje, PreguntaResultado, Resultados, Retencion } from "@/lib/tipos";

const UMBRAL_REFORZAR = 60; // % de acierto por debajo del cual se sugiere reforzar el tema

function tonoBarra(p: number): TonoBarra {
  if (p < UMBRAL_REFORZAR) return "error";
  if (p < 80) return "aviso";
  return "exito";
}

const etiquetaTipo = (t: string) => (t === "practica" ? "Práctica" : t.charAt(0).toUpperCase() + t.slice(1));

function Detalle({ resumen, children }: { resumen: string; children: React.ReactNode }) {
  return (
    <details className="group mt-4 rounded-xl border border-borde bg-superficie-2/60">
      <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-3 px-4 py-2 text-sm font-semibold [&::-webkit-details-marker]:hidden">
        {resumen}
        <Icono nombre="chevron" tamano={18} className="transition group-open:rotate-180" />
      </summary>
      <div className="border-t border-borde px-4 py-3">{children}</div>
    </details>
  );
}

function GananciaSeccion({ ganancia }: { ganancia: GananciaAprendizaje }) {
  if (ganancia.estudiantes === 0) {
    return (
      <Tarjeta as="section">
        <TituloSeccion nivel={3}>Ganancia de aprendizaje</TituloSeccion>
        <p className="mt-3 text-sm text-suave">
          Aún no hay estudiantes con 2 o más intentos. Cuando alguien repita el cuestionario se comparará su primer intento (pre-test) con el
          último (post-test).
        </p>
      </Tarjeta>
    );
  }
  const dif = ganancia.diferencia_puntos ?? 0;
  return (
    <Tarjeta as="section">
      <TituloSeccion nivel={3}>Ganancia de aprendizaje</TituloSeccion>
      <p className="mb-4 mt-3 text-sm text-suave">
        Primer intento (pre-test) frente a último intento (post-test) de los {ganancia.estudiantes} estudiante(s) con 2 o más intentos.
      </p>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Metrica titulo="Promedio primer intento" valor={`${ganancia.promedio_primer_intento}%`} />
        <Metrica titulo="Promedio último intento" valor={`${ganancia.promedio_ultimo_intento}%`} />
        <Metrica className="col-span-2 sm:col-span-1" titulo="Diferencia" valor={`${dif > 0 ? "+" : ""}${dif} puntos`} />
      </div>
      <Detalle resumen="Ver detalle por estudiante">
        <ul className="flex flex-col gap-2 text-sm">
          {ganancia.detalle.map((d) => (
            <li key={d.email} className="flex flex-col gap-0.5 border-b border-borde pb-2 last:border-0 last:pb-0 sm:flex-row sm:justify-between">
              <span className="font-semibold">{d.nombre}</span>
              <span className="text-suave">
                {d.primer_porcentaje}% → {d.ultimo_porcentaje}% ({d.diferencia > 0 ? "+" : ""}
                {d.diferencia} puntos, {d.intentos} intentos)
              </span>
            </li>
          ))}
        </ul>
      </Detalle>
    </Tarjeta>
  );
}

function RetencionSeccion({ retencion }: { retencion: Retencion }) {
  const dias = retencion.repaso_dias;
  if (retencion.estudiantes === 0) {
    return (
      <Tarjeta as="section">
        <TituloSeccion nivel={3}>Retención</TituloSeccion>
        <p className="mt-3 text-sm text-suave">
          {dias
            ? `Aún no hay estudiantes con intento inicial y repaso diferido (el repaso se programa a los ${dias} días de su primer intento).`
            : "Este cuestionario no tiene repaso diferido. Actívalo en el panel del docente para medir la retención."}
        </p>
      </Tarjeta>
    );
  }
  const dif = retencion.diferencia_puntos ?? 0;
  return (
    <Tarjeta as="section">
      <TituloSeccion nivel={3}>Retención</TituloSeccion>
      <p className="mb-4 mt-3 text-sm text-suave">
        Intento inicial frente a repaso diferido{dias ? ` (a los ${dias} días)` : ""} de los {retencion.estudiantes} estudiante(s) que hicieron
        ambos. Retención = diferido / inicial × 100.
      </p>
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Metrica titulo="Promedio inicial" valor={`${retencion.promedio_inicial}%`} />
        <Metrica titulo="Promedio diferido" valor={`${retencion.promedio_diferido}%`} />
        <Metrica titulo="Retención" valor={retencion.retencion_pct === null ? "—" : `${retencion.retencion_pct}%`} />
        <Metrica titulo="Diferencia" valor={`${dif > 0 ? "+" : ""}${dif} puntos`} />
      </div>
      <Detalle resumen="Ver detalle por estudiante">
        <ul className="flex flex-col gap-2 text-sm">
          {retencion.detalle.map((d) => (
            <li key={d.email} className="flex flex-col gap-0.5 border-b border-borde pb-2 last:border-0 last:pb-0 sm:flex-row sm:justify-between">
              <span className="font-semibold">{d.nombre}</span>
              <span className="text-suave">
                {d.inicial}% → {d.diferido}% (retención {d.retencion === null ? "—" : `${d.retencion}%`})
              </span>
            </li>
          ))}
        </ul>
      </Detalle>
    </Tarjeta>
  );
}

function Contenido() {
  const { usuario, cargando } = useRequiereLogin();
  const { id } = useParams<{ id: string }>();
  const [datos, setDatos] = useState<Resultados | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [descargando, setDescargando] = useState(false);

  useEffect(() => {
    if (!usuario) return;
    obtenerResultados(Number(id))
      .then(setDatos)
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
  }, [usuario, id]);

  async function pdf() {
    setError(null);
    setDescargando(true);
    try {
      await descargarPdfCuestionario(Number(id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setDescargando(false);
    }
  }

  async function csv() {
    setError(null);
    setDescargando(true);
    try {
      await descargarCsv(Number(id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setDescargando(false);
    }
  }

  const cerradas: PreguntaResultado[] = datos?.preguntas.filter((p) => p.porcentaje_acierto !== null) ?? [];
  const abiertas = datos?.preguntas.filter((p) => p.tipo === "abierta") ?? [];
  const aReforzar = cerradas
    .filter((p) => p.num_respuestas > 0 && (p.porcentaje_acierto ?? 100) < UMBRAL_REFORZAR)
    .sort((a, b) => (a.porcentaje_acierto ?? 0) - (b.porcentaje_acierto ?? 0));

  return (
    <Pagina ancho="lg">
      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}
      {(cargando || (!datos && !error)) && <EsqueletoPagina />}

      {datos && (
        <>
          <EncabezadoPagina
            atras={{ href: `/cuestionarios/${id}`, texto: "Volver al cuestionario" }}
            titulo={`Resultados: ${datos.titulo}`}
            etiquetas={datos.modo === "control" ? <Insignia tono="neutro">Grupo control</Insignia> : undefined}
            acciones={
              <>
                <Boton onClick={csv} cargando={descargando} disabled={datos.total_intentos === 0}>
                  <Icono nombre="descargar" /> {descargando ? "Descargando…" : "Descargar CSV"}
                </Boton>
                <Boton variante="secundario" onClick={pdf} disabled={descargando}>
                  <Icono nombre="descargar" /> Descargar PDF
                </Boton>
              </>
            }
          />

          <div className="flex flex-col gap-8">
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4">
              <Metrica icono="intentos" titulo="Intentos finalizados" valor={String(datos.total_intentos)} />
              <Metrica icono="grupo" titulo="Estudiantes" valor={String(datos.estudiantes_unicos)} />
              <Metrica className="col-span-2 sm:col-span-1" icono="promedio" titulo="Promedio" valor={`${datos.promedio_porcentaje}%`} />
            </div>

            {datos.total_intentos === 0 ? (
              <EstadoVacio icono="intentos" titulo="Aún nadie ha finalizado este cuestionario">
                Comparte el código desde el panel del docente.
              </EstadoVacio>
            ) : (
              <>
                {aReforzar.length > 0 && (
                  <section className="rounded-2xl border border-aviso-borde border-l-[6px] border-l-cul-naranja bg-aviso-fondo p-4 text-aviso-texto sm:p-5">
                    <h2 className="mb-2 text-lg font-bold">Temas a reforzar</h2>
                    <ul className="list-disc space-y-1.5 pl-5 text-sm">
                      {aReforzar.map((p) => (
                        <li key={p.pregunta_id}>
                          {p.enunciado} <strong>({p.porcentaje_acierto}% de acierto)</strong>
                        </li>
                      ))}
                    </ul>
                  </section>
                )}

                <GananciaSeccion ganancia={datos.ganancia} />

                <RetencionSeccion retencion={datos.retencion} />

                <section className="flex flex-col gap-4">
                  <TituloSeccion>Acierto por pregunta</TituloSeccion>
                  <Tarjeta>
                    <ul className="flex flex-col gap-5">
                      {cerradas.map((p) => {
                        const pct = p.porcentaje_acierto ?? 0;
                        const reforzar = p.num_respuestas > 0 && pct < UMBRAL_REFORZAR;
                        return (
                          <li key={p.pregunta_id}>
                            <p className="mb-2 text-sm font-semibold">
                              {p.orden + 1}. {p.enunciado}
                            </p>
                            <div className="flex items-center gap-3">
                              <BarraPorcentaje valor={pct} etiqueta={`Acierto de la pregunta ${p.orden + 1}`} tono={tonoBarra(pct)} alto="lg" className="flex-1" />
                              <span className="w-12 shrink-0 text-right text-sm font-bold">{pct}%</span>
                            </div>
                            <p className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-suave">
                              {p.num_respuestas} respuestas
                              {reforzar && (
                                <Insignia tono="error">
                                  <Icono nombre="alerta" tamano={12} /> Reforzar
                                </Insignia>
                              )}
                            </p>
                          </li>
                        );
                      })}
                    </ul>
                  </Tarjeta>
                </section>

                {abiertas.length > 0 && (
                  <section className="flex flex-col gap-4">
                    <TituloSeccion>Preguntas abiertas</TituloSeccion>
                    <div className="flex flex-col gap-2">
                      {abiertas.map((p) => (
                        <details key={p.pregunta_id} className="group rounded-xl border border-borde bg-superficie shadow-tarjeta">
                          <summary className="flex min-h-12 cursor-pointer list-none items-center justify-between gap-3 px-4 py-3 font-semibold [&::-webkit-details-marker]:hidden">
                            <span>
                              {p.orden + 1}. {p.enunciado} ({p.num_respuestas} respuestas)
                            </span>
                            <Icono nombre="chevron" className="transition group-open:rotate-180" />
                          </summary>
                          <ul className="flex flex-col gap-2 border-t border-borde p-4 text-sm">
                            {p.respuestas_abiertas.length === 0 && <li className="text-suave">Sin respuestas.</li>}
                            {p.respuestas_abiertas.map((r, i) => (
                              <li key={i} className="rounded-lg bg-superficie-2 p-3">
                                <strong>{r.nombre}:</strong> {r.respuesta || <em>(vacía)</em>}
                              </li>
                            ))}
                          </ul>
                        </details>
                      ))}
                    </div>
                  </section>
                )}

                <section className="flex flex-col gap-4">
                  <TituloSeccion>Intentos</TituloSeccion>
                  {/* Móvil: tarjetas */}
                  <ul className="flex flex-col gap-3 md:hidden">
                    {datos.intentos.map((i) => (
                      <li key={i.intento_id}>
                        <Tarjeta className="flex flex-col gap-2 !p-4">
                          <div className="flex items-start justify-between gap-3">
                            <div className="min-w-0">
                              <p className="font-bold">{i.nombre}</p>
                              <p className="text-xs text-suave">{i.email}</p>
                            </div>
                            <span className="shrink-0 text-xl font-extrabold">{i.porcentaje}%</span>
                          </div>
                          <div className="flex flex-wrap items-center gap-2 text-sm text-suave">
                            <Insignia>{etiquetaTipo(i.tipo)}</Insignia>
                            <span>
                              {i.puntaje}/{i.total}
                            </span>
                            <span>· {formatearFecha(i.fecha)}</span>
                          </div>
                        </Tarjeta>
                      </li>
                    ))}
                  </ul>
                  {/* Tablet y escritorio: tabla */}
                  <div className="hidden overflow-x-auto rounded-2xl border border-borde bg-superficie shadow-tarjeta md:block">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-superficie-2">
                        <tr>
                          <th scope="col" className="px-3 py-2.5">Estudiante</th>
                          <th scope="col" className="px-3 py-2.5">Correo</th>
                          <th scope="col" className="px-3 py-2.5">Puntaje</th>
                          <th scope="col" className="px-3 py-2.5">%</th>
                          <th scope="col" className="px-3 py-2.5">Tipo</th>
                          <th scope="col" className="px-3 py-2.5">Fecha</th>
                        </tr>
                      </thead>
                      <tbody>
                        {datos.intentos.map((i) => (
                          <tr key={i.intento_id} className="border-t border-borde transition hover:bg-superficie-2/60">
                            <td className="px-3 py-2.5 font-semibold">{i.nombre}</td>
                            <td className="px-3 py-2.5">{i.email}</td>
                            <td className="px-3 py-2.5">
                              {i.puntaje}/{i.total}
                            </td>
                            <td className="px-3 py-2.5 font-bold">{i.porcentaje}%</td>
                            <td className="px-3 py-2.5">{etiquetaTipo(i.tipo)}</td>
                            <td className="whitespace-nowrap px-3 py-2.5">{formatearFecha(i.fecha)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </section>
              </>
            )}
          </div>
        </>
      )}
    </Pagina>
  );
}

export default function ResultadosPage() {
  return (
    <Suspense
      fallback={
        <Pagina ancho="lg">
          <EsqueletoPagina />
        </Pagina>
      }
    >
      <Contenido />
    </Suspense>
  );
}
