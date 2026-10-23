"use client";

import { useEffect, useState } from "react";
import {
  Alerta,
  BarraPorcentaje,
  Boton,
  BotonEnlace,
  EncabezadoPagina,
  EsqueletoPagina,
  EstadoVacio,
  Icono,
  Metrica,
  Pagina,
  Tarjeta,
  TituloSeccion,
  type TonoBarra,
} from "@/components/ui";
import { descargarCsvSus, obtenerResumenSus } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";
import type { ResumenSus } from "@/lib/tipos";

const CATEGORIAS: { nombre: string; rango: string; tono: TonoBarra }[] = [
  { nombre: "Pobre", rango: "< 51", tono: "error" },
  { nombre: "Aceptable bajo", rango: "51 – 68", tono: "aviso" },
  { nombre: "Bueno", rango: "68 – 80,3", tono: "primario" },
  { nombre: "Excelente", rango: "> 80,3", tono: "exito" },
];

export default function ResultadosSusPage() {
  const { usuario, cargando } = useRequiereLogin();
  const [datos, setDatos] = useState<ResumenSus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [descargando, setDescargando] = useState(false);

  useEffect(() => {
    if (usuario?.rol !== "docente") return;
    obtenerResumenSus()
      .then(setDatos)
      .catch((e) => setError(e instanceof Error ? e.message : "Error desconocido"));
  }, [usuario]);

  async function csv() {
    setError(null);
    setDescargando(true);
    try {
      await descargarCsvSus();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setDescargando(false);
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
        <Alerta
          tipo="advertencia"
          acciones={
            <BotonEnlace href="/encuesta" tamano="sm">
              Ir a la encuesta
            </BotonEnlace>
          }
        >
          Los resultados de la encuesta son solo para docentes.
        </Alerta>
      </Pagina>
    );
  }

  const maxDistribucion = datos ? Math.max(1, ...Object.values(datos.distribucion)) : 1;

  return (
    <Pagina ancho="lg">
      <EncabezadoPagina
        migas={[{ texto: "Panel", href: "/panel" }, { texto: "Encuesta SUS" }]}
        titulo="Resultados de la encuesta SUS"
        acciones={
          <Boton onClick={csv} cargando={descargando} disabled={!datos || datos.n === 0}>
            <Icono nombre="descargar" /> {descargando ? "Descargando…" : "Descargar CSV (anónimo)"}
          </Boton>
        }
      />

      {error && <Alerta tipo="error" className="mb-4" reintentar>{error}</Alerta>}
      {!datos && !error && <EsqueletoPagina />}

      {datos && datos.n === 0 && (
        <EstadoVacio icono="promedio" titulo="Aún nadie ha respondido la encuesta">
          Pide a tus estudiantes que la respondan desde la opción «Encuesta» del menú.
        </EstadoVacio>
      )}

      {datos && datos.n > 0 && (
        <div className="flex flex-col gap-8">
          <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-5">
            <Metrica titulo="Respuestas (n)" valor={String(datos.n)} />
            <Metrica titulo="Promedio SUS" valor={String(datos.promedio)} />
            <Metrica titulo="Desviación estándar" valor={String(datos.desviacion)} />
            <Metrica titulo="Mínimo" valor={String(datos.minimo)} />
            <Metrica className="col-span-2 sm:col-span-1" titulo="Máximo" valor={String(datos.maximo)} />
          </div>
          <Alerta tipo="info">
            Interpretación del promedio: <strong>{datos.interpretacion_promedio}</strong>
          </Alerta>

          <section className="flex flex-col gap-4">
            <TituloSeccion>Distribución por interpretación</TituloSeccion>
            <Tarjeta>
              <ul className="flex flex-col gap-5">
                {CATEGORIAS.map((c) => {
                  const cantidad = datos.distribucion[c.nombre] ?? 0;
                  return (
                    <li key={c.nombre}>
                      <div className="mb-1.5 flex justify-between gap-3 text-sm">
                        <span className="font-semibold">
                          {c.nombre} <span className="font-normal text-suave">({c.rango})</span>
                        </span>
                        <span className="font-bold">{cantidad}</span>
                      </div>
                      <BarraPorcentaje valor={cantidad} max={maxDistribucion} etiqueta={`${c.nombre}: ${cantidad} respuestas`} tono={c.tono} alto="lg" />
                    </li>
                  );
                })}
              </ul>
            </Tarjeta>
          </section>

          <section className="flex flex-col gap-4">
            <div>
              <TituloSeccion>Promedio por ítem (1 a 5)</TituloSeccion>
              <p className="mt-2 text-sm text-suave">
                En los ítems impares (positivos) un valor alto es bueno; en los pares (negativos) un valor bajo es bueno.
              </p>
            </div>
            <Tarjeta>
              <ul className="flex flex-col gap-4">
                {datos.promedio_por_item.map((v, i) => (
                  <li key={i}>
                    <div className="mb-1.5 flex justify-between gap-3 text-sm">
                      <span className="font-semibold">
                        Ítem {i + 1} <span className="font-normal text-suave">{(i + 1) % 2 === 1 ? "(positivo)" : "(negativo)"}</span>
                      </span>
                      <span className="font-bold">{v}</span>
                    </div>
                    <BarraPorcentaje valor={v} max={5} etiqueta={`Ítem ${i + 1}`} alto="md" />
                  </li>
                ))}
              </ul>
            </Tarjeta>
          </section>
        </div>
      )}
    </Pagina>
  );
}
