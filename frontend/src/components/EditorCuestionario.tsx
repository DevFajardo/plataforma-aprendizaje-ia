"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  agregarPregunta,
  editarCuestionario,
  editarPregunta,
  eliminarPregunta,
  enviarTiempoEdicion,
  reordenarPreguntas,
} from "@/lib/api";
import { Aviso, Boton, ConfirmacionEnLinea, EncabezadoPagina, Icono, Input, Insignia, Select, Tarjeta, Textarea, TituloSeccion } from "./ui";
import type { CuestionarioDetalle, EntradaPregunta, Pregunta, TipoPregunta } from "@/lib/tipos";

/** Borrador de una pregunta en edición (id null = pregunta nueva aún sin guardar). */
interface Borrador {
  clave: string;
  id: number | null;
  tipo: TipoPregunta;
  enunciado: string;
  opciones: string[]; // solo opción múltiple
  indice: number; // índice de la opción correcta (opción múltiple y verdadero/falso)
  modelo: string; // respuesta modelo (abierta)
  explicacion: string;
  marca_tiempo: string;
}

const ETIQUETA_TIPO: Record<TipoPregunta, string> = {
  opcion_multiple: "Opción múltiple",
  verdadero_falso: "Verdadero / Falso",
  abierta: "Abierta",
};

function aBorrador(p: Pregunta): Borrador {
  const opciones = p.tipo === "opcion_multiple" && p.opciones.length >= 2 ? [...p.opciones] : ["", ""];
  let indice = 0;
  if (p.tipo === "opcion_multiple") indice = Math.max(0, p.opciones.indexOf(p.respuesta_correcta ?? ""));
  if (p.tipo === "verdadero_falso") indice = p.respuesta_correcta === "Falso" ? 1 : 0;
  return {
    clave: `p${p.id}`,
    id: p.id,
    tipo: p.tipo,
    enunciado: p.enunciado,
    opciones,
    indice,
    modelo: p.tipo === "abierta" ? (p.respuesta_correcta ?? "") : "",
    explicacion: p.explicacion ?? "",
    marca_tiempo: p.marca_tiempo,
  };
}

function aEntrada(b: Borrador): EntradaPregunta {
  const base = { enunciado: b.enunciado.trim(), explicacion: b.explicacion.trim(), marca_tiempo: b.marca_tiempo.trim() };
  if (b.tipo === "opcion_multiple") {
    const opciones = b.opciones.map((o) => o.trim());
    return { ...base, tipo: b.tipo, opciones, respuesta_correcta: opciones[b.indice] ?? "" };
  }
  if (b.tipo === "verdadero_falso") {
    return { ...base, tipo: b.tipo, opciones: ["Verdadero", "Falso"], respuesta_correcta: b.indice === 1 ? "Falso" : "Verdadero" };
  }
  return { ...base, tipo: b.tipo, opciones: [], respuesta_correcta: b.modelo.trim() };
}

/** Devuelve un mensaje si el borrador no es válido (el servidor valida de nuevo). */
function validar(b: Borrador, numero: number): string | null {
  const e = aEntrada(b);
  if (!e.enunciado) return `Pregunta ${numero}: escribe el enunciado.`;
  if (b.tipo === "opcion_multiple") {
    if (e.opciones.length < 2 || e.opciones.length > 6) return `Pregunta ${numero}: usa entre 2 y 6 opciones.`;
    if (e.opciones.some((o) => !o)) return `Pregunta ${numero}: hay opciones vacías.`;
    if (new Set(e.opciones).size !== e.opciones.length) return `Pregunta ${numero}: hay opciones repetidas.`;
  }
  if (!e.respuesta_correcta) return `Pregunta ${numero}: falta la respuesta ${b.tipo === "abierta" ? "modelo" : "correcta"}.`;
  if (e.marca_tiempo && !/^(\d{1,2}:)?\d{1,2}:\d{2}$/.test(e.marca_tiempo))
    return `Pregunta ${numero}: la marca de tiempo debe tener el formato mm:ss.`;
  return null;
}


interface Props {
  cuestionario: CuestionarioDetalle;
  /** Se llama al terminar (guardado correcto o cancelación). */
  onTerminar: (huboCambios: boolean) => void;
}

export default function EditorCuestionario({ cuestionario: c, onTerminar }: Props) {
  const contador = useRef(0);

  // Tiempo activo de edición (solo con la pestaña visible), que respalda la medición de ahorro de tiempo
  const segundosActivos = useRef(0);
  const volcarTiempo = useCallback(
    (keepalive = false) => {
      const s = Math.min(segundosActivos.current, 4 * 3600);
      if (s < 1) return;
      segundosActivos.current = 0;
      enviarTiempoEdicion(c.id, s, keepalive).catch(() => {
        /* la medición no debe interrumpir la edición */
      });
    },
    [c.id],
  );
  useEffect(() => {
    const reloj = setInterval(() => {
      if (document.visibilityState === "visible") segundosActivos.current += 1;
      if (segundosActivos.current >= 300) volcarTiempo(); // respaldo cada 5 min de edición activa
    }, 1000);
    const alCerrar = () => volcarTiempo(true);
    window.addEventListener("pagehide", alCerrar);
    return () => {
      clearInterval(reloj);
      window.removeEventListener("pagehide", alCerrar);
      volcarTiempo(true); // al salir del editor
    };
  }, [volcarTiempo]);

  const [titulo, setTitulo] = useState(c.titulo);
  const [resumen, setResumen] = useState(c.resumen);
  const [ideas, setIdeas] = useState<string[]>(c.ideas_clave);
  const [preguntas, setPreguntas] = useState<Borrador[]>(() => c.preguntas.map(aBorrador));
  const [eliminados, setEliminados] = useState<number[]>([]);
  const [porEliminar, setPorEliminar] = useState<string | null>(null); // clave con confirmación abierta
  const [guardando, setGuardando] = useState(false);
  const [mensaje, setMensaje] = useState<{ tipo: "ok" | "error"; texto: string } | null>(null);

  function cambiar(clave: string, parche: Partial<Borrador>) {
    setPreguntas((l) => l.map((p) => (p.clave === clave ? { ...p, ...parche } : p)));
  }

  function mover(i: number, delta: number) {
    setPreguntas((l) => {
      const j = i + delta;
      if (j < 0 || j >= l.length) return l;
      const copia = [...l];
      [copia[i], copia[j]] = [copia[j], copia[i]];
      return copia;
    });
  }

  function confirmarEliminar(b: Borrador) {
    if (b.id !== null) setEliminados((l) => [...l, b.id as number]);
    setPreguntas((l) => l.filter((p) => p.clave !== b.clave));
    setPorEliminar(null);
  }

  function nuevaPregunta() {
    contador.current += 1;
    setPreguntas((l) => [
      ...l,
      {
        clave: `n${contador.current}`,
        id: null,
        tipo: "opcion_multiple",
        enunciado: "",
        opciones: ["", "", "", ""],
        indice: 0,
        modelo: "",
        explicacion: "",
        marca_tiempo: "",
      },
    ]);
  }

  async function guardar() {
    setMensaje(null);
    if (!titulo.trim()) return setMensaje({ tipo: "error", texto: "El título no puede estar vacío." });
    if (!resumen.trim()) return setMensaje({ tipo: "error", texto: "El resumen no puede estar vacío." });
    for (let i = 0; i < preguntas.length; i++) {
      const problema = validar(preguntas[i], i + 1);
      if (problema) return setMensaje({ tipo: "error", texto: problema });
    }
    setGuardando(true);
    try {
      await editarCuestionario(c.id, {
        titulo: titulo.trim(),
        resumen: resumen.trim(),
        ideas_clave: ideas.map((x) => x.trim()).filter(Boolean),
      });
      for (const id of eliminados) await eliminarPregunta(id);
      setEliminados([]);
      const ids: number[] = [];
      for (const b of preguntas) {
        if (b.id !== null) {
          await editarPregunta(b.id, aEntrada(b));
          ids.push(b.id);
        } else {
          const creada = await agregarPregunta(c.id, aEntrada(b));
          // La pregunta ya existe en el servidor: si algo falla después no se duplica al reintentar
          cambiar(b.clave, { id: creada.id });
          ids.push(creada.id);
        }
      }
      if (ids.length > 1) await reordenarPreguntas(c.id, ids);
      volcarTiempo();
      setMensaje({ tipo: "ok", texto: "Cambios guardados." });
      setTimeout(() => onTerminar(true), 700);
    } catch (e) {
      setMensaje({ tipo: "error", texto: e instanceof Error ? e.message : "Error desconocido" });
      setGuardando(false);
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <EncabezadoPagina
        titulo="Editando cuestionario"
        descripcion="Ajusta el título, el resumen, las ideas clave y las preguntas. Los cambios se aplican al guardar."
        acciones={
          <Boton variante="secundario" disabled={guardando} onClick={() => onTerminar(false)}>
            Cancelar
          </Boton>
        }
      />

      <Tarjeta as="section" className="flex flex-col gap-4">
        <TituloSeccion>Información general</TituloSeccion>
        <Input etiqueta="Título" value={titulo} onChange={(e) => setTitulo(e.target.value)} maxLength={300} />
        <Textarea etiqueta="Resumen" value={resumen} onChange={(e) => setResumen(e.target.value)} rows={6} />
        <fieldset className="flex flex-col gap-2">
          <legend className="mb-1 text-sm font-semibold">Ideas clave</legend>
          {ideas.map((idea, i) => (
            <div key={i} className="flex items-start gap-2">
              <Input
                etiqueta={`Idea clave ${i + 1}`}
                ocultarEtiqueta
                value={idea}
                onChange={(e) => setIdeas((l) => l.map((x, k) => (k === i ? e.target.value : x)))}
                claseCampo="flex-1"
              />
              <Boton variante="secundario" aria-label={`Quitar idea clave ${i + 1}`} onClick={() => setIdeas((l) => l.filter((_, k) => k !== i))} className="!px-3">
                <Icono nombre="basura" />
                <span className="sr-only">Quitar</span>
              </Boton>
            </div>
          ))}
          <Boton variante="secundario" onClick={() => setIdeas((l) => [...l, ""])} className="self-start">
            <Icono nombre="mas" /> Añadir idea
          </Boton>
        </fieldset>
      </Tarjeta>

      <section className="flex flex-col gap-4">
        <TituloSeccion>Preguntas ({preguntas.length})</TituloSeccion>
        {preguntas.map((b, i) => (
          <Tarjeta as="article" key={b.clave} className="flex flex-col gap-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h3 className="flex items-center gap-2 font-bold">
                <span className="flex h-8 min-w-8 items-center justify-center rounded-full bg-primario px-2 text-sm text-sobre-primario">{i + 1}</span>
                Pregunta {i + 1}
                {b.id === null && <Insignia tono="azul">nueva</Insignia>}
              </h3>
              <div className="flex gap-2">
                <Boton variante="secundario" disabled={i === 0} onClick={() => mover(i, -1)} aria-label="Subir pregunta" className="!px-3">
                  <Icono nombre="subir_flecha" />
                  <span className="sr-only">Subir</span>
                </Boton>
                <Boton variante="secundario" disabled={i === preguntas.length - 1} onClick={() => mover(i, 1)} aria-label="Bajar pregunta" className="!px-3">
                  <Icono nombre="bajar_flecha" />
                  <span className="sr-only">Bajar</span>
                </Boton>
                <Boton variante="peligroSuave" onClick={() => setPorEliminar(b.clave)} aria-label="Eliminar pregunta" className="!px-3 sm:!px-4">
                  <Icono nombre="basura" />
                  <span className="hidden sm:inline">Eliminar</span>
                </Boton>
              </div>
            </div>

            {porEliminar === b.clave && (
              <ConfirmacionEnLinea
                mensaje="¿Eliminar esta pregunta? Se quitará al guardar los cambios."
                textoConfirmar="Sí, eliminar"
                onConfirmar={() => confirmarEliminar(b)}
                onCancelar={() => setPorEliminar(null)}
              />
            )}

            <Select
              etiqueta="Tipo"
              value={b.tipo}
              onChange={(e) => cambiar(b.clave, { tipo: e.target.value as TipoPregunta, indice: 0 })}
            >
              {(Object.keys(ETIQUETA_TIPO) as TipoPregunta[]).map((t) => (
                <option key={t} value={t}>
                  {ETIQUETA_TIPO[t]}
                </option>
              ))}
            </Select>

            <Textarea etiqueta="Enunciado" value={b.enunciado} onChange={(e) => cambiar(b.clave, { enunciado: e.target.value })} rows={2} />

            {b.tipo === "opcion_multiple" && (
              <fieldset className="flex flex-col gap-2">
                <legend className="mb-1 text-sm font-semibold">Opciones (marca la correcta)</legend>
                {b.opciones.map((op, k) => (
                  <div key={k} className="flex items-start gap-2">
                    <label className="flex h-11 w-9 shrink-0 cursor-pointer items-center justify-center">
                      <input
                        type="radio"
                        name={`correcta-${b.clave}`}
                        checked={b.indice === k}
                        onChange={() => cambiar(b.clave, { indice: k })}
                        aria-label={`Marcar la opción ${k + 1} como correcta`}
                        className="h-5 w-5 cursor-pointer accent-primario"
                      />
                    </label>
                    <Input
                      etiqueta={`Opción ${k + 1}`}
                      ocultarEtiqueta
                      value={op}
                      onChange={(e) => cambiar(b.clave, { opciones: b.opciones.map((x, m) => (m === k ? e.target.value : x)) })}
                      claseCampo="flex-1"
                    />
                    <Boton
                      variante="secundario"
                      disabled={b.opciones.length <= 2}
                      aria-label={`Quitar la opción ${k + 1}`}
                      onClick={() =>
                        cambiar(b.clave, {
                          opciones: b.opciones.filter((_, m) => m !== k),
                          indice: b.indice === k ? 0 : b.indice > k ? b.indice - 1 : b.indice,
                        })
                      }
                      className="!px-3"
                    >
                      <Icono nombre="x" />
                      <span className="sr-only">Quitar</span>
                    </Boton>
                  </div>
                ))}
                <Boton variante="secundario" disabled={b.opciones.length >= 6} onClick={() => cambiar(b.clave, { opciones: [...b.opciones, ""] })} className="self-start">
                  <Icono nombre="mas" /> Añadir opción
                </Boton>
              </fieldset>
            )}

            {b.tipo === "verdadero_falso" && (
              <fieldset className="flex flex-col gap-2">
                <legend className="mb-1 text-sm font-semibold">Respuesta correcta</legend>
                <div className="flex flex-wrap gap-3">
                  {["Verdadero", "Falso"].map((txt, k) => (
                    <label
                      key={txt}
                      className={
                        "flex min-h-11 cursor-pointer items-center gap-2 rounded-lg border-2 px-4 font-semibold transition " +
                        (b.indice === k ? "border-primario bg-info-fondo" : "border-borde hover:bg-superficie-2")
                      }
                    >
                      <input
                        type="radio"
                        name={`correcta-${b.clave}`}
                        checked={b.indice === k}
                        onChange={() => cambiar(b.clave, { indice: k })}
                        className="h-5 w-5 accent-primario"
                      />
                      {txt}
                    </label>
                  ))}
                </div>
              </fieldset>
            )}

            {b.tipo === "abierta" && (
              <Textarea etiqueta="Respuesta modelo" value={b.modelo} onChange={(e) => cambiar(b.clave, { modelo: e.target.value })} rows={3} />
            )}

            <Textarea etiqueta="Explicación" value={b.explicacion} onChange={(e) => cambiar(b.clave, { explicacion: e.target.value })} rows={2} />

            <Input
              etiqueta="Marca de tiempo (mm:ss)"
              value={b.marca_tiempo}
              onChange={(e) => cambiar(b.clave, { marca_tiempo: e.target.value })}
              placeholder="01:30"
              claseCampo="sm:w-52"
            />
          </Tarjeta>
        ))}

        <Boton variante="secundario" onClick={nuevaPregunta} className="self-start">
          <Icono nombre="mas" /> Añadir pregunta
        </Boton>
      </section>

      <div className="sticky bottom-0 z-20 -mx-4 flex flex-col gap-3 border-t border-borde bg-superficie/95 px-4 py-3 shadow-[0_-4px_12px_rgb(0_0_0/0.06)] backdrop-blur sm:-mx-6 sm:flex-row sm:items-center sm:px-6 lg:-mx-8 lg:px-8">
        <Boton tamano="lg" cargando={guardando} onClick={guardar}>
          {guardando ? "Guardando…" : "Guardar cambios"}
        </Boton>
        {mensaje && <Aviso mensaje={mensaje} />}
      </div>
    </div>
  );
}
