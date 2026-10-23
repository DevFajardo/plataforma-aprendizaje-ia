import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Crear cuenta",
  description: "Crea tu cuenta de estudiante o docente en la Plataforma de Aprendizaje Activo con IA.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
