"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { crearIntento, finalizarIntento, responderPregunta, urlMedio, urlSubtitulos } from "@/lib/api";
import { formatearFecha } from "@/lib/fechas";
import type { CuestionarioDetalle, IntentoCreado, IntentoResumen, Pregunta } from "@/lib/tipos";
import { PanelCalidad } from "./CalidadPregunta";
import PanelTranscripcion from "./PanelTranscripcion";
import PreguntaCard from "./PreguntaCard";
import TutorChat from "./TutorChat";
import { Alerta, BarraPorcentaje, Boton, EncabezadoPagina, Enlace, Icono, Insignia, Pestanas, Tarjeta, TituloSeccion, cx } from "./ui";
import { pct, plural } from "@/lib/formato";

/** Convierte "mm:ss" (o "hh:mm:ss") en segundos; null si no es válido. */
function aSegundos(marca: string): number | null {
  const partes = marca.split(":").map(Number);
  if (!marca || partes.some((n) => Number.isNaN(n))) return null;
  return partes.reduce((acc, n) => acc * 60 + n, 0);
}

/** URL del reproductor incrustado de YouTube/Vimeo; `segundos` salta a esa marca y reproduce. */
function urlReproductor(c: CuestionarioDetalle, segundos?: number): string {
  if (c.medio === "vimeo") {
    const base = `https://player.vimeo.com/video/${c.video_externo_id}`;
    const h = c.vimeo_hash ? `h=${c.vimeo_hash}` : "";
    if (segundos === undefined) return h ? `${base}?${h}` : base;
    return `${base}?${h ? h + "&" : ""}autoplay=1#t=${segundos}s`;
  }
  const base = `https://www.youtube.com/embed/${c.youtube_id}`;
  return segundos === undefined ? base : `${base}?start=${segundos}&autoplay=1`;
}

/** Anillo de puntaje (SVG) con el porcentaje en el centro. */
function AnilloPuntaje({ porcentaje }: { porcentaje: number }) {
  const r = 52;
  const circ = 2 * Math.PI * r;
  const tono = porcentaje < 60 ? "stroke-error-solido" : porcentaje < 80 ? "stroke-aviso-solido" : "stroke-exito-solido";
  return (
    <div className="relative h-32 w-32 shrink-0 sm:h-36 sm:w-36" aria-hidden="true">
      <svg viewBox="0 0 120 120" className="h-full w-full -rotate-90">
        <circle cx="60" cy="60" r={r} fill="none" strokeWidth="10" className="stroke-pista" />
        <circle
          cx="60"
          cy="60"
          r={r}
          fill="none"
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circ}
          strokeDashoffset={circ * (1 - Math.min(100, Math.max(0, porcentaje)) / 100)}
          className={cx("transition-[stroke-dashoffset] duration-700", tono)}
        />
      </svg>
      <span className="absolute inset-0 flex items-center justify-center text-3xl font-extrabold">{pct(porcentaje)}</span>
    </div>
  );
}

function mensajePuntaje(p: number): string {
  if (p >= 80) return "¡Excelente trabajo!";
  if (p >= 60) return "¡Buen trabajo! Sigue practicando.";
  return "Repasa el video y vuelve a intentarlo.";
}

export default function VisorCuestionario({
  cuestionario: c,
  panel,
  onRecargar,
}: {
  cuestionario: CuestionarioDetalle;
  /** Panel opcional (p. ej. controles del docente) que se muestra bajo el título. */
  panel?: ReactNode;
  /** El docente pide volver a cargar el cuestionario (p. ej. tras verificar la calidad). */
  onRecargar?: () => void;
}) {
  const [srcVideo, setSrcVideo] = useState(urlReproductor(c));
  // YouTube: se muestra una portada y el reproductor (pesado, de terceros) solo se carga al pulsar «Reproducir».
  const [reproduciendo, setReproduciendo] = useState(false);
  const videoRef = useRef<HTMLDivElement>(null);
  const mediaRef = useRef<HTMLVideoElement & HTMLAudioElement>(null);
  const esArchivo = (c.medio === "video" || c.medio === "audio") && c.archivo_url !== null;
  const esIncrustado = c.medio === "youtube" || c.medio === "vimeo";
  // Grupo control: el estudiante ve solo el video y las preguntas
  const soloPreguntas = c.modo === "control" && !c.es_creador;

  const [intento, setIntento] = useState<IntentoCreado | null>(null);
  const [respondidas, setRespondidas] = useState(0);
  const [resumen, setResumen] = useState<IntentoResumen | null>(null);
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Cambiarlo remonta las tarjetas de preguntas (nuevo intento)
  const [ronda, setRonda] = useState(0);
  const [panelIzq, setPanelIzq] = useState<"resumen" | "tutor" | "transcripcion">("resumen");
  // Subtítulos accesibles del reproductor HTML5 (se descargan con el token y se sirven como URL de objeto)
  const [subtitulos, setSubtitulos] = useState<string | null>(null);
  const [tiempoActual, setTiempoActual] = useState<number | null>(null);

  useEffect(() => {
    if (!esArchivo) return;
    let url: string | null = null;
    let cancelado = false;
    urlSubtitulos(c.video_id)
      .then((u) => {
        if (cancelado) URL.revokeObjectURL(u);
        else {
          url = u;
          setSubtitulos(u);
        }
      })
      .catch(() => {
        /* sin subtítulos: el reproductor funciona igual */
      });
    return () => {
      cancelado = true;
      if (url) URL.revokeObjectURL(url);
    };
  }, [esArchivo, c.video_id]);

  function saltar(segundos: number) {
    if (esArchivo) {
      // Reproductor HTML5: saltar y reproducir
      const m = mediaRef.current;
      if (m) {
        m.currentTime = segundos;
        void m.play().catch(() => {
          /* el navegador puede bloquear la reproducción automática */
        });
      }
      videoRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      return;
    }
    setSrcVideo(urlReproductor(c, segundos));
    setReproduciendo(true);
    videoRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  async function empezar() {
    setError(null);
    setOcupado(true);
    try {
      setIntento(await crearIntento(c.id));
      setRespondidas(0);
      setResumen(null);
      setRonda((n) => n + 1);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setOcupado(false);
    }
  }

  async function responder(p: Pregunta, respuesta: string) {
    const r = await responderPregunta(intento!.id, p.id, respuesta);
    setRespondidas((n) => n + 1);
    return r;
  }

  async function finalizar() {
    setError(null);
    setOcupado(true);
    try {
      setResumen(await finalizarIntento(intento!.id));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setOcupado(false);
    }
  }

  const todas = respondidas === c.preguntas.length;
  const conFeedback = intento?.con_feedback ?? true;

  return (
    <div className="flex flex-col gap-6">
      <EncabezadoPagina
        migas={[{ texto: "Mis cuestionarios", href: "/cuestionarios" }, { texto: c.titulo }]}
        titulo={c.titulo}
        etiquetas={
          <>
            {c.modo === "control" && <Insignia tono="neutro">Grupo control</Insignia>}
            <Insignia tono="azul">{plural(c.preguntas.length, "pregunta")}</Insignia>
            <Insignia>{formatearFecha(c.creado_en, "corta")}</Insignia>
          </>
        }
      />

      {panel}

      <div className="grid gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)] lg:items-start xl:gap-8">
        {/* Columna del video y el resumen (fija en escritorio) */}
        <div className="flex min-w-0 flex-col gap-4 lg:sticky lg:top-24 lg:max-h-[calc(100dvh-7rem)]">
          {esArchivo && c.archivo_url && (
            <div ref={videoRef} className="shrink-0">
              {c.medio === "video" ? (
                <video
                  ref={mediaRef}
                  src={urlMedio(c.archivo_url)}
                  controls
                  preload="metadata"
                  onTimeUpdate={(e) => setTiempoActual(e.currentTarget.currentTime)}
                  className="aspect-video w-full rounded-2xl bg-black shadow-tarjeta"
                >
                  {subtitulos && <track kind="captions" srcLang="es" label="Español" src={subtitulos} default />}
                </video>
              ) : (
                <audio
                  ref={mediaRef}
                  src={urlMedio(c.archivo_url)}
                  controls
                  preload="metadata"
                  onTimeUpdate={(e) => setTiempoActual(e.currentTarget.currentTime)}
                  className="w-full"
                />
              )}
            </div>
          )}

          {esIncrustado && (c.youtube_id || c.video_externo_id) && (
            <div ref={videoRef} className="aspect-video w-full shrink-0 overflow-hidden rounded-2xl bg-black shadow-tarjeta">
              {c.medio === "youtube" && !reproduciendo ? (
                <button
                  type="button"
                  onClick={() => {
                    setSrcVideo(urlReproductor(c, 0));
                    setReproduciendo(true);
                  }}
                  aria-label={`Reproducir el video: ${c.titulo}`}
                  className="group relative block h-full w-full overflow-hidden"
                >
                  {/* eslint-disable-next-line @next/next/no-img-element */}
                  <img src={`https://i.ytimg.com/vi/${c.youtube_id}/hqdefault.jpg`} alt="" loading="lazy" className="h-full w-full object-cover opacity-90 transition group-hover:opacity-100" />
                  <span className="absolute inset-0 flex items-center justify-center bg-black/25">
                    <span className="flex h-16 w-16 items-center justify-center rounded-full bg-cul-naranja text-cul-azul-oscuro shadow-lg transition group-hover:scale-105">
                      <Icono nombre="play" tamano={30} />
                    </span>
                  </span>
                </button>
              ) : (
                <iframe
                  key={srcVideo}
                  src={srcVideo}
                  title={c.medio === "vimeo" ? "Video de Vimeo" : "Video de YouTube"}
                  allow="autoplay; encrypted-media; picture-in-picture; fullscreen"
                  allowFullScreen
                  loading="lazy"
                  className="h-full w-full"
                />
              )}
            </div>
          )}

          {!soloPreguntas && (
            <Tarjeta className="scroll-fino flex flex-col gap-5 lg:min-h-0 lg:overflow-y-auto">
              <Pestanas
                etiqueta="Material de estudio"
                items={[
                  { id: "resumen", texto: "Resumen" },
                  { id: "tutor", texto: "Pregúntale al video" },
                  { id: "transcripcion", texto: "Transcripción" },
                ]}
                activa={panelIzq}
                onCambiar={setPanelIzq}
              >
                {panelIzq === "resumen" && (
                  <div className="flex flex-col gap-5">
                    <section>
                      <TituloSeccion nivel={2} visual={3}>Resumen</TituloSeccion>
                      <p className="mt-3 whitespace-pre-line leading-relaxed text-suave">{c.resumen}</p>
                    </section>
                    <section>
                      <TituloSeccion nivel={2} visual={3}>Ideas clave</TituloSeccion>
                      <ul className="mt-3 flex flex-col gap-2">
                        {c.ideas_clave.map((idea, i) => (
                          <li key={i} className="flex items-start gap-3 text-suave">
                            <span aria-hidden="true" className="mt-2 h-2 w-2 shrink-0 rounded-full bg-cul-naranja" />
                            <span>{idea}</span>
                          </li>
                        ))}
                      </ul>
                    </section>
                  </div>
                )}
                {panelIzq === "tutor" && (
                  <TutorChat cuestionarioId={c.id} onSaltar={saltar} claveRefresco={`${intento?.id ?? 0}-${resumen ? 1 : 0}`} />
                )}
                {panelIzq === "transcripcion" && <PanelTranscripcion videoId={c.video_id} onSaltar={saltar} tiempoActual={esArchivo ? tiempoActual : null} />}
              </Pestanas>
            </Tarjeta>
          )}
        </div>

        {/* Columna del cuestionario */}
        <section aria-label="Cuestionario" className="flex min-w-0 flex-col gap-4">
          <TituloSeccion>Cuestionario</TituloSeccion>

          {c.es_creador && intento === null && onRecargar && (
            <PanelCalidad
              cuestionarioId={c.id}
              preguntas={c.preguntas}
              tieneGrupo={!!c.grupo_id}
              onSaltar={saltar}
              onRecargar={onRecargar}
            />
          )}

          {intento === null ? (
            <Tarjeta className="flex flex-col gap-4">
              {c.repaso?.vencido && (
                <Alerta tipo="advertencia" titulo="Repaso diferido pendiente">
                  Tu siguiente intento será el repaso: responderás sin ver si acertaste y, al finalizar, verás las respuestas correctas. Ayuda a
                  medir cuánto recuerdas.
                </Alerta>
              )}
              {c.repaso && !c.repaso.vencido && (
                <p className="text-sm text-suave">Tu repaso diferido estará disponible desde el {formatearFecha(c.repaso.disponible_desde)}.</p>
              )}
              {c.es_creador && (
                <Alerta tipo="info" titulo="Vista previa como estudiante">
                  Puedes probar el cuestionario tal como lo verá un estudiante. Tus respuestas de prueba no se cuentan en los resultados y se descartan al
                  salir de esta página. Para ver lo que respondieron tus estudiantes, abre{" "}
                  <Enlace href={`/cuestionarios/${c.id}/resultados`}>
                    Resultados
                  </Enlace>
                  .
                </Alerta>
              )}
              {soloPreguntas && (
                <p className="text-sm text-suave">En este cuestionario verás tu puntaje al terminar, sin retroalimentación por pregunta.</p>
              )}
              <div className="flex items-start gap-3">
                <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border-b-[3px] border-cul-naranja bg-info-fondo text-info-texto">
                  <Icono nombre="trofeo" tamano={22} />
                </span>
                <p className="text-suave">
                  <strong className="text-texto">{plural(c.preguntas.length, "pregunta")}.</strong> Tus respuestas se califican en el servidor y quedan en tu
                  historial.
                </p>
              </div>
              <Boton tamano="lg" bloque cargando={ocupado} onClick={empezar} className="sm:w-auto sm:self-start">
                {c.repaso?.vencido ? "Hacer el repaso" : c.es_creador ? "Probar como estudiante" : "Empezar cuestionario"}
                <Icono nombre="flecha" />
              </Boton>
            </Tarjeta>
          ) : (
            <>
              {c.es_creador && (
                <Alerta tipo="info" titulo="Vista previa como estudiante">
                  Tus respuestas de prueba no se cuentan en los resultados.
                </Alerta>
              )}
              {intento.tipo === "diferido" && (
                <Alerta tipo="info">
                  Estás en el <strong>repaso diferido</strong>: no verás si acertaste hasta finalizar.
                </Alerta>
              )}

              {/* Progreso de preguntas (fijo bajo la barra superior) */}
              <div className="sticky top-[4.5rem] z-10 -mx-1 rounded-xl border border-borde bg-superficie/95 px-4 py-3 shadow-tarjeta backdrop-blur">
                <div className="mb-2 flex items-center justify-between gap-3 text-sm font-semibold">
                  <span>Preguntas respondidas</span>
                  <span>
                    {respondidas} de {c.preguntas.length}
                  </span>
                </div>
                <BarraPorcentaje valor={respondidas} max={c.preguntas.length} etiqueta="Progreso del cuestionario" alto="md" />
              </div>

              {c.preguntas.map((p, i) => (
                <PreguntaCard key={`${ronda}-${p.id}`} indice={i} pregunta={p} conFeedback={conFeedback} onResponder={responder} onSaltar={saltar} />
              ))}
            </>
          )}

          {error && <Alerta tipo="error">{error}</Alerta>}

          {intento !== null && !resumen && (
            <Boton tamano="lg" bloque disabled={!todas || ocupado} cargando={ocupado} onClick={finalizar} className="sm:w-auto sm:self-start">
              {todas ? "Finalizar y ver puntaje" : `Responde todas las preguntas (${respondidas}/${c.preguntas.length})`}
            </Boton>
          )}

          {resumen && (
            <div className="flex flex-col gap-4">
              <Tarjeta className="border-t-4 border-t-cul-naranja">
                <div className="flex flex-col items-center gap-4 text-center sm:flex-row sm:text-left">
                  <AnilloPuntaje porcentaje={resumen.porcentaje} />
                  <div className="min-w-0">
                    <p className="text-sm font-semibold uppercase tracking-wide text-suave">Resultado</p>
                    <p className="text-2xl font-extrabold">
                      Puntaje: {resumen.puntaje} de {resumen.total} ({pct(resumen.porcentaje)})
                    </p>
                    {c.preguntas.length > resumen.total && (
                      <p className="text-sm text-suave">(las preguntas abiertas cuentan cuando tu docente aprueba su nota)</p>
                    )}
                    <p className="mt-1 font-semibold text-enlace">{mensajePuntaje(resumen.porcentaje)}</p>
                    {resumen.tipo === "diferido" && <p className="mt-1 text-sm">Repaso diferido completado. ¡Gracias!</p>}
                    {resumen.repaso_disponible_desde && (
                      <p className="mt-1 text-sm text-suave">
                        Tu repaso diferido estará disponible desde el {formatearFecha(resumen.repaso_disponible_desde)}. Lo verás en tu panel.
                      </p>
                    )}
                    <Boton variante="secundario" cargando={ocupado} onClick={empezar} className="mt-4">
                      <Icono nombre="repetir" /> Nuevo intento
                    </Boton>
                  </div>
                </div>
              </Tarjeta>

              {resumen.revision && (
                <div className="flex flex-col gap-3">
                  <TituloSeccion nivel={3}>Respuestas correctas del repaso</TituloSeccion>
                  {resumen.revision.map((r, i) => {
                    const seg = aSegundos(r.marca_tiempo);
                    return (
                      <Tarjeta as="article" key={r.pregunta_id} className="text-sm !p-4">
                        <p className="font-bold">
                          {i + 1}. {r.enunciado}
                        </p>
                        <p className="mt-2 flex flex-wrap items-center gap-2">
                          <span>Tu respuesta: {r.respuesta || <em>(vacía)</em>}</span>
                          {r.correcta === true && (
                            <Insignia tono="exito">
                              <Icono nombre="check" tamano={12} /> Correcta
                            </Insignia>
                          )}
                          {r.correcta === false && (
                            <Insignia tono="error">
                              <Icono nombre="x" tamano={12} /> Incorrecta
                            </Insignia>
                          )}
                        </p>
                        <p className="mt-1">
                          <strong>Respuesta correcta:</strong> {r.respuesta_correcta}
                        </p>
                        {r.explicacion && <p className="mt-1 text-suave">{r.explicacion}</p>}
                        {seg !== null && (
                          <Boton variante="secundario" tamano="sm" onClick={() => saltar(seg)} className="mt-3">
                            <Icono nombre="play" tamano={14} /> Ver en el video ({r.marca_tiempo})
                          </Boton>
                        )}
                      </Tarjeta>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
