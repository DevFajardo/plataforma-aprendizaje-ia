/** Mensaje breve de estado de un formulario (éxito o error). Para mensajes destacados usa <Alerta>. */
export type MensajeForm = { tipo: "ok" | "error"; texto: string } | null;

export default function Aviso({ mensaje }: { mensaje: MensajeForm }) {
  if (!mensaje) return null;
  return (
    <p
      role={mensaje.tipo === "error" ? "alert" : "status"}
      className={"text-sm font-semibold " + (mensaje.tipo === "error" ? "text-error-texto" : "text-exito-texto")}
    >
      <span aria-hidden="true">{mensaje.tipo === "ok" ? "✓ " : "⚠ "}</span>
      {mensaje.texto}
    </p>
  );
}
