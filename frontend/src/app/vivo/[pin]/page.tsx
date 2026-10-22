"use client";

import { useParams } from "next/navigation";
import { Suspense } from "react";
import { EsqueletoPagina, Pagina } from "@/components/ui";
import Participante from "@/components/vivo/Participante";

function Contenido() {
  const { pin } = useParams<{ pin: string }>();
  return <Participante pinInicial={pin} />;
}

export default function VivoConPinPage() {
  return (
    <Suspense
      fallback={
        <Pagina ancho="sm">
          <EsqueletoPagina tarjetas={1} />
        </Pagina>
      }
    >
      <Contenido />
    </Suspense>
  );
}
