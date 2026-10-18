import Link from "next/link";
import MarcaInstitucional from "./MarcaInstitucional";

/** Pie de página institucional: aviso de proyecto académico, privacidad y nota de sitio no oficial. */
export default function PiePagina() {
  return (
    <footer className="border-t border-borde bg-superficie">
      <div className="h-1 bg-cul-naranja" aria-hidden="true" />
      <div className="mx-auto flex max-w-7xl flex-col gap-5 px-4 py-8 sm:px-6 lg:flex-row lg:items-center lg:justify-between lg:px-8">
        <MarcaInstitucional variante="pie" titulo="Aprendizaje Activo CUL" />
        <div className="flex flex-col gap-2 text-sm text-suave lg:max-w-xl lg:text-right">
          <p>Proyecto académico — Ingeniería de Sistemas y Computación · Corporación Universitaria Latinoamericana, Barranquilla</p>
          <p>
            <Link href="/privacidad" className="inline-flex min-h-10 items-center font-semibold text-enlace underline underline-offset-2">
              Política de tratamiento de datos personales
            </Link>
          </p>
          <p className="text-xs">Sitio académico, no oficial de la institución.</p>
        </div>
      </div>
    </footer>
  );
}
