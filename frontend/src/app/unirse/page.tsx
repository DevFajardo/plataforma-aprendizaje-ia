"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Alerta, Boton, EncabezadoPagina, EsqueletoPagina, Input, Pagina, Tarjeta } from "@/components/ui";
import { resolverCodigo } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import { useValidacion } from "@/lib/validacion";

const REGLAS = { codigo: (v: string) => (v.trim().length < 6 ? "El código tiene 6 caracteres (letras y números)." : null) };

export default function UnirsePage() {
  const { usuario, cargando } = useRequiereLogin();
  const router = useRouter();
  const [codigo, setCodigo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [buscando, setBuscando] = useState(false);
  const { errores, ref, validarTodo, limpiar } = useValidacion<{ codigo: string }>(REGLAS);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!validarTodo({ codigo })) return;
    setBuscando(true);
    try {
      const r = await resolverCodigo(codigo);
      router.push(`/cuestionarios/${r.cuestionario_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
      setBuscando(false);
    }
  }

  if (cargando || !usuario) {
    return (
      <Pagina ancho="md">
        <EsqueletoPagina tarjetas={1} />
      </Pagina>
    );
  }

  return (
    <Pagina ancho="md">
      <EncabezadoPagina titulo="Unirse a un cuestionario" descripcion="Escribe el código de 6 caracteres que te compartió tu docente." />
      <Tarjeta>
        <form onSubmit={enviar} noValidate ref={ref} className="flex flex-col gap-4">
          <Input
            etiqueta="Código del cuestionario"
            value={codigo}
            onChange={(e) => {
              setCodigo(e.target.value.toUpperCase());
              limpiar("codigo");
            }}
            error={errores.codigo}
            maxLength={6}
            required
            autoFocus
            autoComplete="off"
            autoCapitalize="characters"
            placeholder="ABC123"
            className="text-center font-mono text-2xl font-bold tracking-[0.35em] sm:text-3xl"
          />
          {error && <Alerta tipo="error">{error}</Alerta>}
          <Boton type="submit" tamano="lg" bloque cargando={buscando}>
            {buscando ? "Buscando…" : "Unirme"}
          </Boton>
        </form>
      </Tarjeta>
    </Pagina>
  );
}
