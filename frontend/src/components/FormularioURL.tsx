"use client";

import { useState } from "react";
import { Boton, Icono, Input, Select } from "./ui";

interface Props {
  deshabilitado: boolean;
  onEnviar: (url: string, numPreguntas: number) => void;
}

export default function FormularioURL({ deshabilitado, onEnviar }: Props) {
  const [url, setUrl] = useState("");
  const [numPreguntas, setNumPreguntas] = useState(8);

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (url.trim()) onEnviar(url.trim(), numPreguntas);
      }}
      className="flex flex-col gap-4"
    >
      <Input
        etiqueta="Enlace del video"
        type="url"
        required
        value={url}
        onChange={(e) => setUrl(e.target.value)}
        placeholder="https://www.youtube.com/watch?v=…"
        aria-label="URL del video de YouTube o Vimeo"
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
        <Boton type="submit" tamano="lg" disabled={deshabilitado} className="sm:flex-1">
          <Icono nombre="chispa" />
          Generar
        </Boton>
      </div>
    </form>
  );
}
