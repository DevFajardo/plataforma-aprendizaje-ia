"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  Alerta,
  Boton,
  ConfirmacionEnLinea,
  EncabezadoPagina,
  EsqueletoPagina,
  EstadoVacio,
  Input,
  Insignia,
  Pagina,
  Tarjeta,
  TituloSeccion,
} from "@/components/ui";
import { misCursos, salirDelCurso, unirseACurso } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import type { MiCurso } from "@/lib/tipos";
import { useToast } from "@/components/ui/Toast";
import { plural } from "@/lib/formato";

export default function MisCursosPage() {
  const { avisar } = useToast();
  const { usuario, cargando } = useRequiereLogin();
  const [cursos, setCursos] = useState<MiCurso[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [codigo, setCodigo] = useState("");
  const [uniendo, setUniendo] = useState(false);
  const [saliendo, setSaliendo] = useState<number | null>(null);

  const cargar = useCallback(() => {
    misCursos()
      .then(setCursos)
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
  }, []);

  useEffect(() => {
    if (usuario?.rol === "estudiante") cargar();
  }, [usuario, cargar]);

  async function unirse(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setUniendo(true);
    try {
      const c = await unirseACurso(codigo);
      avisar(`Te matriculaste en ${c.asignatura} · ${c.nombre} (${c.periodo}).`);
      setCodigo("");
      cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    } finally {
      setUniendo(false);
    }
  }

  async function salir(id: number) {
    setError(null);
    try {
      await salirDelCurso(id);
      setSaliendo(null);
      cargar();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error desconocido");
    }
  }

  if (cargando || !usuario) {
    return (
      <Pagina>
        <EsqueletoPagina />
      </Pagina>
    );
  }
  if (usuario.rol !== "estudiante") {
    return (
      <Pagina ancho="md">
        <Alerta tipo="info">Esta sección es para estudiantes. Los docentes gestionan sus grupos en «Cursos».</Alerta>
      </Pagina>
    );
  }

  return (
    <Pagina ancho="lg">
      <EncabezadoPagina titulo="Mis cursos" descripcion="Los cuestionarios que tu docente publica en tu grupo aparecen aquí, sin necesidad de código." />

      <div className="flex flex-col gap-8">
        <Tarjeta as="section" aria-label="Unirse a un curso">
          {/* Rejilla: en móvil campo → ayuda → botón; desde sm el botón va junto al campo, alineado con él (la ayuda queda debajo) */}
          <form onSubmit={unirse} className="grid gap-x-3 gap-y-2 sm:grid-cols-[minmax(0,20rem)_auto] sm:justify-start">
            <Input
              etiqueta="Código de ingreso del curso"
              value={codigo}
              onChange={(e) => setCodigo(e.target.value.toUpperCase())}
              maxLength={6}
              autoComplete="off"
              autoCapitalize="characters"
              placeholder="ABC123"
              aria-describedby="ayuda-codigo-curso"
              className="font-mono text-lg font-bold tracking-[0.3em]"
            />
            <p id="ayuda-codigo-curso" className="text-sm text-suave sm:col-span-2">
              Tu docente te lo comparte al inicio del periodo.
            </p>
            <Boton
              type="submit"
              tamano="lg"
              cargando={uniendo}
              disabled={codigo.trim().length < 6}
              className="mt-2 min-h-[3.125rem] sm:col-start-2 sm:row-start-1 sm:mt-0 sm:self-end"
            >
              Unirme al curso
            </Boton>
          </form>
        </Tarjeta>

        {error && <Alerta tipo="error" reintentar={cursos === null ? cargar : undefined}>{error}</Alerta>}

        {cursos === null && !error && <EsqueletoPagina tarjetas={2} />}
        {cursos?.length === 0 && (
          <EstadoVacio icono="libro" titulo="Aún no estás matriculado en ningún curso">
            Escribe arriba el código de ingreso que te dio tu docente.
          </EstadoVacio>
        )}

        <div className="flex flex-col gap-6">
          {cursos?.map((c) => (
            <Tarjeta as="article" key={c.grupo_id} className="flex flex-col gap-4">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <TituloSeccion nivel={3}>{c.asignatura}</TituloSeccion>
                  <p className="mt-1 text-sm text-suave">
                    {c.programa} · Docente: {c.docente}
                  </p>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Insignia tono="azul">{c.nombre}</Insignia>
                  <Insignia tono="neutro">{c.periodo}</Insignia>
                </div>
              </div>

              {c.cuestionarios.length === 0 ? (
                <p className="rounded-xl bg-superficie-2 p-3 text-sm text-suave">Tu docente aún no ha publicado cuestionarios en este curso.</p>
              ) : (
                <ul className="flex flex-col gap-2">
                  {c.cuestionarios.map((q) => (
                    <li key={q.id}>
                      <Link
                        href={`/cuestionarios/${q.id}`}
                        className="flex min-h-12 flex-wrap items-center justify-between gap-2 rounded-xl border border-borde px-4 py-3 transition hover:border-borde-fuerte hover:bg-superficie-2"
                      >
                        <span className="min-w-0 break-words font-semibold">{q.titulo}</span>
                        <span className="text-xs text-suave">
                          {plural(q.num_preguntas, "pregunta")}
                          {q.mejor_puntaje !== null && ` · Mejor resultado: ${q.mejor_puntaje}/${q.mejor_total}`}
                        </span>
                      </Link>
                    </li>
                  ))}
                </ul>
              )}

              {saliendo === c.grupo_id ? (
                <ConfirmacionEnLinea
                  mensaje="¿Salir de este curso? Dejarás de ver sus cuestionarios en «Mis cursos»; tus intentos se conservan."
                  textoConfirmar="Sí, salir"
                  onConfirmar={() => salir(c.grupo_id)}
                  onCancelar={() => setSaliendo(null)}
                />
              ) : (
                <Boton variante="fantasma" className="self-start" onClick={() => setSaliendo(c.grupo_id)}>
                  Salir del curso
                </Boton>
              )}
            </Tarjeta>
          ))}
        </div>
      </div>
    </Pagina>
  );
}
