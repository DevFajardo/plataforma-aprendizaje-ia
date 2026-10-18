"use client";

import { useRef, useState } from "react";
import { BarraPorcentaje, Boton, Icono, Select, cx } from "./ui";

const EXTENSIONES = ["mp4", "webm", "mov", "mkv", "mp3", "wav", "m4a", "ogg"];
export const MAX_SUBIDA_MB = 200;

interface Props {
  deshabilitado: boolean;
  /** Porcentaje de subida (0-100) o null si no se está subiendo. */
  progreso: number | null;
  onEnviar: (archivo: File, numPreguntas: number) => void;
}

function validar(archivo: File): string | null {
  const ext = archivo.name.split(".").pop()?.toLowerCase() ?? "";
  if (!EXTENSIONES.includes(ext)) return `Formato no permitido. Usa: ${EXTENSIONES.join(", ")}.`;
  if (archivo.size > MAX_SUBIDA_MB * 1024 * 1024) return `El archivo supera el límite de ${MAX_SUBIDA_MB} MB.`;
  if (archivo.size === 0) return "El archivo está vacío.";
  return null;
}

export default function FormularioArchivo({ deshabilitado, progreso, onEnviar }: Props) {
  const entrada = useRef<HTMLInputElement>(null);
  const [archivo, setArchivo] = useState<File | null>(null);
  const [errorLocal, setErrorLocal] = useState<string | null>(null);
  const [arrastrando, setArrastrando] = useState(false);
  const [numPreguntas, setNumPreguntas] = useState(8);

  function elegir(f: File | undefined) {
    if (!f) return;
    const problema = validar(f);
    setErrorLocal(problema);
    setArchivo(problema ? null : f);
  }

  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        if (archivo) onEnviar(archivo, numPreguntas);
      }}
      className="flex flex-col gap-4"
    >
      <div
        onDragOver={(e) => {
          e.preventDefault();
          if (!deshabilitado) setArrastrando(true);
        }}
        onDragLeave={() => setArrastrando(false)}
        onDrop={(e) => {
          e.preventDefault();
          setArrastrando(false);
          if (!deshabilitado) elegir(e.dataTransfer.files[0]);
        }}
        className={cx(
          "flex flex-col items-center gap-3 rounded-2xl border-2 border-dashed p-6 text-center transition duration-150 sm:p-8",
          arrastrando ? "border-anillo bg-info-fondo" : "border-borde-fuerte bg-superficie-2/50",
        )}
      >
        <span className="flex h-12 w-12 items-center justify-center rounded-full bg-info-fondo text-info-texto">
          <Icono nombre="subir" tamano={24} />
        </span>
        <p className="text-texto">
          {archivo ? (
            <>
              <strong className="break-all">{archivo.name}</strong> ({(archivo.size / 1024 / 1024).toFixed(1)} MB)
            </>
          ) : (
            <span className="font-semibold">
              <span className="hidden sm:inline">Arrastra aquí un video o audio, o</span>
              <span className="sm:hidden">Elige un video o audio</span>
            </span>
          )}
        </p>
        <Boton variante="secundario" disabled={deshabilitado} onClick={() => entrada.current?.click()}>
          {archivo ? "Elegir otro archivo" : "Elegir archivo"}
        </Boton>
        <input
          ref={entrada}
          type="file"
          hidden
          accept={EXTENSIONES.map((x) => "." + x).join(",")}
          aria-label="Archivo de video o audio"
          onChange={(e) => {
            elegir(e.target.files?.[0]);
            e.target.value = "";
          }}
        />
        <p className="text-xs text-suave">
          {EXTENSIONES.join(", ")} · máximo {MAX_SUBIDA_MB} MB
        </p>
      </div>

      {errorLocal && (
        <p role="alert" className="text-sm font-semibold text-error-texto">
          {errorLocal}
        </p>
      )}

      {progreso !== null && (
        <div>
          <BarraPorcentaje valor={progreso} etiqueta="Progreso de la subida" alto="lg" />
          <p className="mt-1.5 text-sm text-suave">{progreso < 100 ? `Subiendo… ${progreso}%` : "Subida completa. Procesando…"}</p>
        </div>
      )}

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
        <Boton type="submit" tamano="lg" disabled={deshabilitado || !archivo} className="sm:flex-1">
          <Icono nombre="chispa" />
          Subir y generar
        </Boton>
      </div>
    </form>
  );
}
