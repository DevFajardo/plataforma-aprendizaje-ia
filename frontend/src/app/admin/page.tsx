"use client";

import { useCallback, useEffect, useState } from "react";
import {
  Alerta,
  Boton,
  Casilla,
  ConfirmacionEnLinea,
  EncabezadoPagina,
  EsqueletoPagina,
  EstadoVacio,
  Icono,
  Input,
  Insignia,
  Pagina,
  Pestanas,
  Select,
  Tarjeta,
  Textarea,
  TituloSeccion,
} from "@/components/ui";
import * as api from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import type { Asignatura, Facultad, Programa, ResultadoAprendizaje, UsuarioAdmin } from "@/lib/tipos";
import { plural } from "@/lib/formato";

const mensajeError = (e: unknown) => (e instanceof Error ? e.message : "Error desconocido");

/** Carga una lista y permite recargarla; los errores se reportan al contenedor. */
function useLista<T>(cargador: () => Promise<T[]>, alError: (m: string | null) => void) {
  const [lista, setLista] = useState<T[] | null>(null);
  const recargar = useCallback(() => {
    cargador()
      .then((l) => {
        setLista(l);
        alError(null);
      })
      .catch((e) => alError(mensajeError(e)));
  }, [cargador, alError]);
  useEffect(recargar, [recargar]);
  return [lista, recargar] as const;
}

interface PropsTab {
  alError: (m: string | null) => void;
}

/** Fila genérica de un registro con acciones de editar y eliminar (eliminar pide confirmación). */
function Fila({
  titulo,
  detalle,
  etiquetas,
  onEditar,
  onEliminar,
  textoEliminar,
  children,
}: {
  titulo: string;
  detalle?: string;
  etiquetas?: React.ReactNode;
  onEditar?: () => void;
  onEliminar: () => Promise<void>;
  textoEliminar: string;
  children?: React.ReactNode;
}) {
  const [confirmando, setConfirmando] = useState(false);
  return (
    <li className="flex min-w-0 flex-col gap-3 rounded-xl border border-borde bg-superficie p-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="break-words font-semibold">{titulo}</p>
          {detalle && <p className="break-words text-sm text-suave">{detalle}</p>}
          {etiquetas && <div className="mt-2 flex flex-wrap gap-1.5">{etiquetas}</div>}
        </div>
        <div className="flex gap-2">
          {onEditar && (
            <Boton variante="secundario" tamano="sm" onClick={onEditar}>
              <Icono nombre="lapiz" tamano={16} /> Editar
            </Boton>
          )}
          <Boton variante="peligroSuave" tamano="sm" onClick={() => setConfirmando(true)} aria-label={`Eliminar ${titulo}`}>
            <Icono nombre="basura" tamano={16} /> <span className="hidden sm:inline">Eliminar</span>
          </Boton>
        </div>
      </div>
      {children}
      {confirmando && (
        <ConfirmacionEnLinea
          mensaje={textoEliminar}
          textoConfirmar="Sí, eliminar"
          onConfirmar={async () => {
            await onEliminar();
            setConfirmando(false);
          }}
          onCancelar={() => setConfirmando(false)}
        />
      )}
    </li>
  );
}

function VacioLista({ cargando, vacio }: { cargando: boolean; vacio: string }) {
  return cargando ? <EsqueletoPagina tarjetas={1} /> : <EstadoVacio icono="libro" titulo={vacio} />;
}

// ---------- Facultades ----------

function TabFacultades({ alError }: PropsTab) {
  const [lista, recargar] = useLista<Facultad>(api.adminFacultades, alError);
  const [nombre, setNombre] = useState("");
  const [editando, setEditando] = useState<Facultad | null>(null);

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    try {
      if (editando) await api.adminEditarFacultad(editando.id, nombre.trim());
      else await api.adminCrearFacultad(nombre.trim());
      setNombre("");
      setEditando(null);
      recargar();
    } catch (err) {
      alError(mensajeError(err));
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Tarjeta>
        <form onSubmit={guardar} className="flex flex-col gap-4 sm:flex-row sm:items-end">
          <Input etiqueta={editando ? "Nuevo nombre de la facultad" : "Nueva facultad"} value={nombre} onChange={(e) => setNombre(e.target.value)} required minLength={2} maxLength={150} claseCampo="flex-1" />
          <Boton type="submit">{editando ? "Guardar cambios" : "Agregar facultad"}</Boton>
          {editando && (
            <Boton variante="secundario" onClick={() => { setEditando(null); setNombre(""); }}>
              Cancelar
            </Boton>
          )}
        </form>
      </Tarjeta>
      {lista?.length ? (
        <ul className="flex flex-col gap-3">
          {lista.map((f) => (
            <Fila
              key={f.id}
              titulo={f.nombre}
              detalle={plural(f.num_programas, "programa")}
              onEditar={() => { setEditando(f); setNombre(f.nombre); }}
              onEliminar={() => api.adminEliminarFacultad(f.id).then(recargar).catch((e) => alError(mensajeError(e)))}
              textoEliminar="¿Eliminar esta facultad? Solo es posible si no tiene programas."
            />
          ))}
        </ul>
      ) : (
        <VacioLista cargando={lista === null} vacio="Aún no hay facultades" />
      )}
    </div>
  );
}

// ---------- Programas ----------

function TabProgramas({ alError }: PropsTab) {
  const [lista, recargar] = useLista<Programa>(api.adminProgramas, alError);
  const [facultades] = useLista<Facultad>(api.adminFacultades, alError);
  const [facultadId, setFacultadId] = useState("");
  const [nombre, setNombre] = useState("");
  const [codigo, setCodigo] = useState("");
  const [editando, setEditando] = useState<Programa | null>(null);

  function limpiar() {
    setEditando(null);
    setNombre("");
    setCodigo("");
  }

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    try {
      if (editando) await api.adminEditarPrograma(editando.id, { facultad_id: Number(facultadId), nombre: nombre.trim(), codigo: codigo.trim() });
      else await api.adminCrearPrograma(Number(facultadId), nombre.trim(), codigo.trim());
      limpiar();
      recargar();
    } catch (err) {
      alError(mensajeError(err));
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Tarjeta>
        <form onSubmit={guardar} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-[1.5fr_2fr_1fr_auto] lg:items-end">
          <Select etiqueta="Facultad" value={facultadId} onChange={(e) => setFacultadId(e.target.value)} required>
            <option value="">Selecciona…</option>
            {facultades?.map((f) => (
              <option key={f.id} value={f.id}>
                {f.nombre}
              </option>
            ))}
          </Select>
          <Input etiqueta="Nombre del programa" value={nombre} onChange={(e) => setNombre(e.target.value)} required minLength={2} />
          <Input etiqueta="Código" value={codigo} onChange={(e) => setCodigo(e.target.value)} required maxLength={20} placeholder="ISC" />
          <div className="flex gap-2">
            <Boton type="submit">{editando ? "Guardar" : "Agregar"}</Boton>
            {editando && (
              <Boton variante="secundario" onClick={limpiar}>
                Cancelar
              </Boton>
            )}
          </div>
        </form>
      </Tarjeta>
      {lista?.length ? (
        <ul className="flex flex-col gap-3">
          {lista.map((p) => (
            <Fila
              key={p.id}
              titulo={p.nombre}
              detalle={p.facultad}
              etiquetas={<Insignia tono="azul">{p.codigo}</Insignia>}
              onEditar={() => { setEditando(p); setFacultadId(String(p.facultad_id)); setNombre(p.nombre); setCodigo(p.codigo); }}
              onEliminar={() => api.adminEliminarPrograma(p.id).then(recargar).catch((e) => alError(mensajeError(e)))}
              textoEliminar="¿Eliminar este programa? Solo es posible si no tiene asignaturas ni resultados de aprendizaje."
            />
          ))}
        </ul>
      ) : (
        <VacioLista cargando={lista === null} vacio="Aún no hay programas" />
      )}
    </div>
  );
}

// ---------- Asignaturas ----------

function AsignarRas({ a, ras, alCerrar, alError }: { a: Asignatura; ras: ResultadoAprendizaje[]; alCerrar: () => void; alError: (m: string | null) => void }) {
  const [elegidos, setElegidos] = useState<number[]>(a.ra_ids);
  const delPrograma = ras.filter((r) => r.programa_id === a.programa_id);

  async function guardar() {
    try {
      await api.adminAsignarRas(a.id, elegidos);
      alCerrar();
    } catch (e) {
      alError(mensajeError(e));
    }
  }

  return (
    <div className="flex flex-col gap-2 rounded-xl bg-superficie-2 p-3">
      <p className="text-sm font-semibold">Resultados de aprendizaje que aporta esta asignatura</p>
      {delPrograma.length === 0 && <p className="text-sm text-suave">El programa aún no tiene resultados de aprendizaje.</p>}
      {delPrograma.map((r) => (
        <Casilla key={r.id} checked={elegidos.includes(r.id)} onChange={(e) => setElegidos((l) => (e.target.checked ? [...l, r.id] : l.filter((x) => x !== r.id)))}>
          <strong>{r.codigo}</strong> · {r.descripcion}
        </Casilla>
      ))}
      <div className="flex flex-col gap-2 sm:flex-row">
        <Boton onClick={guardar}>Guardar RA</Boton>
        <Boton variante="secundario" onClick={alCerrar}>
          Cancelar
        </Boton>
      </div>
    </div>
  );
}

function TabAsignaturas({ alError }: PropsTab) {
  const [lista, recargar] = useLista<Asignatura>(api.adminAsignaturas, alError);
  const [programas] = useLista<Programa>(api.adminProgramas, alError);
  const [ras] = useLista<ResultadoAprendizaje>(api.adminRas, alError);
  const [programaId, setProgramaId] = useState("");
  const [nombre, setNombre] = useState("");
  const [codigo, setCodigo] = useState("");
  const [semestre, setSemestre] = useState("1");
  const [asignando, setAsignando] = useState<number | null>(null);

  async function crear(e: React.FormEvent) {
    e.preventDefault();
    try {
      await api.adminCrearAsignatura(Number(programaId), nombre.trim(), codigo.trim(), Number(semestre));
      setNombre("");
      setCodigo("");
      recargar();
    } catch (err) {
      alError(mensajeError(err));
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Tarjeta>
        <form onSubmit={crear} className="grid gap-4 sm:grid-cols-2 lg:grid-cols-[1.5fr_2fr_1fr_0.7fr_auto] lg:items-end">
          <Select etiqueta="Programa" value={programaId} onChange={(e) => setProgramaId(e.target.value)} required>
            <option value="">Selecciona…</option>
            {programas?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre}
              </option>
            ))}
          </Select>
          <Input etiqueta="Nombre de la asignatura" value={nombre} onChange={(e) => setNombre(e.target.value)} required minLength={2} />
          <Input etiqueta="Código" value={codigo} onChange={(e) => setCodigo(e.target.value)} required maxLength={20} />
          <Input etiqueta="Semestre" type="number" min={1} max={12} value={semestre} onChange={(e) => setSemestre(e.target.value)} required />
          <Boton type="submit">Agregar</Boton>
        </form>
      </Tarjeta>
      {lista?.length ? (
        <ul className="flex flex-col gap-3">
          {lista.map((a) => (
            <Fila
              key={a.id}
              titulo={`${a.codigo} · ${a.nombre}`}
              detalle={`${a.programa} · Semestre ${a.semestre}`}
              etiquetas={
                a.ra_ids.length ? (
                  ras?.filter((r) => a.ra_ids.includes(r.id)).map((r) => (
                    <Insignia key={r.id} tono="azul">
                      {r.codigo}
                    </Insignia>
                  ))
                ) : (
                  <Insignia tono="neutro">Sin RA</Insignia>
                )
              }
              onEditar={() => setAsignando(asignando === a.id ? null : a.id)}
              onEliminar={() => api.adminEliminarAsignatura(a.id).then(recargar).catch((e) => alError(mensajeError(e)))}
              textoEliminar="¿Eliminar esta asignatura? Solo es posible si no tiene grupos."
            >
              {asignando === a.id && ras && (
                <AsignarRas
                  a={a}
                  ras={ras}
                  alError={alError}
                  alCerrar={() => {
                    setAsignando(null);
                    recargar();
                  }}
                />
              )}
            </Fila>
          ))}
        </ul>
      ) : (
        <VacioLista cargando={lista === null} vacio="Aún no hay asignaturas" />
      )}
    </div>
  );
}

// ---------- Resultados de aprendizaje ----------

function TabRas({ alError }: PropsTab) {
  const [lista, recargar] = useLista<ResultadoAprendizaje>(api.adminRas, alError);
  const [programas] = useLista<Programa>(api.adminProgramas, alError);
  const [programaId, setProgramaId] = useState("");
  const [codigo, setCodigo] = useState("");
  const [descripcion, setDescripcion] = useState("");
  const [editando, setEditando] = useState<ResultadoAprendizaje | null>(null);

  function limpiar() {
    setEditando(null);
    setCodigo("");
    setDescripcion("");
  }

  async function guardar(e: React.FormEvent) {
    e.preventDefault();
    try {
      if (editando) await api.adminEditarRa(editando.id, { codigo: codigo.trim(), descripcion: descripcion.trim() });
      else await api.adminCrearRa(Number(programaId), codigo.trim(), descripcion.trim());
      limpiar();
      recargar();
    } catch (err) {
      alError(mensajeError(err));
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <Tarjeta>
        <form onSubmit={guardar} className="grid gap-4 sm:grid-cols-2">
          <Select etiqueta="Programa" value={programaId} onChange={(e) => setProgramaId(e.target.value)} required disabled={!!editando}>
            <option value="">Selecciona…</option>
            {programas?.map((p) => (
              <option key={p.id} value={p.id}>
                {p.nombre}
              </option>
            ))}
          </Select>
          <Input etiqueta="Código" value={codigo} onChange={(e) => setCodigo(e.target.value)} required maxLength={20} placeholder="RA1" />
          <Textarea etiqueta="Descripción del resultado de aprendizaje" value={descripcion} onChange={(e) => setDescripcion(e.target.value)} required minLength={3} rows={3} claseCampo="sm:col-span-2" />
          <div className="flex gap-2 sm:col-span-2">
            <Boton type="submit">{editando ? "Guardar cambios" : "Agregar RA"}</Boton>
            {editando && (
              <Boton variante="secundario" onClick={limpiar}>
                Cancelar
              </Boton>
            )}
          </div>
        </form>
      </Tarjeta>
      {lista?.length ? (
        <ul className="flex flex-col gap-3">
          {lista.map((r) => (
            <Fila
              key={r.id}
              titulo={`${r.codigo} · ${r.programa}`}
              detalle={r.descripcion}
              onEditar={() => { setEditando(r); setProgramaId(String(r.programa_id)); setCodigo(r.codigo); setDescripcion(r.descripcion); }}
              onEliminar={() => api.adminEliminarRa(r.id).then(recargar).catch((e) => alError(mensajeError(e)))}
              textoEliminar="¿Eliminar este resultado de aprendizaje? Las preguntas que lo usan quedarán sin RA."
            />
          ))}
        </ul>
      ) : (
        <VacioLista cargando={lista === null} vacio="Aún no hay resultados de aprendizaje" />
      )}
    </div>
  );
}

// ---------- Usuarios ----------

const ROLES = [
  { id: "estudiante", texto: "Estudiante" },
  { id: "docente", texto: "Docente" },
  { id: "coordinador", texto: "Coordinador" },
  { id: "admin", texto: "Administrador" },
];

function FilaUsuario({ u, programas, alError, alGuardar }: { u: UsuarioAdmin; programas: Programa[]; alError: (m: string | null) => void; alGuardar: () => void }) {
  const [rol, setRol] = useState<string>(u.rol);
  const [programaId, setProgramaId] = useState(u.programa_id ? String(u.programa_id) : "");
  const [guardando, setGuardando] = useState(false);
  const cambiado = rol !== u.rol || (rol === "coordinador" && programaId !== (u.programa_id ? String(u.programa_id) : ""));

  async function guardar() {
    setGuardando(true);
    try {
      await api.adminEditarUsuario(u.id, { rol, programa_id: rol === "coordinador" && programaId ? Number(programaId) : null });
      alError(null);
      alGuardar();
    } catch (e) {
      alError(mensajeError(e));
    } finally {
      setGuardando(false);
    }
  }

  return (
    <li className="flex min-w-0 flex-col gap-3 rounded-xl border border-borde bg-superficie p-4 lg:flex-row lg:items-end">
      <div className="min-w-0 lg:flex-1">
        <p className="break-words font-semibold">{u.nombre}</p>
        <p className="break-all text-sm text-suave">{u.email}</p>
      </div>
      <Select etiqueta="Rol" value={rol} onChange={(e) => setRol(e.target.value)} claseCampo="lg:w-44">
        {ROLES.map((r) => (
          <option key={r.id} value={r.id}>
            {r.texto}
          </option>
        ))}
      </Select>
      {rol === "coordinador" && (
        <Select etiqueta="Programa que coordina" value={programaId} onChange={(e) => setProgramaId(e.target.value)} claseCampo="lg:w-64">
          <option value="">Sin programa</option>
          {programas.map((p) => (
            <option key={p.id} value={p.id}>
              {p.nombre}
            </option>
          ))}
        </Select>
      )}
      <Boton onClick={guardar} cargando={guardando} disabled={!cambiado}>
        Guardar
      </Boton>
    </li>
  );
}

function TabUsuarios({ alError }: PropsTab) {
  const [lista, recargar] = useLista<UsuarioAdmin>(api.adminUsuarios, alError);
  const [programas] = useLista<Programa>(api.adminProgramas, alError);
  const [filtro, setFiltro] = useState("");
  const visibles = lista?.filter((u) => `${u.nombre} ${u.email}`.toLowerCase().includes(filtro.trim().toLowerCase()));

  return (
    <div className="flex flex-col gap-6">
      <Input etiqueta="Buscar por nombre o correo" value={filtro} onChange={(e) => setFiltro(e.target.value)} claseCampo="sm:max-w-md" />
      {visibles?.length ? (
        <ul className="flex flex-col gap-3">
          {visibles.map((u) => (
            <FilaUsuario key={`${u.id}-${u.rol}-${u.programa_id}`} u={u} programas={programas ?? []} alError={alError} alGuardar={recargar} />
          ))}
        </ul>
      ) : (
        <VacioLista cargando={lista === null} vacio="No hay usuarios que coincidan" />
      )}
    </div>
  );
}

// ---------- Página ----------

const PESTANAS = [
  { id: "facultades", texto: "Facultades" },
  { id: "programas", texto: "Programas" },
  { id: "asignaturas", texto: "Asignaturas" },
  { id: "ras", texto: "Resultados de aprendizaje" },
  { id: "usuarios", texto: "Usuarios" },
] as const;
type IdPestana = (typeof PESTANAS)[number]["id"];

export default function AdminPage() {
  const { usuario, cargando } = useRequiereLogin();
  const [pestana, setPestana] = useState<IdPestana>("facultades");
  const [error, setError] = useState<string | null>(null);

  if (cargando || !usuario) {
    return (
      <Pagina>
        <EsqueletoPagina />
      </Pagina>
    );
  }
  if (usuario.rol !== "admin") {
    return (
      <Pagina ancho="md">
        <Alerta tipo="info">Esta sección es solo para administradores de la plataforma.</Alerta>
      </Pagina>
    );
  }

  return (
    <Pagina ancho="lg">
      <EncabezadoPagina migas={[{ texto: "Panel", href: "/panel" }, { texto: "Administración" }]} titulo="Administración" descripcion="Estructura académica institucional (facultades, programas, asignaturas y resultados de aprendizaje) y gestión de usuarios." />
      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}
      <Pestanas etiqueta="Secciones de administración" items={PESTANAS} activa={pestana} onCambiar={(id) => { setError(null); setPestana(id); }}>
        <TituloSeccion className="sr-only">{PESTANAS.find((p) => p.id === pestana)?.texto}</TituloSeccion>
        {pestana === "facultades" && <TabFacultades alError={setError} />}
        {pestana === "programas" && <TabProgramas alError={setError} />}
        {pestana === "asignaturas" && <TabAsignaturas alError={setError} />}
        {pestana === "ras" && <TabRas alError={setError} />}
        {pestana === "usuarios" && <TabUsuarios alError={setError} />}
      </Pestanas>
    </Pagina>
  );
}
