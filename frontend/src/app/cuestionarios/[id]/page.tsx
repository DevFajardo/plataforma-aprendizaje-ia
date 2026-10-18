"use client";

import { useParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import EditorCuestionario from "@/components/EditorCuestionario";
import PanelDocente from "@/components/PanelDocente";
import VisorCuestionario from "@/components/VisorCuestionario";
import { Alerta, BotonEnlace, Esqueleto, EsqueletoPagina, Pagina } from "@/components/ui";
import { obtenerCuestionario } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import type { CuestionarioDetalle } from "@/lib/tipos";

function Contenido() {
  const { usuario, cargando } = useRequiereLogin();
  const { id } = useParams<{ id: string }>();
  const [cuestionario, setCuestionario] = useState<CuestionarioDetalle | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [editando, setEditando] = useState(false);

  const [recarga, setRecarga] = useState(0); // al cambiarlo se vuelve a pedir el cuestionario

  useEffect(() => {
    if (!usuario) return;
    obtenerCuestionario(Number(id))
      .then(setCuestionario)
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
  }, [usuario, id, recarga]);

  function terminarEdicion(huboCambios: boolean) {
    if (huboCambios) setRecarga((n) => n + 1);
    setEditando(false);
  }

  const modoEditor = !!cuestionario && editando && cuestionario.es_creador;

  return (
    <Pagina ancho={modoEditor ? "lg" : "completo"}>
      {error && (
        <div className="flex flex-col items-start gap-4">
          <Alerta tipo="error" className="w-full">
            {error}
          </Alerta>
          <BotonEnlace href="/cuestionarios" variante="secundario">
            Volver a mis cuestionarios
          </BotonEnlace>
        </div>
      )}
      {(cargando || (!cuestionario && !error)) && (
        <div className="flex flex-col gap-6">
          <EsqueletoPagina tarjetas={0} />
          <div className="grid gap-6 lg:grid-cols-[5fr_6fr]">
            <Esqueleto className="aspect-video w-full rounded-2xl" />
            <Esqueleto className="h-64 w-full rounded-2xl" />
          </div>
        </div>
      )}
      {modoEditor && cuestionario && <EditorCuestionario cuestionario={cuestionario} onTerminar={terminarEdicion} />}
      {cuestionario && !editando && (
        <VisorCuestionario
          key={`${cuestionario.id}-${recarga}`}
          cuestionario={cuestionario}
          panel={
            cuestionario.es_creador ? (
              <PanelDocente
                cuestionario={cuestionario}
                onEditar={() => setEditando(true)}
                onPublicado={(publicado, estimacion) =>
                  setCuestionario((c) =>
                    c
                      ? {
                          ...c,
                          publicado,
                          publicado_en: c.publicado_en ?? (publicado ? new Date().toISOString() : null),
                          estimacion_manual_min: estimacion ?? c.estimacion_manual_min,
                        }
                      : c,
                  )
                }
                onCambio={(parche) => setCuestionario((c) => (c ? { ...c, ...parche } : c))}
              />
            ) : undefined
          }
        />
      )}
    </Pagina>
  );
}

export default function CuestionarioPage() {
  return (
    <Suspense
      fallback={
        <Pagina ancho="completo">
          <EsqueletoPagina />
        </Pagina>
      }
    >
      <Contenido />
    </Suspense>
  );
}
