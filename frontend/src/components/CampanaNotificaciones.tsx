"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { contarNotificaciones, listarNotificaciones, marcarNotificacionLeida, marcarTodasLeidas } from "@/lib/api";
import type { Notificacion } from "@/lib/tipos";
import ItemNotificacion from "./ItemNotificacion";
import { Icono, Spinner } from "./ui";

const INTERVALO_MS = 60_000; // el contador se consulta cada 60 s (sin WebSocket)

/** Campana de la barra superior: contador de no leídas y panel desplegable (pantalla completa en móvil). */
export default function CampanaNotificaciones() {
  const ruta = usePathname();
  const [noLeidas, setNoLeidas] = useState(0);
  const [abiertoEn, setAbiertoEn] = useState<string | null>(null); // ruta en la que se abrió: al navegar se cierra
  const [items, setItems] = useState<Notificacion[] | null>(null);
  const [error, setError] = useState(false);
  const caja = useRef<HTMLDivElement>(null);
  const boton = useRef<HTMLButtonElement>(null);
  const abierto = abiertoEn === ruta;

  const contar = useCallback(async () => {
    try {
      setNoLeidas((await contarNotificaciones()).no_leidas);
    } catch {
      /* sin conexión: se reintenta en el siguiente ciclo */
    }
  }, []);

  useEffect(() => {
    const primero = setTimeout(() => void contar(), 0);
    const t = setInterval(() => {
      if (document.visibilityState === "visible") void contar();
    }, INTERVALO_MS);
    return () => {
      clearTimeout(primero);
      clearInterval(t);
    };
  }, [contar]);

  useEffect(() => {
    if (!abierto) return;
    let activo = true;
    listarNotificaciones(1, 8)
      .then((p) => {
        if (!activo) return;
        setItems(p.items);
        setNoLeidas(p.no_leidas);
        setError(false);
      })
      .catch(() => activo && setError(true));
    function alTeclear(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setAbiertoEn(null);
        boton.current?.focus();
      }
    }
    function alPulsar(e: MouseEvent) {
      if (caja.current && !caja.current.contains(e.target as Node)) setAbiertoEn(null);
    }
    document.addEventListener("keydown", alTeclear);
    document.addEventListener("mousedown", alPulsar);
    return () => {
      activo = false;
      document.removeEventListener("keydown", alTeclear);
      document.removeEventListener("mousedown", alPulsar);
    };
  }, [abierto]);

  // En móvil el panel ocupa toda la pantalla: el fondo no se desplaza
  useEffect(() => {
    if (!abierto || window.innerWidth >= 640) return;
    const anterior = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = anterior;
    };
  }, [abierto]);

  async function abrirItem(n: Notificacion) {
    setAbiertoEn(null);
    if (n.leida) return;
    setItems((lista) => lista?.map((x) => (x.id === n.id ? { ...x, leida: true } : x)) ?? null);
    try {
      setNoLeidas((await marcarNotificacionLeida(n.id)).no_leidas);
    } catch {
      /* no crítico */
    }
  }

  async function leerTodas() {
    try {
      setNoLeidas((await marcarTodasLeidas()).no_leidas);
      setItems((lista) => lista?.map((x) => ({ ...x, leida: true })) ?? null);
    } catch {
      /* no crítico */
    }
  }

  return (
    <div ref={caja} className="relative">
      <button
        ref={boton}
        type="button"
        aria-haspopup="dialog"
        aria-expanded={abierto}
        aria-label={noLeidas > 0 ? `Notificaciones, ${noLeidas} sin leer` : "Notificaciones"}
        onClick={() => setAbiertoEn(abierto ? null : ruta)}
        className="relative flex h-11 w-11 items-center justify-center rounded-lg border border-white/30 text-white transition hover:bg-white/10 xl:h-10 xl:w-10"
      >
        <Icono nombre="campana" tamano={22} />
        {noLeidas > 0 && (
          <span
            aria-hidden="true"
            className="absolute -right-1.5 -top-1.5 flex h-5 min-w-5 items-center justify-center rounded-full bg-cul-naranja px-1 text-[11px] font-extrabold leading-none text-cul-azul-oscuro ring-2 ring-barra-superior"
          >
            {noLeidas > 9 ? "9+" : noLeidas}
          </span>
        )}
      </button>

      {abierto && (
        <div
          role="dialog"
          aria-label="Notificaciones"
          className="anim-aparecer fixed inset-x-0 bottom-0 top-[4.25rem] z-50 flex flex-col overflow-hidden bg-superficie text-texto sm:absolute sm:inset-x-auto sm:bottom-auto sm:right-0 sm:top-full sm:mt-2 sm:max-h-[min(34rem,calc(100dvh-6rem))] sm:w-[26rem] sm:rounded-xl sm:border sm:border-borde sm:shadow-lg"
        >
          <div className="flex items-center justify-between gap-3 border-b border-borde px-4 py-3">
            <h2 className="text-base font-bold">Notificaciones</h2>
            <button
              type="button"
              onClick={() => void leerTodas()}
              disabled={noLeidas === 0}
              className="min-h-10 rounded-lg px-2 text-sm font-semibold text-enlace hover:underline disabled:cursor-not-allowed disabled:opacity-50"
            >
              Marcar todas como leídas
            </button>
          </div>
          <div className="min-h-0 flex-1 divide-y divide-borde overflow-y-auto scroll-fino">
            {items === null && !error && (
              <p className="flex items-center justify-center gap-2 px-4 py-10 text-sm text-suave">
                <Spinner tamano={16} /> Cargando…
              </p>
            )}
            {error && <p className="px-4 py-10 text-center text-sm text-error-texto">No se pudieron cargar las notificaciones.</p>}
            {items?.length === 0 && <p className="px-4 py-10 text-center text-sm text-suave">No tienes notificaciones por ahora.</p>}
            {items?.map((n) => <ItemNotificacion key={n.id} n={n} onAbrir={abrirItem} />)}
          </div>
          <Link href="/notificaciones" className="flex min-h-12 items-center justify-center border-t border-borde text-sm font-bold text-enlace hover:bg-superficie-2">
            Ver todas
          </Link>
        </div>
      )}
    </div>
  );
}
