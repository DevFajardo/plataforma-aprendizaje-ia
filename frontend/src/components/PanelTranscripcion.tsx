"use client";

import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import { descargarSubtitulos, descargarTranscripcion, obtenerTranscripcion } from "@/lib/api";
import type { TranscripcionVideo } from "@/lib/tipos";
import { Alerta, Boton, Icono, Input, Spinner, cx } from "./ui";

function marca(segundos: number): string {
  const h = Math.floor(segundos / 3600);
  const m = Math.floor((segundos % 3600) / 60);
  const s = Math.floor(segundos % 60);
  const mm = String(m).padStart(2, "0");
  const ss = String(s).padStart(2, "0");
  return h > 0 ? `${h}:${mm}:${ss}` : `${mm}:${ss}`;
}

/** Resalta las coincidencias de `busqueda` dentro de `texto`. */
function Resaltado({ texto, busqueda }: { texto: string; busqueda: string }) {
  if (!busqueda) return <>{texto}</>;
  const partes = texto.split(new RegExp(`(${busqueda.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "i"));
  return (
    <>
      {partes.map((p, i) =>
        p.toLowerCase() === busqueda.toLowerCase() ? (
          <mark key={i} className="rounded bg-cul-amarillo px-0.5 text-cul-azul-oscuro">
            {p}
          </mark>
        ) : (
          <Fragment key={i}>{p}</Fragment>
        ),
      )}
    </>
  );
}

/**
 * Panel «Transcripción»: lista de segmentos clicables con su marca de tiempo, buscador y descargas.
 * Con el reproductor HTML5 (`tiempoActual` definido) resalta el segmento que se está diciendo; con YouTube/Vimeo
 * (iframe) basta la lista clicable.
 */
export default function PanelTranscripcion({
  videoId,
  onSaltar,
  tiempoActual,
}: {
  videoId: number;
  onSaltar: (segundos: number) => void;
  tiempoActual?: number | null;
}) {
  const [datos, setDatos] = useState<TranscripcionVideo | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busqueda, setBusqueda] = useState("");
  const [descargando, setDescargando] = useState(false);
  const contenedor = useRef<HTMLUListElement>(null);

  useEffect(() => {
    obtenerTranscripcion(videoId)
      .then(setDatos)
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
  }, [videoId]);

  const activo = useMemo(() => {
    if (!datos || tiempoActual == null) return -1;
    let idx = -1;
    datos.segmentos.forEach((s, i) => {
      if (s.inicio <= tiempoActual) idx = i;
    });
    return idx;
  }, [datos, tiempoActual]);

  // Mantiene visible el segmento actual dentro de la lista (sin mover la página)
  useEffect(() => {
    if (activo < 0 || busqueda) return;
    const el = contenedor.current?.querySelector<HTMLElement>(`[data-seg="${activo}"]`);
    const caja = contenedor.current;
    if (el && caja) caja.scrollTo({ top: el.offsetTop - caja.clientHeight / 2 + el.clientHeight / 2, behavior: "smooth" });
  }, [activo, busqueda]);

  const q = busqueda.trim();
  const visibles = datos ? datos.segmentos.map((s, i) => ({ s, i })).filter(({ s }) => !q || s.texto.toLowerCase().includes(q.toLowerCase())) : [];

  async function descargar(fn: (id: number) => Promise<void>) {
    setDescargando(true);
    try {
      await fn(videoId);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setDescargando(false);
    }
  }

  if (error && !datos) return <Alerta tipo="error">{error}</Alerta>;
  if (!datos)
    return (
      <div className="flex items-center gap-2 text-sm text-suave">
        <Spinner /> Cargando la transcripción…
      </div>
    );

  return (
    <div className="flex min-w-0 flex-col gap-3">
      <div className="flex flex-wrap gap-2">
        <Boton variante="secundario" tamano="sm" disabled={descargando} onClick={() => descargar(descargarTranscripcion)}>
          <Icono nombre="descargar" tamano={14} /> Transcripción (.txt)
        </Boton>
        <Boton variante="secundario" tamano="sm" disabled={descargando} onClick={() => descargar(descargarSubtitulos)}>
          <Icono nombre="descargar" tamano={14} /> Subtítulos (.vtt)
        </Boton>
      </div>
      <Input
        etiqueta="Buscar en la transcripción"
        type="search"
        value={busqueda}
        onChange={(e) => setBusqueda(e.target.value)}
        placeholder="Escribe una palabra…"
        ayuda={q ? `${visibles.length} resultado(s)` : undefined}
      />
      {error && <Alerta tipo="error">{error}</Alerta>}
      {visibles.length === 0 ? (
        <p className="text-sm text-suave">No hay segmentos que coincidan con «{q}».</p>
      ) : (
        <ul ref={contenedor} aria-label="Segmentos de la transcripción" className="scroll-fino relative flex max-h-[24rem] flex-col gap-0.5 overflow-y-auto pr-1">
          {visibles.map(({ s, i }) => (
            <li key={i} data-seg={i}>
              <button
                type="button"
                onClick={() => onSaltar(s.inicio)}
                aria-current={i === activo ? "true" : undefined}
                className={cx(
                  "flex min-h-11 w-full items-start gap-3 rounded-lg px-2.5 py-2 text-left text-sm transition hover:bg-superficie-2",
                  i === activo && "bg-info-fondo font-semibold text-info-texto",
                )}
              >
                <span className="shrink-0 pt-0.5 font-mono text-xs font-bold text-enlace">▶ {marca(s.inicio)}</span>
                <span className="min-w-0 flex-1">
                  <Resaltado texto={s.texto} busqueda={q} />
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
