import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Comparar grupos",
  description: "Compara dos cuestionarios o grupos: desempeño inicial, retención diferida y tamaño del efecto.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
