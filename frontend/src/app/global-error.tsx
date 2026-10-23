"use client";

/** Último recurso: error en el layout raíz. Debe traer su propio <html> y estilos mínimos. */
export default function ErrorGlobal({ retry }: { error: Error & { digest?: string }; retry: () => void }) {
  return (
    <html lang="es">
      <body style={{ margin: 0, minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", padding: 16, background: "#f3f6fb", color: "#172741", fontFamily: "system-ui, sans-serif" }}>
        <main role="alert" style={{ maxWidth: 440, textAlign: "center", background: "#fff", border: "1px solid #d3dbe8", borderTop: "4px solid #e88a37", borderRadius: 16, padding: "32px 24px" }}>
          <h1 style={{ fontSize: 24, margin: "0 0 8px" }}>Algo no salió como esperábamos</h1>
          <p style={{ color: "#44526d", lineHeight: 1.5 }}>Ocurrió un problema al cargar la aplicación. Intenta de nuevo en unos segundos.</p>
          <button type="button" onClick={() => retry()} style={{ minHeight: 48, padding: "0 24px", border: 0, borderRadius: 10, background: "#0b468a", color: "#fff", fontWeight: 700, cursor: "pointer" }}>
            Intentar de nuevo
          </button>
        </main>
      </body>
    </html>
  );
}
