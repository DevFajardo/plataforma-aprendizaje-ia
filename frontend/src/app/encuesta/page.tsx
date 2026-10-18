"use client";

import { useEffect, useState } from "react";
import { Alerta, BarraPorcentaje, Boton, BotonEnlace, EncabezadoPagina, EsqueletoPagina, Pagina, Tarjeta, Textarea } from "@/components/ui";
import { enviarSus, obtenerMiSus } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import type { RespuestaSus } from "@/lib/tipos";

// Ítems oficiales de la escala SUS (versión estándar en español)
const ITEMS = [
  "Creo que me gustaría usar este sistema con frecuencia.",
  "Encontré el sistema innecesariamente complejo.",
  "Pensé que el sistema era fácil de usar.",
  "Creo que necesitaría el apoyo de un técnico para poder usar este sistema.",
  "Encontré que las diversas funciones de este sistema estaban bien integradas.",
  "Pensé que había demasiada inconsistencia en este sistema.",
  "Imagino que la mayoría de las personas aprenderían a usar este sistema muy rápidamente.",
  "Encontré el sistema muy engorroso de usar.",
  "Me sentí muy seguro/a usando el sistema.",
  "Necesité aprender muchas cosas antes de poder empezar a usar este sistema.",
];

export default function EncuestaPage() {
  const { usuario, cargando } = useRequiereLogin();
  const [respuestas, setRespuestas] = useState<(number | null)[]>(Array(10).fill(null));
  const [comentario, setComentario] = useState("");
  const [previa, setPrevia] = useState<RespuestaSus | null>(null);
  const [resultado, setResultado] = useState<RespuestaSus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);

  useEffect(() => {
    if (!usuario) return;
    obtenerMiSus()
      .then((r) => {
        if (!r) return;
        setPrevia(r);
        setRespuestas(r.respuestas);
        setComentario(r.comentario ?? "");
      })
      .catch(() => {
        /* sin respuesta previa o error de red: el formulario sigue disponible */
      });
  }, [usuario]);

  const completas = respuestas.every((r) => r !== null);
  const respondidas = respuestas.filter((r) => r !== null).length;

  async function enviar(e: React.FormEvent) {
    e.preventDefault();
    if (!completas) {
      setError("Responde las 10 afirmaciones antes de enviar.");
      return;
    }
    setError(null);
    setEnviando(true);
    try {
      setResultado(await enviarSus(respuestas as number[], comentario));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setEnviando(false);
    }
  }

  if (cargando || !usuario) {
    return (
      <Pagina ancho="md">
        <EsqueletoPagina />
      </Pagina>
    );
  }

  if (resultado) {
    return (
      <Pagina ancho="md">
        <EncabezadoPagina titulo="¡Gracias por tu respuesta!" />
        <Tarjeta className="border-t-4 border-t-cul-naranja">
          <p className="text-sm font-semibold text-suave">Tu puntaje de usabilidad (SUS)</p>
          <p className="text-6xl font-extrabold">{resultado.puntaje}</p>
          <p className="mt-1 text-lg">
            Interpretación: <strong>{resultado.interpretacion}</strong>
          </p>
          <p className="mt-3 text-sm text-suave">
            La escala va de 0 a 100: menos de 51 es pobre, de 51 a 68 aceptable bajo, de 68 a 80,3 bueno y más de 80,3 excelente. Puedes volver a
            responder cuando quieras; se actualizará tu respuesta.
          </p>
        </Tarjeta>
        <BotonEnlace href="/panel" tamano="lg" className="mt-6">
          Volver al panel
        </BotonEnlace>
      </Pagina>
    );
  }

  return (
    <Pagina ancho="md">
      <EncabezadoPagina
        titulo="Encuesta de usabilidad"
        descripcion="Indica qué tan de acuerdo estás con cada afirmación sobre esta plataforma (1 = totalmente en desacuerdo, 5 = totalmente de acuerdo). Es anónima en los resultados que ve el docente."
      />
      {previa && (
        <Alerta tipo="info" className="mb-5">
          Ya respondiste esta encuesta (puntaje {previa.puntaje}). Si la envías de nuevo, se actualizará tu respuesta.
        </Alerta>
      )}

      <form onSubmit={enviar} className="flex flex-col gap-4">
        {ITEMS.map((texto, i) => (
          <Tarjeta as="fieldset" key={i} className="!p-4">
            <legend className="float-left mb-3 w-full text-base font-semibold leading-snug">
              {i + 1}. {texto}
            </legend>
            <div className="clear-both grid grid-cols-5 gap-2">
              {[1, 2, 3, 4, 5].map((v) => (
                <label
                  key={v}
                  className="flex min-h-12 cursor-pointer items-center justify-center rounded-xl border-2 border-borde text-lg font-bold transition duration-150 hover:border-anillo hover:bg-superficie-2 has-[:checked]:border-primario has-[:checked]:bg-primario has-[:checked]:text-sobre-primario has-[:focus-visible]:outline has-[:focus-visible]:outline-[3px] has-[:focus-visible]:outline-offset-2 has-[:focus-visible]:outline-anillo"
                >
                  <input
                    type="radio"
                    name={`item-${i}`}
                    value={v}
                    checked={respuestas[i] === v}
                    onChange={() => setRespuestas((r) => r.map((x, j) => (j === i ? v : x)))}
                    className="sr-only"
                    aria-label={`${v}${v === 1 ? " (totalmente en desacuerdo)" : v === 5 ? " (totalmente de acuerdo)" : ""}`}
                  />
                  <span aria-hidden="true">{v}</span>
                </label>
              ))}
            </div>
            <div className="mt-2 flex justify-between gap-4 text-xs text-suave">
              <span>Totalmente en desacuerdo</span>
              <span className="text-right">Totalmente de acuerdo</span>
            </div>
          </Tarjeta>
        ))}

        <Tarjeta>
          <Textarea
            etiqueta="Comentario (opcional)"
            value={comentario}
            onChange={(e) => setComentario(e.target.value)}
            maxLength={2000}
            rows={4}
            placeholder="¿Qué mejorarías? ¿Qué te gustó?"
          />
        </Tarjeta>

        {error && <Alerta tipo="error">{error}</Alerta>}

        <div className="sticky bottom-0 z-10 -mx-4 flex flex-col gap-3 border-t border-borde bg-superficie/95 px-4 py-3 backdrop-blur sm:-mx-6 sm:flex-row sm:items-center sm:px-6">
          <Boton type="submit" tamano="lg" cargando={enviando}>
            {enviando ? "Enviando…" : previa ? "Actualizar respuesta" : "Enviar respuesta"}
          </Boton>
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <BarraPorcentaje valor={respondidas} max={10} etiqueta="Afirmaciones respondidas" alto="sm" className="max-w-40" />
            <span className="text-sm text-suave">{respondidas}/10 respondidas</span>
          </div>
        </div>
      </form>
    </Pagina>
  );
}
