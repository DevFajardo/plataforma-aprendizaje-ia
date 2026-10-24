"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import LayoutAuth from "@/components/LayoutAuth";
import { Alerta, Boton, Casilla, Enlace, EsqueletoPagina, Input, Pagina, Select } from "@/components/ui";
import { useAuth } from "@/lib/auth";
import { destinoSeguro } from "@/lib/navegacion";
import { REGEX_CORREO, useValidacion } from "@/lib/validacion";

interface Valores {
  nombre: string;
  email: string;
  password: string;
  aceptaDatos: boolean;
}
const REGLAS = {
  nombre: (v: string) => (v.trim().length < 2 ? "Escribe tu nombre (mínimo 2 caracteres)." : null),
  email: (v: string) =>
    !v.trim() ? "Escribe tu correo electrónico." : !REGEX_CORREO.test(v.trim()) ? "Revisa el correo: debe tener el formato nombre@dominio.com." : null,
  password: (v: string) => (v.length < 8 ? "La contraseña debe tener al menos 8 caracteres." : null),
  aceptaDatos: (v: boolean) => (!v ? "Debes aceptar la política de tratamiento de datos para crear la cuenta." : null),
};

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
  const { errores, ref, validarCampo, validarTodo, limpiar } = useValidacion<Valores>(REGLAS);
  const valores: Valores = { nombre, email, password, aceptaDatos };

  // Si ya hay una sesión abierta, el destino guardado puede ser de otro usuario: siempre /panel.
  useEffect(() => {
    if (usuario) router.replace("/panel");
  }, [usuario, router]);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!validarTodo(valores)) return;
    setEnviando(true);
    try {
      await registro(nombre.trim(), email.trim(), password, rol, aceptaDatos, aceptaEstudio);
      // Navegación completa: ningún estado de una sesión anterior sobrevive
      window.location.replace(destino);
      return;
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
      <form onSubmit={enviar} noValidate ref={ref} className="flex flex-col gap-4">
        <Input
          etiqueta="Nombre"
          required
          maxLength={100}
          value={nombre}
          onChange={(e) => {
            setNombre(e.target.value);
            limpiar("nombre");
          }}
          onBlur={() => nombre && validarCampo("nombre", valores)}
          error={errores.nombre}
          autoComplete="name"
        />
        <Input
          etiqueta="Correo electrónico"
          type="email"
          required
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            limpiar("email");
          }}
          onBlur={() => email && validarCampo("email", valores)}
          error={errores.email}
          autoComplete="email"
        />
        <Input
          etiqueta="Contraseña"
          ayuda="Mínimo 8 caracteres."
          type="password"
          required
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            limpiar("password");
          }}
          onBlur={() => password && validarCampo("password", valores)}
          error={errores.password}
          autoComplete="new-password"
        />
        <Select etiqueta="Rol" value={rol} onChange={(e) => setRol(e.target.value)}>
          <option value="estudiante">Estudiante</option>
          <option value="docente">Docente</option>
        </Select>
        <div className="flex flex-col gap-1 rounded-xl border border-borde bg-superficie-2 p-3">
          <Casilla
            required
            checked={aceptaDatos}
            onChange={(e) => {
              setAceptaDatos(e.target.checked);
              limpiar("aceptaDatos");
            }}
            aria-invalid={errores.aceptaDatos ? true : undefined}
            aria-describedby={errores.aceptaDatos ? "error-datos" : undefined}
          >
            Acepto la{" "}
            <Enlace href="/privacidad" target="_blank">
              política de tratamiento de datos personales
            </Enlace>{" "}
            (obligatorio).
          </Casilla>
          {errores.aceptaDatos && (
            <p id="error-datos" role="alert" className="text-sm font-medium text-error-texto">
              {errores.aceptaDatos}
            </p>
          )}
          <Casilla checked={aceptaEstudio} onChange={(e) => setAceptaEstudio(e.target.checked)}>
            Acepto participar en el estudio de evaluación de la plataforma (mis resultados se usarán de forma anónima). Es opcional y puedes
            cambiarlo después en «Mi cuenta».
          </Casilla>
        </div>
        {error && <Alerta tipo="error">{error}</Alerta>}
        <Boton type="submit" tamano="lg" bloque cargando={enviando}>
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
