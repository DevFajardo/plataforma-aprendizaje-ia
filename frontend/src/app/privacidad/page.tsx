import type { Metadata } from "next";
import { Alerta, EncabezadoPagina, Enlace, Pagina, Tarjeta, TituloSeccion } from "@/components/ui";

export const metadata: Metadata = {
  title: "Política de tratamiento de datos personales",
  description: "Política de tratamiento de datos personales de la Plataforma de Aprendizaje Activo con IA (proyecto académico).",
};

export default function PrivacidadPage() {
  return (
    <Pagina ancho="lg">
      <EncabezadoPagina migas={[{ texto: "Inicio", href: "/" }, { texto: "Privacidad" }]} titulo="Política de tratamiento de datos personales" />
      <Alerta tipo="advertencia" titulo="Aviso" className="mb-6">
        Esta plataforma es un <strong>proyecto académico universitario</strong>, no un servicio comercial. Esta política describe cómo se tratan los
        datos personales dentro de ese proyecto, en cumplimiento de la Ley Estatutaria 1581 de 2012 y del Decreto 1377 de 2013 de la República de
        Colombia (régimen general de protección de datos personales).
      </Alerta>

      <Tarjeta>
      <div className="flex flex-col gap-8 leading-relaxed">
        <section>
          <TituloSeccion className="mb-3">1. Responsable del tratamiento</TituloSeccion>
          <p>
            El responsable del tratamiento es el equipo estudiantil que desarrolla el proyecto académico «Plataforma de
            Aprendizaje Activo con IA», en el marco de una asignatura universitaria. No existe una persona jurídica
            comercial detrás de la plataforma. Para cualquier solicitud relacionada con tus datos puedes escribir a:{" "}
            <strong>emmanuel.fajardo@ul.edu.co</strong>.
          </p>
        </section>

        <section>
          <TituloSeccion className="mb-3">2. Finalidad del tratamiento</TituloSeccion>
          <p className="mb-2">Los datos personales se tratan exclusivamente con fines académicos y de investigación educativa:</p>
          <ul className="list-disc space-y-1 pl-6">
            <li>Crear y administrar tu cuenta y permitirte usar las funciones de la plataforma (generar, responder y compartir cuestionarios).</li>
            <li>Calificar tus intentos, mostrarte tu progreso y programar repasos diferidos.</li>
            <li>Permitir que el docente creador de un cuestionario vea los resultados de los estudiantes que lo responden.</li>
            <li>
              Evaluar la usabilidad y la efectividad de la plataforma (encuesta de usabilidad SUS, comparación de la
              retención entre grupos), <strong>solo si tú lo autorizas</strong> de forma expresa y, en ese caso, con
              datos anonimizados en los reportes y exportaciones.
            </li>
          </ul>
          <p className="mt-2">No se usan tus datos para publicidad, perfilamiento comercial ni se venden a terceros.</p>
        </section>

        <section>
          <TituloSeccion className="mb-3">3. Datos que se recolectan</TituloSeccion>
          <ul className="list-disc space-y-1 pl-6">
            <li>Datos de la cuenta: nombre, correo electrónico, rol (estudiante o docente) y contraseña (almacenada solo como un resumen cifrado, nunca en texto legible).</li>
            <li>Datos de uso académico: cuestionarios generados, intentos, respuestas, puntajes, repasos programados y fechas.</li>
            <li>Respuestas de la encuesta de usabilidad SUS y tu comentario opcional.</li>
            <li>Para docentes: tiempo activo de edición de tus cuestionarios y, de forma opcional, tu estimación del tiempo que tomaría crearlos manualmente.</li>
            <li>Videos o archivos de audio que decidas subir, y la transcripción generada a partir de ellos.</li>
            <li>Tus decisiones de consentimiento y la fecha en que las registraste.</li>
          </ul>
          <p className="mt-2">No se recolectan datos sensibles ni datos de menores de edad de manera intencional.</p>
        </section>

        <section>
          <TituloSeccion className="mb-3">4. Servicios de terceros (inteligencia artificial)</TituloSeccion>
          <p>
            Para generar el resumen y el cuestionario, el <strong>texto de la transcripción de los videos</strong> se envía
            a servicios de inteligencia artificial de terceros: <strong>Google Gemini</strong> y <strong>Groq</strong> (que
            también se usa para transcribir audio con Whisper). Estos proveedores operan en el exterior y su{" "}
            <strong>plan gratuito puede utilizar los datos enviados para mejorar sus propios servicios</strong>. Por esta
            razón, <strong>no subas videos ni audios que contengan datos personales, información confidencial o sensible</strong>{" "}
            (por ejemplo, grabaciones de clases con nombres, voces o datos de otras personas sin su autorización). Al subir
            un contenido declaras que tienes derecho a usarlo y que no incluye ese tipo de información.
          </p>
        </section>

        <section>
          <TituloSeccion className="mb-3">5. Derechos del titular (hábeas data)</TituloSeccion>
          <p className="mb-2">De acuerdo con la Ley 1581 de 2012, tienes derecho a:</p>
          <ul className="list-disc space-y-1 pl-6">
            <li><strong>Conocer</strong> los datos que se tienen sobre ti: en «Mi cuenta» puedes usar «Descargar mis datos».</li>
            <li><strong>Actualizar y rectificar</strong> tus datos: puedes cambiar tu nombre y tu contraseña en «Mi cuenta».</li>
            <li><strong>Suprimir</strong> tus datos y revocar la autorización: la opción «Eliminar mi cuenta» borra de forma definitiva tu cuenta, intentos, repasos, encuesta, tareas, los cuestionarios que creaste (con sus preguntas) y los archivos que subiste.</li>
            <li><strong>Revocar</strong> en cualquier momento el consentimiento de participación en el estudio, sin que ello afecte el uso de la plataforma.</li>
            <li>Ser informado, previa solicitud, sobre el uso que se ha dado a tus datos, y presentar quejas ante la Superintendencia de Industria y Comercio.</li>
          </ul>
          <p className="mt-2">
            También puedes ejercer estos derechos escribiendo a <strong>emmanuel.fajardo@ul.edu.co</strong>.
          </p>
        </section>

        <section>
          <TituloSeccion className="mb-3">6. Consentimiento</TituloSeccion>
          <p>
            Para crear una cuenta es obligatorio aceptar esta política. La participación en el estudio de evaluación es{" "}
            <strong>voluntaria</strong>: si no la autorizas, podrás usar la plataforma con normalidad y tus resultados
            no se incluirán en las exportaciones con fines de investigación. Los docentes pueden ver los resultados de sus
            propios cursos independientemente de esta autorización, porque forman parte de la función docente.
          </p>
        </section>

        <section>
          <TituloSeccion className="mb-3">7. Seguridad y conservación</TituloSeccion>
          <p>
            Las contraseñas se almacenan cifradas, las sesiones usan tokens firmados con expiración y cada recurso
            comprueba que quien lo consulta tenga permiso. Los datos se conservan mientras tu cuenta exista o hasta que
            el proyecto académico concluya; al terminar el proyecto, la base de datos se eliminará o se anonimizará. Dado
            su carácter académico y el uso de planes gratuitos, no se garantiza disponibilidad continua del servicio.
          </p>
        </section>

        <section>
          <TituloSeccion className="mb-3">8. Cambios a esta política</TituloSeccion>
          <p>
            Esta política puede actualizarse durante el desarrollo del proyecto. Los cambios sustanciales se informarán en
            la plataforma. Última actualización: octubre de 2026.
          </p>
        </section>
      </div>

      </Tarjeta>

      <p className="mt-8 flex flex-wrap gap-x-4 text-sm">
        <Enlace href="/registro">Volver al registro</Enlace>
        <Enlace href="/cuenta">Mi cuenta</Enlace>
      </p>
    </Pagina>
  );
}
