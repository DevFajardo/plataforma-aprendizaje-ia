"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import LayoutAuth from "@/components/LayoutAuth";
import { Alerta, Boton, Enlace, EsqueletoPagina, Input, Pagina } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { destinoSeguro } from "@/lib/navegacion";

function Contenido() {
  const { usuario, login } = useAuth();
  const router = useRouter();
  const siguiente = useSearchParams().get("siguiente");
  const destino = destinoSeguro(siguiente);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (usuario) router.replace(destino);
  }, [usuario, router, destino]);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setEnviando(true);
    try {
      await login(email.trim(), password);
      router.replace(destino);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <LayoutAuth
      titulo="Iniciar sesión"
      descripcion="Ingresa con tu cuenta para generar cuestionarios, responderlos y ver tu progreso."
      pie={
        <>
          ¿No tienes cuenta?{" "}
          <Enlace href={siguiente ? `/registro?siguiente=${encodeURIComponent(siguiente)}` : "/registro"}>Regístrate</Enlace>
        </>
      }
    >
      <form onSubmit={enviar} className="flex flex-col gap-4">
        <Input etiqueta="Correo electrónico" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
        <Input
          etiqueta="Contraseña"
          type="password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="current-password"
        />
        {error && <Alerta tipo="error">{error}</Alerta>}
        <Boton type="submit" tamano="lg" bloque cargando={enviando}>
          {enviando ? "Entrando…" : "Entrar"}
        </Boton>
      </form>
    </LayoutAuth>
  );
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <Pagina ancho="sm">
          <EsqueletoPagina tarjetas={1} />
        </Pagina>
      }
    >
      <Contenido />
    </Suspense>
  );
}
