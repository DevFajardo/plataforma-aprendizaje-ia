/** Devuelve una ruta interna segura para redirigir tras iniciar sesión (evita redirecciones a otros sitios). */
export function destinoSeguro(siguiente: string | null): string {
  if (siguiente && siguiente.startsWith("/") && !siguiente.startsWith("//") && !siguiente.includes("\\")) {
    return siguiente;
  }
  return "/panel"; // destino por defecto tras iniciar sesión
}

/** Ruta de login que recuerda a dónde volver. */
export function rutaLogin(siguiente: string): string {
  return siguiente === "/" ? "/login" : `/login?siguiente=${encodeURIComponent(siguiente)}`;
}
