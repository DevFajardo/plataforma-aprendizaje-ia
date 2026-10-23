import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
  title: "Resultados del cuestionario",
  description: "Resultados del cuestionario: intentos, análisis de ítems, ganancia de aprendizaje y retención.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
