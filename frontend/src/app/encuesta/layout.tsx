import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Encuesta de usabilidad",
  description: "Responde la encuesta de usabilidad SUS (10 preguntas) para ayudar a mejorar la plataforma.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
