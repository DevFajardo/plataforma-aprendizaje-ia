"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { useAuth } from "@/lib/auth";
import CampanaNotificaciones from "./CampanaNotificaciones";
import MarcaInstitucional from "./MarcaInstitucional";
import { Icono, cx } from "./ui";

interface Enlace {
  href: string;
  texto: string;
}

const PANEL: Enlace = { href: "/panel", texto: "Panel" };
const GENERAR: Enlace = { href: "/", texto: "Generar" };
const CUESTIONARIOS: Enlace = { href: "/cuestionarios", texto: "Mis cuestionarios" };
const UNIRSE: Enlace = { href: "/unirse", texto: "Unirse" };
const HISTORIAL: Enlace = { href: "/historial", texto: "Historial" };
const ENCUESTA: Enlace = { href: "/encuesta", texto: "Encuesta" };
const BANCO: Enlace = { href: "/banco", texto: "Banco" };

/**
 * Enlaces del menú según el rol. Los `principales` van siempre en la barra; los de `mas` pasan al menú «Más» para
 * que la barra quepa en pantallas de escritorio (el contenedor mide como máximo 1280 px). En móvil y tablet se listan todos.
 */
function enlacesPorRol(rol: string): { principales: Enlace[]; mas: Enlace[] } {
  switch (rol) {
    case "docente":
      return {
        principales: [PANEL, GENERAR, CUESTIONARIOS, { href: "/cursos", texto: "Cursos" }, BANCO, { href: "/comparar", texto: "Comparar" }],
        mas: [UNIRSE, HISTORIAL, ENCUESTA],
      };
    case "coordinador":
      return { principales: [PANEL, { href: "/coordinacion", texto: "Coordinación" }, BANCO, ENCUESTA], mas: [] };
    case "admin":
      return { principales: [PANEL, { href: "/admin", texto: "Admin" }, { href: "/coordinacion", texto: "Coordinación" }, { href: "/cursos", texto: "Cursos" }, BANCO, ENCUESTA], mas: [] };
    default:
      return { principales: [PANEL, GENERAR, CUESTIONARIOS, { href: "/mis-cursos", texto: "Mis cursos" }, UNIRSE, HISTORIAL, ENCUESTA], mas: [] };
  }
}

const ROL: Record<string, string> = { docente: "Docente", estudiante: "Estudiante", coordinador: "Coordinador", admin: "Administrador" };

export default function Navbar() {
  const { usuario, logout } = useAuth();
  const ruta = usePathname();
  // Se guarda la ruta en la que se abrió cada menú: al navegar cambia la ruta y el menú queda cerrado solo.
  const [menuEn, setMenuEn] = useState<string | null>(null);
  const [usuarioEn, setUsuarioEn] = useState<string | null>(null);
  const [masEn, setMasEn] = useState<string | null>(null);
  const menuAbierto = menuEn === ruta;
  const usuarioAbierto = usuarioEn === ruta;
  const masAbierto = masEn === ruta;
  const botonMenu = useRef<HTMLButtonElement>(null);
  const cajaUsuario = useRef<HTMLDivElement>(null);
  const cajaMas = useRef<HTMLDivElement>(null);

  // Escape cierra los menús; clic fuera cierra el menú de usuario
  useEffect(() => {
    if (!menuAbierto && !usuarioAbierto && !masAbierto) return;
    function alTeclear(e: KeyboardEvent) {
      if (e.key !== "Escape") return;
      if (menuAbierto) botonMenu.current?.focus();
      setMenuEn(null);
      setUsuarioEn(null);
      setMasEn(null);
    }
    function alPulsar(e: MouseEvent) {
      if (usuarioAbierto && cajaUsuario.current && !cajaUsuario.current.contains(e.target as Node)) setUsuarioEn(null);
      if (masAbierto && cajaMas.current && !cajaMas.current.contains(e.target as Node)) setMasEn(null);
    }
    document.addEventListener("keydown", alTeclear);
    document.addEventListener("mousedown", alPulsar);
    return () => {
      document.removeEventListener("keydown", alTeclear);
      document.removeEventListener("mousedown", alPulsar);
    };
  }, [menuAbierto, usuarioAbierto, masAbierto]);

  // Con el menú móvil abierto, el fondo no se desplaza
  useEffect(() => {
    if (!menuAbierto) return;
    const anterior = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = anterior;
    };
  }, [menuAbierto]);

  function salir() {
    logout("/login");
  }

  function esActivo(href: string) {
    if (href === "/") return ruta === "/";
    return ruta.startsWith(href) || (href === "/unirse" && ruta.startsWith("/c/"));
  }

  const { principales, mas } = usuario ? enlacesPorRol(usuario.rol) : { principales: [{ href: "/", texto: "Inicio" }], mas: [] as Enlace[] };
  const enlaces: Enlace[] = [...principales, ...mas];
  const masActivo = mas.some((e) => esActivo(e.href));

  const claseEnlace = (href: string, movil: boolean) =>
    cx(
      "relative flex items-center rounded-lg text-sm font-semibold transition duration-150",
      movil ? "min-h-12 px-4 text-base" : "min-h-10 whitespace-nowrap px-2.5",
      esActivo(href) ? "bg-white/15 text-white" : "text-white/85 hover:bg-white/10 hover:text-white",
    );

  const inicial = usuario?.nombre.trim().charAt(0).toUpperCase() ?? "";

  return (
    <header className="sticky top-0 z-50 border-b-4 border-cul-naranja bg-barra-superior text-white shadow-md">
      <nav aria-label="Principal" className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-3 px-4 sm:px-6 lg:px-8">
        <Link href="/" className="min-w-0 rounded-md xl:shrink-0">
          <MarcaInstitucional titulo="Aprendizaje Activo" subtituloClase="xl:hidden" />
          <span className="sr-only"> (ir al inicio)</span>
        </Link>

        {/* Navegación de escritorio */}
        <div className="hidden min-w-0 items-center gap-1 xl:flex">
          {principales.map((e) => (
            <Link
              key={e.href}
              href={e.href}
              data-tutorial={`nav-${e.href}`}
              aria-current={esActivo(e.href) ? "page" : undefined}
              className={claseEnlace(e.href, false)}
            >
              {e.texto}
              {esActivo(e.href) && <span aria-hidden="true" className="absolute inset-x-3 bottom-0.5 h-0.5 rounded-full bg-cul-naranja" />}
            </Link>
          ))}

          {mas.length > 0 && (
            <div ref={cajaMas} className="relative">
              <button
                type="button"
                data-tutorial="mas"
                aria-haspopup="menu"
                aria-expanded={masAbierto}
                onClick={() => setMasEn(masAbierto ? null : ruta)}
                className={cx(
                  "relative flex min-h-10 items-center gap-1 whitespace-nowrap rounded-lg px-2.5 text-sm font-semibold transition duration-150",
                  masActivo ? "bg-white/15 text-white" : "text-white/85 hover:bg-white/10 hover:text-white",
                )}
              >
                Más
                <Icono nombre="chevron" tamano={16} className={masAbierto ? "rotate-180 transition" : "transition"} />
                {masActivo && <span aria-hidden="true" className="absolute inset-x-3 bottom-0.5 h-0.5 rounded-full bg-cul-naranja" />}
              </button>
              {masAbierto && (
                <div
                  role="menu"
                  aria-label="Más opciones"
                  className="anim-aparecer absolute right-0 top-full z-50 mt-2 w-48 overflow-hidden rounded-xl border border-borde bg-superficie py-1 text-texto shadow-lg"
                >
                  {mas.map((e) => (
                    <Link
                      key={e.href}
                      role="menuitem"
                      href={e.href}
                      data-tutorial={`nav-${e.href}`}
                      aria-current={esActivo(e.href) ? "page" : undefined}
                      className={cx(
                        "flex min-h-11 items-center px-4 text-sm font-semibold hover:bg-superficie-2",
                        esActivo(e.href) && "bg-superficie-2 text-enlace",
                      )}
                    >
                      {e.texto}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          )}

          {usuario && (
            <div className="ml-3">
              <CampanaNotificaciones />
            </div>
          )}
          {usuario ? (
            <div ref={cajaUsuario} className="relative ml-1">
              <button
                type="button"
                data-tutorial="usuario"
                aria-haspopup="menu"
                aria-expanded={usuarioAbierto}
                onClick={() => setUsuarioEn(usuarioAbierto ? null : ruta)}
                className="flex min-h-10 items-center gap-2 rounded-lg border border-white/25 py-1 pl-1.5 pr-3 text-sm font-semibold transition hover:bg-white/10"
              >
                <span aria-hidden="true" className="flex h-7 w-7 items-center justify-center rounded-full bg-cul-naranja text-sm font-bold text-cul-azul-oscuro">
                  {inicial}
                </span>
                <span className="max-w-32 truncate">{usuario.nombre}</span>
                <Icono nombre="chevron" tamano={16} className={usuarioAbierto ? "rotate-180 transition" : "transition"} />
              </button>
              {usuarioAbierto && (
                <div
                  role="menu"
                  className="anim-aparecer absolute right-0 top-full z-50 mt-2 w-64 overflow-hidden rounded-xl border border-borde bg-superficie py-1 text-texto shadow-lg"
                >
                  <div className="border-b border-borde px-4 py-3">
                    <p className="truncate text-sm font-bold">{usuario.nombre}</p>
                    <p className="truncate text-xs text-suave">{usuario.email}</p>
                    <p className="mt-1 text-xs font-semibold text-enlace">{ROL[usuario.rol] ?? usuario.rol}</p>
                  </div>
                  <Link role="menuitem" href="/cuenta" className="flex min-h-11 items-center gap-3 px-4 text-sm font-semibold hover:bg-superficie-2">
                    <Icono nombre="usuario" tamano={18} /> Mi cuenta
                  </Link>
                  <button
                    type="button"
                    role="menuitem"
                    onClick={salir}
                    className="flex min-h-11 w-full items-center gap-3 px-4 text-left text-sm font-semibold hover:bg-superficie-2"
                  >
                    <Icono nombre="salir" tamano={18} /> Salir
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="ml-3 flex items-center gap-2">
              <Link href="/login" className="flex min-h-10 items-center rounded-lg px-3.5 text-sm font-semibold text-white/90 hover:bg-white/10">
                Iniciar sesión
              </Link>
              <Link
                href="/registro"
                className="flex min-h-10 items-center rounded-lg bg-cul-naranja px-4 text-sm font-bold text-cul-azul-oscuro transition hover:brightness-110"
              >
                Crear cuenta
              </Link>
            </div>
          )}
        </div>

        {/* Campana y botón hamburguesa (móvil y tablet) */}
        <div className="flex items-center gap-2 xl:hidden">
          {usuario && <CampanaNotificaciones />}
          <button
            ref={botonMenu}
            type="button"
            aria-expanded={menuAbierto}
            data-tutorial="menu-movil"
            aria-controls="menu-movil"
            aria-label={menuAbierto ? "Cerrar menú" : "Abrir menú"}
            onClick={() => setMenuEn(menuAbierto ? null : ruta)}
            className="flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-white/30 transition hover:bg-white/10"
          >
            <Icono nombre={menuAbierto ? "cerrar" : "menu"} tamano={24} />
          </button>
        </div>
      </nav>

      {/* Panel desplegable a pantalla completa (móvil y tablet) */}
      {menuAbierto && (
        <div
          id="menu-movil"
          className="anim-aparecer absolute inset-x-0 top-full h-[calc(100dvh-4.25rem)] overflow-y-auto bg-barra-superior xl:hidden"
        >
          <div className="mx-auto flex max-w-xl flex-col gap-1 px-4 pb-10 pt-4 sm:px-6">
            {usuario && (
              <div className="mb-3 flex items-center gap-3 rounded-xl border border-white/20 bg-white/10 p-3">
                <span aria-hidden="true" className="flex h-11 w-11 shrink-0 items-center justify-center rounded-full bg-cul-naranja text-lg font-bold text-cul-azul-oscuro">
                  {inicial}
                </span>
                <div className="min-w-0">
                  <p className="truncate font-bold">{usuario.nombre}</p>
                  <p className="truncate text-xs text-white/85">{usuario.email}</p>
                  <p className="text-xs font-semibold text-cul-amarillo-vivo">{ROL[usuario.rol] ?? usuario.rol}</p>
                </div>
              </div>
            )}
            {enlaces.map((e) => (
              <Link key={e.href} href={e.href} aria-current={esActivo(e.href) ? "page" : undefined} className={claseEnlace(e.href, true)}>
                {esActivo(e.href) && <span aria-hidden="true" className="mr-3 h-6 w-1 rounded-full bg-cul-naranja" />}
                {e.texto}
              </Link>
            ))}
            <div className="my-3 h-px bg-white/20" />
            {usuario ? (
              <>
                <Link href="/cuenta" aria-current={esActivo("/cuenta") ? "page" : undefined} className={claseEnlace("/cuenta", true)}>
                  <Icono nombre="usuario" className="mr-3" /> Mi cuenta
                </Link>
                <button
                  type="button"
                  onClick={salir}
                  className="flex min-h-12 items-center rounded-lg px-4 text-left text-base font-semibold text-white/90 hover:bg-white/10"
                >
                  <Icono nombre="salir" className="mr-3" /> Salir
                </button>
              </>
            ) : (
              <div className="flex flex-col gap-3 pt-1">
                <Link href="/login" className="flex min-h-12 items-center justify-center rounded-lg border border-white/40 text-base font-semibold hover:bg-white/10">
                  Iniciar sesión
                </Link>
                <Link
                  href="/registro"
                  className="flex min-h-12 items-center justify-center rounded-lg bg-cul-naranja text-base font-bold text-cul-azul-oscuro hover:brightness-110"
                >
                  Crear cuenta
                </Link>
              </div>
            )}
          </div>
        </div>
      )}
    </header>
  );
}
