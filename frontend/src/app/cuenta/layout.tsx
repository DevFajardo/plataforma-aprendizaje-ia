import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
  title: "Mi cuenta",
  description: "Edita tus datos, descarga tu información, repite el tutorial e instala la aplicación.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
