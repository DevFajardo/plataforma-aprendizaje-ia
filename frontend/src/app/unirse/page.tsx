"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Alerta, Boton, EncabezadoPagina, EsqueletoPagina, Input, Pagina, Tarjeta } from "@/components/ui";
import { resolverCodigo } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";

export default function UnirsePage() {
  const { usuario, cargando } = useRequiereLogin();
  const router = useRouter();
  const [codigo, setCodigo] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [buscando, setBuscando] = useState(false);

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
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
        <form onSubmit={enviar} className="flex flex-col gap-4">
          <Input
            etiqueta="Código del cuestionario"
            value={codigo}
            onChange={(e) => setCodigo(e.target.value.toUpperCase())}
            maxLength={6}
            required
            autoFocus
            autoComplete="off"
            autoCapitalize="characters"
            placeholder="ABC123"
            className="text-center font-mono text-2xl font-bold tracking-[0.35em] sm:text-3xl"
          />
          {error && <Alerta tipo="error">{error}</Alerta>}
          <Boton type="submit" tamano="lg" bloque cargando={buscando} disabled={codigo.trim().length < 6}>
            {buscando ? "Buscando…" : "Unirme"}
          </Boton>
        </form>
      </Tarjeta>
    </Pagina>
  );
}
