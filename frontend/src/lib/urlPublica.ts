/**
 * Origen (esquema + host + puerto) que otras personas deben usar para entrar a la plataforma.
 *
 * Por defecto es el origen con el que se abrió la página. Si el docente abre la plataforma por «localhost», el
 * código QR de la clase en vivo y los enlaces para compartir no servirían en los celulares de los estudiantes:
 * en ese caso se define `NEXT_PUBLIC_URL_PUBLICA` (p. ej. `http://192.168.1.20:3000` o la URL pública del despliegue).
 * Solo se puede llamar en el navegador.
 */
export function origenPublico(): string {
  const configurado = process.env.NEXT_PUBLIC_URL_PUBLICA?.trim().replace(/\/+$/, "");
  return configurado || window.location.origin;
}
