"use client";

import { useEffect } from "react";
import { useToast } from "./Toast";

/** Mensaje de estado de un formulario. Los errores se muestran en línea (role=alert); los éxitos se confirman con un toast accesible. */
export type MensajeForm = { tipo: "ok" | "error"; texto: string } | null;

export default function Aviso({ mensaje }: { mensaje: MensajeForm }) {
  const { avisar } = useToast();
  useEffect(() => {
    if (mensaje?.tipo === "ok") avisar(mensaje.texto, "ok");
  }, [mensaje, avisar]);

  if (!mensaje || mensaje.tipo === "ok") return null;
  return (
    <p role="alert" className="text-sm font-semibold text-error-texto">
      <span aria-hidden="true">⚠ </span>
      {mensaje.texto}
    </p>
  );
}
