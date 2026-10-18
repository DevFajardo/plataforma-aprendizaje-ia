"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import LayoutAuth from "@/components/LayoutAuth";
import { Alerta, Boton, Casilla, Enlace, EsqueletoPagina, Input, Pagina, Select } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { destinoSeguro } from "@/lib/navegacion";

function Contenido() {
  const { usuario, registro } = useAuth();
  const router = useRouter();
  const siguiente = useSearchParams().get("siguiente");
  const destino = destinoSeguro(siguiente);
  const [nombre, setNombre] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [rol, setRol] = useState("estudiante");
  const [aceptaDatos, setAceptaDatos] = useState(false);
  const [aceptaEstudio, setAceptaEstudio] = useState(false);
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
      await registro(nombre.trim(), email.trim(), password, rol, aceptaDatos, aceptaEstudio);
      router.replace(destino);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setEnviando(false);
    }
  }

  return (
    <LayoutAuth
      titulo="Crear cuenta"
      descripcion="Regístrate gratis para convertir videos en cuestionarios y seguir tu aprendizaje."
      pie={
        <>
          ¿Ya tienes cuenta?{" "}
          <Enlace href={siguiente ? `/login?siguiente=${encodeURIComponent(siguiente)}` : "/login"}>Inicia sesión</Enlace>
        </>
      }
    >
      <form onSubmit={enviar} className="flex flex-col gap-4">
        <Input etiqueta="Nombre" required maxLength={100} value={nombre} onChange={(e) => setNombre(e.target.value)} autoComplete="name" />
        <Input etiqueta="Correo electrónico" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" />
        <Input
          etiqueta="Contraseña (mínimo 8 caracteres)"
          type="password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          autoComplete="new-password"
        />
        <Select etiqueta="Rol" value={rol} onChange={(e) => setRol(e.target.value)}>
          <option value="estudiante">Estudiante</option>
          <option value="docente">Docente</option>
        </Select>
        <div className="flex flex-col gap-1 rounded-xl border border-borde bg-superficie-2 p-3">
          <Casilla required checked={aceptaDatos} onChange={(e) => setAceptaDatos(e.target.checked)}>
            Acepto la{" "}
            <Enlace href="/privacidad" target="_blank">
              política de tratamiento de datos personales
            </Enlace>{" "}
            (obligatorio).
          </Casilla>
          <Casilla checked={aceptaEstudio} onChange={(e) => setAceptaEstudio(e.target.checked)}>
            Acepto participar en el estudio de evaluación de la plataforma (mis resultados se usarán de forma anónima). Es opcional y puedes
            cambiarlo después en «Mi cuenta».
          </Casilla>
        </div>
        {error && <Alerta tipo="error">{error}</Alerta>}
        <Boton type="submit" tamano="lg" bloque cargando={enviando} disabled={!aceptaDatos}>
          {enviando ? "Creando…" : "Registrarme"}
        </Boton>
      </form>
    </LayoutAuth>
  );
}

export default function RegistroPage() {
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
