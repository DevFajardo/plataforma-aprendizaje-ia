import Link from "next/link";
import type { ReactNode } from "react";
import Icono from "./Icono";

interface Props {
  titulo: ReactNode;
  descripcion?: ReactNode;
  acciones?: ReactNode;
  /** Enlace «volver» sobre el título. */
  atras?: { href: string; texto: string };
  /** Insignias u otros elementos junto al título. */
  etiquetas?: ReactNode;
}

/** Título de página con franja naranja de marca, descripción y acciones. */
export default function EncabezadoPagina({ titulo, descripcion, acciones, atras, etiquetas }: Props) {
  return (
    <header className="mb-6 sm:mb-8">
      {atras && (
        <Link href={atras.href} className="mb-3 inline-flex min-h-10 items-center gap-1.5 text-sm font-semibold text-enlace hover:underline">
          <Icono nombre="atras" tamano={16} />
          {atras.texto}
        </Link>
      )}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h1 className="text-2xl font-bold leading-tight tracking-tight sm:text-3xl">{titulo}</h1>
          {etiquetas && <div className="mt-2 flex flex-wrap gap-2">{etiquetas}</div>}
          <span aria-hidden="true" className="mt-3 block h-1 w-14 rounded-full bg-cul-naranja" />
          {descripcion && <p className="mt-3 max-w-2xl text-suave">{descripcion}</p>}
        </div>
        {acciones && <div className="flex shrink-0 flex-wrap gap-2">{acciones}</div>}
      </div>
    </header>
  );
}
