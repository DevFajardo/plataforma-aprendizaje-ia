import type { Rol } from "./tipos";

/** Un paso del tutorial de primer uso. `objetivo` es el valor de `data-tutorial` del elemento real que se destaca. */
export interface PasoTutorial {
  titulo: string;
  texto: string;
  /** Elemento a destacar; sin él, la tarjeta se muestra centrada. Si no está visible (p. ej. en móvil), se usa el respaldo. */
  objetivo?: string;
  /** Texto alternativo cuando el elemento no es visible en este tamaño de pantalla. */
  textoMovil?: string;
}

export const ROLES_CON_TUTORIAL: Rol[] = ["estudiante", "docente", "coordinador"];

const USUARIO: PasoTutorial = {
  titulo: "Tu cuenta",
  objetivo: "usuario",
  texto: "Desde «Mi cuenta» editas tus datos, descargas tu información y puedes volver a ver este tutorial cuando quieras.",
};

const CAMPANA: PasoTutorial = {
  titulo: "Notificaciones",
  objetivo: "campana",
  texto: "La campana te avisa de cuestionarios nuevos, repasos pendientes y novedades de tus grupos.",
};

export const TUTORIALES: Partial<Record<Rol, PasoTutorial[]>> = {
  estudiante: [
    {
      titulo: "Bienvenido/a a Aprendizaje Activo",
      texto: "En menos de un minuto te mostramos lo esencial: aprender con videos, responder cuestionarios y ver tu progreso.",
    },
    {
      titulo: "Genera un cuestionario desde un video",
      objetivo: "nav-/",
      texto: "Pega el enlace de un video de YouTube o Vimeo, o sube un archivo. La IA prepara un resumen y preguntas para practicar.",
    },
    {
      titulo: "Únete a una clase o a un grupo",
      objetivo: "nav-/unirse",
      texto: "Con el código de tu grupo accedes a los cuestionarios de tu docente; con el PIN entras a una clase en vivo desde el celular.",
    },
    {
      titulo: "Tus cursos",
      objetivo: "nav-/mis-cursos",
      texto: "Aquí ves los cuestionarios publicados en tus cursos y cuáles tienes pendientes.",
    },
    CAMPANA,
    {
      titulo: "Tu progreso en el panel",
      objetivo: "nav-/panel",
      texto: "El panel muestra tus resultados, tu evolución y los repasos que debes hacer unos días después para fijar lo aprendido.",
    },
    USUARIO,
  ],
  docente: [
    {
      titulo: "Bienvenido/a, docente",
      texto: "Te mostramos cómo convertir un video en una evaluación, compartirla con tus grupos y analizar los resultados.",
    },
    {
      titulo: "Genera desde un video o archivo",
      objetivo: "nav-/",
      texto: "Pega un enlace de YouTube o Vimeo, o sube un archivo de audio o video. La IA crea el resumen y las preguntas con su verificación.",
    },
    {
      titulo: "Edita, publica y analiza",
      objetivo: "nav-/cuestionarios",
      texto: "En «Mis cuestionarios» editas las preguntas, las publicas, lanzas una clase en vivo y revisas resultados, análisis de ítems y respuestas abiertas.",
    },
    {
      titulo: "Cursos y grupos",
      objetivo: "nav-/cursos",
      texto: "Crea tus grupos por asignatura y periodo, comparte el código de ingreso y asigna cuestionarios a cada grupo.",
    },
    {
      titulo: "Banco de preguntas",
      objetivo: "nav-/banco",
      texto: "Guarda tus mejores preguntas y reutilízalas en otros cuestionarios, con su resultado de aprendizaje y nivel de Bloom.",
    },
    CAMPANA,
    USUARIO,
  ],
  coordinador: [
    {
      titulo: "Bienvenido/a, coordinación",
      texto: "Esta vista te ayuda a seguir el logro de los resultados de aprendizaje de tu programa y a detectar a tiempo a quienes necesitan apoyo.",
    },
    {
      titulo: "Panel de coordinación",
      objetivo: "nav-/coordinacion",
      texto: "Consulta el logro por resultado de aprendizaje, por nivel de Bloom y por asignatura, con su tendencia semanal y las alertas tempranas.",
    },
    {
      titulo: "Banco institucional",
      objetivo: "nav-/banco",
      texto: "Revisa las preguntas compartidas por los docentes, filtradas por resultado de aprendizaje y asignatura.",
    },
    CAMPANA,
    {
      titulo: "Encuesta de usabilidad",
      objetivo: "nav-/encuesta",
      texto: "La encuesta SUS mide qué tan fácil de usar es la plataforma. Los resultados son anónimos.",
    },
    USUARIO,
  ],
};
