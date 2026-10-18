import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = { title: "Encuesta de usabilidad" };

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
