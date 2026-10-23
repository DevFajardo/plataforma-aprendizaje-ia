import Image from "next/image";
import { BotonEnlace, Icono, Tarjeta, TituloSeccion, type NombreIcono } from "./ui";

const PASOS: { icono: NombreIcono; titulo: string; texto: string }[] = [
  {
    icono: "enlace",
    titulo: "Pega el enlace o sube el video",
    texto: "Usa un video de YouTube o Vimeo, o sube tu propio archivo de video o audio.",
  },
  {
    icono: "chispa",
    titulo: "La IA transcribe y genera",
    texto: "En minutos obtienes un resumen, las ideas clave y un cuestionario con preguntas variadas.",
  },
  {
    icono: "trofeo",
    titulo: "Responde y aprende",
    texto: "Recibe retroalimentación inmediata con la marca de tiempo del video donde se explica cada tema.",
  },
];

// Cifras verificables del proyecto (no son métricas de uso).
const CIFRAS: { valor: string; etiqueta: string; detalle: string }[] = [
  { valor: "317", etiqueta: "pruebas automáticas", detalle: "en el servidor, en cada cambio" },
  { valor: "WCAG 2.1 AA", etiqueta: "accesibilidad", detalle: "verificada con axe-core y Lighthouse" },
  { valor: "$0", etiqueta: "de costo de operación", detalle: "todo el stack usa planes gratuitos" },
  { valor: "3", etiqueta: "proveedores de IA", detalle: "con respaldo automático si uno falla" },
];

interface Destacada {
  id: string;
  icono: NombreIcono;
  titulo: string;
  texto: string;
  puntos: string[];
  imagen: string;
  alt: string;
  ancho: number;
  alto: number;
  movil?: boolean;
}

const DESTACADAS: Destacada[] = [
  {
    id: "tutor",
    icono: "chispa",
    titulo: "Tutor de IA que responde con lo que dice el video",
    texto: "Pregúntale al video: el tutor contesta solo con el contenido de la transcripción y cita el minuto exacto para que verifiques.",
    puntos: ["Citas con marca de tiempo que llevan al momento del video", "No inventa: si el video no lo dice, te lo indica", "Transcripción completa y resumen con ideas clave"],
    imagen: "/capturas/visor.webp",
    alt: "Pantalla de un cuestionario con el video, el resumen y el tutor de IA",
    ancho: 1280,
    alto: 800,
  },
  {
    id: "vivo",
    icono: "grupo",
    titulo: "Clase en vivo, sin instalar nada",
    texto: "El docente proyecta un PIN y un código QR; el grupo responde desde el celular, con apodo y sin crear cuenta.",
    puntos: ["Preguntas con cuenta regresiva y retroalimentación al instante", "Podio y distribución de respuestas en tiempo real", "Historial de cada clase para analizar después"],
    imagen: "/capturas/vivo.webp",
    alt: "Pantalla de celular con una pregunta de clase en vivo y cuatro opciones de colores",
    ancho: 540,
    alto: 1066,
    movil: true,
  },
  {
    id: "resultados",
    icono: "promedio",
    titulo: "Resultados de aprendizaje que se entienden",
    texto: "Acierto por pregunta, análisis de ítems, ganancia de aprendizaje y retención, listos para decidir qué reforzar.",
    puntos: ["Semáforo por resultado de aprendizaje y nivel de Bloom", "Alertas tempranas de estudiantes en riesgo", "Exportación a CSV y PDF"],
    imagen: "/capturas/resultados.webp",
    alt: "Pantalla de resultados de un cuestionario con ganancia de aprendizaje, retención y análisis de ítems",
    ancho: 1280,
    alto: 800,
  },
];

const HEROE = {
  imagen: "/capturas/panel.webp",
  alt: "Panel del docente con el resumen de cuestionarios publicados, estudiantes e intentos",
  ancho: 1280,
  alto: 800,
};

const ROLES: { icono: NombreIcono; titulo: string; items: string[] }[] = [
  {
    icono: "libro",
    titulo: "Para estudiantes",
    items: [
      "Retroalimentación al instante, con enlace al minuto exacto del video.",
      "Panel con tu evolución y los temas que más debes reforzar.",
      "Repasos programados para consolidar lo aprendido.",
      "Únete a los cuestionarios de tu docente con un código de 6 caracteres.",
    ],
  },
  {
    icono: "usuario",
    titulo: "Para docentes",
    items: [
      "Genera un cuestionario completo a partir de cualquier video en minutos.",
      "Edita las preguntas y publícalo con un código para compartir.",
      "Dirige clases en vivo y consulta resultados por pregunta.",
      "Mide la ganancia de aprendizaje y la retención de tu grupo.",
    ],
  },
  {
    icono: "escudo",
    titulo: "Para la institución",
    items: [
      "Logro por resultado de aprendizaje de cada programa y asignatura.",
      "Tendencia semanal y alertas tempranas para el acompañamiento.",
      "Estructura académica administrable: facultades, programas y asignaturas.",
      "Informe PDF para coordinación y acreditación.",
    ],
  },
];

function Lista({ items }: { items: string[] }) {
  return (
    <ul className="mt-4 flex flex-col gap-3">
      {items.map((t) => (
        <li key={t} className="flex items-start gap-3">
          <span className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-exito-fondo text-exito-texto">
            <Icono nombre="check" tamano={14} />
          </span>
          <span className="text-suave">{t}</span>
        </li>
      ))}
    </ul>
  );
}

/** Marco de navegador con una captura real del producto. */
function Captura({ d, prioridad = false }: { d: Pick<Destacada, "imagen" | "alt" | "ancho" | "alto" | "movil">; prioridad?: boolean }) {
  if (d.movil) {
    return (
      <div className="mx-auto w-56 overflow-hidden rounded-[2rem] border-[6px] border-cul-azul-oscuro bg-cul-azul-oscuro shadow-xl sm:w-64">
        <Image src={d.imagen} alt={d.alt} width={d.ancho} height={d.alto} sizes="256px" className="h-auto w-full rounded-[1.5rem]" priority={prioridad} />
      </div>
    );
  }
  return (
    <div className="overflow-hidden rounded-2xl border border-borde bg-superficie shadow-xl">
      <div aria-hidden="true" className="flex items-center gap-1.5 border-b border-borde bg-superficie-2 px-4 py-2.5">
        <span className="h-2.5 w-2.5 rounded-full bg-borde-fuerte/60" />
        <span className="h-2.5 w-2.5 rounded-full bg-borde-fuerte/60" />
        <span className="h-2.5 w-2.5 rounded-full bg-borde-fuerte/60" />
      </div>
      <Image
        src={d.imagen}
        alt={d.alt}
        width={d.ancho}
        height={d.alto}
        sizes="(min-width: 1024px) 560px, calc(100vw - 2rem)"
        className="h-auto w-full"
        priority={prioridad}
      />
    </div>
  );
}

/** Página de inicio para visitantes sin sesión. */
export default function Landing() {
  return (
    <main id="contenido" tabIndex={-1} className="flex-1 outline-none">
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-cul-azul via-cul-azul to-cul-marino text-white">
        <div aria-hidden="true" className="pointer-events-none absolute -right-32 -top-32 h-96 w-96 rounded-full border-[40px] border-white/5" />
        <div aria-hidden="true" className="pointer-events-none absolute -bottom-40 left-1/3 h-96 w-96 rounded-full border-[40px] border-cul-cian/10" />
        <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-4 py-12 sm:px-6 sm:py-16 lg:grid-cols-[minmax(0,1fr)_minmax(0,1fr)] lg:gap-12 lg:px-8 lg:py-20">
          <div>
            <p className="inline-flex items-center gap-2 rounded-full border border-white/30 bg-white/10 px-3 py-1 text-xs font-semibold sm:text-sm">
              <span aria-hidden="true" className="h-2 w-2 rounded-full bg-cul-naranja" />
              Proyecto académico · Ingeniería de Sistemas y Computación
            </p>
            <h1 className="mt-5 text-3xl font-extrabold leading-tight tracking-tight sm:text-4xl lg:text-5xl">
              Convierte cualquier video en un <span className="text-cul-amarillo-vivo">cuestionario interactivo</span> con IA
            </h1>
            <span aria-hidden="true" className="mt-5 block h-1 w-20 rounded-full bg-cul-naranja" />
            <p className="mt-5 max-w-xl text-base text-white/90 sm:text-lg">
              Pega el enlace de un video de YouTube o Vimeo, o sube tu archivo. La plataforma genera un resumen, las ideas clave y preguntas para
              que aprendas de forma activa, con retroalimentación inmediata.
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <BotonEnlace
                href="/registro"
                tamano="lg"
                className="!border-transparent !bg-cul-naranja !text-cul-azul-oscuro hover:brightness-110 sm:min-w-44"
              >
                Crear cuenta gratis
              </BotonEnlace>
              <BotonEnlace href="/login" tamano="lg" variante="secundario" className="!border-white/60 !bg-transparent !text-white hover:!bg-white/10 sm:min-w-44">
                Iniciar sesión
              </BotonEnlace>
            </div>
            <p className="mt-4 text-sm text-white/80">Sin tarjeta de crédito. Tus datos se tratan conforme a la Ley 1581 de 2012.</p>
          </div>
          <div className="rounded-2xl bg-white/10 p-2 shadow-2xl backdrop-blur sm:p-3">
            <Captura d={HEROE} prioridad />
          </div>
        </div>
        <div aria-hidden="true" className="h-1.5 bg-cul-naranja" />
      </section>

      {/* Cifras verificables */}
      <section aria-label="El proyecto en cifras" className="border-b border-borde bg-superficie">
        <ul className="mx-auto grid max-w-6xl grid-cols-2 gap-x-4 gap-y-6 px-4 py-8 sm:px-6 lg:grid-cols-4 lg:px-8">
          {CIFRAS.map((c) => (
            <li key={c.etiqueta} className="min-w-0">
              <p className="text-2xl font-extrabold tracking-tight text-enlace sm:text-3xl">{c.valor}</p>
              <p className="text-sm font-semibold text-texto">{c.etiqueta}</p>
              <p className="text-xs text-suave">{c.detalle}</p>
            </li>
          ))}
        </ul>
      </section>

      {/* Cómo funciona */}
      <section aria-labelledby="como-funciona" className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
        <TituloSeccion className="text-2xl sm:text-3xl">
          <span id="como-funciona">Cómo funciona</span>
        </TituloSeccion>
        <p className="mt-3 max-w-2xl text-suave">Tres pasos para pasar de un video a una experiencia de aprendizaje activo.</p>
        <ol className="mt-8 grid gap-4 sm:gap-6 md:grid-cols-3">
          {PASOS.map((p, i) => (
            <li key={p.titulo}>
              <Tarjeta interactiva className="relative h-full">
                <span className="absolute right-4 top-3 text-5xl font-extrabold text-borde" aria-hidden="true">
                  {i + 1}
                </span>
                <span className="flex h-12 w-12 items-center justify-center rounded-xl border-b-[3px] border-cul-naranja bg-info-fondo text-info-texto">
                  <Icono nombre={p.icono} tamano={24} />
                </span>
                <h3 className="mt-4 text-lg font-bold">
                  <span className="sr-only">Paso {i + 1}: </span>
                  {p.titulo}
                </h3>
                <p className="mt-2 text-suave">{p.texto}</p>
              </Tarjeta>
            </li>
          ))}
        </ol>
      </section>

      {/* Características destacadas */}
      <section aria-labelledby="caracteristicas" className="bg-superficie-2">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
          <TituloSeccion className="text-2xl sm:text-3xl">
            <span id="caracteristicas">Lo que la hace distinta</span>
          </TituloSeccion>
          <p className="mt-3 max-w-2xl text-suave">Capturas reales de la plataforma, con datos de demostración.</p>
          <div className="mt-10 flex flex-col gap-14 sm:gap-20">
            {DESTACADAS.map((d, i) => (
              <article key={d.id} className="grid items-center gap-8 lg:grid-cols-2 lg:gap-14">
                <div className={i % 2 === 1 ? "lg:order-2" : undefined}>
                  <span className="flex h-12 w-12 items-center justify-center rounded-xl border-b-[3px] border-cul-naranja bg-info-fondo text-info-texto">
                    <Icono nombre={d.icono} tamano={24} />
                  </span>
                  <h3 className="mt-4 text-xl font-bold tracking-tight sm:text-2xl">{d.titulo}</h3>
                  <p className="mt-3 text-suave">{d.texto}</p>
                  <Lista items={d.puntos} />
                </div>
                <div className={i % 2 === 1 ? "lg:order-1" : undefined}>
                  <Captura d={d} />
                </div>
              </article>
            ))}
          </div>
        </div>
      </section>

      {/* Por rol */}
      <section aria-labelledby="por-rol" className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
        <TituloSeccion className="text-2xl sm:text-3xl">
          <span id="por-rol">Pensada para toda la comunidad académica</span>
        </TituloSeccion>
        <div className="mt-8 grid gap-4 sm:gap-6 lg:grid-cols-3">
          {ROLES.map((r) => (
            <Tarjeta key={r.titulo}>
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-info-fondo text-info-texto">
                  <Icono nombre={r.icono} tamano={22} />
                </span>
                <h3 className="text-xl font-bold">{r.titulo}</h3>
              </div>
              <Lista items={r.items} />
            </Tarjeta>
          ))}
        </div>
      </section>

      {/* Confianza */}
      <section aria-labelledby="confianza" className="bg-superficie-2">
        <div className="mx-auto grid max-w-6xl items-center gap-6 px-4 py-12 sm:px-6 sm:py-14 lg:grid-cols-[auto_1fr_auto] lg:gap-8 lg:px-8">
          <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-info-fondo text-info-texto">
            <Icono nombre="escudo" tamano={28} />
          </span>
          <div>
            <h2 id="confianza" className="text-xl font-bold sm:text-2xl">
              Tus datos, bajo tu control
            </h2>
            <p className="mt-2 max-w-3xl text-suave">
              La calificación se hace en el servidor, el consentimiento de investigación es opcional y desde «Mi cuenta» puedes descargar tus datos o eliminar
              tu cuenta cuando quieras, conforme a la Ley 1581 de 2012.
            </p>
          </div>
          <BotonEnlace href="/privacidad" variante="secundario">
            Leer la política de datos
          </BotonEnlace>
        </div>
      </section>

      {/* CTA final */}
      <section className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
        <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-cul-azul to-cul-marino px-6 py-10 text-center text-white sm:px-12 sm:py-14">
          <div aria-hidden="true" className="absolute inset-x-0 bottom-0 h-1.5 bg-cul-naranja" />
          <h2 className="text-2xl font-extrabold sm:text-3xl">Empieza a aprender de forma activa</h2>
          <p className="mx-auto mt-3 max-w-xl text-white/90">Crear una cuenta es gratis y toma menos de un minuto.</p>
          <div className="mt-7 flex flex-col justify-center gap-3 sm:flex-row">
            <BotonEnlace href="/registro" tamano="lg" className="!border-transparent !bg-cul-naranja !text-cul-azul-oscuro hover:brightness-110">
              Crear cuenta gratis
            </BotonEnlace>
            <BotonEnlace href="/login" tamano="lg" variante="secundario" className="!border-white/60 !bg-transparent !text-white hover:!bg-white/10">
              Iniciar sesión
            </BotonEnlace>
          </div>
        </div>
      </section>
    </main>
  );
}
