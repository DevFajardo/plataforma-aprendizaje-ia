import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
  title: "Unirse a un cuestionario",
  description: "Únete a un grupo con el código de ingreso o a una clase en vivo con el PIN.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
