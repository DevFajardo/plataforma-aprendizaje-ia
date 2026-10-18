"use client";

import { useParams, useRouter } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { Alerta, BotonEnlace, EsqueletoPagina, Pagina, Spinner } from "@/components/ui";
import { resolverCodigo } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";

function Contenido() {
  // Si no hay sesión, useRequiereLogin manda a /login?siguiente=/c/CODIGO y se vuelve aquí después
  const { usuario } = useRequiereLogin();
  const { codigo } = useParams<{ codigo: string }>();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!usuario) return;
    resolverCodigo(codigo)
      .then((r) => router.replace(`/cuestionarios/${r.cuestionario_id}`))
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
  }, [usuario, codigo, router]);

  return (
    <Pagina ancho="md">
      {error ? (
        <div className="flex flex-col items-start gap-4">
          <Alerta tipo="error" className="w-full">
            {error}
          </Alerta>
          <BotonEnlace href="/unirse" variante="secundario">
            Probar con otro código
          </BotonEnlace>
        </div>
      ) : (
        <p role="status" className="flex items-center gap-3 text-suave">
          <Spinner /> Buscando el cuestionario…
        </p>
      )}
    </Pagina>
  );
}

export default function CodigoPage() {
  return (
    <Suspense
      fallback={
        <Pagina ancho="md">
          <EsqueletoPagina tarjetas={1} />
        </Pagina>
      }
    >
      <Contenido />
    </Suspense>
  );
}
