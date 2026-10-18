import { useId, type InputHTMLAttributes, type ReactNode, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";
import { cx } from "./cx";

const CONTROL =
  "w-full min-h-11 rounded-lg border bg-superficie px-3.5 py-2.5 text-base text-texto transition duration-150 " +
  "placeholder:text-suave/80 hover:border-anillo focus-visible:border-anillo focus-visible:ring-2 focus-visible:ring-anillo/40 " +
  "disabled:cursor-not-allowed disabled:opacity-60";

/** Clase de un control de formulario, por si hace falta aplicarla a un elemento propio. */
export function claseControl(conError = false, extra?: string) {
  return cx(CONTROL, conError ? "border-error-solido" : "border-borde-fuerte", extra);
}

interface CamposComunes {
  etiqueta: string;
  /** Oculta la etiqueta visualmente pero la mantiene para lectores de pantalla. */
  ocultarEtiqueta?: boolean;
  ayuda?: ReactNode;
  error?: string | null;
  /** Clase del contenedor (p. ej. para fijar ancho). */
  claseCampo?: string;
}

function Envoltura({
  id,
  etiqueta,
  ocultarEtiqueta,
  ayuda,
  error,
  claseCampo,
  children,
}: CamposComunes & { id: string; children: ReactNode }) {
  return (
    <div className={cx("flex min-w-0 flex-col gap-1.5", claseCampo)}>
      <label htmlFor={id} className={cx("text-sm font-semibold", ocultarEtiqueta && "sr-only")}>
        {etiqueta}
      </label>
      {children}
      {ayuda && (
        <p id={`${id}-ayuda`} className="text-xs text-suave">
          {ayuda}
        </p>
      )}
      {error && (
        <p id={`${id}-error`} role="alert" className="text-sm font-medium text-error-texto">
          {error}
        </p>
      )}
    </div>
  );
}

function descripciones(id: string, ayuda: unknown, error: unknown) {
  const ids = [ayuda ? `${id}-ayuda` : "", error ? `${id}-error` : ""].filter(Boolean).join(" ");
  return ids || undefined;
}

export interface PropsInput extends Omit<InputHTMLAttributes<HTMLInputElement>, "className">, CamposComunes {
  className?: string;
}

/** Campo de texto con etiqueta, ayuda y error. */
export function Input({ etiqueta, ocultarEtiqueta, ayuda, error, claseCampo, className, id: idProp, ...resto }: PropsInput) {
  const auto = useId();
  const id = idProp ?? auto;
  return (
    <Envoltura {...{ id, etiqueta, ocultarEtiqueta, ayuda, error, claseCampo }}>
      <input
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={descripciones(id, ayuda, error)}
        className={claseControl(!!error, className)}
        {...resto}
      />
    </Envoltura>
  );
}

export interface PropsSelect extends Omit<SelectHTMLAttributes<HTMLSelectElement>, "className">, CamposComunes {
  className?: string;
}

/** Lista desplegable con etiqueta, ayuda y error. */
export function Select({ etiqueta, ocultarEtiqueta, ayuda, error, claseCampo, className, id: idProp, children, ...resto }: PropsSelect) {
  const auto = useId();
  const id = idProp ?? auto;
  return (
    <Envoltura {...{ id, etiqueta, ocultarEtiqueta, ayuda, error, claseCampo }}>
      <select
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={descripciones(id, ayuda, error)}
        className={claseControl(!!error, cx("pr-9", className))}
        {...resto}
      >
        {children}
      </select>
    </Envoltura>
  );
}

export interface PropsTextarea extends Omit<TextareaHTMLAttributes<HTMLTextAreaElement>, "className">, CamposComunes {
  className?: string;
}

/** Área de texto con etiqueta, ayuda y error. */
export function Textarea({ etiqueta, ocultarEtiqueta, ayuda, error, claseCampo, className, id: idProp, ...resto }: PropsTextarea) {
  const auto = useId();
  const id = idProp ?? auto;
  return (
    <Envoltura {...{ id, etiqueta, ocultarEtiqueta, ayuda, error, claseCampo }}>
      <textarea
        id={id}
        aria-invalid={error ? true : undefined}
        aria-describedby={descripciones(id, ayuda, error)}
        className={claseControl(!!error, cx("leading-relaxed", className))}
        {...resto}
      />
    </Envoltura>
  );
}

interface PropsCasilla extends Omit<InputHTMLAttributes<HTMLInputElement>, "className" | "type"> {
  children: ReactNode;
}

/** Casilla de verificación con área tocable amplia. */
export function Casilla({ children, ...resto }: PropsCasilla) {
  return (
    <label className="flex cursor-pointer items-start gap-3 rounded-lg py-1.5 text-sm leading-relaxed">
      <input type="checkbox" className="mt-0.5 h-5 w-5 shrink-0 cursor-pointer accent-primario" {...resto} />
      <span className="min-w-0">{children}</span>
    </label>
  );
}
