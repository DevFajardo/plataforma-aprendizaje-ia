import type { MetadataRoute } from "next";

/** Solo la portada, el registro y la política de datos son públicas; el resto exige sesión y no debe indexarse. */
export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/registro", "/privacidad"],
        disallow: [
          "/admin",
          "/banco",
          "/c/",
          "/comparar",
          "/coordinacion",
          "/cuenta",
          "/cuestionarios",
          "/cursos",
          "/encuesta",
          "/historial",
          "/login",
          "/mis-cursos",
          "/notificaciones",
          "/panel",
          "/unirse",
          "/vivo",
        ],
      },
    ],
  };
}
