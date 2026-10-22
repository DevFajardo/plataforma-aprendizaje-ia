"use client";

import { useCallback, useEffect, useState } from "react";
import ItemNotificacion from "@/components/ItemNotificacion";
import { Alerta, Boton, EncabezadoPagina, EsqueletoPagina, EstadoVacio, Pagina, Tarjeta } from "@/components/ui";
import { listarNotificaciones, marcarNotificacionLeida, marcarTodasLeidas } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import type { Notificacion, PaginaNotificaciones } from "@/lib/tipos";

const POR_PAGINA = 15;

export default function NotificacionesPage() {
  const { usuario, cargando } = useRequiereLogin();
  const [pagina, setPagina] = useState(1);
  const [datos, setDatos] = useState<PaginaNotificaciones | null>(null);
  const [error, setError] = useState<string | null>(null);

  const cargar = useCallback(async (p: number) => {
    try {
      setDatos(await listarNotificaciones(p, POR_PAGINA));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudieron cargar las notificaciones.");
    }
  }, []);

  useEffect(() => {
    if (!usuario) return;
    const t = setTimeout(() => void cargar(pagina), 0);
    return () => clearTimeout(t);
  }, [usuario, pagina, cargar]);

  async function abrir(n: Notificacion) {
    if (n.leida) return;
    setDatos((d) => (d ? { ...d, items: d.items.map((x) => (x.id === n.id ? { ...x, leida: true } : x)), no_leidas: Math.max(0, d.no_leidas - 1) } : d));
    try {
      await marcarNotificacionLeida(n.id);
    } catch {
      /* no crítico */
    }
  }

  async function leerTodas() {
    try {
      await marcarTodasLeidas();
      await cargar(pagina);
    } catch (e) {
      setError(e instanceof Error ? e.message : "No se pudo completar la acción.");
    }
  }

  const totalPaginas = datos ? Math.max(1, Math.ceil(datos.total / datos.por_pagina)) : 1;

  return (
    <Pagina ancho="md">
      <EncabezadoPagina
        titulo="Notificaciones"
        descripcion="Avisos de tus cursos, repasos pendientes, alertas y resultados de clases en vivo."
        acciones={
          <Boton variante="secundario" onClick={() => void leerTodas()} disabled={!datos || datos.no_leidas === 0}>
            Marcar todas como leídas
          </Boton>
        }
      />
      {error && (
        <Alerta tipo="error" className="mb-4">
          {error}
        </Alerta>
      )}
      {(cargando || (!datos && !error)) && <EsqueletoPagina tarjetas={1} />}
      {datos && datos.items.length === 0 && (
        <EstadoVacio icono="campana" titulo="No tienes notificaciones">
          Cuando haya novedades en tus cursos aparecerán aquí.
        </EstadoVacio>
      )}
      {datos && datos.items.length > 0 && (
        <Tarjeta sinRelleno className="overflow-hidden">
          <ul className="divide-y divide-borde">
            {datos.items.map((n) => (
              <li key={n.id}>
                <ItemNotificacion n={n} onAbrir={abrir} />
              </li>
            ))}
          </ul>
        </Tarjeta>
      )}
      {datos && totalPaginas > 1 && (
        <nav aria-label="Paginación" className="mt-6 flex items-center justify-between gap-3">
          <Boton variante="secundario" disabled={pagina <= 1} onClick={() => setPagina((p) => p - 1)}>
            Anteriores
          </Boton>
          <span className="text-sm text-suave">
            Página {pagina} de {totalPaginas}
          </span>
          <Boton variante="secundario" disabled={pagina >= totalPaginas} onClick={() => setPagina((p) => p + 1)}>
            Siguientes
          </Boton>
        </nav>
      )}
    </Pagina>
  );
}
