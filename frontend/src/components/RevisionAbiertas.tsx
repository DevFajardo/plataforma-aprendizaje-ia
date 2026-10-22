"use client";

import { useState } from "react";
import { calificarAbierta } from "@/lib/api";
import type { NivelCalificacion, PreguntaResultado, RespuestaAbierta } from "@/lib/tipos";
import { Alerta, Boton, Icono, Input, Insignia } from "./ui";

const ETIQUETA_NIVEL: Record<NivelCalificacion, string> = { insuficiente: "Insuficiente", basico: "Básico", bueno: "Bueno", excelente: "Excelente" };
const TONO_NIVEL: Record<NivelCalificacion, "error" | "aviso" | "azul" | "exito"> = {
  insuficiente: "error",
  basico: "aviso",
  bueno: "azul",
  excelente: "exito",
};

function FilaRespuesta({ r, preguntaId, onCambio }: { r: RespuestaAbierta; preguntaId: number; onCambio: () => void }) {
  const [nota, setNota] = useState(String(r.nota_final ?? r.sugerida?.puntaje ?? ""));
  const [guardando, setGuardando] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const valor = Number(nota);
  const valida = nota.trim() !== "" && Number.isInteger(valor) && valor >= 0 && valor <= 100;

  async function guardar(n: number) {
    if (r.intento_id === null) return;
    setError(null);
    setGuardando(true);
    try {
      await calificarAbierta(r.intento_id, preguntaId, n);
      onCambio();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setGuardando(false);
    }
  }

  return (
    <li className="flex flex-col gap-3 rounded-lg bg-superficie-2 p-3">
      <p>
        <strong>{r.nombre}:</strong> {r.respuesta || <em>(vacía)</em>}
      </p>

      {r.sugerida ? (
        <div className="rounded-lg border border-borde bg-superficie p-3">
          <p className="flex flex-wrap items-center gap-2 font-bold">
            Sugerida por la IA: {r.sugerida.puntaje}/100
            <Insignia tono={TONO_NIVEL[r.sugerida.nivel]}>{ETIQUETA_NIVEL[r.sugerida.nivel]}</Insignia>
          </p>
          <p className="mt-1 leading-relaxed">{r.sugerida.retroalimentacion}</p>
          {r.sugerida.falto && (
            <p className="mt-1 text-suave">
              <strong>Qué faltó:</strong> {r.sugerida.falto}
            </p>
          )}
        </div>
      ) : (
        <p className="text-suave">Sin calificación sugerida (la IA no estuvo disponible al responder).</p>
      )}

      <div className="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-end">
        <Input
          etiqueta="Nota final (0 a 100)"
          type="number"
          inputMode="numeric"
          min={0}
          max={100}
          value={nota}
          onChange={(e) => setNota(e.target.value)}
          claseCampo="sm:w-44"
        />
        {r.sugerida && (
          <Boton tamano="sm" cargando={guardando} onClick={() => guardar(r.sugerida!.puntaje)} disabled={r.nota_final === r.sugerida.puntaje}>
            <Icono nombre="check" tamano={14} /> Aprobar sugerida
          </Boton>
        )}
        <Boton variante="secundario" tamano="sm" cargando={guardando} disabled={!valida || r.nota_final === valor} onClick={() => guardar(valor)}>
          Guardar nota
        </Boton>
        {r.nota_final !== null && (
          <Insignia tono="exito">
            <Icono nombre="check" tamano={12} /> Nota final: {r.nota_final}
          </Insignia>
        )}
        {r.nota_final === null && <Insignia tono="neutro">Pendiente de aprobación</Insignia>}
      </div>
      {error && <Alerta tipo="error">{error}</Alerta>}
    </li>
  );
}

/** Respuestas a una pregunta abierta con la nota sugerida por la IA y los controles para aprobar o ajustar la nota. */
export default function RevisionAbiertas({ pregunta, onCambio }: { pregunta: PreguntaResultado; onCambio: () => void }) {
  return (
    <ul className="flex flex-col gap-2 border-t border-borde p-4 text-sm">
      {pregunta.respuestas_abiertas.length === 0 && <li className="text-suave">Sin respuestas.</li>}
      {pregunta.respuestas_abiertas.map((r, i) => (
        <FilaRespuesta key={`${r.intento_id}-${i}`} r={r} preguntaId={pregunta.pregunta_id} onCambio={onCambio} />
      ))}
    </ul>
  );
}
