import { Suspense } from "react";
import Presentador from "@/components/vivo/Presentador";
import { EsqueletoPagina, Pagina } from "@/components/ui";

export default function PresentarPage() {
  return (
    <Suspense
      fallback={
        <Pagina ancho="lg">
          <EsqueletoPagina />
        </Pagina>
      }
    >
      <Presentador />
    </Suspense>
  );
}
