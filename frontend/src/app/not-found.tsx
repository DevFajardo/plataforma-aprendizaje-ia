import type { Metadata } from "next";
import { BotonEnlace, Pagina } from "@/components/ui";

export const metadata: Metadata = {
  title: "Página no encontrada",
  description: "La página que buscas no existe o fue movida.",
};

/** 404 amable con el diseño de la plataforma. */
export default function NoEncontrada() {
  return (
    <Pagina ancho="md" className="flex items-center">
      <section className="flex w-full flex-col items-center gap-5 rounded-2xl border border-borde border-t-4 border-t-cul-naranja bg-superficie px-6 py-12 text-center shadow-sm">
        <p aria-hidden="true" className="text-6xl font-extrabold tracking-tight text-primario sm:text-7xl">
          404
        </p>
        <h1 className="text-2xl font-extrabold sm:text-3xl">No encontramos esta página</h1>
        <p className="max-w-md text-suave">
          Puede que el enlace esté mal escrito o que el contenido ya no exista. Revisa la dirección o vuelve al inicio para seguir aprendiendo.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row">
          <BotonEnlace href="/">Ir al inicio</BotonEnlace>
          <BotonEnlace href="/panel" variante="secundario">
            Ir a mi panel
          </BotonEnlace>
        </div>
      </section>
    </Pagina>
  );
}
