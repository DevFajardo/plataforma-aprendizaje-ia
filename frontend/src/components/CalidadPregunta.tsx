"use client";

import { useState } from "react";
import { guardarEnBanco, verificarCalidad } from "@/lib/api";
import type { Pregunta, Verificacion } from "@/lib/tipos";
import { Alerta, Boton, Icono, Input, Insignia, Select, Tarjeta, TituloSeccion } from "./ui";
import { useToast } from "@/components/ui/Toast";

/** Convierte "mm:ss" (o "hh:mm:ss") en segundos; null si no es válido. */
function aSegundos(marca: string): number | null {
  const partes = marca.split(":").map(Number);
  if (!marca || partes.some((n) => Number.isNaN(n))) return null;
  return partes.reduce((acc, n) => acc * 60 + n, 0);
}

/** Sello de calidad de una pregunta. El significado va siempre en el texto, no solo en el color. */
export function SelloVerificacion({ v }: { v: Verificacion | null | undefined }) {
  if (!v) return <Insignia tono="neutro">Sin verificar</Insignia>;
  if (v.estado === "verificada")
    return (
      <Insignia tono="exito">
        <Icono nombre="check" tamano={12} /> Verificada en el video
      </Insignia>
    );
  return (
    <Insignia tono="aviso">
      <Icono nombre="alerta" tamano={12} /> Revisar
    </Insignia>
  );
}

const TEXTO_RESPALDO = {
  si: "La pregunta y su respuesta están respaldadas por el video.",
  parcial: "El video respalda la pregunta solo en parte.",
  no: "No se encontró respaldo en el video.",
} as const;

/** Detalle de la verificación para el docente (desplegable). */
export function DetalleVerificacion({ v, onSaltar }: { v: Verificacion | null | undefined; onSaltar?: (segundos: number) => void }) {
  if (!v) return null;
  const seg = aSegundos(v.marca_tiempo);
  return (
    <details className="group rounded-xl border border-borde bg-superficie-2/60 text-sm">
      <summary className="flex min-h-10 cursor-pointer list-none items-center justify-between gap-3 px-3 py-1.5 font-semibold [&::-webkit-details-marker]:hidden">
        Ver detalle de la verificación
        <Icono nombre="chevron" tamano={16} className="transition group-open:rotate-180" />
      </summary>
      <div className="flex flex-col gap-2 border-t border-borde px-3 py-3">
        <p>{TEXTO_RESPALDO[v.respaldo]}</p>
        {v.cita && (
          <blockquote className="border-l-4 border-cul-naranja pl-3 italic text-suave">
            «{v.cita}»
            {seg !== null && onSaltar && (
              <Boton variante="secundario" tamano="sm" onClick={() => onSaltar(seg)} className="ml-2 not-italic">
                <Icono nombre="play" tamano={12} /> {v.marca_tiempo}
              </Boton>
            )}
          </blockquote>
        )}
        <p>{v.inequivoca ? "La respuesta correcta es inequívoca." : "Otra opción también podría ser defendible: revisa la respuesta y los distractores."}</p>
        {v.problemas.length > 0 && (
          <ul className="list-disc pl-5">
            {v.problemas.map((p, i) => (
              <li key={i}>{p}</li>
            ))}
          </ul>
        )}
      </div>
    </details>
  );
}

/** Botón y formulario en línea para guardar una pregunta en el banco institucional. */
export function GuardarEnBanco({ pregunta, tieneGrupo, onGuardada }: { pregunta: Pregunta; tieneGrupo: boolean; onGuardada?: () => void }) {
  const [abierto, setAbierto] = useState(false);
  const { avisar } = useToast();
  const [visibilidad, setVisibilidad] = useState<"institucional" | "privada">("institucional");
  const [etiquetas, setEtiquetas] = useState("");
  const [asignatura, setAsignatura] = useState("");
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [listo, setListo] = useState(!!pregunta.banco_id);

  async function guardar() {
    setError(null);
    setGuardando(true);
    try {
      await guardarEnBanco(pregunta.id, {
        visibilidad,
        etiquetas: etiquetas.split(",").map((e) => e.trim()).filter(Boolean),
        ...(!tieneGrupo && asignatura.trim() ? { asignatura_nombre: asignatura.trim() } : {}),
      });
      setListo(true);
      avisar("Pregunta guardada en el banco.");
      setAbierto(false);
      onGuardada?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setGuardando(false);
    }
  }

  if (listo)
    return (
      <Insignia tono="azul">
        <Icono nombre="libro" tamano={12} /> En el banco
      </Insignia>
    );
  return (
    <div className="flex flex-col gap-2">
      {!abierto ? (
        <Boton variante="secundario" tamano="sm" onClick={() => setAbierto(true)} className="self-start">
          <Icono nombre="libro" tamano={14} /> Guardar en el banco
        </Boton>
      ) : (
        <div className="flex flex-col gap-3 rounded-xl border border-borde bg-superficie-2/60 p-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <Select etiqueta="Visibilidad" value={visibilidad} onChange={(e) => setVisibilidad(e.target.value as "institucional" | "privada")}>
              <option value="institucional">Institucional (todos los docentes)</option>
              <option value="privada">Privada (solo yo)</option>
            </Select>
            <Input etiqueta="Etiquetas (separadas por comas)" value={etiquetas} onChange={(e) => setEtiquetas(e.target.value)} maxLength={200} />
          </div>
          {!tieneGrupo && (
            <Input etiqueta="Asignatura (opcional)" value={asignatura} onChange={(e) => setAsignatura(e.target.value)} maxLength={150} />
          )}
          {error && <Alerta tipo="error">{error}</Alerta>}
          <div className="flex flex-wrap gap-2">
            <Boton tamano="sm" cargando={guardando} onClick={guardar}>
              Guardar
            </Boton>
            <Boton variante="secundario" tamano="sm" onClick={() => setAbierto(false)}>
              Cancelar
            </Boton>
          </div>
        </div>
      )}
    </div>
  );
}

/** Panel del docente en el visor: estado de calidad de todas las preguntas, con filtro de las que requieren revisión. */
export function PanelCalidad({
  cuestionarioId,
  preguntas,
  tieneGrupo,
  onSaltar,
  onRecargar,
}: {
  cuestionarioId: number;
  preguntas: Pregunta[];
  tieneGrupo: boolean;
  onSaltar: (segundos: number) => void;
  onRecargar: () => void;
}) {
  const [soloRevisar, setSoloRevisar] = useState(false);
  const [verificando, setVerificando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sinVerificar = preguntas.filter((p) => !p.verificacion).length;
  const aRevisar = preguntas.filter((p) => p.verificacion?.estado === "revisar").length;
  const visibles = soloRevisar ? preguntas.filter((p) => p.verificacion?.estado === "revisar") : preguntas;

  async function verificar() {
    setError(null);
    setVerificando(true);
    try {
      await verificarCalidad(cuestionarioId);
      onRecargar();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setVerificando(false);
    }
  }

  return (
    <Tarjeta as="section" aria-label="Calidad de las preguntas" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <TituloSeccion nivel={3}>Calidad de las preguntas</TituloSeccion>
          <p className="mt-1 text-sm text-suave">
            {aRevisar > 0 ? `${aRevisar} ${aRevisar === 1 ? "pregunta requiere" : "preguntas requieren"} revisión. ` : sinVerificar === preguntas.length ? "" : "Todas las verificadas están respaldadas por el video. "}
            {sinVerificar > 0 && `${sinVerificar} sin verificar.`}
          </p>
        </div>
        {sinVerificar > 0 && (
          <Boton variante="secundario" tamano="sm" cargando={verificando} onClick={verificar}>
            <Icono nombre="escudo" tamano={14} /> {sinVerificar === preguntas.length ? "Verificar ahora" : "Volver a verificar"}
          </Boton>
        )}
      </div>
      {error && <Alerta tipo="error">{error}</Alerta>}
      <label className="flex min-h-11 cursor-pointer items-center gap-3 text-sm font-semibold">
        <input type="checkbox" checked={soloRevisar} onChange={(e) => setSoloRevisar(e.target.checked)} className="h-5 w-5 accent-primario" />
        Ver solo las que requieren revisión
      </label>
      {visibles.length === 0 ? (
        <p className="text-sm text-suave">No hay preguntas que requieran revisión.</p>
      ) : (
        <ul className="flex flex-col gap-3">
          {visibles.map((p) => (
            <li key={p.id} className="flex flex-col gap-2 rounded-xl border border-borde p-3">
              <p className="text-sm font-semibold">
                {p.orden + 1}. {p.enunciado}
              </p>
              <div className="flex flex-wrap items-center gap-2">
                <SelloVerificacion v={p.verificacion} />
                <GuardarEnBanco pregunta={p} tieneGrupo={tieneGrupo} />
              </div>
              <DetalleVerificacion v={p.verificacion} onSaltar={onSaltar} />
            </li>
          ))}
        </ul>
      )}
    </Tarjeta>
  );
}
