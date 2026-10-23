import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Banco de preguntas",
  description: "Banco de preguntas institucional: busca y reutiliza preguntas por resultado de aprendizaje, nivel de Bloom y asignatura.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
