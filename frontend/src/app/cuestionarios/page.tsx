"use client";

import { useEffect, useState } from "react";
import {
  Alerta,
  Boton,
  BotonEnlace,
  ConfirmacionEnLinea,
  EncabezadoPagina,
  EsqueletoPagina,
  EstadoVacio,
  Icono,
  Insignia,
  Pagina,
  Tarjeta,
  TituloSeccion,
} from "@/components/ui";
import { eliminarCuestionario, listarCuestionarios } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import { formatearFecha } from "@/lib/fechas";
import type { CuestionarioResumen } from "@/lib/tipos";

function TarjetaCuestionario({
  c,
  onBorrar,
}: {
  c: CuestionarioResumen;
  onBorrar?: (c: CuestionarioResumen) => Promise<void>;
}) {
  const [confirmando, setConfirmando] = useState(false);
  const [borrando, setBorrando] = useState(false);

  async function confirmar() {
    setBorrando(true);
    await onBorrar?.(c);
    setBorrando(false);
    setConfirmando(false);
  }

  return (
    <Tarjeta as="article" sinRelleno interactiva className="flex h-full flex-col overflow-hidden">
      {c.youtube_id ? (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={`https://i.ytimg.com/vi/${c.youtube_id}/mqdefault.jpg`} alt="" loading="lazy" className="aspect-video w-full bg-superficie-2 object-cover" />
      ) : (
        <div aria-hidden="true" className="flex aspect-video w-full items-center justify-center bg-gradient-to-br from-cul-azul to-cul-marino text-white/80">
          <Icono nombre="video" tamano={40} />
        </div>
      )}
      <div className="flex flex-1 flex-col gap-3 p-4">
        <h2 className="line-clamp-2 font-bold leading-snug">{c.titulo}</h2>
        <div className="flex flex-wrap gap-1.5">
          {c.propio ? (
            <Insignia tono={c.publicado ? "exito" : "aviso"}>{c.publicado ? "Publicado" : "Borrador"}</Insignia>
          ) : (
            c.creador && <Insignia tono="azul">de {c.creador}</Insignia>
          )}
          {c.plataforma === "vimeo" && <Insignia>Vimeo</Insignia>}
          {c.modo === "control" && <Insignia tono="neutro">Grupo control</Insignia>}
        </div>
        <p className="text-sm text-suave">
          {formatearFecha(c.creado_en, "corta")} · {c.num_preguntas} preguntas
        </p>
        <p className="text-sm font-semibold">
          {c.mejor_puntaje !== null ? `Mejor puntaje: ${c.mejor_puntaje}/${c.mejor_total}` : <span className="font-normal text-suave">Sin intentos finalizados</span>}
        </p>
        <div className="mt-auto flex flex-wrap gap-2 pt-1">
          <BotonEnlace href={`/cuestionarios/${c.id}`} tamano="sm">
            Abrir
          </BotonEnlace>
          {onBorrar && !confirmando && (
            <Boton variante="peligroSuave" tamano="sm" onClick={() => setConfirmando(true)}>
              <Icono nombre="basura" tamano={16} /> Eliminar
            </Boton>
          )}
        </div>
        {confirmando && (
          <ConfirmacionEnLinea
            mensaje="¿Eliminar este cuestionario? Se borrarán también los intentos asociados."
            textoConfirmar="Sí, eliminar"
            textoOcupado="Eliminando…"
            ocupado={borrando}
            onConfirmar={confirmar}
            onCancelar={() => setConfirmando(false)}
          />
        )}
      </div>
    </Tarjeta>
  );
}

export default function CuestionariosPage() {
  const { usuario, cargando } = useRequiereLogin();
  const [lista, setLista] = useState<CuestionarioResumen[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!usuario) return;
    listarCuestionarios()
      .then(setLista)
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
  }, [usuario]);

  async function borrar(c: CuestionarioResumen) {
    try {
      await eliminarCuestionario(c.id);
      setLista((l) => l?.filter((x) => x.id !== c.id) ?? null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    }
  }

  const propios = lista?.filter((c) => c.propio) ?? [];
  const unidos = lista?.filter((c) => !c.propio) ?? [];

  if (cargando || !usuario) {
    return (
      <Pagina>
        <EsqueletoPagina />
      </Pagina>
    );
  }

  return (
    <Pagina>
      <EncabezadoPagina
        titulo="Mis cuestionarios"
        descripcion="Los cuestionarios que generaste y los que te compartieron."
        acciones={
          <BotonEnlace href="/" tamano="md">
            <Icono nombre="mas" /> Nuevo cuestionario
          </BotonEnlace>
        }
      />

      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}
      {lista === null && !error && <EsqueletoPagina />}

      {lista !== null && (
        <div className="flex flex-col gap-10">
          <section className="flex flex-col gap-4">
            <TituloSeccion>Creados por mí</TituloSeccion>
            {propios.length === 0 ? (
              <EstadoVacio
                titulo="Aún no tienes cuestionarios"
                accion={
                  <BotonEnlace href="/" tamano="sm">
                    Genera el primero
                  </BotonEnlace>
                }
              >
                Pega el enlace de un video y la IA creará el resumen y las preguntas.
              </EstadoVacio>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {propios.map((c) => (
                  <TarjetaCuestionario key={c.id} c={c} onBorrar={borrar} />
                ))}
              </div>
            )}
          </section>

          <section className="flex flex-col gap-4">
            <TituloSeccion>Cuestionarios a los que me uní</TituloSeccion>
            {unidos.length === 0 ? (
              <EstadoVacio
                icono="grupo"
                titulo="Aún no te has unido a ninguno"
                accion={
                  <BotonEnlace href="/unirse" variante="secundario" tamano="sm">
                    Unirme con un código
                  </BotonEnlace>
                }
              >
                Pídele a tu docente el código de 6 caracteres.
              </EstadoVacio>
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                {unidos.map((c) => (
                  <TarjetaCuestionario key={c.id} c={c} />
                ))}
              </div>
            )}
          </section>
        </div>
      )}
    </Pagina>
  );
}
