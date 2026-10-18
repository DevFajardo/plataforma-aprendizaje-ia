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

const ESTUDIANTES = [
  "Retroalimentación al instante, con enlace al minuto exacto del video.",
  "Panel con tu evolución y los temas que más debes reforzar.",
  "Repasos programados para consolidar lo aprendido.",
  "Únete a los cuestionarios de tu docente con un código de 6 caracteres.",
];

const DOCENTES = [
  "Genera un cuestionario completo a partir de cualquier video en minutos.",
  "Edita las preguntas y publícalo con un código para compartir.",
  "Consulta resultados, acierto por pregunta y exporta los datos en CSV.",
  "Mide la ganancia de aprendizaje y la retención de tu grupo.",
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

/** Maqueta decorativa: un video y una pregunta con su retroalimentación. */
function Maqueta() {
  return (
    <div aria-hidden="true" className="relative mx-auto w-full max-w-md">
      <div className="rounded-2xl border border-white/20 bg-white/10 p-3 shadow-2xl backdrop-blur">
        <div className="relative flex aspect-video items-center justify-center rounded-xl bg-cul-azul-oscuro">
          <span className="flex h-14 w-14 items-center justify-center rounded-full bg-cul-naranja text-cul-azul-oscuro">
            <Icono nombre="play" tamano={26} />
          </span>
          <span className="absolute inset-x-4 bottom-3 h-1.5 overflow-hidden rounded-full bg-white/25">
            <span className="block h-full w-1/3 rounded-full bg-cul-amarillo" />
          </span>
        </div>
        <div className="mt-3 rounded-xl bg-white p-4 text-cul-azul-oscuro">
          <p className="text-sm font-bold">¿Cuál es la idea principal del video?</p>
          <div className="mt-3 flex flex-col gap-2 text-xs font-semibold">
            <span className="flex items-center gap-2 rounded-lg border-2 border-[#1e8a4c] bg-[#e3f4e8] px-3 py-2 text-[#0f5e2e]">
              <Icono nombre="check" tamano={14} /> Opción correcta
            </span>
            <span className="rounded-lg border border-[#d3dbe8] px-3 py-2">Otra opción</span>
            <span className="rounded-lg border border-[#d3dbe8] px-3 py-2">Una opción más</span>
          </div>
        </div>
      </div>
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
        <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-4 py-12 sm:px-6 sm:py-16 lg:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)] lg:gap-14 lg:px-8 lg:py-24">
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
                Crear cuenta
              </BotonEnlace>
              <BotonEnlace href="/login" tamano="lg" variante="secundario" className="!border-white/60 !bg-transparent !text-white hover:!bg-white/10 sm:min-w-44">
                Iniciar sesión
              </BotonEnlace>
            </div>
          </div>
          <Maqueta />
        </div>
        <div aria-hidden="true" className="h-1.5 bg-cul-naranja" />
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

      {/* Beneficios */}
      <section aria-labelledby="beneficios" className="bg-superficie-2">
        <div className="mx-auto max-w-6xl px-4 py-12 sm:px-6 sm:py-16 lg:px-8">
          <TituloSeccion className="text-2xl sm:text-3xl">
            <span id="beneficios">Pensada para estudiantes y docentes</span>
          </TituloSeccion>
          <div className="mt-8 grid gap-4 sm:gap-6 md:grid-cols-2">
            <Tarjeta>
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-info-fondo text-info-texto">
                  <Icono nombre="libro" tamano={22} />
                </span>
                <h3 className="text-xl font-bold">Para estudiantes</h3>
              </div>
              <Lista items={ESTUDIANTES} />
            </Tarjeta>
            <Tarjeta>
              <div className="flex items-center gap-3">
                <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-info-fondo text-info-texto">
                  <Icono nombre="grupo" tamano={22} />
                </span>
                <h3 className="text-xl font-bold">Para docentes</h3>
              </div>
              <Lista items={DOCENTES} />
            </Tarjeta>
          </div>
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
              Crear cuenta
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
