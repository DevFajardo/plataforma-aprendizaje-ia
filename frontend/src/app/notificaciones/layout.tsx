import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Notificaciones",
  description: "Avisos de cuestionarios nuevos, repasos pendientes y alertas.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
