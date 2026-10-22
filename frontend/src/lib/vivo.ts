"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { accionSesionVivo, estadoClaseVivo, leerToken, responderClaseVivo, urlWsVivo } from "./api";
import type { EstadoVivo } from "./tipos";

export type ModoConexion = "conectando" | "ws" | "sondeo";

const MAX_FALLOS_WS = 3; // tras 3 fallos seguidos se pasa al sondeo HTTP
const INTERVALO_SONDEO_MS = 1500;
const CODIGOS_FATALES = [4401, 4403, 4404];

interface Opciones {
  pin: string | null;
  rol: "presentador" | "participante";
  /** Participante: token secreto de reconexión. Presentador: se usa el JWT de la sesión. */
  tokenParticipante?: string | null;
  /** Presentador: id de la sesión (para los controles por HTTP cuando no hay WebSocket). */
  sesionId?: number | null;
}

export interface SesionVivoCliente {
  estado: EstadoVivo | null;
  modo: ModoConexion;
  /** Código de cierre definitivo (PIN inexistente, sin permiso…) o null. */
  fatal: number | null;
  error: string | null;
  limpiarError: () => void;
  /** Presentador: iniciar | siguiente | saltar | finalizar. */
  accion: (accion: "iniciar" | "siguiente" | "saltar" | "finalizar") => Promise<void>;
  /** Participante: envía su respuesta. */
  responder: (respuesta: string) => Promise<void>;
}

/**
 * Conexión en tiempo real con la clase en vivo: WebSocket con reconexión (backoff exponencial) y, si falla
 * 3 veces seguidas, sondeo HTTP cada 1,5 s. En ambos casos el servidor entrega el estado completo, así que
 * reconectar recupera la pregunta en curso sin perder nada.
 */
export function useSesionVivo({ pin, rol, tokenParticipante, sesionId }: Opciones): SesionVivoCliente {
  const [estado, setEstado] = useState<EstadoVivo | null>(null);
  const [modo, setModo] = useState<ModoConexion>("conectando");
  const [fatal, setFatal] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const sondearRef = useRef<(() => Promise<void>) | null>(null);

  const credencial = rol === "presentador" ? leerToken() : (tokenParticipante ?? null);

  useEffect(() => {
    if (!pin || !credencial) return;
    let activo = true;
    let fallos = 0;
    let reintento: ReturnType<typeof setTimeout> | undefined;
    let sondeo: ReturnType<typeof setInterval> | undefined;

    const recibir = (e: EstadoVivo) => setEstado({ ...e, _t: performance.now() });

    async function sondear() {
      try {
        const e = await estadoClaseVivo(pin!, rol === "participante" ? credencial! : undefined);
        if (activo) recibir(e);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "";
        if (activo && /No hay una clase|ya termin/i.test(msg)) setFatal(4404);
        else if (activo && /no reconocido/i.test(msg)) setFatal(4401);
      }
    }
    sondearRef.current = sondear;

    function iniciarSondeo() {
      if (!activo) return;
      setModo("sondeo");
      void sondear();
      sondeo = setInterval(() => void sondear(), INTERVALO_SONDEO_MS);
    }

    function conectar() {
      if (!activo) return;
      let ws: WebSocket;
      try {
        ws = new WebSocket(urlWsVivo(pin!, rol, credencial!));
      } catch {
        iniciarSondeo();
        return;
      }
      wsRef.current = ws;
      ws.onopen = () => {
        fallos = 0;
        setModo("ws");
      };
      ws.onmessage = (ev) => {
        try {
          const m = JSON.parse(ev.data as string);
          if (m.tipo === "estado") recibir(m as EstadoVivo);
          else if (m.tipo === "error") setError(String(m.mensaje ?? "Error"));
        } catch {
          /* mensaje ilegible: se ignora */
        }
      };
      ws.onclose = (ev) => {
        if (wsRef.current === ws) wsRef.current = null;
        if (!activo) return;
        if (CODIGOS_FATALES.includes(ev.code)) {
          setFatal(ev.code);
          return;
        }
        fallos += 1;
        if (fallos >= MAX_FALLOS_WS) {
          iniciarSondeo();
          return;
        }
        setModo("conectando");
        reintento = setTimeout(conectar, Math.min(8000, 500 * 2 ** fallos));
      };
    }

    conectar();
    return () => {
      activo = false;
      clearTimeout(reintento);
      clearInterval(sondeo);
      const ws = wsRef.current;
      wsRef.current = null;
      sondearRef.current = null;
      ws?.close();
    };
  }, [pin, rol, credencial]);

  const accion = useCallback(
    async (a: "iniciar" | "siguiente" | "saltar" | "finalizar") => {
      setError(null);
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ accion: a }));
        return;
      }
      if (!sesionId) return;
      try {
        await accionSesionVivo(sesionId, a);
        await sondearRef.current?.();
      } catch (e) {
        setError(e instanceof Error ? e.message : "No se pudo ejecutar la acción.");
      }
    },
    [sesionId],
  );

  const responder = useCallback(
    async (respuesta: string) => {
      setError(null);
      const ws = wsRef.current;
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ accion: "responder", respuesta }));
        return;
      }
      if (!pin || !tokenParticipante) return;
      try {
        await responderClaseVivo(pin, tokenParticipante, respuesta);
        await sondearRef.current?.();
      } catch (e) {
        setError(e instanceof Error ? e.message : "No se pudo enviar la respuesta.");
      }
    },
    [pin, tokenParticipante],
  );

  return { estado, modo, fatal, error, limpiarError: () => setError(null), accion, responder };
}

/** Milisegundos que le quedan a la pregunta, calculados con el reloj local a partir de lo que informó el servidor. */
export function useRestanteMs(estado: EstadoVivo | null): number {
  const [ahora, setAhora] = useState(0);
  useEffect(() => {
    if (estado?.estado !== "pregunta") return;
    const t = setInterval(() => setAhora(performance.now()), 100);
    return () => clearInterval(t);
  }, [estado?.estado, estado?._t]);
  if (!estado || estado.estado !== "pregunta") return 0;
  const referencia = ahora > (estado._t ?? 0) ? ahora : (estado._t ?? 0);
  return Math.max(0, estado.restante_ms - (referencia - (estado._t ?? referencia)));
}
