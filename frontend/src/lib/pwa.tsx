"use client";

import { useEffect, useSyncExternalStore } from "react";

/**
 * PWA: registro del service worker y estado de instalación.
 * El evento `beforeinstallprompt` (Chrome, Edge, Android) se guarda para poder lanzar el cuadro de instalación
 * desde un botón propio; en iPhone/iPad no existe y se muestra una ayuda (Compartir → Agregar a inicio).
 */
interface EventoInstalacion extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

let evento: EventoInstalacion | null = null;
let instalada = false;
let iniciado = false;
const oyentes = new Set<() => void>();

function avisar() {
  oyentes.forEach((o) => o());
}

function iniciar() {
  if (iniciado || typeof window === "undefined") return;
  iniciado = true;
  instalada =
    window.matchMedia("(display-mode: standalone)").matches || (navigator as Navigator & { standalone?: boolean }).standalone === true;
  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    evento = e as EventoInstalacion;
    avisar();
  });
  window.addEventListener("appinstalled", () => {
    evento = null;
    instalada = true;
    avisar();
  });
  avisar();
}

function suscribirse(oyente: () => void) {
  oyentes.add(oyente);
  return () => oyentes.delete(oyente);
}

export type EstadoInstalacion = "instalada" | "disponible" | "ios" | "no-disponible";

function esIOS(): boolean {
  const ua = navigator.userAgent;
  return /iPhone|iPad|iPod/.test(ua) || (ua.includes("Macintosh") && navigator.maxTouchPoints > 1);
}

function instantanea(): string {
  if (instalada) return "instalada";
  if (evento) return "disponible";
  return esIOS() ? "ios" : "no-disponible";
}

/** Estado de la instalación de la app y acción para lanzarla. */
export function useInstalarApp(): { estado: EstadoInstalacion; instalar: () => Promise<void> } {
  const estado = useSyncExternalStore(suscribirse, instantanea, () => "no-disponible") as EstadoInstalacion;
  return {
    estado,
    instalar: async () => {
      if (!evento) return;
      const e = evento;
      await e.prompt();
      await e.userChoice;
      evento = null; // el navegador solo permite usar el evento una vez
      avisar();
    },
  };
}

/** Se monta una sola vez en el layout: registra el service worker (solo en producción) y escucha la instalación. */
export default function RegistroPWA() {
  useEffect(() => {
    iniciar();
    if (process.env.NODE_ENV !== "production" || !("serviceWorker" in navigator)) return;
    navigator.serviceWorker.register("/sw.js", { scope: "/" }).catch(() => {
      /* sin service worker la app funciona igual, solo que sin caché */
    });
  }, []);
  return null;
}
