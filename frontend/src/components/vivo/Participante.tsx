"use client";

import { useEffect, useRef, useState } from "react";
import { Alerta, Boton, Icono, Input, Pagina, Spinner, Tarjeta, cx } from "@/components/ui";
import { unirseClaseVivo } from "@/lib/api";
import type { EstadoVivo } from "@/lib/tipos";
import { useRestanteMs, useSesionVivo } from "@/lib/vivo";
import { Forma, Podio, estiloOpcion } from "./comunes";

interface Guardado {
  token: string;
  apodo: string;
}

const clave = (pin: string) => `vivo:${pin}`;

function leerGuardado(pin: string): Guardado | null {
  try {
    const bruto = localStorage.getItem(clave(pin));
    return bruto ? (JSON.parse(bruto) as Guardado) : null;
  } catch {
    return null;
  }
}

function guardar(pin: string, datos: Guardado | null) {
  try {
    if (datos) localStorage.setItem(clave(pin), JSON.stringify(datos));
    else localStorage.removeItem(clave(pin));
  } catch {
    /* almacenamiento no disponible: se pierde la reconexión automática, nada más */
  }
}

// ---------- Pantalla para unirse ----------

function Unirse({ pinInicial, onUnido }: { pinInicial: string; onUnido: (pin: string, g: Guardado) => void }) {
  const [pin, setPin] = useState(pinInicial);
  const [apodo, setApodo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      const r = await unirseClaseVivo(pin, apodo.trim());
      guardar(r.pin, { token: r.token, apodo: r.apodo });
      onUnido(r.pin, { token: r.token, apodo: r.apodo });
    } catch (err) {
      setError(err instanceof Error ? err.message : "No se pudo unir a la clase.");
      setEnviando(false);
    }
  }

  return (
    <Pagina ancho="sm">
      <div className="mb-6 flex flex-col items-center gap-2 text-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-full bg-cul-naranja text-cul-azul-oscuro">
          <Icono nombre="vivo" tamano={30} />
        </span>
        <h1 className="text-3xl font-extrabold tracking-tight">Clase en vivo</h1>
        <p className="text-suave">Escribe el PIN que ves en la pantalla y elige un apodo. No necesitas cuenta.</p>
      </div>
      <Tarjeta>
        <form onSubmit={enviar} className="flex flex-col gap-4">
          <Input
            etiqueta="PIN de la clase"
            value={pin}
            onChange={(e) => setPin(e.target.value.replace(/\D/g, "").slice(0, 6))}
            inputMode="numeric"
            autoComplete="off"
            maxLength={6}
            required
            placeholder="123456"
            className="text-center font-mono text-3xl font-bold tracking-[0.3em]"
          />
          <Input
            etiqueta="Tu apodo"
            ayuda="Entre 2 y 20 caracteres. Lo verán todos en la pantalla."
            value={apodo}
            onChange={(e) => setApodo(e.target.value)}
            minLength={2}
            maxLength={20}
            required
            autoComplete="nickname"
            placeholder="Ej.: Tigre"
            className="text-center text-xl font-bold"
          />
          {error && <Alerta tipo="error">{error}</Alerta>}
          <Boton type="submit" tamano="lg" bloque cargando={enviando} disabled={pin.length < 6 || apodo.trim().length < 2}>
            {enviando ? "Entrando…" : "Unirme"}
          </Boton>
        </form>
      </Tarjeta>
    </Pagina>
  );
}

// ---------- Juego ----------

function Insignias({ estado }: { estado: EstadoVivo }) {
  const yo = estado.yo;
  if (!yo) return null;
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-borde bg-superficie px-4 py-2 shadow-tarjeta">
      <span className="min-w-0 truncate font-bold">{yo.apodo}</span>
      <span className="flex shrink-0 items-center gap-3 text-sm font-semibold">
        <span>
          Puesto <strong className="text-lg">{yo.posicion}</strong>
        </span>
        <span aria-hidden="true">·</span>
        <span>
          <strong className="text-lg tabular-nums">{yo.puntos}</strong> pts
        </span>
      </span>
    </div>
  );
}

function Espera({ estado }: { estado: EstadoVivo }) {
  return (
    <Tarjeta className="flex flex-col items-center gap-3 py-10 text-center">
      <Spinner tamano={36} />
      <h2 className="text-2xl font-extrabold">¡Estás dentro, {estado.yo?.apodo}!</h2>
      <p className="text-suave">Mira la pantalla del salón. La clase empezará cuando el docente lo indique.</p>
      <p className="text-sm font-semibold" aria-live="polite">
        {estado.num_participantes} {estado.num_participantes === 1 ? "participante" : "participantes"} conectados
      </p>
    </Tarjeta>
  );
}

function Pregunta({ estado, restanteMs, onResponder }: { estado: EstadoVivo; restanteMs: number; onResponder: (r: string) => Promise<void> }) {
  const p = estado.pregunta!;
  const [texto, setTexto] = useState("");
  const [enviando, setEnviando] = useState<string | null>(null);
  const yaRespondio = estado.yo?.respondio ?? false;
  const elegida = estado.yo?.mi_respuesta ?? enviando;
  const fraccion = Math.min(1, Math.max(0, restanteMs / (estado.segundos * 1000)));
  const segundos = Math.ceil(restanteMs / 1000);
  const largas = p.opciones.some((o) => o.length > 22);

  async function elegir(r: string) {
    if (yaRespondio || enviando) return;
    setEnviando(r);
    await onResponder(r);
  }

  return (
    <div className="flex flex-col gap-4">
      <div>
        <div className="mb-1 flex items-center justify-between text-sm font-semibold">
          <span>
            Pregunta {estado.indice + 1} de {estado.total_preguntas}
          </span>
          <span role="timer" aria-label={`${segundos} segundos restantes`} className="tabular-nums">
            {segundos} s
          </span>
        </div>
        <div className="h-3 overflow-hidden rounded-full bg-pista" aria-hidden="true">
          <div className={cx("h-full rounded-full", segundos <= 5 ? "bg-error-solido" : "bg-cul-naranja")} style={{ width: `${fraccion * 100}%`, transition: "width 0.15s linear" }} />
        </div>
      </div>
      <h2 className="text-xl font-extrabold leading-snug sm:text-2xl">{p.enunciado}</h2>

      {p.tipo === "abierta" ? (
        yaRespondio ? (
          <Alerta tipo="exito">Respuesta enviada. Espera a que termine el tiempo.</Alerta>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (texto.trim()) void elegir(texto.trim());
            }}
            className="flex flex-col gap-3"
          >
            <Input etiqueta="Tu respuesta" value={texto} onChange={(e) => setTexto(e.target.value)} maxLength={200} autoComplete="off" />
            <Boton type="submit" tamano="lg" bloque cargando={!!enviando} disabled={!texto.trim()}>
              Enviar respuesta
            </Boton>
          </form>
        )
      ) : (
        <>
          <div className={cx("grid gap-3", largas ? "grid-cols-1" : "grid-cols-2")}>
            {p.opciones.map((o, i) => {
              const e = estiloOpcion(i);
              const esMia = elegida === o;
              return (
                <button
                  key={o}
                  type="button"
                  disabled={yaRespondio || !!enviando}
                  aria-pressed={esMia}
                  onClick={() => void elegir(o)}
                  className={cx(
                    "flex min-h-20 items-center gap-3 rounded-2xl px-4 py-3 text-left text-lg font-bold shadow-md transition active:scale-[0.97]",
                    largas ? "justify-start" : "flex-col justify-center text-center",
                    e.fondo,
                    (yaRespondio || enviando) && !esMia && "opacity-35",
                    esMia && "ring-4 ring-texto ring-offset-2 ring-offset-fondo",
                  )}
                >
                  <Forma forma={e.forma} tamano={largas ? 28 : 32} />
                  <span className="sr-only">Opción {e.letra}:</span>
                  <span className="min-w-0 break-words">{o}</span>
                </button>
              );
            })}
          </div>
          {yaRespondio && (
            <p className="flex items-center justify-center gap-2 text-center font-semibold text-suave" aria-live="polite">
              <Spinner tamano={16} /> Respuesta enviada. Esperando a los demás…
            </p>
          )}
        </>
      )}
    </div>
  );
}

function Feedback({ estado }: { estado: EstadoVivo }) {
  const yo = estado.yo!;
  const r = estado.resultados;
  const abierta = estado.pregunta?.tipo === "abierta";
  const sinResponder = !yo.respondio;
  const acierto = yo.correcta === true;
  const tono = abierta && yo.respondio ? "info" : acierto ? "exito" : "error";
  return (
    <div className="flex flex-col gap-4">
      <div
        className={cx(
          "anim-rebote flex flex-col items-center gap-2 rounded-2xl border-2 p-6 text-center",
          tono === "exito" && "border-exito-borde bg-exito-fondo text-exito-texto",
          tono === "error" && "border-error-borde bg-error-fondo text-error-texto",
          tono === "info" && "border-info-borde bg-info-fondo text-info-texto",
        )}
        role="status"
      >
        <Icono nombre={tono === "error" ? "x" : tono === "exito" ? "check" : "info"} tamano={44} />
        <p className="text-3xl font-extrabold">
          {sinResponder ? "Sin respuesta" : abierta ? "Respuesta recibida" : acierto ? "¡Correcto!" : "Incorrecto"}
        </p>
        {!abierta && <p className="text-xl font-bold">+{yo.puntos_ganados ?? 0} puntos</p>}
        {abierta && <p className="text-sm">Las preguntas abiertas no suman puntos.</p>}
      </div>
      {!abierta && !acierto && r?.correcta && (
        <p className="rounded-xl border border-borde bg-superficie p-4 text-sm">
          Respuesta correcta: <strong>{r.correcta}</strong>
        </p>
      )}
      {r?.explicacion && !abierta && <p className="text-sm text-suave">{r.explicacion}</p>}
      <div className="grid grid-cols-2 gap-3 text-center">
        <div className="rounded-xl border border-borde bg-superficie p-4 shadow-tarjeta">
          <p className="text-xs font-semibold uppercase text-suave">Tu puesto</p>
          <p className="text-4xl font-extrabold">{yo.posicion}</p>
        </div>
        <div className="rounded-xl border border-borde bg-superficie p-4 shadow-tarjeta">
          <p className="text-xs font-semibold uppercase text-suave">Tus puntos</p>
          <p className="text-4xl font-extrabold tabular-nums">{yo.puntos}</p>
        </div>
      </div>
      <p className="text-center text-sm text-suave">Mira la pantalla: la siguiente pregunta viene en breve.</p>
    </div>
  );
}

function Final({ estado, onSalir }: { estado: EstadoVivo; onSalir: () => void }) {
  const yo = estado.yo;
  return (
    <div className="flex flex-col items-center gap-6 text-center">
      <h2 className="text-3xl font-extrabold">¡La clase terminó!</h2>
      {yo && (
        <div className="anim-rebote w-full rounded-2xl border-2 border-cul-naranja bg-superficie p-6 shadow-tarjeta">
          <p className="text-sm font-semibold uppercase text-suave">Quedaste en el puesto</p>
          <p className="text-7xl font-extrabold text-enlace">{yo.posicion}</p>
          <p className="text-lg font-bold tabular-nums">
            {yo.puntos} puntos · de {estado.num_participantes}
          </p>
        </div>
      )}
      <div className="w-full rounded-2xl bg-cul-azul-oscuro p-4 pt-8 text-white">
        <Podio ranking={estado.ranking} resaltar={yo?.apodo} />
      </div>
      <Boton variante="secundario" onClick={onSalir}>
        Unirme a otra clase
      </Boton>
    </div>
  );
}

function Juego({ pin, guardado, onSalir }: { pin: string; guardado: Guardado; onSalir: () => void }) {
  const sesion = useSesionVivo({ pin, rol: "participante", tokenParticipante: guardado.token });
  const { estado } = sesion;
  const restanteMs = useRestanteMs(estado);
  const salio = useRef(false);

  useEffect(() => {
    if (sesion.fatal && !salio.current) {
      salio.current = true;
      guardar(pin, null);
    }
  }, [sesion.fatal, pin]);

  if (sesion.fatal) {
    return (
      <Pagina ancho="sm">
        <Alerta tipo="error">
          {sesion.fatal === 4404 ? "Esta clase ya terminó o el PIN no existe." : "Tu sesión de participante ya no es válida."}
        </Alerta>
        <Boton className="mt-4" onClick={onSalir}>
          Volver a unirme
        </Boton>
      </Pagina>
    );
  }

  return (
    <Pagina ancho="sm" className="flex flex-col gap-4">
      {sesion.modo !== "ws" && estado && (
        <p className="rounded-lg bg-aviso-fondo px-3 py-1.5 text-center text-xs font-semibold text-aviso-texto" role="status">
          {sesion.modo === "sondeo" ? "Conexión de respaldo activa" : "Reconectando…"}
        </p>
      )}
      {estado && <Insignias estado={estado} />}
      {sesion.error && <Alerta tipo="error">{sesion.error}</Alerta>}
      {!estado && (
        <div className="flex items-center justify-center gap-3 py-16">
          <Spinner /> Conectando con la clase…
        </div>
      )}
      {estado?.estado === "lobby" && <Espera estado={estado} />}
      {estado?.estado === "pregunta" && estado.pregunta && (
        <Pregunta key={estado.pregunta.id} estado={estado} restanteMs={restanteMs} onResponder={sesion.responder} />
      )}
      {estado?.estado === "resultados_pregunta" && estado.yo && <Feedback estado={estado} />}
      {estado?.estado === "finalizada" && <Final estado={estado} onSalir={onSalir} />}
    </Pagina>
  );
}

export default function Participante({ pinInicial = "" }: { pinInicial?: string }) {
  const [pinActivo, setPinActivo] = useState<string | null>(null);
  const [guardado, setGuardado] = useState<Guardado | null>(null);
  const [listo, setListo] = useState(false);

  // Si ya se había unido a este PIN en este navegador, se reconecta sin pedir nada
  useEffect(() => {
    (async () => {
      if (/^\d{6}$/.test(pinInicial)) {
        const g = leerGuardado(pinInicial);
        if (g) {
          setPinActivo(pinInicial);
          setGuardado(g);
        }
      }
      setListo(true);
    })();
  }, [pinInicial]);

  if (!listo) {
    return (
      <Pagina ancho="sm">
        <div className="flex justify-center py-16">
          <Spinner tamano={32} />
        </div>
      </Pagina>
    );
  }

  if (pinActivo && guardado) {
    return (
      <Juego
        pin={pinActivo}
        guardado={guardado}
        onSalir={() => {
          guardar(pinActivo, null);
          setPinActivo(null);
          setGuardado(null);
        }}
      />
    );
  }

  return (
    <Unirse
      pinInicial={pinInicial}
      onUnido={(pin, g) => {
        setPinActivo(pin);
        setGuardado(g);
      }}
    />
  );
}
