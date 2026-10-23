import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
  title: "Resultados de la encuesta",
  description: "Resultados agregados y anónimos de la encuesta de usabilidad SUS.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
