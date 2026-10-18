import type { SVGProps } from "react";

/** Iconos SVG inline (trazo 2, 24×24). Decorativos por defecto: aria-hidden. */
const RUTAS = {
  menu: "M4 6h16M4 12h16M4 18h16",
  cerrar: "M6 6l12 12M18 6L6 18",
  flecha: "M5 12h14M13 6l6 6-6 6",
  atras: "M19 12H5M11 6l-6 6 6 6",
  check: "M5 13l4 4L19 7",
  x: "M6 6l12 12M18 6L6 18",
  info: "M12 8h.01M11 12h1v5h1M3 12a9 9 0 1018 0 9 9 0 00-18 0z",
  alerta: "M12 9v4m0 4h.01M10.3 3.9L2.4 18a2 2 0 001.7 3h15.8a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z",
  chevron: "M6 9l6 6 6-6",
  intentos: "M9 11l3 3 8-8M20 12v7a2 2 0 01-2 2H6a2 2 0 01-2-2V7a2 2 0 012-2h9",
  promedio: "M4 20V10m6 10V4m6 16v-7m4 7H2",
  trofeo: "M8 21h8m-4-4v4M7 4h10v5a5 5 0 01-10 0V4zM7 6H4v1a3 3 0 003 3m10-4h3v1a3 3 0 01-3 3",
  repetir: "M17 2l4 4-4 4M3 11V9a3 3 0 013-3h15M7 22l-4-4 4-4m14 3v2a3 3 0 01-3 3H3",
  libro: "M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2V5zm0 14a2 2 0 002 2h13M9 7h6",
  grupo: "M17 20v-2a4 4 0 00-4-4H7a4 4 0 00-4 4v2m18 0v-2a4 4 0 00-3-3.9M16 4.1a4 4 0 010 7.8M10 10a4 4 0 100-8 4 4 0 000 8z",
  reloj: "M12 7v5l3 2m6-2a9 9 0 11-18 0 9 9 0 0118 0z",
  enlace: "M10 14a5 5 0 007 0l3-3a5 5 0 00-7-7l-1 1m2 6a5 5 0 00-7 0l-3 3a5 5 0 007 7l1-1",
  subir: "M12 16V4m0 0L7 9m5-5l5 5M4 16v3a2 2 0 002 2h12a2 2 0 002-2v-3",
  chispa: "M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9L12 3zm7 12l.8 2.2L22 18l-2.2.8L19 21l-.8-2.2L16 18l2.2-.8L19 15z",
  video: "M3 7a2 2 0 012-2h9a2 2 0 012 2v10a2 2 0 01-2 2H5a2 2 0 01-2-2V7zm13 3l5-3v10l-5-3",
  usuario: "M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2m8-10a4 4 0 100-8 4 4 0 000 8z",
  salir: "M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4m7 14l5-5-5-5m5 5H9",
  escudo: "M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6l8-3zm-3 9l2 2 4-4",
  copiar: "M9 9h10a2 2 0 012 2v10a2 2 0 01-2 2H9a2 2 0 01-2-2V11a2 2 0 012-2zM5 15H4a2 2 0 01-2-2V3a2 2 0 012-2h10a2 2 0 012 2v1",
  descargar: "M12 4v12m0 0l-5-5m5 5l5-5M4 20h16",
  subir_flecha: "M12 19V7m0 0l-5 5m5-5l5 5",
  bajar_flecha: "M12 5v12m0 0l5-5m-5 5l-5-5",
  basura: "M4 7h16M10 11v6m4-6v6M6 7l1 13a2 2 0 002 2h6a2 2 0 002-2l1-13M9 7V4h6v3",
  mas: "M12 5v14M5 12h14",
  lapiz: "M4 20h4l10.5-10.5a2.1 2.1 0 00-3-3L5 17v3zM13.5 6.5l3 3",
  play: "M8 5v14l11-7L8 5z",
} as const;

export type NombreIcono = keyof typeof RUTAS;

interface Props extends Omit<SVGProps<SVGSVGElement>, "name"> {
  nombre: NombreIcono;
  tamano?: number;
  /** Texto accesible; si se omite el icono es decorativo. */
  titulo?: string;
}

export default function Icono({ nombre, tamano = 20, titulo, className, ...resto }: Props) {
  return (
    <svg
      width={tamano}
      height={tamano}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden={titulo ? undefined : true}
      role={titulo ? "img" : undefined}
      aria-label={titulo}
      className={"shrink-0 " + (className ?? "")}
      {...resto}
    >
      <path d={RUTAS[nombre]} />
    </svg>
  );
}
