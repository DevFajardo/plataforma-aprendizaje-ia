import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  robots: { index: false, follow: false },
  title: "Mis cuestionarios",
  description: "Tus cuestionarios generados a partir de videos: edítalos, publícalos y compártelos.",
};

export default function Layout({ children }: { children: ReactNode }) {
  return children;
}
