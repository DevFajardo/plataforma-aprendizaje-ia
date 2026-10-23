import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
  title: "Clase en vivo",
  description: "Clase en vivo estilo concurso: ingresa el PIN, responde desde tu celular y compite en el podio.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
