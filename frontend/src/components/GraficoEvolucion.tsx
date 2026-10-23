"use client";

import { useEffect, useRef, useState } from "react";
import { formatearFecha } from "@/lib/fechas";
import type { PuntoEvolucion } from "@/lib/tipos";
import { pct } from "@/lib/formato";

// Gráfico de línea hecho a mano con SVG (sin librerías). Eje Y fijo 0-100 %.
// El viewBox se ajusta al ancho real del contenedor para que los textos se mantengan legibles en móvil.
const ANCHO_INICIAL = 640;
const MARCAS_Y = [0, 25, 50, 75, 100];

export default function GraficoEvolucion({ puntos }: { puntos: PuntoEvolucion[] }) {
  const [activo, setActivo] = useState<number | null>(null);
  const [ancho, setAncho] = useState(ANCHO_INICIAL);
  const caja = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = caja.current;
    if (!el) return;
    const medir = () => setAncho(Math.max(260, Math.round(el.clientWidth)));
    medir();
    const obs = new ResizeObserver(medir);
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const estrecho = ancho < 480;
  const ALTO = estrecho ? 230 : 280;
  const M = { izq: estrecho ? 38 : 44, der: estrecho ? 12 : 16, arr: 16, aba: 36 };
  const anchoUtil = ancho - M.izq - M.der;
  const altoUtil = ALTO - M.arr - M.aba;
  const x = (i: number) => M.izq + (puntos.length === 1 ? anchoUtil / 2 : (i * anchoUtil) / (puntos.length - 1));
  const y = (pct: number) => M.arr + altoUtil * (1 - pct / 100);

  const linea = puntos.map((p, i) => `${i === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(p.porcentaje).toFixed(1)}`).join(" ");
  const area = puntos.length > 1 ? `${linea} L${x(puntos.length - 1).toFixed(1)},${y(0)} L${x(0).toFixed(1)},${y(0)} Z` : "";
  const sel = activo !== null ? puntos[activo] : null;

  // Etiquetas del eje X: primera, última y alguna intermedia para no solaparse
  // En móvil solo primera y última, con formato corto (día y mes) para que no se solapen
  const maxEtiquetas = estrecho ? 2 : 5;
  const etiquetaX = (fecha: string) =>
    estrecho
      ? new Intl.DateTimeFormat("es-CO", { day: "numeric", month: "short" }).format(new Date(fecha))
      : formatearFecha(fecha, "corta");
  const nEtiquetas = Math.min(puntos.length, maxEtiquetas);
  const indicesX = Array.from(new Set(Array.from({ length: nEtiquetas }, (_, k) => (nEtiquetas === 1 ? 0 : Math.round((k * (puntos.length - 1)) / (nEtiquetas - 1))))));

  const resumen = `Gráfico de línea con la evolución de tus ${puntos.length} últimos intentos, del ${pct(puntos[0].porcentaje)} al ${pct(puntos[puntos.length - 1].porcentaje)}.`;

  // El globo de detalle se mantiene dentro del gráfico
  const izq = activo !== null ? Math.min(Math.max(x(activo), 80), ancho - 80) : 0;

  return (
    <div ref={caja} className="relative w-full">
      <svg viewBox={`0 0 ${ancho} ${ALTO}`} role="img" aria-label={resumen} className="block h-auto w-full" onMouseLeave={() => setActivo(null)}>
        {/* Cuadrícula y eje Y */}
        {MARCAS_Y.map((m) => (
          <g key={m}>
            <line x1={M.izq} x2={ancho - M.der} y1={y(m)} y2={y(m)} className="stroke-borde" strokeWidth={1} />
            <text x={M.izq - 8} y={y(m) + 4} textAnchor="end" className="fill-suave text-[11px]">
              {pct(m)}
            </text>
          </g>
        ))}

        {/* Eje X */}
        {indicesX.map((i) => (
          <text key={i} x={x(i) + (puntos.length > 1 && i === 0 ? -M.izq + 4 : 0) + (puntos.length > 1 && i === puntos.length - 1 ? M.der - 4 : 0)} y={ALTO - 12} textAnchor={puntos.length > 1 && i === 0 ? "start" : puntos.length > 1 && i === puntos.length - 1 ? "end" : "middle"} className="fill-suave text-[11px]">
            {etiquetaX(puntos[i].fecha)}
          </text>
        ))}

        {/* Área, línea y puntos */}
        {puntos.length > 1 && <path d={area} className="fill-barra/10" />}
        {puntos.length > 1 && <path d={linea} fill="none" strokeWidth={2.5} strokeLinejoin="round" strokeLinecap="round" className="stroke-barra" />}
        {puntos.map((p, i) => (
          <g key={i}>
            {/* Zona sensible más grande que el punto, también accesible con teclado */}
            <circle
              cx={x(i)}
              cy={y(p.porcentaje)}
              r={16}
              fill="transparent"
              tabIndex={0}
              role="img"
              aria-label={`${formatearFecha(p.fecha)}: ${pct(p.porcentaje)}`}
              onMouseEnter={() => setActivo(i)}
              onFocus={() => setActivo(i)}
              onBlur={() => setActivo(null)}
              onClick={() => setActivo(i)}
              className="cursor-pointer outline-none [&:focus-visible]:stroke-anillo [&:focus-visible]:stroke-2"
            />
            <circle
              cx={x(i)}
              cy={y(p.porcentaje)}
              r={activo === i ? 6.5 : 4.5}
              strokeWidth={2.5}
              className="pointer-events-none fill-superficie stroke-barra transition-all"
            />
          </g>
        ))}
      </svg>

      {sel && activo !== null && (
        <div
          role="status"
          className="pointer-events-none absolute z-10 -translate-x-1/2 -translate-y-full whitespace-nowrap rounded-lg border border-borde-fuerte bg-superficie px-3 py-2 text-xs shadow-lg"
          style={{
            left: `${izq}px`,
            top: `${y(sel.porcentaje)}px`,
            marginTop: -12,
          }}
        >
          <div className="text-sm font-bold">{pct(sel.porcentaje)}</div>
          <div className="text-suave">{formatearFecha(sel.fecha)}</div>
          {sel.cuestionario_titulo && <div className="max-w-48 truncate text-suave">{sel.cuestionario_titulo}</div>}
        </div>
      )}
    </div>
  );
}
