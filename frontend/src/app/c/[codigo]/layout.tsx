import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Unirse a un cuestionario",
  description: "Únete a un cuestionario compartido por tu docente y responde con retroalimentación inmediata.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
