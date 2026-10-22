"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { duplicarCuestionario, editarCuestionario, listarGrupos, publicarCuestionario } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { CuestionarioDetalle, Grupo } from "@/lib/tipos";
import { Alerta, Boton, BotonEnlace, Icono, Input, Insignia, Select, cx } from "./ui";

interface Props {
  cuestionario: CuestionarioDetalle;
  onEditar: () => void;
  onPublicado: (publicado: boolean, estimacionManualMin?: number) => void;
  // Cambios de configuración ya guardados en el servidor (repaso, estimación)
  onCambio: (parche: Partial<CuestionarioDetalle>) => void;
}

const OPCIONES_REPASO = [1, 3, 7, 14];

export default function PanelDocente({ cuestionario: c, onEditar, onPublicado, onCambio }: Props) {
  const { usuario } = useAuth();
  const router = useRouter();
  const esDocente = usuario?.rol === "docente";
  const [ocupado, setOcupado] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copiado, setCopiado] = useState(false);
  const [estimacion, setEstimacion] = useState("");
  const [grupos, setGrupos] = useState<Grupo[]>([]);

  useEffect(() => {
    if (!esDocente) return;
    listarGrupos()
      .then(setGrupos)
      .catch(() => setGrupos([])); // el selector de grupo es opcional
  }, [esDocente]);

  async function cambiarGrupo(valor: string) {
    setError(null);
    const id = valor === "" ? null : Number(valor);
    try {
      await editarCuestionario(c.id, { grupo_id: id });
      const g = grupos.find((x) => x.id === id);
      onCambio({ grupo_id: id, grupo_nombre: g?.nombre ?? null, asignatura_nombre: g?.asignatura ?? null });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    }
  }

  async function alternar() {
    setError(null);
    setOcupado(true);
    try {
      const minutos = Math.round(Number(estimacion));
      const enviar = !c.publicado && c.estimacion_manual_min === null && Number.isFinite(minutos) && minutos >= 1;
      const r = await publicarCuestionario(c.id, !c.publicado, enviar ? minutos : undefined);
      onPublicado(r.publicado, enviar ? minutos : undefined);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setOcupado(false);
    }
  }

  async function cambiarRepaso(valor: string) {
    setError(null);
    const dias = valor === "" ? null : Number(valor);
    try {
      await editarCuestionario(c.id, { repaso_dias: dias });
      onCambio({ repaso_dias: dias });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    }
  }

  async function guardarEstimacion() {
    setError(null);
    const minutos = Math.round(Number(estimacion));
    if (!Number.isFinite(minutos) || minutos < 1) return setError("Escribe un número de minutos mayor que 0.");
    try {
      await editarCuestionario(c.id, { estimacion_manual_min: minutos });
      onCambio({ estimacion_manual_min: minutos });
      setEstimacion("");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    }
  }

  async function crearControl() {
    setError(null);
    setOcupado(true);
    try {
      const copia = await duplicarCuestionario(c.id, "control");
      router.push(`/cuestionarios/${copia.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
      setOcupado(false);
    }
  }

  async function copiar() {
    const enlace = `${window.location.origin}/c/${c.codigo_compartir}`;
    try {
      await navigator.clipboard.writeText(enlace);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2500);
    } catch {
      setError(`No se pudo copiar automáticamente. Copia este enlace: ${enlace}`);
    }
  }

  if (!esDocente) {
    return (
      <Alerta tipo="info">
        Este cuestionario es para tu estudio personal. Solo las cuentas de docente pueden publicarlo, editarlo o ver resultados.
      </Alerta>
    );
  }

  return (
    <section
      aria-label="Panel del docente"
      className="flex min-w-0 flex-col gap-5 rounded-2xl border border-borde border-l-[6px] border-l-cul-naranja bg-superficie p-4 shadow-tarjeta sm:p-6"
    >
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h2 className="flex flex-wrap items-center gap-2 text-lg font-bold">
          <Icono nombre="escudo" /> Panel del docente
          {c.modo === "control" && <Insignia tono="neutro">Grupo control</Insignia>}
        </h2>
        <div className="flex items-center gap-3">
          <Insignia tono={c.publicado ? "exito" : "aviso"}>{c.publicado ? "Publicado" : "Borrador"}</Insignia>
          <button
            type="button"
            role="switch"
            aria-checked={c.publicado}
            aria-label="Publicar cuestionario"
            disabled={ocupado}
            onClick={alternar}
            className="group flex h-11 w-14 items-center justify-center disabled:opacity-50"
          >
            <span
              className={cx(
                "relative h-7 w-12 rounded-full border-2 transition-colors duration-200",
                c.publicado ? "border-exito-solido bg-exito-solido" : "border-borde-fuerte bg-pista",
              )}
            >
              <span
                className={cx(
                  "absolute top-0.5 h-5 w-5 rounded-full bg-white shadow transition-all duration-200",
                  c.publicado ? "left-[24px]" : "left-0.5",
                )}
              />
            </span>
          </button>
        </div>
      </div>

      {c.publicado ? (
        <div className="flex flex-col gap-4 rounded-xl bg-superficie-2 p-4 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-suave">Código para unirse</p>
            <p className="font-mono text-3xl font-extrabold tracking-[0.3em] sm:text-4xl">{c.codigo_compartir}</p>
          </div>
          <Boton variante="secundario" onClick={copiar}>
            <Icono nombre={copiado ? "check" : "copiar"} /> {copiado ? "¡Enlace copiado!" : "Copiar enlace"}
          </Boton>
        </div>
      ) : (
        <div className="flex flex-col gap-3 rounded-xl border border-aviso-borde bg-aviso-fondo p-4 text-aviso-texto">
          <p className="text-sm">
            Este cuestionario es un <strong>borrador</strong>: los estudiantes todavía no pueden unirse. Publícalo para obtener el código y el
            enlace para compartir.
          </p>
          {c.estimacion_manual_min === null && (
            <Input
              etiqueta="¿Cuántos minutos te tomaría crear manualmente este cuestionario? (opcional)"
              type="number"
              min={1}
              max={100000}
              value={estimacion}
              onChange={(e) => setEstimacion(e.target.value)}
              placeholder="Ej.: 45"
              claseCampo="sm:max-w-xs"
            />
          )}
          <Boton onClick={alternar} cargando={ocupado} className="sm:self-start">
            {ocupado ? "Publicando…" : "Publicar y compartir"}
          </Boton>
        </div>
      )}

      <Select
        etiqueta="Grupo (curso) del cuestionario"
        value={c.grupo_id ?? ""}
        onChange={(e) => cambiarGrupo(e.target.value)}
        ayuda={
          grupos.length === 0
            ? "Aún no tienes grupos. Créalos en «Cursos» para que los estudiantes matriculados vean este cuestionario y para medir resultados de aprendizaje."
            : "Los estudiantes matriculados lo ven en «Mis cursos» sin necesitar el código. Cambiar de grupo limpia los RA de las preguntas."
        }
      >
        <option value="">Sin grupo</option>
        {grupos.map((g) => (
          <option key={g.id} value={g.id}>
            {g.asignatura} · {g.nombre} ({g.periodo})
          </option>
        ))}
      </Select>

      <div className="grid gap-4 sm:grid-cols-2">
        <Select
          etiqueta="Repaso diferido (medir retención)"
          value={c.repaso_dias ?? ""}
          onChange={(e) => cambiarRepaso(e.target.value)}
          ayuda="Se programa para quienes terminen su primer intento desde ahora."
        >
          <option value="">Sin repaso</option>
          {OPCIONES_REPASO.map((d) => (
            <option key={d} value={d}>
              A los {d} {d === 1 ? "día" : "días"}
            </option>
          ))}
        </Select>
        <div className="flex flex-col gap-1.5 text-sm">
          <span className="font-semibold">Tiempo con la herramienta</span>
          <span className="text-suave">
            Edición acumulada: {Math.round((c.segundos_edicion ?? 0) / 60)} min
            {c.estimacion_manual_min !== null && ` · Estimación manual: ${c.estimacion_manual_min} min`}
          </span>
          {c.estimacion_manual_min === null && c.publicado && (
            <div className="flex flex-col gap-2 sm:flex-row">
              <Input
                etiqueta="Minutos que tomaría crear el cuestionario manualmente"
                ocultarEtiqueta
                type="number"
                min={1}
                value={estimacion}
                onChange={(e) => setEstimacion(e.target.value)}
                placeholder="Minutos si fuera manual"
                claseCampo="flex-1"
              />
              <Boton variante="secundario" onClick={guardarEstimacion}>
                Guardar
              </Boton>
            </div>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2 min-[480px]:grid-cols-2 lg:flex lg:flex-wrap">
        <Boton onClick={onEditar}>
          <Icono nombre="lapiz" /> Editar
        </Boton>
        <BotonEnlace href={`/cuestionarios/${c.id}/resultados`} variante="secundario">
          <Icono nombre="promedio" /> Ver resultados
        </BotonEnlace>
        {c.modo === "aprendizaje" && (
          <Boton variante="secundario" onClick={crearControl} disabled={ocupado}>
            <Icono nombre="copiar" /> Crear versión grupo control
          </Boton>
        )}
        <BotonEnlace href={`/comparar?a=${c.id}`} variante="secundario">
          <Icono nombre="grupo" /> Comparar grupos
        </BotonEnlace>
      </div>

      {error && <Alerta tipo="error">{error}</Alerta>}
    </section>
  );
}
