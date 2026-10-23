"use client";

import { useEffect } from "react";
import { Boton, BotonEnlace, Icono, Pagina } from "@/components/ui";

/** Error inesperado en una página: mensaje amable, sin detalles técnicos, con opción de reintentar. */
export default function Error({ error, retry }: { error: Error & { digest?: string }; retry: () => void }) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <Pagina ancho="md" className="flex items-center">
      <section
        role="alert"
        className="flex w-full flex-col items-center gap-5 rounded-2xl border border-borde border-t-4 border-t-cul-naranja bg-superficie px-6 py-12 text-center shadow-sm"
      >
        <span aria-hidden="true" className="flex h-16 w-16 items-center justify-center rounded-full bg-aviso-fondo text-aviso-texto">
          <Icono nombre="alerta" tamano={32} />
        </span>
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">Algo no salió como esperábamos</h1>
        <p className="max-w-md text-suave">
          Tuvimos un problema al mostrar esta página. Tu información está a salvo. Intenta de nuevo y, si el problema continúa, vuelve al inicio.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <Boton onClick={() => retry()}>Intentar de nuevo</Boton>
          <BotonEnlace href="/" variante="secundario">
            Ir al inicio
          </BotonEnlace>
        </div>
      </section>
    </Pagina>
  );
}
