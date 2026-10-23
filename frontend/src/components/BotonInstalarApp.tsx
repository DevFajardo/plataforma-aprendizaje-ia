"use client";

import { useState } from "react";
import { useInstalarApp } from "@/lib/pwa";
import { Boton, Icono } from "./ui";

/**
 * Botón «Instalar app». Solo aparece cuando el navegador permite instalar (Chrome, Edge, Android) o en iPhone/iPad,
 * donde muestra los pasos manuales. Si la app ya está instalada no se muestra.
 * `variante="discreta"` es un enlace pequeño para el pie de página.
 */
export default function BotonInstalarApp({ variante = "discreta" }: { variante?: "discreta" | "completa" }) {
  const { estado, instalar } = useInstalarApp();
  const [ayuda, setAyuda] = useState(false);

  if (estado === "instalada") {
    return variante === "completa" ? (
      <p className="flex items-center gap-2 text-sm text-exito-texto">
        <Icono nombre="check" tamano={18} /> La app ya está instalada en este dispositivo.
      </p>
    ) : null;
  }
  if (estado === "no-disponible") {
    return variante === "completa" ? (
      <p className="text-sm text-suave">
        Tu navegador no ofrece la instalación en este momento. En Chrome o Edge aparece un botón «Instalar app» cuando la página se abre por una
        dirección segura (https) o desde este mismo equipo.
      </p>
    ) : null;
  }

  const alPulsar = estado === "disponible" ? instalar : () => setAyuda((v) => !v);
  return (
    <div className="flex flex-col gap-2">
      {variante === "completa" ? (
        <Boton onClick={alPulsar} variante="secundario" aria-expanded={estado === "ios" ? ayuda : undefined} className="sm:self-start">
          <Icono nombre="instalar" /> Instalar app
        </Boton>
      ) : (
        <button
          type="button"
          onClick={alPulsar}
          aria-expanded={estado === "ios" ? ayuda : undefined}
          className="inline-flex min-h-10 items-center gap-2 self-start rounded-lg text-sm font-semibold text-enlace underline underline-offset-2 lg:self-end"
        >
          <Icono nombre="instalar" tamano={18} /> Instalar app
        </button>
      )}
      {estado === "ios" && ayuda && (
        <div role="note" className="max-w-sm rounded-xl border border-info-borde bg-info-fondo p-3 text-sm text-info-texto">
          <p className="font-bold">Instalar en iPhone o iPad</p>
          <ol className="mt-1 list-decimal pl-5">
            <li>Abre esta página en Safari.</li>
            <li>
              Toca el botón <strong>Compartir</strong> (el cuadro con una flecha hacia arriba).
            </li>
            <li>
              Elige <strong>Agregar a inicio</strong> y confirma.
            </li>
          </ol>
        </div>
      )}
    </div>
  );
}
