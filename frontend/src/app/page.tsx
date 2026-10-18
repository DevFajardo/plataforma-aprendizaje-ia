"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import EstadoProceso from "@/components/EstadoProceso";
import FormularioArchivo from "@/components/FormularioArchivo";
import FormularioURL from "@/components/FormularioURL";
import Landing from "@/components/Landing";
import { Alerta, EncabezadoPagina, EsqueletoPagina, Icono, Pagina, Pestanas, Tarjeta, type NombreIcono } from "@/components/ui";
import { obtenerTarea, procesarVideo, subirArchivo } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import type { Tarea } from "@/lib/tipos";

const CONSEJOS: { icono: NombreIcono; texto: string }[] = [
  { icono: "video", texto: "Funciona mejor con videos educativos que tengan voz clara." },
  { icono: "reloj", texto: "La generación suele tardar entre uno y dos minutos." },
  { icono: "escudo", texto: "No subas videos con datos personales de otras personas." },
];

function Generador() {
  const router = useRouter();
  const [tarea, setTarea] = useState<Tarea | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [pestana, setPestana] = useState<"youtube" | "archivo">("youtube");
  const [progreso, setProgreso] = useState<number | null>(null);

  const idTarea = tarea?.id;
  const estado = tarea?.estado;
  const enCurso = estado === "pendiente" || estado === "transcribiendo" || estado === "generando";

  // Polling cada 2 s mientras la tarea siga en curso
  useEffect(() => {
    if (!idTarea || !enCurso) return;
    const temporizador = setInterval(async () => {
      try {
        setTarea(await obtenerTarea(idTarea));
      } catch (e) {
        setError(e instanceof Error ? e.message : "Error desconocido");
        setTarea(null);
      }
    }, 2000);
    return () => clearInterval(temporizador);
  }, [idTarea, enCurso]);

  // Al terminar, ir al cuestionario generado
  useEffect(() => {
    if (tarea?.estado === "listo" && tarea.cuestionario_id) {
      router.push(`/cuestionarios/${tarea.cuestionario_id}`);
    }
  }, [tarea, router]);

  async function enviar(url: string, numPreguntas: number) {
    setError(null);
    setTarea(null);
    setEnviando(true);
    try {
      setTarea(await procesarVideo(url, numPreguntas));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setEnviando(false);
    }
  }

  async function enviarArchivo(archivo: File, numPreguntas: number) {
    setError(null);
    setTarea(null);
    setEnviando(true);
    setProgreso(0);
    try {
      setTarea(await subirArchivo(archivo, numPreguntas, setProgreso));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error desconocido");
    } finally {
      setEnviando(false);
      setProgreso(null);
    }
  }

  const bloqueado = enviando || enCurso || tarea?.estado === "listo";

  return (
    <Pagina ancho="xl">
      <EncabezadoPagina
        titulo="Generar cuestionario"
        descripcion="Usa un video de YouTube o Vimeo, o sube tu propio archivo y obtén un resumen y un cuestionario interactivo."
      />

      <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_20rem] lg:items-start">
        <div className="flex min-w-0 flex-col gap-5">
          <Tarjeta>
            <Pestanas
              etiqueta="Origen del video"
              activa={pestana}
              onCambiar={setPestana}
              items={[
                { id: "youtube", texto: "Enlace de YouTube / Vimeo" },
                { id: "archivo", texto: "Subir archivo" },
              ]}
            >
              {pestana === "youtube" ? (
                <FormularioURL deshabilitado={bloqueado} onEnviar={enviar} />
              ) : (
                <FormularioArchivo deshabilitado={bloqueado} progreso={progreso} onEnviar={enviarArchivo} />
              )}
            </Pestanas>
          </Tarjeta>

          {error && <Alerta tipo="error">{error}</Alerta>}
          {tarea && enCurso && <EstadoProceso estado={tarea.estado} />}
          {tarea?.estado === "error" && <Alerta tipo="error">{tarea.mensaje || "Ocurrió un error al procesar el video."}</Alerta>}
        </div>

        <Tarjeta as="aside" aria-label="Consejos" className="bg-superficie-2">
          <h2 className="flex items-center gap-2 font-bold">
            <span aria-hidden="true" className="h-5 w-1.5 rounded-full bg-cul-naranja" />
            Antes de empezar
          </h2>
          <ul className="mt-4 flex flex-col gap-4">
            {CONSEJOS.map((c) => (
              <li key={c.texto} className="flex items-start gap-3 text-sm text-suave">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-info-fondo text-info-texto">
                  <Icono nombre={c.icono} tamano={18} />
                </span>
                <span className="pt-1">{c.texto}</span>
              </li>
            ))}
          </ul>
        </Tarjeta>
      </div>
    </Pagina>
  );
}

export default function Home() {
  const { usuario, cargando } = useAuth();

  if (cargando) {
    return (
      <Pagina ancho="xl">
        <EsqueletoPagina tarjetas={3} />
      </Pagina>
    );
  }
  // Visitantes: página de presentación. Con sesión: pantalla de generar.
  if (!usuario) return <Landing />;
  return <Generador />;
}
