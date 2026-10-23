import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Historial de intentos",
  description: "Historial de tus intentos, puntajes y evolución en los cuestionarios.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
