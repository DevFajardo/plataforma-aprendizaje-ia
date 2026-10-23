import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Mi panel",
  description: "Tu panel de progreso: resultados, evolución y repasos pendientes.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
