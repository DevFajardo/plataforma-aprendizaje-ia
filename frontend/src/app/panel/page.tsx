"use client";

import { useEffect, useState } from "react";
import GraficoEvolucion from "@/components/GraficoEvolucion";
import {
  Alerta,
  BotonEnlace,
  EncabezadoPagina,
  Enlace,
  EsqueletoPagina,
  EstadoVacio,
  Icono,
  Insignia,
  Metrica,
  Pagina,
  Tarjeta,
  TituloSeccion,
} from "@/components/ui";
import { listarRepasos, obtenerEstadisticas, obtenerMiSus } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import { formatearFecha } from "@/lib/fechas";
import type { Estadisticas, Repaso } from "@/lib/tipos";

const pct = (v: number | null) => (v === null ? "—" : `${v}%`);

export default function PanelPage() {
  const { usuario, cargando } = useRequiereLogin();
  const [datos, setDatos] = useState<Estadisticas | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [respondioSus, setRespondioSus] = useState<boolean | null>(null);
  const [repasos, setRepasos] = useState<Repaso[]>([]);

  useEffect(() => {
    if (!usuario) return;
    listarRepasos()
      .then(setRepasos)
      .catch(() => setRepasos([])); // la tarjeta de repasos es opcional
    obtenerEstadisticas()
      .then(setDatos)
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
    obtenerMiSus()
      .then((r) => setRespondioSus(r !== null))
      .catch(() => setRespondioSus(true)); // ante un error, no molestar con el banner
  }, [usuario]);

  if (cargando || !usuario) {
    return (
      <Pagina>
        <EsqueletoPagina />
      </Pagina>
    );
  }

  const d = datos?.docente;

  return (
    <Pagina>
      <EncabezadoPagina titulo={`Hola, ${usuario.nombre}`} descripcion="Este es tu panel de progreso." />

      <div className="flex flex-col gap-6">
        {!usuario.acepta_tratamiento_datos && (
          <Alerta
            tipo="advertencia"
            acciones={
              <BotonEnlace href="/cuenta" tamano="sm">
                Revisar en Mi cuenta
              </BotonEnlace>
            }
          >
            Aún no has aceptado la política de tratamiento de datos personales (Ley 1581 de 2012).
          </Alerta>
        )}

        {repasos.length > 0 && (
          <section aria-label="Repasos pendientes" className="rounded-2xl border border-borde border-l-[6px] border-l-cul-naranja bg-superficie p-4 shadow-tarjeta sm:p-6">
            <div className="flex items-center gap-3">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-aviso-fondo text-aviso-texto">
                <Icono nombre="repetir" tamano={22} />
              </span>
              <h2 className="text-xl font-bold">Repasos pendientes</h2>
              <Insignia tono="acento" className="ml-auto">
                {repasos.length}
              </Insignia>
            </div>
            <p className="mb-4 mt-2 text-sm text-suave">
              Volver a responder un cuestionario días después ayuda a consolidar lo aprendido. En el repaso no verás si aciertas hasta terminar.
            </p>
            <ul className="flex flex-col gap-2">
              {repasos.map((r) => (
                <li key={r.id} className="flex flex-col gap-3 rounded-xl bg-superficie-2 p-3 sm:flex-row sm:items-center sm:justify-between">
                  <span className="min-w-0">
                    <strong className="block">{r.cuestionario_titulo}</strong>
                    <span className="block text-sm text-suave">
                      {r.vencido ? "Listo para hacer" : `Disponible desde el ${formatearFecha(r.disponible_desde)}`}
                    </span>
                  </span>
                  {r.vencido && (
                    <BotonEnlace href={`/cuestionarios/${r.cuestionario_id}`} tamano="sm" className="shrink-0">
                      Hacer repaso
                    </BotonEnlace>
                  )}
                </li>
              ))}
            </ul>
          </section>
        )}

        {respondioSus === false && (
          <Alerta
            tipo="info"
            acciones={
              <BotonEnlace href="/encuesta" tamano="sm">
                Responder encuesta
              </BotonEnlace>
            }
          >
            ¿Nos ayudas a mejorar? Responde la encuesta de usabilidad (2 minutos, 10 preguntas).
          </Alerta>
        )}

        {error && <Alerta tipo="error">{error}</Alerta>}
        {!datos && !error && <EsqueletoPagina />}

        {datos && (
          <>
            <section aria-label="Métricas personales">
              <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3">
                <Metrica icono="intentos" titulo="Intentos finalizados" valor={String(datos.intentos_finalizados)} />
                <Metrica icono="promedio" titulo="Promedio" valor={pct(datos.promedio_porcentaje)} />
                <Metrica icono="trofeo" titulo="Mejor resultado" valor={pct(datos.mejor_porcentaje)} />
                <Metrica icono="repetir" titulo="Retención promedio (repasos)" valor={pct(datos.retencion_promedio)} />
                <Metrica icono="chispa" titulo="Cuestionarios generados" valor={String(datos.cuestionarios_generados)} />
                <Metrica icono="grupo" titulo="Cuestionarios a los que me uní" valor={String(datos.cuestionarios_unidos)} />
              </div>
            </section>

            <section className="flex flex-col gap-3">
              <TituloSeccion>Evolución de tus resultados</TituloSeccion>
              {datos.evolucion.length === 0 ? (
                <EstadoVacio
                  icono="promedio"
                  titulo="Aún no tienes intentos"
                  accion={
                    <BotonEnlace href="/" tamano="sm">
                      Genera tu primer cuestionario
                    </BotonEnlace>
                  }
                >
                  Genera un cuestionario y respóndelo para ver aquí tu progreso.
                </EstadoVacio>
              ) : (
                <Tarjeta>
                  <GraficoEvolucion puntos={datos.evolucion} />
                  <p className="mt-3 text-xs text-suave">
                    Últimos {datos.evolucion.length} intentos. Pasa el mouse, toca un punto o usa Tab para ver el detalle.
                  </p>
                </Tarjeta>
              )}
            </section>

            <section className="flex flex-col gap-3">
              <TituloSeccion>Temas a reforzar</TituloSeccion>
              {datos.temas_a_reforzar.length === 0 ? (
                <p className="text-suave">
                  {datos.intentos_finalizados === 0
                    ? "Cuando respondas cuestionarios, aquí verás las preguntas que más se te dificultan."
                    : "¡Muy bien! No has fallado ninguna pregunta cerrada."}
                </p>
              ) : (
                <ul className="flex flex-col gap-2">
                  {datos.temas_a_reforzar.map((t) => (
                    <li
                      key={t.pregunta_id}
                      className="rounded-xl border border-aviso-borde border-l-[6px] border-l-cul-naranja bg-aviso-fondo p-4 text-sm text-aviso-texto"
                    >
                      <p className="font-bold">{t.enunciado}</p>
                      <p className="mt-1">
                        Fallada {t.fallos} {t.fallos === 1 ? "vez" : "veces"} en{" "}
                        <Enlace href={`/cuestionarios/${t.cuestionario_id}`} className="!text-current">
                          {t.cuestionario_titulo || "el cuestionario"}
                        </Enlace>
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            {d && (
              <section className="flex flex-col gap-4">
                <TituloSeccion>Tus cuestionarios publicados</TituloSeccion>
                <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
                  <Metrica icono="libro" titulo="Publicados" valor={String(d.cuestionarios_publicados)} />
                  <Metrica icono="grupo" titulo="Estudiantes" valor={String(d.estudiantes_unicos)} />
                  <Metrica icono="intentos" titulo="Intentos recibidos" valor={String(d.intentos_recibidos)} />
                  <Metrica icono="promedio" titulo="Promedio de tus estudiantes" valor={pct(d.promedio_general)} />
                </div>

                <Tarjeta>
                  <h3 className="flex items-center gap-2 font-bold">
                    <Icono nombre="reloj" /> Tiempo ahorrado con la herramienta
                  </h3>
                  {d.tiempo.cuestionarios_con_estimacion === 0 ? (
                    <p className="mt-2 text-sm text-suave">
                      Al publicar un cuestionario puedes indicar cuántos minutos te habría tomado crearlo manualmente; así se calcula el ahorro
                      (generación + edición frente a tu estimación).
                    </p>
                  ) : (
                    <>
                      <div className="mt-3 grid gap-3 sm:grid-cols-3">
                        <Metrica titulo="Promedio con la herramienta" valor={`${d.tiempo.promedio_herramienta_min} min`} />
                        <Metrica titulo="Promedio estimado manual" valor={`${d.tiempo.promedio_manual_min} min`} />
                        <Metrica titulo="Ahorro" valor={pct(d.tiempo.ahorro_pct)} />
                      </div>
                      <p className="mt-3 text-xs text-suave">Basado en {d.tiempo.cuestionarios_con_estimacion} cuestionario(s) con estimación.</p>
                    </>
                  )}
                </Tarjeta>

                {d.por_cuestionario.length === 0 ? (
                  <EstadoVacio
                    titulo="Aún no has publicado ningún cuestionario"
                    accion={
                      <BotonEnlace href="/cuestionarios" tamano="sm">
                        Ir a Mis cuestionarios
                      </BotonEnlace>
                    }
                  >
                    Abre uno desde «Mis cuestionarios» y pulsa «Publicar» para compartirlo con tus estudiantes.
                  </EstadoVacio>
                ) : (
                  <>
                    {/* Móvil: lista de tarjetas */}
                    <ul className="flex flex-col gap-3 md:hidden">
                      {d.por_cuestionario.map((c) => (
                        <li key={c.id}>
                          <Tarjeta className="flex flex-col gap-3 !p-4">
                            <p className="font-bold">{c.titulo}</p>
                            <dl className="grid grid-cols-3 gap-2 text-sm">
                              <div>
                                <dt className="text-xs text-suave">Código</dt>
                                <dd className="font-mono font-semibold">{c.codigo_compartir}</dd>
                              </div>
                              <div>
                                <dt className="text-xs text-suave">Intentos</dt>
                                <dd className="font-semibold">{c.intentos}</dd>
                              </div>
                              <div>
                                <dt className="text-xs text-suave">Promedio</dt>
                                <dd className="font-semibold">{pct(c.promedio)}</dd>
                              </div>
                            </dl>
                            <BotonEnlace href={`/cuestionarios/${c.id}/resultados`} variante="secundario" tamano="sm">
                              Ver resultados
                            </BotonEnlace>
                          </Tarjeta>
                        </li>
                      ))}
                    </ul>
                    {/* Tablet y escritorio: tabla */}
                    <div className="hidden overflow-x-auto rounded-2xl border border-borde bg-superficie shadow-tarjeta md:block">
                      <table className="w-full text-left text-sm">
                        <thead className="bg-superficie-2">
                          <tr>
                            <th scope="col" className="px-4 py-3">Cuestionario</th>
                            <th scope="col" className="px-4 py-3">Código</th>
                            <th scope="col" className="px-4 py-3">Intentos</th>
                            <th scope="col" className="px-4 py-3">Promedio</th>
                            <th scope="col" className="px-4 py-3">
                              <span className="sr-only">Acciones</span>
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          {d.por_cuestionario.map((c) => (
                            <tr key={c.id} className="border-t border-borde transition hover:bg-superficie-2/60">
                              <td className="px-4 py-3 font-semibold">{c.titulo}</td>
                              <td className="px-4 py-3 font-mono">{c.codigo_compartir}</td>
                              <td className="px-4 py-3">{c.intentos}</td>
                              <td className="px-4 py-3 font-semibold">{pct(c.promedio)}</td>
                              <td className="px-4 py-3 text-right">
                                <Enlace href={`/cuestionarios/${c.id}/resultados`}>Ver resultados</Enlace>
                              </td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </>
                )}

                <div className="grid gap-3 sm:grid-cols-2">
                  <BotonEnlace href="/comparar" variante="secundario" className="justify-between">
                    Comparar grupo de aprendizaje y control <Icono nombre="flecha" />
                  </BotonEnlace>
                  <BotonEnlace href="/encuesta/resultados" variante="secundario" className="justify-between">
                    Resultados de la encuesta (SUS) <Icono nombre="flecha" />
                  </BotonEnlace>
                </div>
              </section>
            )}
          </>
        )}
      </div>
    </Pagina>
  );
}
