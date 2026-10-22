"use client";

import { useEffect, useState } from "react";
import { SelloVerificacion } from "@/components/CalidadPregunta";
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
} from "@/components/ui";
import { agregarDesdeBanco, buscarBanco, editarBanco, eliminarDelBanco, filtrosBanco, listarCuestionarios } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import { NIVELES_BLOOM, type CuestionarioResumen, type FiltrosBanco, type PaginaBanco, type PreguntaBanco } from "@/lib/tipos";

const TIPOS: Record<string, string> = { opcion_multiple: "Opción múltiple", verdadero_falso: "Verdadero / Falso", abierta: "Abierta" };
const mayus = (t: string) => t.charAt(0).toUpperCase() + t.slice(1);

function TarjetaPregunta({
  p,
  propios,
  esDocente,
  onCambio,
  onError,
}: {
  p: PreguntaBanco;
  propios: CuestionarioResumen[];
  esDocente: boolean;
  onCambio: () => void;
  onError: (m: string) => void;
}) {
  const [destino, setDestino] = useState("");
  const [agregando, setAgregando] = useState(false);
  const [aviso, setAviso] = useState<string | null>(null);
  const [eliminando, setEliminando] = useState(false);

  async function agregar() {
    if (!destino) return;
    setAgregando(true);
    setAviso(null);
    try {
      await agregarDesdeBanco(p.id, Number(destino));
      setAviso("Pregunta agregada al cuestionario.");
    } catch (e) {
      onError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setAgregando(false);
    }
  }

  async function cambiarVisibilidad() {
    try {
      await editarBanco(p.id, { visibilidad: p.visibilidad === "privada" ? "institucional" : "privada" });
      onCambio();
    } catch (e) {
      onError(e instanceof Error ? e.message : "Error desconocido");
    }
  }

  async function eliminar() {
    try {
      await eliminarDelBanco(p.id);
      onCambio();
    } catch (e) {
      onError(e instanceof Error ? e.message : "Error desconocido");
    }
  }

  return (
    <Tarjeta as="article" className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-1.5">
        <Insignia tono="azul">{TIPOS[p.tipo] ?? p.tipo}</Insignia>
        {p.nivel_bloom && <Insignia>{mayus(p.nivel_bloom)}</Insignia>}
        {p.ra_codigo && <Insignia tono="neutro">{p.ra_codigo}</Insignia>}
        {p.asignatura_nombre && <Insignia tono="neutro">{p.asignatura_nombre}</Insignia>}
        <SelloVerificacion v={p.verificacion} />
        <Insignia tono={p.visibilidad === "privada" ? "aviso" : "exito"}>{p.visibilidad === "privada" ? "Privada" : "Institucional"}</Insignia>
      </div>

      <p className="font-semibold leading-snug">{p.enunciado}</p>

      {p.opciones.length > 0 && (
        <ul className="flex flex-col gap-1.5 text-sm">
          {p.opciones.map((o, i) => (
            <li key={o} className="flex items-start gap-2">
              <span aria-hidden="true" className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full border border-current text-xs font-bold">
                {String.fromCharCode(65 + i)}
              </span>
              <span className="min-w-0 flex-1 break-words">{o}</span>
              {o === p.respuesta_correcta && (
                <Insignia tono="exito">
                  <Icono nombre="check" tamano={12} /> Correcta
                </Insignia>
              )}
            </li>
          ))}
        </ul>
      )}
      {p.tipo === "abierta" && (
        <p className="rounded-xl border border-info-borde bg-info-fondo p-3 text-sm text-info-texto">
          <strong>Respuesta modelo:</strong> {p.respuesta_correcta}
        </p>
      )}

      {p.etiquetas.length > 0 && (
        <ul className="flex flex-wrap gap-1.5" aria-label="Etiquetas">
          {p.etiquetas.map((e) => (
            <li key={e}>
              <Insignia tono="neutro">#{e}</Insignia>
            </li>
          ))}
        </ul>
      )}

      <p className="text-xs text-suave">
        Autor: {p.autor}
        {p.estadisticas &&
          ` · Usada en ${p.estadisticas.usos} cuestionario(s) · ${p.estadisticas.respuestas} respuesta(s)` +
            (p.estadisticas.porcentaje_acierto !== null ? ` · ${String(p.estadisticas.porcentaje_acierto).replace(".", ",")} % de acierto` : "")}
      </p>

      {aviso && <Alerta tipo="exito">{aviso}</Alerta>}

      <div className="flex flex-col gap-2 border-t border-borde pt-3 sm:flex-row sm:flex-wrap sm:items-end">
        {esDocente && (
          <>
            <Select etiqueta="Agregar a un cuestionario mío" value={destino} onChange={(e) => setDestino(e.target.value)} claseCampo="sm:w-72">
              <option value="">Elige un cuestionario…</option>
              {propios.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.titulo}
                </option>
              ))}
            </Select>
            <Boton tamano="md" cargando={agregando} disabled={!destino} onClick={agregar}>
              <Icono nombre="mas" tamano={16} /> Agregar
            </Boton>
          </>
        )}
        {p.es_mia && (
          <>
            <Boton variante="secundario" onClick={cambiarVisibilidad}>
              Hacer {p.visibilidad === "privada" ? "institucional" : "privada"}
            </Boton>
            <Boton variante="peligroSuave" onClick={() => setEliminando(true)}>
              <Icono nombre="basura" tamano={16} /> Quitar del banco
            </Boton>
          </>
        )}
      </div>
      {eliminando && (
        <ConfirmacionEnLinea
          mensaje="¿Quitar esta pregunta del banco? Los cuestionarios que ya la usan conservan su copia."
          textoConfirmar="Sí, quitar"
          onConfirmar={eliminar}
          onCancelar={() => setEliminando(false)}
        />
      )}
    </Tarjeta>
  );
}

export default function BancoPage() {
  const { usuario, cargando } = useRequiereLogin();
  const [q, setQ] = useState("");
  const [qAplicada, setQAplicada] = useState("");
  const [asignatura, setAsignatura] = useState("");
  const [ra, setRa] = useState("");
  const [bloom, setBloom] = useState("");
  const [tipo, setTipo] = useState("");
  const [verificacion, setVerificacion] = useState("");
  const [soloMias, setSoloMias] = useState(false);
  const [pagina, setPagina] = useState(1);
  const [datos, setDatos] = useState<PaginaBanco | null>(null);
  const [filtros, setFiltros] = useState<FiltrosBanco>({ asignaturas: [], ras: [] });
  const [propios, setPropios] = useState<CuestionarioResumen[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [recarga, setRecarga] = useState(0);

  const rolOk = usuario && ["docente", "coordinador", "admin"].includes(usuario.rol);
  const esDocente = usuario?.rol === "docente";

  useEffect(() => {
    if (!rolOk) return;
    filtrosBanco().then(setFiltros).catch(() => undefined);
    if (esDocente) listarCuestionarios().then((l) => setPropios(l.filter((c) => c.propio))).catch(() => undefined);
  }, [rolOk, esDocente, recarga]);

  useEffect(() => {
    if (!rolOk) return;
    buscarBanco({ q: qAplicada, asignatura, ra, bloom, tipo, verificacion, solo_mias: soloMias, pagina })
      .then((d) => {
        setDatos(d);
        setError(null);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
  }, [rolOk, qAplicada, asignatura, ra, bloom, tipo, verificacion, soloMias, pagina, recarga]);

  function buscar(e: React.FormEvent) {
    e.preventDefault();
    setPagina(1);
    setQAplicada(q.trim());
  }

  const filtra = (fn: (v: string) => void) => (e: React.ChangeEvent<HTMLSelectElement>) => {
    fn(e.target.value);
    setPagina(1);
  };

  if (cargando || !usuario) return <Pagina><EsqueletoPagina /></Pagina>;
  if (!rolOk)
    return (
      <Pagina ancho="md">
        <Alerta tipo="advertencia">El banco de preguntas es solo para docentes y coordinadores.</Alerta>
      </Pagina>
    );

  const totalPaginas = datos ? Math.max(1, Math.ceil(datos.total / datos.por_pagina)) : 1;

  return (
    <Pagina ancho="lg">
      <EncabezadoPagina
        titulo="Banco de preguntas"
        descripcion="Preguntas reutilizables de la institución. Guarda las tuyas desde el editor o el visor del cuestionario y agrégalas a nuevos cuestionarios."
      />

      <form onSubmit={buscar} className="mb-6 flex flex-col gap-4" role="search" aria-label="Buscar en el banco">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
          <Input etiqueta="Buscar por texto" type="search" value={q} onChange={(e) => setQ(e.target.value)} placeholder="Enunciado, opción o etiqueta…" claseCampo="flex-1" />
          <Boton type="submit">
            <Icono nombre="flecha" tamano={16} /> Buscar
          </Boton>
        </div>
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-5">
          <Select etiqueta="Asignatura" value={asignatura} onChange={filtra(setAsignatura)}>
            <option value="">Todas</option>
            {filtros.asignaturas.map((a) => (
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </Select>
          <Select etiqueta="Resultado de aprendizaje" value={ra} onChange={filtra(setRa)}>
            <option value="">Todos</option>
            {filtros.ras.map((r) => (
              <option key={r} value={r}>
                {r}
              </option>
            ))}
          </Select>
          <Select etiqueta="Nivel de Bloom" value={bloom} onChange={filtra(setBloom)}>
            <option value="">Todos</option>
            {NIVELES_BLOOM.map((n) => (
              <option key={n} value={n}>
                {mayus(n)}
              </option>
            ))}
          </Select>
          <Select etiqueta="Tipo" value={tipo} onChange={filtra(setTipo)}>
            <option value="">Todos</option>
            {Object.entries(TIPOS).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </Select>
          <Select etiqueta="Verificación" value={verificacion} onChange={filtra(setVerificacion)}>
            <option value="">Todas</option>
            <option value="verificada">Verificadas en el video</option>
            <option value="revisar">Requieren revisión</option>
            <option value="sin_verificar">Sin verificar</option>
          </Select>
        </div>
        <label className="flex min-h-11 cursor-pointer items-center gap-3 text-sm font-semibold">
          <input
            type="checkbox"
            checked={soloMias}
            onChange={(e) => {
              setSoloMias(e.target.checked);
              setPagina(1);
            }}
            className="h-5 w-5 accent-primario"
          />
          Ver solo las mías
        </label>
      </form>

      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}

      {!datos && !error && <EsqueletoPagina tarjetas={2} />}

      {datos && datos.items.length === 0 && (
        <EstadoVacio icono="libro" titulo="No hay preguntas con esos criterios">
          Guarda preguntas desde el editor de un cuestionario con «Guardar en el banco», o cambia los filtros.
        </EstadoVacio>
      )}

      {datos && datos.items.length > 0 && (
        <>
          <p className="mb-3 text-sm text-suave" role="status">
            {datos.total} pregunta(s)
          </p>
          <div className="flex flex-col gap-4">
            {datos.items.map((p) => (
              <TarjetaPregunta key={p.id} p={p} propios={propios} esDocente={!!esDocente} onCambio={() => setRecarga((n) => n + 1)} onError={setError} />
            ))}
          </div>
          {totalPaginas > 1 && (
            <nav aria-label="Paginación" className="mt-6 flex items-center justify-between gap-3">
              <Boton variante="secundario" disabled={pagina <= 1} onClick={() => setPagina((n) => n - 1)}>
                <Icono nombre="atras" tamano={16} /> Anterior
              </Boton>
              <span className="text-sm font-semibold">
                Página {pagina} de {totalPaginas}
              </span>
              <Boton variante="secundario" disabled={pagina >= totalPaginas} onClick={() => setPagina((n) => n + 1)}>
                Siguiente <Icono nombre="flecha" tamano={16} />
              </Boton>
            </nav>
          )}
        </>
      )}
    </Pagina>
  );
}
