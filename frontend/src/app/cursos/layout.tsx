import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "Cursos",
  description: "Crea y administra tus grupos por asignatura y periodo, y comparte el código de ingreso.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
