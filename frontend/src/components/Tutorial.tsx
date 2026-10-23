"use client";

import { usePathname } from "next/navigation";
import { Suspense, createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type CSSProperties, type KeyboardEvent, type ReactNode } from "react";
import { marcarTutorial } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { TUTORIALES } from "@/lib/tutoriales";
import { Boton, cx } from "./ui";

/**
 * Tutorial guiado de primer uso (implementación propia, ligera y accesible).
 * - Destaca elementos reales marcados con `data-tutorial="..."` (barra de navegación) con un foco sobre el fondo oscurecido.
 * - Si el elemento no se ve en ese tamaño de pantalla (menú móvil, menú «Más»), destaca el botón del menú o centra la tarjeta.
 * - Accesible: diálogo modal con foco atrapado, Escape = omitir, botones Anterior / Siguiente / Omitir, lectura de «Paso X de N».
 * - Al terminar u omitir se guarda «visto» en el usuario (por rol); se repite desde «Mi cuenta» → «Ver tutorial».
 */
interface ContextoTutorial {
  /** Abre el tutorial del rol actual (false si el rol no tiene tutorial). */
  abrir: () => boolean;
  disponible: boolean;
}

const Contexto = createContext<ContextoTutorial>({ abrir: () => false, disponible: false });
export const useTutorial = () => useContext(Contexto);

interface Medida {
  rect: { top: number; left: number; width: number; height: number } | null;
  ancho: number;
  alto: number;
  respaldo: boolean; // el elemento pedido no está visible y se destaca el botón del menú
}

function buscar(objetivo?: string): { el: HTMLElement; respaldo: boolean } | null {
  if (!objetivo) return null;
  const cadena = [objetivo, ...(objetivo.startsWith("nav-") ? ["mas", "menu-movil"] : ["menu-movil"])];
  for (const [i, id] of cadena.entries()) {
    for (const el of document.querySelectorAll<HTMLElement>(`[data-tutorial="${id}"]`)) {
      const r = el.getBoundingClientRect();
      if (r.width > 0 && r.height > 0) return { el, respaldo: i > 0 };
    }
  }
  return null;
}

/** Inicio automático del tutorial: solo en el panel. Aislado porque `usePathname` debe ir dentro de <Suspense>. */
function InicioAutomatico({ pendienteBase, clave, yaMostrado, iniciar }: { pendienteBase: boolean; clave: string | null; yaMostrado: React.RefObject<string | null>; iniciar: () => void }) {
  const ruta = usePathname();
  const pendiente = pendienteBase && ruta === "/panel";
  useEffect(() => {
    if (!pendiente || !clave || yaMostrado.current === clave) return;
    const t = setTimeout(() => {
      yaMostrado.current = clave;
      iniciar();
    }, 900);
    return () => clearTimeout(t);
  }, [pendiente, clave, yaMostrado, iniciar]);
  return null;
}

export default function ProveedorTutorial({ children }: { children: ReactNode }) {
  const { usuario, actualizarUsuario } = useAuth();
  const [abierto, setAbierto] = useState(false);
  const [paso, setPaso] = useState(0);
  const [medida, setMedida] = useState<Medida>({ rect: null, ancho: 1024, alto: 768, respaldo: false });
  const tarjeta = useRef<HTMLDivElement>(null);
  const previo = useRef<HTMLElement | null>(null);
  const yaAutomatico = useRef<string | null>(null);

  const rol = usuario?.rol;
  const pasos = rol ? TUTORIALES[rol] : undefined;
  const actual = pasos?.[paso];

  // Inicio automático: primer uso del rol, en el panel (la página a la que se llega tras iniciar sesión)
  const clave = usuario && rol ? `${usuario.id}:${rol}` : null;
  const pendienteBase = !!usuario && !!pasos && !(usuario.tutorial_visto ?? []).includes(usuario.rol);

  const abrir = useCallback(() => {
    if (!pasos) return false;
    previo.current = document.activeElement as HTMLElement | null;
    setPaso(0);
    setAbierto(true);
    return true;
  }, [pasos]);

  const iniciarAuto = useCallback(() => {
    previo.current = document.activeElement as HTMLElement | null;
    setPaso(0);
    setAbierto(true);
  }, []);

  const cerrar = useCallback(async () => {
    setAbierto(false);
    previo.current?.focus?.();
    if (usuario && !(usuario.tutorial_visto ?? []).includes(usuario.rol)) {
      try {
        actualizarUsuario(await marcarTutorial(true));
      } catch {
        /* no crítico: se mostrará de nuevo la próxima vez */
      }
    }
  }, [usuario, actualizarUsuario]);

  // Medir el elemento destacado (y volver a medir al cambiar el tamaño o desplazar la página)
  useEffect(() => {
    if (!abierto || !actual) return;
    let marco = 0;
    const medir = () => {
      cancelAnimationFrame(marco);
      marco = requestAnimationFrame(() => {
        const encontrado = buscar(actual.objetivo);
        const r = encontrado?.el.getBoundingClientRect();
        setMedida({
          rect: r ? { top: r.top, left: r.left, width: r.width, height: r.height } : null,
          ancho: window.innerWidth,
          alto: window.innerHeight,
          respaldo: encontrado?.respaldo ?? false,
        });
      });
    };
    medir();
    window.addEventListener("resize", medir);
    window.addEventListener("scroll", medir, true);
    return () => {
      cancelAnimationFrame(marco);
      window.removeEventListener("resize", medir);
      window.removeEventListener("scroll", medir, true);
    };
  }, [abierto, actual]);

  // El foco pasa a la tarjeta al abrir y en cada paso (para lectores de pantalla y teclado)
  useEffect(() => {
    if (abierto) tarjeta.current?.focus();
  }, [abierto, paso]);

  function alTeclear(e: KeyboardEvent<HTMLDivElement>) {
    if (e.key === "Escape") {
      e.stopPropagation();
      void cerrar();
      return;
    }
    if (e.key !== "Tab" || !tarjeta.current) return;
    const foco = tarjeta.current.querySelectorAll<HTMLElement>("button:not([disabled])");
    if (foco.length === 0) return;
    const primero = foco[0];
    const ultimo = foco[foco.length - 1];
    if (e.shiftKey && (document.activeElement === primero || document.activeElement === tarjeta.current)) {
      e.preventDefault();
      ultimo.focus();
    } else if (!e.shiftKey && document.activeElement === ultimo) {
      e.preventDefault();
      primero.focus();
    }
  }

  const valor = useMemo(() => ({ abrir, disponible: !!pasos }), [abrir, pasos]);

  let estiloTarjeta: CSSProperties = {};
  const movil = medida.ancho < 640;
  if (!medida.rect) {
    estiloTarjeta = { inset: 0, margin: "auto", height: "fit-content", width: "min(26rem, calc(100vw - 1.5rem))" };
  } else if (movil) {
    estiloTarjeta = { left: 12, right: 12, bottom: 12 };
  } else {
    const ancho = 360;
    const centro = medida.rect.left + medida.rect.width / 2;
    estiloTarjeta = {
      width: ancho,
      top: Math.min(medida.rect.top + medida.rect.height + 16, Math.max(12, medida.alto - 280)),
      left: Math.max(12, Math.min(centro - ancho / 2, medida.ancho - ancho - 12)),
    };
  }

  return (
    <Contexto.Provider value={valor}>
      {children}
      <Suspense fallback={null}>
        <InicioAutomatico pendienteBase={pendienteBase} clave={clave} yaMostrado={yaAutomatico} iniciar={iniciarAuto} />
      </Suspense>
      {abierto && actual && pasos && (
        <div className="fixed inset-0 z-[80]" onKeyDown={alTeclear}>
          {/* Fondo oscuro con foco sobre el elemento real; también bloquea los clics mientras dura el tutorial */}
          {medida.rect ? (
            <div
              aria-hidden="true"
              className="pointer-events-none fixed rounded-xl border-2 border-cul-naranja transition-all duration-200 motion-reduce:transition-none"
              style={{
                top: medida.rect.top - 6,
                left: medida.rect.left - 6,
                width: medida.rect.width + 12,
                height: medida.rect.height + 12,
                boxShadow: "0 0 0 9999px rgba(8, 16, 32, 0.72)",
              }}
            />
          ) : (
            <div aria-hidden="true" className="fixed inset-0 bg-[rgba(8,16,32,0.72)]" />
          )}
          <div aria-hidden="true" className="fixed inset-0" />

          <div
            ref={tarjeta}
            role="dialog"
            aria-modal="true"
            aria-labelledby="tutorial-titulo"
            aria-describedby="tutorial-texto"
            tabIndex={-1}
            style={estiloTarjeta}
            className="anim-aparecer fixed flex flex-col gap-3 rounded-2xl border border-borde bg-superficie p-5 text-texto shadow-2xl outline-none"
          >
            <p className="text-xs font-bold uppercase tracking-wide text-enlace" aria-live="polite">
              Paso {paso + 1} de {pasos.length}
            </p>
            <h2 id="tutorial-titulo" className="text-lg font-extrabold leading-snug">
              {actual.titulo}
            </h2>
            <p id="tutorial-texto" className="text-sm leading-relaxed text-suave">
              {actual.texto}
              {medida.respaldo && " Lo encuentras en el menú de arriba."}
            </p>
            <div className="flex items-center gap-1.5" aria-hidden="true">
              {pasos.map((_, i) => (
                <span key={i} className={cx("h-1.5 flex-1 rounded-full", i <= paso ? "bg-cul-naranja" : "bg-borde")} />
              ))}
            </div>
            <div className="flex flex-wrap items-center justify-between gap-2 pt-1">
              <button
                type="button"
                onClick={() => void cerrar()}
                className="min-h-11 rounded-lg px-2 text-sm font-semibold text-suave underline underline-offset-2 hover:text-texto"
              >
                Omitir
              </button>
              <div className="flex gap-2">
                <Boton variante="secundario" tamano="sm" onClick={() => setPaso((p) => Math.max(0, p - 1))} disabled={paso === 0}>
                  Anterior
                </Boton>
                {paso < pasos.length - 1 ? (
                  <Boton tamano="sm" onClick={() => setPaso((p) => p + 1)}>
                    Siguiente
                  </Boton>
                ) : (
                  <Boton tamano="sm" onClick={() => void cerrar()}>
                    Terminar
                  </Boton>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </Contexto.Provider>
  );
}
