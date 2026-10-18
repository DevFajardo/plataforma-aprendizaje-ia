import type { Metadata, Viewport } from "next";
import { Montserrat } from "next/font/google";
import { existsSync } from "node:fs";
import { join } from "node:path";
import { Suspense } from "react";
import "./globals.css";
import { ProveedorLogo } from "@/components/MarcaInstitucional";
import Navbar from "@/components/Navbar";
import PiePagina from "@/components/PiePagina";
import { AuthProvider } from "@/lib/auth";

// Tipografía institucional de la CUL (Montserrat, fuente variable: pesos 100-900)
const montserrat = Montserrat({
  variable: "--font-montserrat",
  subsets: ["latin"],
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Aprendizaje Activo CUL · Plataforma de Aprendizaje Activo con IA",
    template: "%s · Aprendizaje Activo CUL",
  },
  description:
    "Convierte un video de YouTube o Vimeo en un resumen y un cuestionario interactivo generados con IA. Proyecto académico de Ingeniería de Sistemas y Computación, Corporación Universitaria Latinoamericana.",
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#0B468A" },
    { media: "(prefers-color-scheme: dark)", color: "#172741" },
  ],
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  // Si el estudiante coloca el logo oficial en public/logo-cul.png, se usa; si no, un monograma de texto.
  const hayLogo = existsSync(join(process.cwd(), "public", "logo-cul.png"));

  return (
    <html lang="es" className={`${montserrat.variable} h-full antialiased`}>
      <body className="relative flex min-h-full flex-col">
        <a
          href="#contenido"
          className="sr-only z-[60] rounded-lg bg-cul-amarillo px-4 py-2 font-bold text-cul-azul-oscuro focus:not-sr-only focus:fixed focus:left-3 focus:top-3"
        >
          Saltar al contenido
        </a>
        <ProveedorLogo hayLogo={hayLogo}>
          <AuthProvider>
            <Suspense fallback={null}>
              <Navbar />
            </Suspense>
            {children}
            <PiePagina />
          </AuthProvider>
        </ProveedorLogo>
      </body>
    </html>
  );
}
