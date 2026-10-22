"use client";

import { useCallback, useEffect, useState } from "react";
import AlertasTempranas from "@/components/AlertasTempranas";
import {
  Alerta,
  Boton,
  ConfirmacionEnLinea,
  EncabezadoPagina,
  EsqueletoPagina,
  EstadoVacio,
  Icono,
  Input,
  Insignia,
  Pagina,
  Select,
  Tarjeta,
  TituloSeccion,
} from "@/components/ui";
import {
  catalogoAsignaturas,
  crearGrupo,
  editarGrupo,
  eliminarGrupo,
  listarGrupos,
  listarMatriculados,
  quitarMatriculado,
  renovarCodigoGrupo,
} from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import { formatearFecha } from "@/lib/fechas";
import type { Asignatura, Grupo, Matriculado } from "@/lib/tipos";

/** Periodo académico por defecto: año y semestre en curso (p. ej. 2026-2). */
function periodoActual() {
  const f = new Date();
  return `${f.getFullYear()}-${f.getMonth() < 6 ? 1 : 2}`;
}

function TarjetaGrupo({ g, esDocente, alCambiar, alError }: { g: Grupo; esDocente: boolean; alCambiar: () => void; alError: (m: string) => void }) {
  const [matriculados, setMatriculados] = useState<Matriculado[] | null>(null);
  const [verMatriculados, setVerMatriculados] = useState(false);
  const [editando, setEditando] = useState(false);
  const [nombre, setNombre] = useState(g.nombre);
  const [periodo, setPeriodo] = useState(g.periodo);
  const [eliminando, setEliminando] = useState(false);
  const [copiado, setCopiado] = useState(false);

  const falla = (e: unknown) => alError(e instanceof Error ? e.message : "Error desconocido");

  async function alternarMatriculados() {
    if (!verMatriculados && matriculados === null) {
      try {
        setMatriculados(await listarMatriculados(g.id));
      } catch (e) {
        return falla(e);
      }
    }
    setVerMatriculados(!verMatriculados);
  }

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    try {
      await editarGrupo(g.id, { nombre, periodo });
      setEditando(false);
      alCambiar();
    } catch (err) {
      falla(err);
    }
  }

  async function quitar(m: Matriculado) {
    try {
      await quitarMatriculado(g.id, m.estudiante_id);
      setMatriculados((l) => l?.filter((x) => x.estudiante_id !== m.estudiante_id) ?? null);
      alCambiar();
    } catch (err) {
      falla(err);
    }
  }

  async function copiar() {
    try {
      await navigator.clipboard.writeText(g.codigo_ingreso);
      setCopiado(true);
      setTimeout(() => setCopiado(false), 2000);
    } catch {
      alError(`No se pudo copiar. El código es ${g.codigo_ingreso}.`);
    }
  }

  return (
    <Tarjeta as="article" className="flex flex-col gap-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <TituloSeccion nivel={3}>{g.asignatura}</TituloSeccion>
          <p className="mt-1 text-sm text-suave">
            {g.programa}
            {!esDocente && ` · Docente: ${g.docente}`}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <Insignia tono="azul">{g.nombre}</Insignia>
          <Insignia tono="neutro">{g.periodo}</Insignia>
        </div>
      </div>

      <div className="flex flex-col gap-3 rounded-xl bg-superficie-2 p-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-xs font-semibold uppercase tracking-wide text-suave">Código de ingreso</p>
          <p className="font-mono text-3xl font-extrabold tracking-[0.3em]">{g.codigo_ingreso}</p>
        </div>
        <div className="text-sm text-suave">
          <p>
            <strong className="text-texto">{g.num_matriculados}</strong> matriculados
          </p>
          <p>
            <strong className="text-texto">{g.num_cuestionarios}</strong> cuestionarios asignados
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-2 min-[480px]:grid-cols-2 lg:flex lg:flex-wrap">
        <Boton variante="secundario" onClick={alternarMatriculados} aria-expanded={verMatriculados}>
          <Icono nombre="grupo" /> {verMatriculados ? "Ocultar matriculados" : "Ver matriculados"}
        </Boton>
        <Boton variante="secundario" onClick={copiar}>
          <Icono nombre={copiado ? "check" : "copiar"} /> {copiado ? "¡Copiado!" : "Copiar código"}
        </Boton>
        {esDocente && (
          <>
            <Boton variante="secundario" onClick={() => setEditando(!editando)}>
              <Icono nombre="lapiz" /> Editar
            </Boton>
            <Boton
              variante="secundario"
              onClick={async () => {
                try {
                  await renovarCodigoGrupo(g.id);
                  alCambiar();
                } catch (e) {
                  falla(e);
                }
              }}
            >
              <Icono nombre="repetir" /> Nuevo código
            </Boton>
            <Boton variante="peligroSuave" onClick={() => setEliminando(true)}>
              <Icono nombre="basura" /> Eliminar
            </Boton>
          </>
        )}
      </div>

      {editando && (
        <form onSubmit={guardar} className="flex flex-col gap-3 rounded-xl border border-borde p-4 sm:flex-row sm:items-end">
          <Input etiqueta="Nombre del grupo" value={nombre} onChange={(e) => setNombre(e.target.value)} required maxLength={100} claseCampo="flex-1" />
          <Input etiqueta="Periodo" value={periodo} onChange={(e) => setPeriodo(e.target.value)} required placeholder="2026-2" claseCampo="sm:w-36" />
          <Boton type="submit">Guardar</Boton>
        </form>
      )}

      {eliminando && (
        <ConfirmacionEnLinea
          mensaje="¿Eliminar el grupo? Se quitan las matrículas y los cuestionarios quedan sin grupo (no se borran)."
          textoConfirmar="Sí, eliminar grupo"
          onConfirmar={async () => {
            try {
              await eliminarGrupo(g.id);
              alCambiar();
            } catch (e) {
              falla(e);
            }
          }}
          onCancelar={() => setEliminando(false)}
        />
      )}

      {verMatriculados && (
        <div className="rounded-xl border border-borde">
          {matriculados?.length === 0 ? (
            <p className="p-4 text-sm text-suave">Aún no hay estudiantes matriculados. Comparte el código de ingreso.</p>
          ) : (
            <ul className="divide-y divide-borde">
              {matriculados?.map((m) => (
                <li key={m.estudiante_id} className="flex flex-wrap items-center justify-between gap-2 px-4 py-2.5 text-sm">
                  <span className="min-w-0">
                    <span className="block break-words font-semibold">{m.nombre}</span>
                    <span className="block break-all text-xs text-suave">
                      {m.email} · desde {formatearFecha(m.desde, "corta")}
                    </span>
                  </span>
                  {esDocente && (
                    <Boton variante="fantasma" tamano="sm" onClick={() => quitar(m)}>
                      Quitar
                    </Boton>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
    </Tarjeta>
  );
}

export default function CursosPage() {
  const { usuario, cargando } = useRequiereLogin();
  const [grupos, setGrupos] = useState<Grupo[] | null>(null);
  const [asignaturas, setAsignaturas] = useState<Asignatura[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [asignaturaId, setAsignaturaId] = useState("");
  const [periodo, setPeriodo] = useState("");
  const [nombre, setNombre] = useState("");
  const [creando, setCreando] = useState(false);

  const permitido = usuario?.rol === "docente" || usuario?.rol === "admin";
  const esDocente = usuario?.rol === "docente";

  const cargar = useCallback(() => {
    listarGrupos()
      .then(setGrupos)
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
  }, []);

  // La fecha actual no puede leerse al renderizar (Cache Components): se propone el periodo tras montar
  useEffect(() => {
    const propuesta = periodoActual();
    setPeriodo((p) => p || propuesta); // eslint-disable-line react-hooks/set-state-in-effect
  }, []);

  useEffect(() => {
    if (!permitido) return;
    cargar();
    catalogoAsignaturas()
      .then(setAsignaturas)
      .catch(() => setAsignaturas([]));
  }, [permitido, cargar]);

  async function crear(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setCreando(true);
    try {
      await crearGrupo(Number(asignaturaId), periodo.trim(), nombre.trim());
      setNombre("");
      cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setCreando(false);
    }
  }

  if (cargando || !usuario) {
    return (
      <Pagina>
        <EsqueletoPagina />
      </Pagina>
    );
  }
  if (!permitido) {
    return (
      <Pagina ancho="md">
        <Alerta tipo="info">Esta sección es para docentes. Los estudiantes consultan sus cursos en «Mis cursos».</Alerta>
      </Pagina>
    );
  }

  return (
    <Pagina ancho="lg">
      <EncabezadoPagina
        titulo="Cursos"
        descripcion={esDocente ? "Crea tus grupos por asignatura y periodo, comparte el código de ingreso y consulta a los matriculados." : "Todos los grupos de la institución."}
      />

      <div className="flex flex-col gap-8">
        {esDocente && (
          <Tarjeta as="section" aria-label="Crear un grupo">
            <TituloSeccion nivel={3}>Nuevo grupo</TituloSeccion>
            {asignaturas.length === 0 ? (
              <p className="mt-3 text-sm text-suave">
                Todavía no hay asignaturas registradas. Pide al administrador que cree la estructura académica (o ejecute el script de datos semilla).
              </p>
            ) : (
              <form onSubmit={crear} className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-[2fr_1fr_1.5fr_auto] lg:items-end">
                <Select etiqueta="Asignatura" value={asignaturaId} onChange={(e) => setAsignaturaId(e.target.value)} required>
                  <option value="">Selecciona…</option>
                  {asignaturas.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.codigo} · {a.nombre} ({a.programa})
                    </option>
                  ))}
                </Select>
                <Input etiqueta="Periodo" value={periodo} onChange={(e) => setPeriodo(e.target.value)} required placeholder="2026-2" ayuda="Formato AAAA-S" />
                <Input etiqueta="Nombre del grupo" value={nombre} onChange={(e) => setNombre(e.target.value)} required maxLength={100} placeholder="Grupo A" />
                <Boton type="submit" cargando={creando} disabled={!asignaturaId || !nombre.trim()}>
                  <Icono nombre="mas" /> Crear grupo
                </Boton>
              </form>
            )}
          </Tarjeta>
        )}

        {error && <Alerta tipo="error">{error}</Alerta>}
        {grupos === null && !error && <EsqueletoPagina tarjetas={2} />}
        {grupos?.length === 0 && (
          <EstadoVacio icono="grupo" titulo="Aún no tienes grupos">
            Crea un grupo para obtener el código de ingreso que compartirás con tus estudiantes.
          </EstadoVacio>
        )}
        <div className="flex flex-col gap-6">
          {grupos?.map((g) => (
            <TarjetaGrupo key={g.id} g={g} esDocente={esDocente} alCambiar={cargar} alError={setError} />
          ))}
        </div>

        <AlertasTempranas />
      </div>
    </Pagina>
  );
}
