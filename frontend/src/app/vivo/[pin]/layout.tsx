import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
  title: "Unirse a la clase en vivo",
  description: "Entra a la clase en vivo con tu apodo, sin necesidad de cuenta.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
