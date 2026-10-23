import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Administración",
  description: "Administra facultades, programas, asignaturas, resultados de aprendizaje y roles de usuario.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
