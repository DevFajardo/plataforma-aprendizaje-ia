import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
  title: "Presentar clase en vivo",
  description: "Pantalla del docente para presentar la clase en vivo: PIN, código QR, preguntas y podio.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
