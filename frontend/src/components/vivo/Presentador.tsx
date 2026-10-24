"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import QRCode from "qrcode";
import { useEffect, useMemo, useState } from "react";
import { Alerta, Boton, Icono, Spinner, cx } from "@/components/ui";
import { obtenerSesionVivo } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import type { EstadoVivo, SesionVivoInfo } from "@/lib/tipos";
import { origenPublico } from "@/lib/urlPublica";
import { useRestanteMs, useSesionVivo } from "@/lib/vivo";
import { AroTemporizador, Forma, Podio, estiloOpcion } from "./comunes";

function CodigoQR({ url }: { url: string }) {
  const [src, setSrc] = useState<string | null>(null);
  useEffect(() => {
    let activo = true;
    QRCode.toDataURL(url, { margin: 1, width: 560, color: { dark: "#172741", light: "#ffffff" } })
      .then((d) => activo && setSrc(d))
      .catch(() => activo && setSrc(null));
    return () => {
      activo = false;
    };
  }, [url]);
  return (
    <div className="flex aspect-square w-full max-w-72 items-center justify-center rounded-2xl bg-white p-3 shadow-lg lg:max-w-80">
      {src ? (
        // eslint-disable-next-line @next/next/no-img-element -- data URL generada en el navegador
        <img src={src} alt={`Código QR para unirse: ${url}`} className="h-full w-full" />
      ) : (
        <Spinner />
      )}
    </div>
  );
}

function Lobby({ estado, origen }: { estado: EstadoVivo; origen: string }) {
  const url = `${origen}/vivo/${estado.pin}`;
  return (
    <div className="grid items-center gap-8 lg:grid-cols-[auto_1fr] lg:gap-14">
      <div className="flex flex-col items-center gap-4">
        <CodigoQR url={url} />
        <p className="max-w-72 text-center text-sm text-white/80 lg:max-w-80">Escanea el código con la cámara del celular</p>
      </div>
      <div className="min-w-0">
        <p className="text-lg font-semibold text-white/85 sm:text-2xl">
          Entra a <span className="font-extrabold text-cul-amarillo-vivo">{origen.replace(/^https?:\/\//, "")}/vivo</span> e ingresa el PIN
        </p>
        <p
          className="my-3 font-mono text-[clamp(3.5rem,14vw,9rem)] font-extrabold leading-none tracking-[0.12em] text-white"
          aria-label={`PIN ${estado.pin.split("").join(" ")}`}
        >
          {estado.pin}
        </p>
        <p className="mb-4 flex items-center gap-3 text-2xl font-bold sm:text-3xl" aria-live="polite">
          <Icono nombre="grupo" tamano={32} className="text-cul-naranja" />
          {estado.num_participantes} {estado.num_participantes === 1 ? "participante" : "participantes"}
        </p>
        <ul className="flex max-h-56 flex-wrap gap-2 overflow-y-auto scroll-fino sm:max-h-72" aria-label="Participantes conectados">
          {estado.participantes.length === 0 && <li className="text-lg text-white/70">Esperando a que se unan…</li>}
          {estado.participantes.map((a) => (
            <li key={a} className="anim-rebote rounded-full bg-white/15 px-4 py-1.5 text-lg font-bold sm:text-xl">
              {a}
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

function Opciones({ estado }: { estado: EstadoVivo }) {
  const p = estado.pregunta!;
  if (p.tipo === "abierta") {
    return <p className="rounded-2xl bg-white/10 p-6 text-center text-xl font-semibold sm:text-2xl">Pregunta abierta: los participantes escriben su respuesta en el celular.</p>;
  }
  return (
    <ul className="grid gap-3 sm:grid-cols-2 sm:gap-4">
      {p.opciones.map((o, i) => {
        const e = estiloOpcion(i);
        return (
          <li key={o} className={cx("flex min-h-20 items-center gap-4 rounded-2xl px-5 py-4 text-xl font-bold sm:min-h-28 sm:text-3xl", e.fondo)}>
            <Forma forma={e.forma} tamano={36} />
            <span className="sr-only">Opción {e.letra}:</span>
            <span className="min-w-0">{o}</span>
          </li>
        );
      })}
    </ul>
  );
}

function Pregunta({ estado, restanteMs }: { estado: EstadoVivo; restanteMs: number }) {
  const p = estado.pregunta!;
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-start justify-between gap-4 sm:gap-8">
        <h2 className="min-w-0 flex-1 text-2xl font-extrabold leading-tight sm:text-4xl lg:text-5xl">{p.enunciado}</h2>
        <AroTemporizador restanteMs={restanteMs} totalMs={estado.segundos * 1000} tamano={112} />
      </div>
      <p className="text-xl font-bold sm:text-2xl" aria-live="polite">
        <span className="text-cul-amarillo-vivo">{estado.respondieron}</span> de {estado.num_participantes} respondieron
      </p>
      <Opciones estado={estado} />
    </div>
  );
}

/** Nube simple de respuestas abiertas: el tamaño de cada palabra crece con su frecuencia. */
function NubeAbiertas({ respuestas }: { respuestas: string[] }) {
  const items = useMemo(() => {
    const cuenta = new Map<string, { texto: string; n: number }>();
    for (const r of respuestas) {
      const clave = r.trim().toLowerCase();
      if (!clave) continue;
      const previo = cuenta.get(clave);
      if (previo) previo.n += 1;
      else cuenta.set(clave, { texto: r.trim(), n: 1 });
    }
    return [...cuenta.values()].sort((a, b) => b.n - a.n).slice(0, 60);
  }, [respuestas]);
  if (items.length === 0) return <p className="text-xl text-white/80">Nadie respondió esta pregunta.</p>;
  const max = items[0].n;
  return (
    <ul className="flex flex-wrap items-center gap-3" aria-label="Respuestas de los participantes">
      {items.map((it) => (
        <li
          key={it.texto}
          className="rounded-xl bg-white/15 px-4 py-2 font-bold"
          style={{ fontSize: `${1 + (it.n / max) * 1.2}rem` }}
        >
          {it.texto}
          {it.n > 1 && <span className="ml-2 text-sm text-cul-amarillo-vivo">×{it.n}</span>}
        </li>
      ))}
    </ul>
  );
}

function Resultados({ estado }: { estado: EstadoVivo }) {
  const r = estado.resultados!;
  const p = estado.pregunta!;
  const total = Math.max(1, r.respondieron);
  return (
    <div className="flex flex-col gap-6">
      <h2 className="text-xl font-extrabold leading-tight sm:text-3xl">{p.enunciado}</h2>
      <div className="grid gap-8 lg:grid-cols-[3fr_2fr]">
        <div className="flex flex-col gap-3">
          {p.tipo === "abierta" ? (
            <NubeAbiertas respuestas={r.abiertas} />
          ) : (
            r.distribucion.map((d, i) => {
              const e = estiloOpcion(i);
              const pct = Math.round((d.cantidad / total) * 100);
              return (
                <div
                  key={d.opcion}
                  className={cx("rounded-2xl p-3 sm:p-4", d.correcta ? "bg-white/20 ring-4 ring-cul-amarillo-vivo" : "bg-white/10 opacity-80")}
                >
                  <div className="mb-2 flex items-center gap-3 text-lg font-bold sm:text-2xl">
                    <Forma forma={e.forma} tamano={26} />
                    <span className="min-w-0 flex-1">{d.opcion}</span>
                    {d.correcta && (
                      <span className="flex shrink-0 items-center gap-1 rounded-full bg-cul-amarillo-vivo px-3 py-0.5 text-sm font-extrabold text-cul-azul-oscuro sm:text-base">
                        <Icono nombre="check" tamano={18} /> Correcta
                      </span>
                    )}
                    <span className="w-12 shrink-0 text-right tabular-nums">{d.cantidad}</span>
                  </div>
                  <div className="h-5 overflow-hidden rounded-full bg-black/25" role="img" aria-label={`${d.cantidad} respuestas, ${pct}%`}>
                    <div className={cx("h-full rounded-full transition-[width] duration-700", e.barra)} style={{ width: `${pct}%` }} />
                  </div>
                </div>
              );
            })
          )}
          {r.explicacion && p.tipo !== "abierta" && <p className="rounded-xl bg-white/10 p-4 text-base sm:text-lg">{r.explicacion}</p>}
        </div>
        <div>
          <h3 className="mb-3 text-xl font-extrabold sm:text-2xl">Los 5 mejores</h3>
          <ol className="flex flex-col gap-2">
            {estado.ranking.map((q) => (
              <li key={q.apodo} className="flex items-center gap-3 rounded-xl bg-white/10 px-4 py-2.5 text-lg font-bold sm:text-xl">
                <span className="w-7 shrink-0 text-cul-amarillo-vivo">{q.posicion}.</span>
                <span className="min-w-0 flex-1 truncate">{q.apodo}</span>
                <span className="tabular-nums">{q.puntos}</span>
              </li>
            ))}
            {estado.ranking.length === 0 && <li className="text-white/70">Aún sin puntos.</li>}
          </ol>
        </div>
      </div>
    </div>
  );
}

function Final({ estado, info }: { estado: EstadoVivo; info: SesionVivoInfo }) {
  const resto = estado.ranking.slice(3);
  return (
    <div className="flex flex-col items-center gap-8 text-center">
      <h2 className="text-3xl font-extrabold sm:text-5xl">¡Podio final!</h2>
      {estado.ranking.length === 0 ? <p className="text-xl">Nadie participó en esta clase.</p> : <Podio ranking={estado.ranking} grande />}
      {resto.length > 0 && (
        <ol className="flex w-full max-w-md flex-col gap-2">
          {resto.map((q) => (
            <li key={q.apodo} className="flex items-center gap-3 rounded-xl bg-white/10 px-4 py-2.5 text-lg font-bold">
              <span className="w-7 shrink-0 text-cul-amarillo-vivo">{q.posicion}.</span>
              <span className="min-w-0 flex-1 truncate text-left">{q.apodo}</span>
              <span className="tabular-nums">{q.puntos}</span>
            </li>
          ))}
        </ol>
      )}
      <div className="flex flex-wrap justify-center gap-3">
        <Link
          href={`/cuestionarios/${info.cuestionario_id}/resultados`}
          className="inline-flex min-h-12 items-center rounded-lg bg-cul-naranja px-6 font-bold text-cul-azul-oscuro hover:brightness-110"
        >
          Ver historial de sesiones
        </Link>
        <Link href={`/cuestionarios/${info.cuestionario_id}`} className="inline-flex min-h-12 items-center rounded-lg border border-white/40 px-6 font-semibold hover:bg-white/10">
          Volver al cuestionario
        </Link>
      </div>
    </div>
  );
}

export default function Presentador() {
  const { usuario, cargando } = useRequiereLogin();
  const { id } = useParams<{ id: string }>();
  const [info, setInfo] = useState<SesionVivoInfo | null>(null);
  const [errorInfo, setErrorInfo] = useState<string | null>(null);
  const [pantallaCompleta, setPantallaCompleta] = useState(false);
  const [origen, setOrigen] = useState("");

  useEffect(() => {
    if (!usuario) return;
    obtenerSesionVivo(Number(id))
      .then(setInfo)
      .catch((e) => setErrorInfo(e instanceof Error ? e.message : "No se pudo abrir la sesión."));
  }, [usuario, id]);

  useEffect(() => {
    const t = setTimeout(() => setOrigen(origenPublico()), 0);
    const alCambiar = () => setPantallaCompleta(!!document.fullscreenElement);
    document.addEventListener("fullscreenchange", alCambiar);
    return () => {
      clearTimeout(t);
      document.removeEventListener("fullscreenchange", alCambiar);
    };
  }, []);

  const sesion = useSesionVivo({ pin: info?.pin ?? null, rol: "presentador", sesionId: info?.id });
  const { estado } = sesion;
  const restanteMs = useRestanteMs(estado);

  async function alternarPantallaCompleta() {
    try {
      if (document.fullscreenElement) await document.exitFullscreen();
      else await document.documentElement.requestFullscreen();
    } catch {
      /* el navegador puede negar la pantalla completa */
    }
  }

  const ultima = !!estado && estado.indice + 1 >= estado.total_preguntas;
  const [confirmarFin, setConfirmarFin] = useState(false);

  return (
    <div className="fixed inset-0 z-[70] overflow-y-auto bg-cul-azul-oscuro text-white" data-presentador>
      <div className="mx-auto flex min-h-full w-full max-w-7xl flex-col gap-6 px-4 py-4 sm:px-8 sm:py-6">
        <header className="flex flex-wrap items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="flex items-center gap-2 text-sm font-bold uppercase tracking-wider text-cul-naranja">
              <Icono nombre="vivo" tamano={18} /> Clase en vivo
            </p>
            <h1 className="truncate text-lg font-bold sm:text-xl">{info?.titulo ?? (errorInfo || sesion.fatal ? "Clase no disponible" : "Cargando…")}</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            {estado && estado.estado !== "lobby" && estado.estado !== "finalizada" && (
              <span className="rounded-full bg-white/15 px-3 py-1 text-sm font-bold">
                Pregunta {estado.indice + 1} de {estado.total_preguntas}
              </span>
            )}
            {sesion.modo === "sondeo" && <span className="rounded-full bg-cul-amarillo px-3 py-1 text-sm font-bold text-cul-azul-oscuro">Modo de respaldo</span>}
            {sesion.modo === "conectando" && !errorInfo && !sesion.fatal && <span className="rounded-full bg-white/15 px-3 py-1 text-sm font-semibold">Conectando…</span>}
            <button
              type="button"
              onClick={alternarPantallaCompleta}
              className="inline-flex min-h-11 items-center gap-2 rounded-lg border border-white/40 px-4 text-sm font-semibold hover:bg-white/10"
            >
              <Icono nombre={pantallaCompleta ? "contraer" : "expandir"} tamano={18} />
              <span className="hidden sm:inline">{pantallaCompleta ? "Salir de pantalla completa" : "Pantalla completa"}</span>
              <span className="sr-only sm:hidden">Pantalla completa</span>
            </button>
          </div>
        </header>

        {(errorInfo || sesion.fatal) && (
          <Alerta tipo="error">
            {errorInfo ?? "Esta clase en vivo ya no está disponible."}{" "}
            <Link href="/cuestionarios" className="font-bold underline">
              Volver a mis cuestionarios
            </Link>
          </Alerta>
        )}
        {sesion.error && <Alerta tipo="error">{sesion.error}</Alerta>}

        <main id="contenido" tabIndex={-1} className="flex-1 outline-none">
          {cargando || (!estado && !errorInfo && !sesion.fatal) ? (
            <div className="flex items-center justify-center gap-3 py-20 text-xl">
              <Spinner /> Preparando la sesión…
            </div>
          ) : null}
          {estado && info && estado.estado === "lobby" && <Lobby estado={estado} origen={origen} />}
          {estado && estado.estado === "pregunta" && estado.pregunta && <Pregunta estado={estado} restanteMs={restanteMs} />}
          {estado && estado.estado === "resultados_pregunta" && estado.pregunta && estado.resultados && <Resultados estado={estado} />}
          {estado && info && estado.estado === "finalizada" && <Final estado={estado} info={info} />}
        </main>

        {estado && estado.estado !== "finalizada" && (
          <footer className="sticky bottom-0 -mx-4 flex flex-wrap items-center justify-between gap-3 border-t border-white/15 bg-cul-azul-oscuro/95 px-4 py-3 backdrop-blur sm:-mx-8 sm:px-8">
            {confirmarFin ? (
              <div className="flex flex-wrap items-center gap-3">
                <span className="font-semibold">¿Terminar la clase ahora?</span>
                <Boton variante="peligro" onClick={() => void sesion.accion("finalizar")}>
                  Sí, finalizar
                </Boton>
                <button type="button" onClick={() => setConfirmarFin(false)} className="min-h-11 rounded-lg px-4 font-semibold hover:bg-white/10">
                  Cancelar
                </button>
              </div>
            ) : (
              <button type="button" onClick={() => setConfirmarFin(true)} className="min-h-11 rounded-lg border border-white/30 px-4 text-sm font-semibold hover:bg-white/10">
                Finalizar clase
              </button>
            )}
            <div className="flex flex-wrap gap-3">
              {estado.estado === "lobby" && (
                <Boton tamano="lg" onClick={() => void sesion.accion("iniciar")} className="bg-cul-naranja! text-cul-azul-oscuro!">
                  <Icono nombre="play" /> Iniciar ({estado.num_participantes})
                </Boton>
              )}
              {estado.estado === "pregunta" && (
                <Boton tamano="lg" onClick={() => void sesion.accion("saltar")} className="bg-cul-naranja! text-cul-azul-oscuro!">
                  Saltar al resultado <Icono nombre="flecha" />
                </Boton>
              )}
              {estado.estado === "resultados_pregunta" && (
                <Boton tamano="lg" onClick={() => void sesion.accion("siguiente")} className="bg-cul-naranja! text-cul-azul-oscuro!">
                  {ultima ? "Ver podio" : "Siguiente pregunta"} <Icono nombre="flecha" />
                </Boton>
              )}
            </div>
          </footer>
        )}
      </div>
    </div>
  );
}
