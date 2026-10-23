"use client";

import { useEffect, useState } from "react";
import { Alerta, BarraPorcentaje, BotonEnlace, EncabezadoPagina, Enlace, EsqueletoPagina, EstadoVacio, Pagina, Tarjeta, type TonoBarra } from "@/components/ui";
import { listarIntentos } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import { formatearFecha } from "@/lib/fechas";
import type { IntentoHistorial } from "@/lib/tipos";
import { pct } from "@/lib/formato";

const tonoPorcentaje = (p: number): TonoBarra => (p < 60 ? "error" : p < 80 ? "aviso" : "exito");

export default function HistorialPage() {
  const { usuario, cargando } = useRequiereLogin();
  const [intentos, setIntentos] = useState<IntentoHistorial[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!usuario) return;
    listarIntentos()
      .then(setIntentos)
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
  }, [usuario]);

  if (cargando || !usuario) {
    return (
      <Pagina>
        <EsqueletoPagina />
      </Pagina>
    );
  }

  return (
    <Pagina>
      <EncabezadoPagina titulo="Historial de intentos" descripcion="Todos los cuestionarios que has respondido, del más reciente al más antiguo." />
      {error && <Alerta tipo="error" reintentar>{error}</Alerta>}
      {intentos === null && !error && <EsqueletoPagina tarjetas={2} />}
      {intentos?.length === 0 && (
        <EstadoVacio
          icono="intentos"
          titulo="Todavía no has completado ningún intento"
          accion={
            <BotonEnlace href="/" tamano="sm">
              Generar un cuestionario
            </BotonEnlace>
          }
        >
          Cuando termines un cuestionario aparecerá aquí con su puntaje.
        </EstadoVacio>
      )}
      {intentos && intentos.length > 0 && (
        <>
          {/* Móvil: tarjetas */}
          <ul className="flex flex-col gap-3 md:hidden">
            {intentos.map((i) => (
              <li key={i.id}>
                <Tarjeta className="flex flex-col gap-3 !p-4">
                  <div className="flex items-start justify-between gap-3">
                    <Enlace href={`/cuestionarios/${i.cuestionario_id}`} className="min-w-0">
                      {i.cuestionario_titulo}
                    </Enlace>
                    <span className="shrink-0 text-xl font-bold">{pct(i.porcentaje)}</span>
                  </div>
                  <BarraPorcentaje valor={i.porcentaje} etiqueta={`Resultado del ${formatearFecha(i.creado_en)}`} tono={tonoPorcentaje(i.porcentaje)} />
                  <p className="flex flex-wrap justify-between gap-2 text-sm text-suave">
                    <span>{formatearFecha(i.creado_en)}</span>
                    <span>
                      Puntaje: {i.puntaje}/{i.total}
                    </span>
                  </p>
                </Tarjeta>
              </li>
            ))}
          </ul>

          {/* Tablet y escritorio: tabla */}
          <div tabIndex={0} role="region" aria-label="Historial de intentos" className="hidden overflow-x-auto rounded-2xl border border-borde bg-superficie shadow-tarjeta md:block">
            <table className="w-full text-left text-sm">
              <thead className="bg-superficie-2">
                <tr>
                  <th scope="col" className="px-4 py-3">Fecha</th>
                  <th scope="col" className="px-4 py-3">Cuestionario</th>
                  <th scope="col" className="px-4 py-3">Puntaje</th>
                  <th scope="col" className="px-4 py-3">Porcentaje</th>
                </tr>
              </thead>
              <tbody>
                {intentos.map((i) => (
                  <tr key={i.id} className="border-t border-borde transition hover:bg-superficie-2/60">
                    <td className="whitespace-nowrap px-4 py-3">{formatearFecha(i.creado_en)}</td>
                    <td className="px-4 py-3">
                      <Enlace href={`/cuestionarios/${i.cuestionario_id}`}>{i.cuestionario_titulo}</Enlace>
                    </td>
                    <td className="px-4 py-3">
                      {i.puntaje}/{i.total}
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <BarraPorcentaje
                          valor={i.porcentaje}
                          etiqueta={`Resultado del ${formatearFecha(i.creado_en)}`}
                          tono={tonoPorcentaje(i.porcentaje)}
                          alto="sm"
                          className="w-24"
                        />
                        <span className="font-bold">{pct(i.porcentaje)}</span>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </Pagina>
  );
}
