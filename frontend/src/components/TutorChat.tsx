"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { estadoTutor, nuevaConversacionTutor, preguntarAlTutor } from "@/lib/api";
import type { EstadoTutor, MensajeTutor } from "@/lib/tipos";
import { Alerta, Boton, Icono, Spinner, Textarea, cx } from "./ui";

/** Convierte "mm:ss" (o "hh:mm:ss") en segundos; null si no es válido. */
function aSegundos(marca: string): number | null {
  const partes = marca.split(":").map(Number);
  if (!marca || partes.some((n) => Number.isNaN(n))) return null;
  return partes.reduce((acc, n) => acc * 60 + n, 0);
}

function Burbuja({ m, onSaltar }: { m: MensajeTutor; onSaltar: (segundos: number) => void }) {
  const propio = m.rol === "usuario";
  return (
    <li className={cx("flex flex-col gap-2", propio ? "items-end" : "items-start")}>
      <div
        className={cx(
          "max-w-[92%] whitespace-pre-line rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed sm:max-w-[85%]",
          propio ? "rounded-br-sm bg-primario text-sobre-primario" : "rounded-bl-sm border border-borde bg-superficie-2 text-texto",
        )}
      >
        <span className="sr-only">{propio ? "Tú: " : "Tutor: "}</span>
        {m.texto}
      </div>
      {m.citas.length > 0 && (
        <ul className="flex max-w-[92%] flex-col gap-1.5 sm:max-w-[85%]" aria-label="Citas del video">
          {m.citas.map((c) => {
            const seg = aSegundos(c.marca_tiempo);
            return (
              <li key={c.marca_tiempo} className="flex items-start gap-2 text-xs text-suave">
                <button
                  type="button"
                  onClick={() => seg !== null && onSaltar(seg)}
                  aria-label={`Ir al minuto ${c.marca_tiempo} del video`}
                  className="inline-flex min-h-9 shrink-0 items-center gap-1 rounded-full border border-info-borde bg-info-fondo px-3 text-xs font-bold text-info-texto transition hover:brightness-95 active:scale-95"
                >
                  <Icono nombre="play" tamano={11} /> {c.marca_tiempo}
                </button>
                <span className="pt-2 italic">«{c.fragmento}»</span>
              </li>
            );
          })}
        </ul>
      )}
    </li>
  );
}

/** Panel «Pregúntale al video»: chat con el tutor IA, que responde solo con base en la transcripción y cita el minuto. */
export default function TutorChat({
  cuestionarioId,
  onSaltar,
  claveRefresco,
}: {
  cuestionarioId: number;
  onSaltar: (segundos: number) => void;
  /** Al cambiar (p. ej. al empezar o terminar un intento) se vuelve a consultar si el tutor está disponible. */
  claveRefresco: string | number;
}) {
  const [estado, setEstado] = useState<EstadoTutor | null>(null);
  const [mensajes, setMensajes] = useState<MensajeTutor[]>([]);
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const lista = useRef<HTMLUListElement>(null);

  useEffect(() => {
    estadoTutor(cuestionarioId)
      .then((e) => {
        setEstado(e);
        setMensajes(e.mensajes);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Error desconocido"));
  }, [cuestionarioId, claveRefresco]);

  useEffect(() => {
    // Desplaza solo la lista de mensajes (no la página)
    lista.current?.scrollTo({ top: lista.current.scrollHeight, behavior: "smooth" });
  }, [mensajes, enviando]);

  async function enviar(pregunta: string) {
    const limpia = pregunta.trim();
    if (!limpia || enviando) return;
    setError(null);
    setEnviando(true);
    // Muestra la pregunta enseguida; si falla se retira
    const provisional: MensajeTutor = { id: -1, rol: "usuario", texto: limpia, citas: [], creado_en: new Date().toISOString() };
    setMensajes((l) => [...l, provisional]);
    setTexto("");
    try {
      const r = await preguntarAlTutor(cuestionarioId, limpia);
      setMensajes((l) => [...l.filter((m) => m.id !== -1), r.usuario, r.tutor]);
      setEstado((e) => (e ? { ...e, restantes: r.restantes } : e));
    } catch (err) {
      setMensajes((l) => l.filter((m) => m.id !== -1));
      setTexto(limpia);
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setEnviando(false);
    }
  }

  async function nueva() {
    setError(null);
    try {
      const e = await nuevaConversacionTutor(cuestionarioId);
      setEstado(e);
      setMensajes([]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    }
  }

  function alEnviar(e: FormEvent) {
    e.preventDefault();
    void enviar(texto);
  }

  if (!estado) {
    return error ? <Alerta tipo="error">{error}</Alerta> : <div className="flex items-center gap-2 text-sm text-suave"><Spinner /> Cargando el tutor…</div>;
  }

  if (!estado.habilitado) {
    return (
      <Alerta tipo="info" titulo="Pregúntale al video">
        {estado.motivo}
      </Alerta>
    );
  }

  const agotado = estado.restantes <= 0;

  return (
    <div className="flex min-w-0 flex-col gap-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-sm text-suave">
          Respondo solo con lo que dice el video y cito el minuto. {mensajes.length > 0 && "Puedes seguir preguntando."}
        </p>
        {mensajes.length > 0 && (
          <Boton variante="fantasma" tamano="sm" onClick={nueva} disabled={enviando}>
            <Icono nombre="repetir" tamano={14} /> Nueva conversación
          </Boton>
        )}
      </div>

      {mensajes.length === 0 && !enviando ? (
        <div className="flex flex-col gap-2" aria-label="Preguntas sugeridas">
          <p className="text-sm font-semibold">Prueba con una pregunta:</p>
          {estado.sugerencias.map((s) => (
            <button
              key={s}
              type="button"
              disabled={agotado}
              onClick={() => enviar(s)}
              className="min-h-11 rounded-xl border border-borde-fuerte bg-superficie px-3.5 py-2 text-left text-sm font-medium transition hover:bg-superficie-2 disabled:opacity-55"
            >
              {s}
            </button>
          ))}
        </div>
      ) : (
        <ul ref={lista} aria-live="polite" aria-label="Conversación con el tutor" className="scroll-fino flex max-h-[26rem] flex-col gap-3 overflow-y-auto pr-1">
          {mensajes.map((m) => (
            <Burbuja key={m.id} m={m} onSaltar={onSaltar} />
          ))}
          {enviando && (
            <li className="flex items-center gap-2 text-sm text-suave" role="status">
              <Spinner /> El tutor está revisando el video…
            </li>
          )}
        </ul>
      )}

      {error && <Alerta tipo="error">{error}</Alerta>}

      <form onSubmit={alEnviar} className="flex flex-col gap-2">
        <Textarea
          etiqueta="Tu pregunta sobre el video"
          ocultarEtiqueta
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              void enviar(texto);
            }
          }}
          rows={2}
          maxLength={1000}
          disabled={agotado}
          placeholder={agotado ? "Alcanzaste el límite diario de mensajes." : "Escribe tu pregunta sobre el video…"}
        />
        <div className="flex flex-wrap items-center justify-between gap-2">
          <span className="text-xs text-suave">
            {estado.restantes} de {estado.limite} mensajes disponibles hoy
          </span>
          <Boton type="submit" cargando={enviando} disabled={!texto.trim() || agotado}>
            Preguntar <Icono nombre="flecha" tamano={16} />
          </Boton>
        </div>
      </form>
    </div>
  );
}
