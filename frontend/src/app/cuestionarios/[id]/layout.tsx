import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
  title: "Cuestionario",
  description: "Resumen, ideas clave y preguntas del cuestionario, con tutor de IA y resultados.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
