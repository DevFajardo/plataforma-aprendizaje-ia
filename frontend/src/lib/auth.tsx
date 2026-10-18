"use client";

import { useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
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
  login: (email: string, password: string) => Promise<void>;
  registro: (
    nombre: string,
    email: string,
    password: string,
    rol: string,
    aceptaTratamientoDatos: boolean,
    consentimientoInvestigacion: boolean,
  ) => Promise<void>;
  logout: () => void;
  /** Actualiza el usuario en memoria (p. ej. tras editar la cuenta). */
  actualizarUsuario: (u: Usuario) => void;
}

const Contexto = createContext<ContextoAuth | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [usuario, setUsuario] = useState<Usuario | null>(null);
  const [cargando, setCargando] = useState(true);

  const logout = useCallback(() => {
    api.guardarToken(null);
    setUsuario(null);
  }, []);

  // Ante un 401 del servidor: cerrar sesión y volver al login
  useEffect(() => {
    api.registrarManejador401(() => {
      logout();
      router.replace("/login");
    });
    return () => api.registrarManejador401(null);
  }, [logout, router]);

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
    setUsuario(r.usuario);
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
