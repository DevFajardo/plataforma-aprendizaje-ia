import type { FormEvent, ReactNode } from "react";
import Boton from "./Boton";

interface Props {
  mensaje: ReactNode;
  textoConfirmar: string;
  textoOcupado?: string;
  ocupado?: boolean;
  onConfirmar?: () => void;
  onCancelar: () => void;
  /** Contenido extra (p. ej. campo de contraseña). */
  children?: ReactNode;
  /** Si se pasa, se renderiza como <form> y el botón de confirmar es de envío. */
  alEnviar?: (e: FormEvent) => void;
}

/** Confirmación sin ventana modal: aparece dentro de la propia tarjeta. Botones apilados en móvil. */
export default function ConfirmacionEnLinea({ mensaje, textoConfirmar, textoOcupado, ocupado, onConfirmar, onCancelar, children, alEnviar }: Props) {
  const contenido = (
    <>
      <div className="text-sm font-medium">{mensaje}</div>
      {children}
      <div className="flex flex-col gap-2 sm:flex-row">
        <Boton
          type={alEnviar ? "submit" : "button"}
          onClick={alEnviar ? undefined : onConfirmar}
          cargando={ocupado}
          variante="peligro"
        >
          {ocupado && textoOcupado ? textoOcupado : textoConfirmar}
        </Boton>
        <Boton variante="secundario" disabled={ocupado} onClick={onCancelar}>
          Cancelar
        </Boton>
      </div>
    </>
  );
  const clase = "flex flex-col gap-3 rounded-xl border border-error-borde bg-error-fondo p-4 text-error-texto";
  return alEnviar ? (
    <form role="alertdialog" onSubmit={alEnviar} className={clase}>
      {contenido}
    </form>
  ) : (
    <div role="alertdialog" className={clase}>
      {contenido}
    </div>
  );
}
