"use client";

import { useId, useState } from "react";
import type { NivelCalificacion, Pregunta, RespuestaServidor } from "@/lib/tipos";
import { Boton, Icono, Insignia, Textarea, cx } from "./ui";

interface Props {
  indice: number;
  pregunta: Pregunta;
  /** Envía la respuesta al servidor, que la califica y devuelve el feedback. */
  onResponder: (pregunta: Pregunta, respuesta: string) => Promise<RespuestaServidor>;
  onSaltar: (segundos: number) => void;
  /** false en repasos diferidos y en el grupo control: se registra la respuesta sin mostrar la corrección. */
  conFeedback?: boolean;
}

/** Convierte "mm:ss" (o "hh:mm:ss") en segundos; null si no es válido. */
function aSegundos(marca: string): number | null {
  const partes = marca.split(":").map(Number);
  if (!marca || partes.some((n) => Number.isNaN(n))) return null;
  return partes.reduce((acc, n) => acc * 60 + n, 0);
}

const TIPOS: Record<Pregunta["tipo"], string> = {
  opcion_multiple: "Opción múltiple",
  verdadero_falso: "Verdadero / Falso",
  abierta: "Abierta",
};

const ETIQUETA_NIVEL: Record<NivelCalificacion, string> = { insuficiente: "Insuficiente", basico: "Básico", bueno: "Bueno", excelente: "Excelente" };
const TONO_NIVEL: Record<NivelCalificacion, "error" | "aviso" | "azul" | "exito"> = {
  insuficiente: "error",
  basico: "aviso",
  bueno: "azul",
  excelente: "exito",
};

export default function PreguntaCard({ indice, pregunta, onResponder, onSaltar, conFeedback = true }: Props) {
  const idEnunciado = useId();
  const [elegida, setElegida] = useState<string | null>(null);
  const [respuestaAbierta, setRespuestaAbierta] = useState("");
  const [feedback, setFeedback] = useState<RespuestaServidor | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const esAbierta = pregunta.tipo === "abierta";
  const mostrarCorreccion = feedback !== null && feedback.con_feedback;
  const segundos = mostrarCorreccion && feedback ? aSegundos(feedback.marca_tiempo) : null;

  async function enviar(respuesta: string) {
    if (enviando || feedback) return;
    setError(null);
    setEnviando(true);
    if (!esAbierta) setElegida(respuesta);
    try {
      setFeedback(await onResponder(pregunta, respuesta));
    } catch (e) {
      setElegida(null);
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setEnviando(false);
    }
  }

  /** Estado visual de una opción: clases y, si corresponde, la etiqueta (icono + texto) que no depende del color. */
  function estadoOpcion(op: string) {
    const base =
      "flex w-full min-h-12 items-center gap-3 rounded-xl border-2 px-3 py-2.5 text-left text-base transition duration-150 disabled:cursor-default sm:px-4 ";
    if (!feedback) {
      return {
        clase: base + (elegida === op ? "border-primario bg-info-fondo " : "border-borde bg-superficie hover:border-anillo hover:bg-superficie-2 "),
        etiqueta: null,
      };
    }
    if (!feedback.con_feedback) {
      return {
        clase: base + (op === elegida ? "border-primario bg-info-fondo" : "border-borde opacity-60"),
        etiqueta: op === elegida ? { icono: "check" as const, texto: "Tu respuesta" } : null,
      };
    }
    if (op === feedback.respuesta_correcta)
      return {
        clase: base + "border-exito-solido bg-exito-fondo text-exito-texto",
        etiqueta: { icono: "check" as const, texto: "Correcta" },
      };
    if (op === elegida)
      return {
        clase: base + "border-error-solido bg-error-fondo text-error-texto",
        etiqueta: { icono: "x" as const, texto: "Tu respuesta" },
      };
    return { clase: base + "border-borde opacity-60", etiqueta: null };
  }

  return (
    <article className="anim-aparecer min-w-0 rounded-2xl border border-borde bg-superficie p-4 shadow-tarjeta sm:p-5">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="flex h-8 min-w-8 items-center justify-center rounded-full bg-primario px-2 text-sm font-bold text-sobre-primario">{indice + 1}</span>
        <Insignia>{TIPOS[pregunta.tipo]}</Insignia>
      </div>
      <p id={idEnunciado} className="mb-4 text-base font-semibold leading-snug sm:text-lg">
        {pregunta.enunciado}
      </p>

      {!esAbierta && (
        <div role="group" aria-labelledby={idEnunciado} className="flex flex-col gap-2.5">
          {pregunta.opciones.map((op, k) => {
            const { clase, etiqueta } = estadoOpcion(op);
            return (
              <button key={op} type="button" disabled={enviando || feedback !== null} onClick={() => enviar(op)} className={clase}>
                <span
                  aria-hidden="true"
                  className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full border border-current text-sm font-bold"
                >
                  {String.fromCharCode(65 + k)}
                </span>
                <span className="min-w-0 flex-1">{op}</span>
                {etiqueta && (
                  <span className="flex shrink-0 items-center gap-1 rounded-full bg-superficie/70 px-2 py-0.5 text-xs font-bold">
                    <Icono nombre={etiqueta.icono} tamano={14} />
                    {etiqueta.texto}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      {esAbierta && (
        <div className="flex flex-col gap-3">
          <Textarea
            etiqueta="Tu respuesta"
            ocultarEtiqueta
            value={respuestaAbierta}
            onChange={(e) => setRespuestaAbierta(e.target.value)}
            disabled={feedback !== null}
            rows={4}
            placeholder="Escribe tu respuesta…"
          />
          {!feedback && (
            <Boton cargando={enviando} onClick={() => enviar(respuestaAbierta)} className="self-start">
              {conFeedback ? "Enviar y ver respuesta modelo" : "Enviar respuesta"}
            </Boton>
          )}
          {mostrarCorreccion && feedback && (
            <p className="rounded-xl border border-info-borde bg-info-fondo p-3 text-info-texto">
              <strong>Respuesta modelo:</strong> {feedback.respuesta_correcta}
            </p>
          )}
          {mostrarCorreccion && feedback?.calificacion_ia && (
            <div className="rounded-xl border border-borde bg-superficie-2 p-3 text-sm" aria-label="Calificación sugerida por la IA">
              <p className="flex flex-wrap items-center gap-2 font-bold">
                Calificación sugerida: {feedback.calificacion_ia.puntaje}/100
                <Insignia tono={TONO_NIVEL[feedback.calificacion_ia.nivel]}>{ETIQUETA_NIVEL[feedback.calificacion_ia.nivel]}</Insignia>
              </p>
              <p className="mt-1.5 leading-relaxed">{feedback.calificacion_ia.retroalimentacion}</p>
              {feedback.calificacion_ia.falto && (
                <p className="mt-1.5 text-suave">
                  <strong>Qué faltó:</strong> {feedback.calificacion_ia.falto}
                </p>
              )}
              <p className="mt-2 text-xs text-suave">Es una sugerencia de la IA: la nota oficial la confirma tu docente.</p>
            </div>
          )}
        </div>
      )}

      {error && (
        <p role="alert" className="mt-3 text-sm font-semibold text-error-texto">
          {error}
        </p>
      )}

      {feedback && !feedback.con_feedback && (
        <p role="status" className="mt-3 flex items-center gap-2 text-sm font-semibold text-suave">
          <Icono nombre="check" tamano={16} /> Respuesta registrada.
        </p>
      )}

      {mostrarCorreccion && feedback && (
        <div
          role="status"
          className={cx(
            "mt-4 rounded-xl border p-4 text-sm",
            esAbierta || feedback.correcta ? "border-exito-borde bg-exito-fondo text-exito-texto" : "border-error-borde bg-error-fondo text-error-texto",
          )}
        >
          {!esAbierta && (
            <p className="flex items-center gap-2 text-base font-bold">
              <Icono nombre={feedback.correcta ? "check" : "x"} />
              {feedback.correcta ? "¡Correcto!" : "Incorrecto"}
            </p>
          )}
          {feedback.explicacion && <p className={cx("leading-relaxed", !esAbierta && "mt-1.5")}>{feedback.explicacion}</p>}
          {segundos !== null && (
            <Boton variante="secundario" tamano="sm" onClick={() => onSaltar(segundos)} className="mt-3">
              <Icono nombre="play" tamano={14} /> Ver en el video ({feedback.marca_tiempo})
            </Boton>
          )}
        </div>
      )}
    </article>
  );
}
