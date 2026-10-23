import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Mis cursos",
  description: "Tus cursos y los cuestionarios publicados por tus docentes.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
