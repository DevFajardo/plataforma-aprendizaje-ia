"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import * as api from "./api";
import { rutaLogin } from "./navegacion";
import type { RespuestaAuth, Usuario } from "./tipos";

interface ContextoAuth {
  usuario: Usuario | null;
  cargando: boolean; // true mientras se valida el token guardado
  /** Guarda el token y devuelve el usuario. No actualiza el estado: quien llama debe hacer una navegación completa. */
  login: (email: string, password: string) => Promise<Usuario>;
  registro: (
    nombre: string,
    email: string,
    password: string,
    rol: string,
    aceptaTratamientoDatos: boolean,
    consentimientoInvestigacion: boolean,
  ) => Promise<Usuario>;
  /** Cierra la sesión con una navegación COMPLETA (descarta todo el estado del cliente y la caché del router). */
  logout: (destino?: string) => void;
  /** Actualiza el usuario en memoria (p. ej. tras editar la cuenta). */
  actualizarUsuario: (u: Usuario) => void;
}

const Contexto = createContext<ContextoAuth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);
  // Token con el que se cargó esta página: si cambia (otra pestaña, bfcache) se recarga todo.
  const tokenInicial = useRef<string | null>(null);

  // No se pone usuario=null: así las páginas privadas no redirigen a /login?siguiente=<ruta actual>.
  const logout = useCallback((destino: string = "/login") => {
    api.guardarToken(null);
    window.location.replace(destino);
  }, []);

  // Ante un 401 del servidor: cerrar sesión y volver al login
  useEffect(() => {
    api.registrarManejador401(() => logout("/login"));
    return () => api.registrarManejador401(null);
  }, [logout]);

  // Sesión cambiada en otra pestaña o página restaurada desde la caché del navegador (botón Atrás)
  useEffect(() => {
    tokenInicial.current = api.leerToken();
    function revisar() {
      if (api.leerToken() !== tokenInicial.current) window.location.reload();
    }
    function alMostrar(e: PageTransitionEvent) {
      if (e.persisted) revisar();
    }
    window.addEventListener("pageshow", alMostrar);
    window.addEventListener("storage", revisar);
    return () => {
      window.removeEventListener("pageshow", alMostrar);
      window.removeEventListener("storage", revisar);
    };
  }, []);

  // Al cargar la app, validar el token guardado
  useEffect(() => {
    let activo = true;
    (async () => {
      if (api.leerToken()) {
        try {
          const u = await api.obtenerYo();
          if (activo) setUsuario(u);
        } catch {
          /* el manejador 401 ya limpió la sesión si correspondía */
        }
      }
      if (activo) setCargando(false);
    })();
    return () => {
      activo = false;
    };
  }, []);

  const aceptar = useCallback((r: RespuestaAuth) => {
    api.guardarToken(r.token);
    return r.usuario;
  }, []);

  const valor = useMemo<ContextoAuth>(
    () => ({
      usuario,
      cargando,
      logout,
      login: async (email, password) => aceptar(await api.login(email, password)),
      registro: async (nombre, email, password, rol, acepta, investigacion) =>
        aceptar(await api.registro(nombre, email, password, rol, acepta, investigacion)),
      actualizarUsuario: setUsuario,
    }),
    [usuario, cargando, logout, aceptar],
  );

  return <Contexto.Provider value={valor}>{children}</Contexto.Provider>;
}

export function useAuth(): ContextoAuth {
  const ctx = useContext(Contexto);
  if (!ctx) throw new Error("useAuth debe usarse dentro de <AuthProvider>");
  return ctx;
}

/** Para páginas privadas: redirige a /login si no hay sesión. */
export function useRequiereLogin(): ContextoAuth {
  const auth = useAuth();
  const router = useRouter();
  useEffect(() => {
    if (!auth.cargando && !auth.usuario) {
      // Recuerda la página actual para volver tras iniciar sesión
      router.replace(rutaLogin(window.location.pathname + window.location.search));
    }
  }, [auth.cargando, auth.usuario, router]);
  return auth;
}
