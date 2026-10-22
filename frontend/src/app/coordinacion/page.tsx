"use client";

import { useEffect, useState } from "react";
import AlertasTempranas from "@/components/AlertasTempranas";
import { FilaLogro, pct } from "@/components/LogroUI";
import {
  Alerta,
  BarraPorcentaje,
  Boton,
  EncabezadoPagina,
  EsqueletoPagina,
  EstadoVacio,
  Icono,
  Metrica,
  Pagina,
  Select,
  Tarjeta,
  TituloSeccion,
} from "@/components/ui";
import { descargarPdfRa, obtenerCoordinacion } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import { formatearFecha } from "@/lib/fechas";
import type { Coordinacion } from "@/lib/tipos";

const ETIQUETA_BLOOM: Record<string, string> = {
  recordar: "Recordar",
  comprender: "Comprender",
  aplicar: "Aplicar",
  analizar: "Analizar",
  evaluar: "Evaluar",
  crear: "Crear",
};

export default function CoordinacionPage() {
  const { usuario, cargando } = useRequiereLogin();
  const [datos, setDatos] = useState<Coordinacion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [programaId, setProgramaId] = useState("");
  const [periodo, setPeriodo] = useState("");
  const [descargando, setDescargando] = useState(false);
  const permitido = usuario?.rol === "coordinador" || usuario?.rol === "admin";

  useEffect(() => {
    if (!permitido) return;
    let activo = true;
    obtenerCoordinacion(programaId ? Number(programaId) : null, periodo || null)
      .then((d) => {
        if (activo) {
          setDatos(d);
          setError(null);
        }
      })
      .catch((e) => activo && setError(e instanceof Error ? e.message : "Error desconocido"));
    return () => {
      activo = false;
    };
  }, [permitido, programaId, periodo]);

  async function pdf() {
    setError(null);
    setDescargando(true);
    try {
      await descargarPdfRa(programaId ? Number(programaId) : null, periodo || null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setDescargando(false);
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
        <Alerta tipo="info">Este panel es para coordinadores de programa y administradores.</Alerta>
      </Pagina>
    );
  }

  return (
    <Pagina ancho="completo">
      <EncabezadoPagina
        titulo="Coordinación académica"
        descripcion={datos ? `Resultados de aprendizaje de ${datos.programa_nombre}.` : "Resultados de aprendizaje del programa."}
        acciones={
          <Boton onClick={pdf} cargando={descargando} disabled={!datos}>
            <Icono nombre="descargar" /> Descargar PDF
          </Boton>
        }
      />

      {error && <Alerta tipo="error" className="mb-4">{error}</Alerta>}
      {!datos && !error && <EsqueletoPagina />}

      {datos && (
        <div className="flex flex-col gap-8">
          <Tarjeta as="section" aria-label="Filtros" className="grid gap-4 sm:grid-cols-2">
            {usuario.rol === "admin" ? (
              <Select etiqueta="Programa" value={programaId} onChange={(e) => setProgramaId(e.target.value)}>
                <option value="">Todos los programas</option>
                {datos.programas.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.nombre}
                  </option>
                ))}
              </Select>
            ) : (
              <div className="flex flex-col gap-1.5">
                <span className="text-sm font-semibold">Programa</span>
                <span className="flex min-h-11 items-center rounded-lg border border-borde bg-superficie-2 px-3.5 text-sm">{datos.programa_nombre}</span>
              </div>
            )}
            <Select etiqueta="Periodo" value={periodo} onChange={(e) => setPeriodo(e.target.value)}>
              <option value="">Todos los periodos</option>
              {datos.periodos.map((p) => (
                <option key={p} value={p}>
                  {p}
                </option>
              ))}
            </Select>
          </Tarjeta>

          <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3">
            <Metrica icono="trofeo" titulo="Logro global" valor={pct(datos.logro_global)} />
            <Metrica icono="intentos" titulo="Respuestas evaluadas" valor={String(datos.respuestas)} />
            <Metrica className="col-span-2 lg:col-span-1" icono="grupo" titulo="Estudiantes evaluados" valor={String(datos.estudiantes)} />
          </div>

          <section aria-label="Logro por resultado de aprendizaje" className="flex flex-col gap-4">
            <div>
              <TituloSeccion>Logro por resultado de aprendizaje</TituloSeccion>
              <p className="mt-1 text-sm text-suave">
                Porcentaje de acierto en las preguntas asociadas a cada RA. Semáforo: verde desde 70 %, amarillo de 50 a 69 %, rojo por debajo de 50 %.
              </p>
            </div>
            {datos.ras.length === 0 ? (
              <EstadoVacio icono="libro" titulo="Este programa aún no tiene resultados de aprendizaje">
                El administrador puede definirlos en «Admin».
              </EstadoVacio>
            ) : (
              <div className="grid gap-4 lg:grid-cols-2">
                {datos.ras.map((r) => (
                  <Tarjeta key={r.ra_id} className="flex flex-col gap-3">
                    <p className="text-sm">
                      <strong className="text-enlace">{r.codigo}</strong> · {r.descripcion}
                      {usuario.rol === "admin" && !programaId && <span className="block text-xs text-suave">{r.programa}</span>}
                    </p>
                    <FilaLogro etiqueta={r.codigo} logro={r.logro} semaforo={r.semaforo} detalle={`${r.respuestas} respuestas · ${r.estudiantes} estudiantes evaluados`} />
                  </Tarjeta>
                ))}
              </div>
            )}
          </section>

          <section aria-label="Niveles de Bloom" className="flex flex-col gap-4">
            <TituloSeccion>Distribución por nivel de Bloom</TituloSeccion>
            <Tarjeta className="grid gap-5 sm:grid-cols-2">
              {datos.bloom.map((b) => (
                <div key={b.nivel} className="flex min-w-0 flex-col gap-1.5">
                  <div className="flex items-center justify-between gap-2 text-sm">
                    <span className="font-semibold">{ETIQUETA_BLOOM[b.nivel]}</span>
                    <span className="tabular-nums">{pct(b.logro)}</span>
                  </div>
                  <BarraPorcentaje valor={b.logro ?? 0} etiqueta={`Logro en nivel ${b.nivel}`} />
                  <span className="text-xs text-suave">
                    {b.preguntas} preguntas · {b.respuestas} respuestas
                  </span>
                </div>
              ))}
            </Tarjeta>
          </section>

          <section aria-label="Desempeño por asignatura y grupo" className="flex flex-col gap-4">
            <TituloSeccion>Desempeño por asignatura y grupo</TituloSeccion>
            {datos.asignaturas.length === 0 ? (
              <EstadoVacio icono="grupo" titulo="Sin asignaturas con grupos en este filtro" />
            ) : (
              <div className="grid gap-4 lg:grid-cols-2">
                {datos.asignaturas.map((a) => (
                  <Tarjeta key={a.asignatura_id} className="flex flex-col gap-4">
                    <FilaLogro
                      etiqueta={`${a.codigo} · ${a.nombre}`}
                      logro={a.logro}
                      semaforo={a.semaforo}
                      detalle={`${a.respuestas} respuestas · ${a.estudiantes} estudiantes`}
                    />
                    {a.grupos.length > 0 && (
                      <ul className="flex flex-col gap-3 border-t border-borde pt-3">
                        {a.grupos.map((g) => (
                          <li key={g.grupo_id}>
                            <FilaLogro
                              etiqueta={`${g.nombre} (${g.periodo}) · ${g.docente}`}
                              logro={g.logro}
                              semaforo={g.semaforo}
                              detalle={`${g.respuestas} respuestas · ${g.estudiantes} estudiantes`}
                            />
                          </li>
                        ))}
                      </ul>
                    )}
                  </Tarjeta>
                ))}
              </div>
            )}
          </section>

          <section aria-label="Tendencia semanal" className="flex flex-col gap-4">
            <TituloSeccion>Tendencia semanal del logro</TituloSeccion>
            {datos.tendencia.length === 0 ? (
              <EstadoVacio icono="promedio" titulo="Aún no hay intentos finalizados en este filtro" />
            ) : (
              <Tarjeta>
                <ul className="flex flex-col gap-3">
                  {datos.tendencia.slice(-12).map((t) => (
                    <li key={t.semana} className="grid grid-cols-[6.5rem_1fr_3.5rem] items-center gap-3 text-sm">
                      <span className="text-suave">Sem. {formatearFecha(`${t.semana}T12:00:00`, "corta")}</span>
                      <BarraPorcentaje valor={t.logro} etiqueta={`Logro de la semana del ${t.semana}`} alto="sm" />
                      <span className="text-right font-semibold tabular-nums" title={`${t.respuestas} respuestas`}>
                        {pct(t.logro)}
                      </span>
                    </li>
                  ))}
                </ul>
              </Tarjeta>
            )}
          </section>

          <AlertasTempranas />
        </div>
      )}
    </Pagina>
  );
}
