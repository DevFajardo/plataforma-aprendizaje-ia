import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
  title: "Iniciar sesión",
  description: "Inicia sesión en la Plataforma de Aprendizaje Activo con IA.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
