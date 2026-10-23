"use client";

import { useState } from "react";
import { useValidacion } from "@/lib/validacion";
import { Boton, Icono, Input, Select } from "./ui";

interface Props {
  deshabilitado: boolean;
  onEnviar: (url: string, numPreguntas: number) => void;
}

function validarUrl(v: string): string | null {
  if (!v.trim()) return "Pega el enlace de un video de YouTube o Vimeo.";
  try {
    const u = new URL(v.trim());
    if (u.protocol !== "http:" && u.protocol !== "https:") throw new Error("protocolo");
  } catch {
    return "Ese enlace no parece válido. Debe empezar por https://";
  }
  return null;
}
const REGLAS = { url: validarUrl };

export default function FormularioURL({ deshabilitado, onEnviar }: Props) {
  const [url, setUrl] = useState("");
  const [numPreguntas, setNumPreguntas] = useState(8);
  const { errores, ref, validarCampo, validarTodo, limpiar } = useValidacion<{ url: string }>(REGLAS);

  return (
    <form
      noValidate
      ref={ref}
      onSubmit={(e) => {
        e.preventDefault();
        if (validarTodo({ url })) onEnviar(url.trim(), numPreguntas);
      }}
      className="flex flex-col gap-4"
    >
      <Input
        etiqueta="Enlace del video"
        type="url"
        required
        value={url}
        onChange={(e) => {
          setUrl(e.target.value);
          limpiar("url");
        }}
        onBlur={() => url && validarCampo("url", { url })}
        error={errores.url}
        placeholder="https://www.youtube.com/watch?v=…"
        ayuda="Pega la URL de un video de YouTube o Vimeo (no se admiten transmisiones en vivo)."
        disabled={deshabilitado}
      />
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end">
        <Select
          etiqueta="Número de preguntas"
          value={numPreguntas}
          onChange={(e) => setNumPreguntas(Number(e.target.value))}
          disabled={deshabilitado}
          claseCampo="sm:w-52"
        >
          {[5, 8, 10].map((n) => (
            <option key={n} value={n}>
              {n} preguntas
            </option>
          ))}
        </Select>
        <Boton type="submit" tamano="lg" disabled={deshabilitado} cargando={deshabilitado} className="sm:flex-1">
          <Icono nombre="chispa" />
          Generar
        </Boton>
      </div>
    </form>
  );
}
