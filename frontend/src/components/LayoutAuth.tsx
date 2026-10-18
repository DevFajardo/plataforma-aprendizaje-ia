import type { ReactNode } from "react";
import { Icono, type NombreIcono } from "./ui";
import MarcaInstitucional from "./MarcaInstitucional";

const PUNTOS: { icono: NombreIcono; texto: string }[] = [
  { icono: "video", texto: "Pega el enlace de un video o sube tu propio archivo." },
  { icono: "chispa", texto: "La IA transcribe y genera resumen, ideas clave y cuestionario." },
  { icono: "trofeo", texto: "Responde, recibe retroalimentación al instante y sigue tu progreso." },
];

interface Props {
  titulo: string;
  descripcion: string;
  children: ReactNode;
  /** Texto bajo el formulario (p. ej. enlace a la otra pantalla). */
  pie?: ReactNode;
}

/** Pantalla de acceso: panel institucional azul + formulario (dos columnas en escritorio, una en móvil). */
export default function LayoutAuth({ titulo, descripcion, children, pie }: Props) {
  return (
    <div className="flex flex-1 flex-col lg:grid lg:grid-cols-[minmax(0,5fr)_minmax(0,6fr)]">
      <aside
        aria-label="Presentación"
        className="relative overflow-hidden bg-gradient-to-br from-cul-azul via-cul-azul to-cul-marino px-4 py-6 text-white sm:px-8 sm:py-8 lg:flex lg:flex-col lg:justify-between lg:px-12 lg:py-14"
      >
        <div aria-hidden="true" className="pointer-events-none absolute -right-24 -top-24 h-72 w-72 rounded-full border-[28px] border-white/5" />
        <div aria-hidden="true" className="pointer-events-none absolute -bottom-32 -left-20 hidden h-80 w-80 rounded-full border-[36px] border-cul-cian/10 lg:block" />
        <div className="relative">
          <MarcaInstitucional variante="panel" titulo="Aprendizaje Activo con IA" />
          <h2 className="mt-5 text-xl font-bold leading-snug sm:text-2xl lg:mt-14 lg:text-4xl">
            Aprende viendo, <span className="text-cul-amarillo-vivo">practicando</span> y recibiendo respuestas al instante.
          </h2>
          <span aria-hidden="true" className="mt-4 block h-1 w-16 rounded-full bg-cul-naranja" />
          <p className="mt-4 hidden max-w-md text-white/90 sm:block">
            Convierte cualquier video educativo en un resumen y un cuestionario interactivo con inteligencia artificial.
          </p>
        </div>
        <ul className="relative mt-8 hidden flex-col gap-4 lg:flex">
          {PUNTOS.map((p) => (
            <li key={p.texto} className="flex items-start gap-3 text-white/95">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white/15">
                <Icono nombre={p.icono} />
              </span>
              <span className="pt-1 text-sm leading-snug">{p.texto}</span>
            </li>
          ))}
        </ul>
      </aside>

      <main id="contenido" tabIndex={-1} className="flex flex-1 items-start justify-center px-4 py-8 outline-none sm:px-8 sm:py-12 lg:items-center lg:py-14">
        <div className="w-full max-w-md">
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{titulo}</h1>
          <span aria-hidden="true" className="mt-3 block h-1 w-14 rounded-full bg-cul-naranja" />
          <p className="mb-6 mt-3 text-suave">{descripcion}</p>
          {children}
          {pie && <div className="mt-6 text-sm text-suave">{pie}</div>}
        </div>
      </main>
    </div>
  );
}
