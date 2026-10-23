import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
  title: "Coordinación",
  description: "Logro de los resultados de aprendizaje por programa, asignatura y nivel de Bloom, con tendencia semanal y alertas tempranas.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
