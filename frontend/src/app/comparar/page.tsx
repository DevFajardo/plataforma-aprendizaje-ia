"use client";

import { useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { Alerta, BarraPorcentaje, Boton, EncabezadoPagina, EsqueletoPagina, Icono, Pagina, Select, Tarjeta, TituloSeccion } from "@/components/ui";
import { compararGrupos, descargarCsvComparar, listarCuestionarios } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import type { Comparacion, CuestionarioResumen, Efecto, GrupoComparacion, MetricaGrupo } from "@/lib/tipos";
import { num, pct } from "@/lib/formato";

type Metrica = "inicial" | "diferido" | "retencion";

const ETIQUETAS: Record<Metrica, string> = {
  inicial: "Intento inicial (%)",
  diferido: "Repaso diferido (%)",
  retencion: "Retención (%)",
};


function Barras({ datos, metrica }: { datos: Comparacion; metrica: Metrica }) {
  const grupos: [string, GrupoComparacion, "primario" | "aviso"][] = [
    ["A", datos.a, "primario"],
    ["B", datos.b, "aviso"],
  ];
  const maximo = Math.max(100, ...grupos.map(([, g]) => g[metrica].media ?? 0));
  return (
    <Tarjeta>
      <h3 className="mb-3 text-sm font-bold">{ETIQUETAS[metrica]}</h3>
      <ul className="flex flex-col gap-4">
        {grupos.map(([letra, g, tono]) => {
          const m = g[metrica].media;
          return (
            <li key={letra}>
              <div className="mb-1.5 flex justify-between gap-2 text-xs">
                <span className="font-semibold">
                  Grupo {letra} ({g.modo === "control" ? "control" : "aprendizaje"})
                </span>
                <span className="font-bold">{m === null ? "sin datos" : pct(m)}</span>
              </div>
              <BarraPorcentaje
                valor={m ?? 0}
                max={maximo}
                etiqueta={`${ETIQUETAS[metrica]}, grupo ${letra}`}
                tono={tono}
                alto="lg"
              />
            </li>
          );
        })}
      </ul>
    </Tarjeta>
  );
}

function Fila({ nombre, a, b, efecto }: { nombre: string; a: MetricaGrupo; b: MetricaGrupo; efecto: Efecto }) {
  return (
    <tr className="border-t border-borde align-top transition hover:bg-superficie-2/60">
      <th scope="row" className="px-3 py-2.5 text-left font-semibold">
        {nombre}
      </th>
      <td className="px-3 py-2.5">{a.n}</td>
      <td className="px-3 py-2.5">
        {num(a.media)} <span className="text-suave">± {num(a.desviacion)}</span>
      </td>
      <td className="px-3 py-2.5">{b.n}</td>
      <td className="px-3 py-2.5">
        {num(b.media)} <span className="text-suave">± {num(b.desviacion)}</span>
      </td>
      <td className="px-3 py-2.5">{num(efecto.diferencia_medias)}</td>
      <td className="px-3 py-2.5">{num(efecto.d_cohen)}</td>
      <td className="px-3 py-2.5 text-xs">{efecto.interpretacion}</td>
    </tr>
  );
}

function TarjetaMedida({ nombre, a, b, efecto }: { nombre: string; a: MetricaGrupo; b: MetricaGrupo; efecto: Efecto }) {
  return (
    <Tarjeta as="article" className="!p-4">
      <h3 className="font-bold">{nombre}</h3>
      <dl className="mt-3 grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
        <div>
          <dt className="text-xs text-suave">Grupo A · n = {a.n}</dt>
          <dd className="font-semibold">
            {num(a.media)} <span className="font-normal text-suave">± {num(a.desviacion)}</span>
          </dd>
        </div>
        <div>
          <dt className="text-xs text-suave">Grupo B · n = {b.n}</dt>
          <dd className="font-semibold">
            {num(b.media)} <span className="font-normal text-suave">± {num(b.desviacion)}</span>
          </dd>
        </div>
        <div>
          <dt className="text-xs text-suave">Diferencia (A − B)</dt>
          <dd className="font-semibold">{num(efecto.diferencia_medias)}</dd>
        </div>
        <div>
          <dt className="text-xs text-suave">d de Cohen</dt>
          <dd className="font-semibold">{num(efecto.d_cohen)}</dd>
        </div>
      </dl>
      <p className="mt-3 rounded-lg bg-superficie-2 p-2.5 text-xs">{efecto.interpretacion}</p>
    </Tarjeta>
  );
}

function Contenido() {
  const { usuario, cargando } = useRequiereLogin();
  const params = useSearchParams();
  const [lista, setLista] = useState<CuestionarioResumen[] | null>(null);
  const [a, setA] = useState(params.get("a") ?? "");
  const [b, setB] = useState(params.get("b") ?? "");
  const [datos, setDatos] = useState<Comparacion | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [ocupado, setOcupado] = useState(false);

  useEffect(() => {
    if (usuario?.rol !== "docente") return;
    listarCuestionarios()
      .then((l) => setLista(l.filter((c) => c.propio)))
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
  }, [usuario]);

  async function comparar() {
    setError(null);
    setOcupado(true);
    try {
      setDatos(await compararGrupos(Number(a), Number(b)));
    } catch (e) {
      setDatos(null);
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setOcupado(false);
    }
  }

  async function csv() {
    setError(null);
    try {
      await descargarCsvComparar(Number(a), Number(b));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    }
  }

  if (cargando || !usuario) {
    return (
      <Pagina ancho="lg">
        <EsqueletoPagina />
      </Pagina>
    );
  }
  if (usuario.rol !== "docente") {
    return (
      <Pagina ancho="lg">
        <Alerta tipo="advertencia">La comparación de grupos es solo para docentes.</Alerta>
      </Pagina>
    );
  }

  return (
    <Pagina ancho="lg">
      <EncabezadoPagina
        migas={[{ texto: "Panel", href: "/panel" }, { texto: "Comparar grupos" }]}
        titulo="Comparar grupos"
        descripcion="Elige dos de tus cuestionarios (por ejemplo, el original y su versión grupo control) para comparar el intento inicial, el repaso diferido y la retención."
      />

      <Tarjeta>
        <div className="grid gap-4 sm:grid-cols-[1fr_1fr_auto] sm:items-end">
          {(
            [
              ["Grupo A", a, setA],
              ["Grupo B", b, setB],
            ] as const
          ).map(([etiqueta, valor, cambiar]) => (
            <Select key={etiqueta} etiqueta={etiqueta} value={valor} onChange={(e) => cambiar(e.target.value)}>
              <option value="">Elige un cuestionario…</option>
              {lista?.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.titulo}
                  {c.modo === "control" ? " (control)" : ""} · #{c.id}
                </option>
              ))}
            </Select>
          ))}
          <Boton onClick={comparar} cargando={ocupado} disabled={!a || !b || a === b}>
            {ocupado ? "Calculando…" : "Comparar"}
          </Boton>
        </div>
        {a && b && a === b && <p className="mt-3 text-sm font-semibold text-aviso-texto">Elige dos cuestionarios distintos.</p>}
      </Tarjeta>

      {error && <Alerta tipo="error" className="mt-4">{error}</Alerta>}

      {datos && (
        <div className="mt-8 flex flex-col gap-8">
          <section className="flex flex-col gap-4">
            <TituloSeccion>Resultados de la comparación</TituloSeccion>
            <p className="text-xs text-suave">
              A: {datos.a.titulo} · B: {datos.b.titulo}. Media ± desviación estándar muestral. Diferencia = A − B.
            </p>
            {/* Móvil: una tarjeta por medida */}
            <div className="flex flex-col gap-3 lg:hidden">
              <TarjetaMedida nombre="Intento inicial" a={datos.a.inicial} b={datos.b.inicial} efecto={datos.efecto_inicial} />
              <TarjetaMedida nombre="Repaso diferido" a={datos.a.diferido} b={datos.b.diferido} efecto={datos.efecto_diferido} />
              <TarjetaMedida nombre="Retención" a={datos.a.retencion} b={datos.b.retencion} efecto={datos.efecto_retencion} />
            </div>
            {/* Tablet y escritorio: tabla con desplazamiento contenido */}
            <div tabIndex={0} role="region" aria-label="Comparación de grupos" className="hidden overflow-x-auto rounded-2xl border border-borde bg-superficie shadow-tarjeta lg:block">
              <table className="w-full text-sm">
                <caption className="sr-only">Comparación de medidas entre el grupo A y el grupo B</caption>
                <thead className="bg-superficie-2 text-left">
                  <tr>
                    <th scope="col" className="px-3 py-2.5">Medida</th>
                    <th scope="col" className="px-3 py-2.5">n (A)</th>
                    <th scope="col" className="px-3 py-2.5">Media (A)</th>
                    <th scope="col" className="px-3 py-2.5">n (B)</th>
                    <th scope="col" className="px-3 py-2.5">Media (B)</th>
                    <th scope="col" className="px-3 py-2.5">Diferencia</th>
                    <th scope="col" className="px-3 py-2.5">d de Cohen</th>
                    <th scope="col" className="px-3 py-2.5">Interpretación</th>
                  </tr>
                </thead>
                <tbody>
                  <Fila nombre="Intento inicial" a={datos.a.inicial} b={datos.b.inicial} efecto={datos.efecto_inicial} />
                  <Fila nombre="Repaso diferido" a={datos.a.diferido} b={datos.b.diferido} efecto={datos.efecto_diferido} />
                  <Fila nombre="Retención" a={datos.a.retencion} b={datos.b.retencion} efecto={datos.efecto_retencion} />
                </tbody>
              </table>
            </div>
          </section>

          <section className="flex flex-col gap-4" aria-label="Gráfico comparativo">
            <TituloSeccion>Gráfico comparativo</TituloSeccion>
            <div className="grid gap-4 md:grid-cols-3">
              {(["inicial", "diferido", "retencion"] as Metrica[]).map((m) => (
                <Barras key={m} datos={datos} metrica={m} />
              ))}
            </div>
          </section>

          <Alerta tipo="info">{datos.nota}</Alerta>

          <div className="flex flex-col gap-2">
            <Boton onClick={csv} className="self-start">
              <Icono nombre="descargar" /> Descargar CSV (anónimo)
            </Boton>
            <span className="text-xs text-suave">
              El CSV incluye solo a los estudiantes que aceptaron participar en el estudio, identificados como E1, E2…; la tabla de arriba incluye
              a todos los estudiantes de tus cuestionarios.
            </span>
          </div>
        </div>
      )}
    </Pagina>
  );
}

export default function CompararPage() {
  return (
    <Suspense
      fallback={
        <Pagina ancho="lg">
          <EsqueletoPagina />
        </Pagina>
      }
    >
      <Contenido />
    </Suspense>
  );
}
