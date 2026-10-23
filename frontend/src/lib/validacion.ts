"use client";

import { useCallback, useRef, useState } from "react";

type Reglas<T> = { [K in keyof T]?: (valor: T[K], todos: T) => string | null };

/**
 * Validación en línea de formularios: errores por campo (al salir del campo y al enviar), mensajes claros
 * y foco automático en el primer campo con error. Se usa con `<form noValidate ref={ref}>`.
 */
export function useValidacion<T extends object>(reglas: Reglas<T>) {
  const [errores, setErrores] = useState<Partial<Record<keyof T, string>>>({});
  const ref = useRef<HTMLFormElement>(null);

  const validarCampo = useCallback(
    (campo: keyof T, valores: T) => {
      const mensaje = reglas[campo]?.(valores[campo], valores) ?? null;
      setErrores((e) => {
        const siguiente = { ...e };
        if (mensaje) siguiente[campo] = mensaje;
        else delete siguiente[campo];
        return siguiente;
      });
      return mensaje;
    },
    [reglas],
  );

  const validarTodo = useCallback(
    (valores: T) => {
      const nuevo: Partial<Record<keyof T, string>> = {};
      for (const campo of Object.keys(reglas) as (keyof T)[]) {
        const mensaje = reglas[campo]?.(valores[campo], valores) ?? null;
        if (mensaje) nuevo[campo] = mensaje;
      }
      setErrores(nuevo);
      const hay = Object.keys(nuevo).length > 0;
      if (hay) {
        // Espera al render para que aria-invalid ya esté en el DOM y enfoca el primer campo con error.
        requestAnimationFrame(() => ref.current?.querySelector<HTMLElement>('[aria-invalid="true"]')?.focus());
      }
      return !hay;
    },
    [reglas],
  );

  const limpiar = useCallback((campo: keyof T) => {
    setErrores((e) => {
      if (!e[campo]) return e;
      const siguiente = { ...e };
      delete siguiente[campo];
      return siguiente;
    });
  }, []);

  return { errores, ref, validarCampo, validarTodo, limpiar };
}

export const REGEX_CORREO = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;
