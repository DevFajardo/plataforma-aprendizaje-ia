import type {
  Comparacion,
  Compartido,
  IntentoCreado,
  ModoCuestionario,
  Repaso,
  CuestionarioDetalle,
  EntradaPregunta,
  Pregunta,
  Resultados,
  CuestionarioResumen,
  Estadisticas,
  Alerta,
  Asignatura,
  Coordinacion,
  Facultad,
  Grupo,
  Matriculado,
  MiCurso,
  Programa,
  ResultadoAprendizaje,
  UsuarioAdmin,
  RespuestaSus,
  ResumenSus,
  IntentoHistorial,
  IntentoResumen,
  RespuestaAuth,
  RespuestaServidor,
  Tarea,
  Usuario,
  EstadoVivo,
  HistorialVivo,
  PaginaNotificaciones,
  SesionVivoInfo,
  UnidoVivo,
  EstadoTutor,
  FiltrosBanco,
  PaginaBanco,
  PreguntaBanco,
  RespuestaTutor,
  TranscripcionVideo,
} from "./tipos";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const CLAVE_TOKEN = "token";

// ---------- Token (localStorage puede fallar o no existir) ----------

export function leerToken(): string | null {
  try {
    return localStorage.getItem(CLAVE_TOKEN);
  } catch {
    return null;
  }
}

export function guardarToken(token: string | null): void {
  try {
    if (token) localStorage.setItem(CLAVE_TOKEN, token);
    else localStorage.removeItem(CLAVE_TOKEN);
  } catch {
    /* almacenamiento no disponible */
  }
}

// El AuthProvider registra aquí qué hacer ante un 401 (cerrar sesión y redirigir)
let manejador401: (() => void) | null = null;
export function registrarManejador401(fn: (() => void) | null) {
  manejador401 = fn;
}

async function peticion<T>(ruta: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = leerToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  let resp: Response;
  try {
    resp = await fetch(`${API_URL}${ruta}`, { ...init, headers });
  } catch {
    throw new Error(
      "No se pudo conectar con el servidor. Verifica que el backend esté encendido en " +
        API_URL +
        ".",
    );
  }
  if (!resp.ok) {
    let detalle = `Error del servidor (${resp.status}).`;
    try {
      const datos = await resp.json();
      if (typeof datos.detail === "string") detalle = datos.detail;
      else if (Array.isArray(datos.detail) && datos.detail.length > 0) {
        // Errores de validación de FastAPI: mostrar el primer mensaje legible
        const msg = String(datos.detail[0]?.msg ?? "").replace(/^Value error, /, "");
        detalle = msg || "Los datos ingresados no son válidos.";
      } else if (resp.status === 422) detalle = "Los datos ingresados no son válidos.";
    } catch {
      /* respuesta sin JSON */
    }
    if (resp.status === 401 && !ruta.startsWith("/api/auth/login")) manejador401?.();
    throw new Error(detalle);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json() as Promise<T>;
}

const post = <T,>(ruta: string, cuerpo?: unknown) =>
  peticion<T>(ruta, { method: "POST", body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo) });

// ---------- Autenticación ----------

export const login = (email: string, password: string) =>
  post<RespuestaAuth>("/api/auth/login", { email, password });

export const registro = (
  nombre: string,
  email: string,
  password: string,
  rol: string,
  aceptaTratamientoDatos: boolean,
  consentimientoInvestigacion: boolean,
) =>
  post<RespuestaAuth>("/api/auth/registro", {
    nombre,
    email,
    password,
    rol,
    acepta_tratamiento_datos: aceptaTratamientoDatos,
    consentimiento_investigacion: consentimientoInvestigacion,
  });

export const obtenerYo = () => peticion<Usuario>("/api/auth/yo");

// ---------- Cuenta y datos personales (Ley 1581 de 2012) ----------

export const editarCuenta = (datos: {
  nombre?: string;
  password_actual?: string;
  password_nueva?: string;
  consentimiento_investigacion?: boolean;
  acepta_tratamiento_datos?: boolean;
}) => peticion<Usuario>("/api/auth/cuenta", { method: "PATCH", body: JSON.stringify(datos) });

/** Marca (o desmarca, para repetirlo) el tutorial de primer uso del rol actual. */
export const marcarTutorial = (visto: boolean) =>
  peticion<Usuario>("/api/auth/tutorial", { method: "PUT", body: JSON.stringify({ visto }) });

export const obtenerMisDatos = () => peticion<unknown>("/api/auth/mis-datos");

export const eliminarCuenta = (password: string) =>
  peticion<void>("/api/auth/cuenta", { method: "DELETE", body: JSON.stringify({ password }) });

// ---------- Procesamiento ----------

export const procesarVideo = (url: string, numPreguntas: number) =>
  post<Tarea>("/api/procesar", { url, num_preguntas: numPreguntas });

export const obtenerTarea = (id: string) => peticion<Tarea>(`/api/tareas/${id}`);

// ---------- Cuestionarios e intentos ----------

export const listarCuestionarios = () => peticion<CuestionarioResumen[]>("/api/cuestionarios");

export const obtenerCuestionario = (id: number) =>
  peticion<CuestionarioDetalle>(`/api/cuestionarios/${id}`);

export const eliminarCuestionario = (id: number) =>
  peticion<void>(`/api/cuestionarios/${id}`, { method: "DELETE" });

export const crearIntento = (cuestionarioId: number) =>
  post<IntentoCreado>(`/api/cuestionarios/${cuestionarioId}/intentos`);

export const listarRepasos = () => peticion<Repaso[]>("/api/repasos");

export const responderPregunta = (intentoId: number, preguntaId: number, respuesta: string) =>
  post<RespuestaServidor>(`/api/intentos/${intentoId}/responder`, {
    pregunta_id: preguntaId,
    respuesta,
  });

export const finalizarIntento = (intentoId: number) =>
  post<IntentoResumen>(`/api/intentos/${intentoId}/finalizar`);

export const listarIntentos = () => peticion<IntentoHistorial[]>("/api/intentos");

// ---------- Publicar y compartir ----------

export const publicarCuestionario = (id: number, publicado: boolean, estimacionManualMin?: number) =>
  post<{ publicado: boolean; codigo_compartir: string }>(`/api/cuestionarios/${id}/publicar`, {
    publicado,
    ...(estimacionManualMin ? { estimacion_manual_min: estimacionManualMin } : {}),
  });

export const duplicarCuestionario = (id: number, modo: ModoCuestionario, titulo?: string) =>
  post<{ id: number; titulo: string; modo: ModoCuestionario; codigo_compartir: string }>(
    `/api/cuestionarios/${id}/duplicar`,
    { modo, ...(titulo ? { titulo } : {}) },
  );

/** Suma el tiempo activo de edición. `keepalive` permite enviarlo al cerrar la pestaña. */
export const enviarTiempoEdicion = (id: number, segundos: number, keepalive = false) =>
  peticion<{ segundos_edicion: number }>(`/api/cuestionarios/${id}/tiempo-edicion`, {
    method: "POST",
    body: JSON.stringify({ segundos }),
    keepalive,
  });

export const resolverCodigo = (codigo: string) =>
  peticion<Compartido>(`/api/compartido/${encodeURIComponent(codigo.trim())}`);

// ---------- Edición (docente) ----------

export const editarCuestionario = (
  id: number,
  datos: {
    titulo?: string;
    resumen?: string;
    ideas_clave?: string[];
    repaso_dias?: number | null;
    estimacion_manual_min?: number | null;
    grupo_id?: number | null;
  },
) => peticion<unknown>(`/api/cuestionarios/${id}`, { method: "PATCH", body: JSON.stringify(datos) });

export const editarPregunta = (id: number, datos: EntradaPregunta) =>
  peticion<Pregunta>(`/api/preguntas/${id}`, { method: "PUT", body: JSON.stringify(datos) });

export const agregarPregunta = (cuestionarioId: number, datos: EntradaPregunta) =>
  post<Pregunta>(`/api/cuestionarios/${cuestionarioId}/preguntas`, datos);

export const eliminarPregunta = (id: number) => peticion<void>(`/api/preguntas/${id}`, { method: "DELETE" });

export const reordenarPreguntas = (cuestionarioId: number, ids: number[]) =>
  post<Pregunta[]>(`/api/cuestionarios/${cuestionarioId}/reordenar`, { ids });

// ---------- Resultados (docente) ----------

export const obtenerResultados = (id: number) => peticion<Resultados>(`/api/cuestionarios/${id}/resultados`);

/** Descarga un CSV con el token (fetch -> blob) y dispara la descarga en el navegador. */
async function descargarArchivo(ruta: string, nombre: string): Promise<void> {
  const token = leerToken();
  let resp: Response;
  try {
    resp = await fetch(`${API_URL}${ruta}`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
  } catch {
    throw new Error("No se pudo conectar con el servidor.");
  }
  if (!resp.ok) throw new Error(`No se pudo descargar el archivo (${resp.status}).`);
  const url = URL.createObjectURL(await resp.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = nombre;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export const descargarPdfCuestionario = (id: number) =>
  descargarArchivo(`/api/cuestionarios/${id}/reporte.pdf`, `resultados_${id}.pdf`);

export const descargarCsv = (id: number) =>
  descargarArchivo(`/api/cuestionarios/${id}/resultados.csv`, `resultados_${id}.csv`);

// ---------- Comparación de grupos (docente) ----------

export const compararGrupos = (a: number, b: number) => peticion<Comparacion>(`/api/comparar?a=${a}&b=${b}`);

export const descargarCsvComparar = (a: number, b: number) =>
  descargarArchivo(`/api/comparar.csv?a=${a}&b=${b}`, `comparacion_${a}_${b}.csv`);

// ---------- Estadísticas y encuesta SUS ----------

export const obtenerEstadisticas = () => peticion<Estadisticas>("/api/estadisticas/yo");

export const enviarSus = (respuestas: number[], comentario: string) =>
  post<RespuestaSus>("/api/sus", { respuestas, comentario: comentario.trim() || null });

/** Devuelve null si el usuario aún no respondió la encuesta. */
export async function obtenerMiSus(): Promise<RespuestaSus | null> {
  try {
    return await peticion<RespuestaSus>("/api/sus/mia");
  } catch (e) {
    if (e instanceof Error && e.message.startsWith("Aún no has respondido")) return null;
    throw e;
  }
}

export const obtenerResumenSus = () => peticion<ResumenSus>("/api/sus/resumen");

export const descargarCsvSus = () => descargarArchivo("/api/sus/resumen.csv", "encuesta_sus.csv");

// ---------- Archivos ----------

/** URL absoluta de un archivo de video/audio subido (ruta relativa que entrega la API). */
export const urlMedio = (rutaRelativa: string) => `${API_URL}${rutaRelativa}`;

/** Sube un archivo con barra de progreso (XMLHttpRequest, porque fetch no reporta la subida). */
export function subirArchivo(
  archivo: File,
  numPreguntas: number,
  onProgreso: (porcentaje: number) => void,
): Promise<Tarea> {
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${API_URL}/api/procesar/archivo`);
    const token = leerToken();
    if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) onProgreso(Math.round((100 * e.loaded) / e.total));
    };
    xhr.onerror = () => reject(new Error("No se pudo conectar con el servidor. Verifica que el backend esté encendido."));
    xhr.onload = () => {
      let cuerpo: unknown = null;
      try {
        cuerpo = JSON.parse(xhr.responseText);
      } catch {
        /* sin JSON */
      }
      if (xhr.status >= 200 && xhr.status < 300) return resolve(cuerpo as Tarea);
      if (xhr.status === 401) manejador401?.();
      const detalle = (cuerpo as { detail?: unknown } | null)?.detail;
      reject(new Error(typeof detalle === "string" ? detalle : `Error del servidor (${xhr.status}).`));
    };
    const form = new FormData();
    form.append("archivo", archivo);
    form.append("num_preguntas", String(numPreguntas));
    xhr.send(form);
  });
}

// ---------- Sprint 6: cursos, administración, coordinación y alertas ----------

const enviar = <T,>(metodo: "PATCH" | "PUT", ruta: string, cuerpo: unknown) =>
  peticion<T>(ruta, { method: metodo, body: JSON.stringify(cuerpo) });
const borrar = (ruta: string) => peticion<void>(ruta, { method: "DELETE" });

export const listarGrupos = () => peticion<Grupo[]>("/api/grupos");
export const catalogoAsignaturas = () => peticion<Asignatura[]>("/api/catalogo/asignaturas");
export const crearGrupo = (asignatura_id: number, periodo: string, nombre: string) =>
  post<Grupo>("/api/grupos", { asignatura_id, periodo, nombre });
export const editarGrupo = (id: number, datos: { periodo?: string; nombre?: string }) => enviar<Grupo>("PATCH", `/api/grupos/${id}`, datos);
export const renovarCodigoGrupo = (id: number) => post<Grupo>(`/api/grupos/${id}/nuevo-codigo`);
export const eliminarGrupo = (id: number) => borrar(`/api/grupos/${id}`);
export const listarMatriculados = (id: number) => peticion<Matriculado[]>(`/api/grupos/${id}/matriculados`);
export const quitarMatriculado = (grupo: number, estudiante: number) => borrar(`/api/grupos/${grupo}/matriculados/${estudiante}`);
export const rasDelCuestionario = (id: number) =>
  peticion<{ id: number; codigo: string; descripcion: string }[]>(`/api/cuestionarios/${id}/ras`);

export const misCursos = () => peticion<MiCurso[]>("/api/mis-cursos");
export const unirseACurso = (codigo: string) => post<MiCurso>("/api/mis-cursos/unirse", { codigo: codigo.trim() });
export const salirDelCurso = (grupoId: number) => borrar(`/api/mis-cursos/${grupoId}`);

export const obtenerCoordinacion = (programaId?: number | null, periodo?: string | null) => {
  const q = new URLSearchParams();
  if (programaId) q.set("programa_id", String(programaId));
  if (periodo) q.set("periodo", periodo);
  return peticion<Coordinacion>(`/api/coordinacion/resumen${q.size ? `?${q}` : ""}`);
};
export const descargarPdfRa = (programaId?: number | null, periodo?: string | null) => {
  const q = new URLSearchParams();
  if (programaId) q.set("programa_id", String(programaId));
  if (periodo) q.set("periodo", periodo);
  return descargarArchivo(`/api/coordinacion/reporte-ra.pdf${q.size ? `?${q}` : ""}`, `reporte_ra_${periodo ?? "todos"}.pdf`);
};

export const listarAlertas = () => peticion<Alerta[]>("/api/alertas");
export const atenderAlerta = (grupo_id: number, estudiante_id: number, nota: string) =>
  post<unknown>("/api/alertas/atender", { grupo_id, estudiante_id, nota });

// Administración (rol admin)
export const adminFacultades = () => peticion<Facultad[]>("/api/admin/facultades");
export const adminCrearFacultad = (nombre: string) => post<Facultad>("/api/admin/facultades", { nombre });
export const adminEditarFacultad = (id: number, nombre: string) => enviar<Facultad>("PATCH", `/api/admin/facultades/${id}`, { nombre });
export const adminEliminarFacultad = (id: number) => borrar(`/api/admin/facultades/${id}`);

export const adminProgramas = () => peticion<Programa[]>("/api/admin/programas");
export const adminCrearPrograma = (facultad_id: number, nombre: string, codigo: string) =>
  post<Programa>("/api/admin/programas", { facultad_id, nombre, codigo });
export const adminEditarPrograma = (id: number, datos: { facultad_id?: number; nombre?: string; codigo?: string }) =>
  enviar<Programa>("PATCH", `/api/admin/programas/${id}`, datos);
export const adminEliminarPrograma = (id: number) => borrar(`/api/admin/programas/${id}`);

export const adminAsignaturas = () => peticion<Asignatura[]>("/api/admin/asignaturas");
export const adminCrearAsignatura = (programa_id: number, nombre: string, codigo: string, semestre: number) =>
  post<Asignatura>("/api/admin/asignaturas", { programa_id, nombre, codigo, semestre });
export const adminEditarAsignatura = (id: number, datos: { nombre?: string; codigo?: string; semestre?: number }) =>
  enviar<Asignatura>("PATCH", `/api/admin/asignaturas/${id}`, datos);
export const adminAsignarRas = (id: number, ra_ids: number[]) => enviar<Asignatura>("PUT", `/api/admin/asignaturas/${id}/ras`, { ra_ids });
export const adminEliminarAsignatura = (id: number) => borrar(`/api/admin/asignaturas/${id}`);

export const adminRas = () => peticion<ResultadoAprendizaje[]>("/api/admin/ras");
export const adminCrearRa = (programa_id: number, codigo: string, descripcion: string) =>
  post<ResultadoAprendizaje>("/api/admin/ras", { programa_id, codigo, descripcion });
export const adminEditarRa = (id: number, datos: { codigo?: string; descripcion?: string }) =>
  enviar<ResultadoAprendizaje>("PATCH", `/api/admin/ras/${id}`, datos);
export const adminEliminarRa = (id: number) => borrar(`/api/admin/ras/${id}`);

export const adminUsuarios = () => peticion<UsuarioAdmin[]>("/api/admin/usuarios");
export const adminEditarUsuario = (id: number, datos: { rol?: string; programa_id?: number | null }) =>
  enviar<UsuarioAdmin>("PATCH", `/api/admin/usuarios/${id}`, datos);

// ---------- Clase en vivo (Sprint 7) ----------

export const iniciarClaseVivo = (cuestionarioId: number, segundos: number) =>
  post<SesionVivoInfo>(`/api/cuestionarios/${cuestionarioId}/vivo`, { segundos_por_pregunta: segundos });

export const obtenerSesionVivo = (id: number) => peticion<SesionVivoInfo>(`/api/vivo/sesiones/${id}`);

export const accionSesionVivo = (id: number, accion: string) =>
  post<void>(`/api/vivo/sesiones/${id}/accion`, { accion });

export const unirseClaseVivo = (pin: string, apodo: string) => post<UnidoVivo>("/api/vivo/unirse", { pin, apodo });

/** Sondeo de respaldo. Con `participante` va como participante; sin él, el JWT guardado lo identifica como presentador. */
export const estadoClaseVivo = (pin: string, participante?: string) =>
  peticion<EstadoVivo>(`/api/vivo/${pin}/estado${participante ? `?participante=${encodeURIComponent(participante)}` : ""}`);

export const responderClaseVivo = (pin: string, token: string, respuesta: string) =>
  post<void>(`/api/vivo/${pin}/responder`, { token, respuesta });

/** URL del WebSocket de la clase en vivo (el esquema ws/wss sigue al de la API). */
export function urlWsVivo(pin: string, rol: "presentador" | "participante", credencial: string): string {
  const base = API_URL.replace(/^http/, "ws");
  const param = rol === "presentador" ? "token" : "participante";
  return `${base}/ws/vivo/${pin}?${param}=${encodeURIComponent(credencial)}`;
}

export const historialClaseVivo = (cuestionarioId: number) =>
  peticion<HistorialVivo[]>(`/api/cuestionarios/${cuestionarioId}/vivo`);

export const descargarCsvVivo = (cuestionarioId: number) =>
  descargarArchivo(`/api/cuestionarios/${cuestionarioId}/vivo.csv`, `clases_en_vivo_${cuestionarioId}.csv`);

// ---------- Notificaciones (Sprint 7) ----------

export const listarNotificaciones = (pagina = 1, porPagina = 20) =>
  peticion<PaginaNotificaciones>(`/api/notificaciones?pagina=${pagina}&por_pagina=${porPagina}`);

export const contarNotificaciones = () => peticion<{ no_leidas: number }>("/api/notificaciones/no-leidas");

export const marcarNotificacionLeida = (id: number) => post<{ no_leidas: number }>(`/api/notificaciones/${id}/leer`);

export const marcarTodasLeidas = () => post<{ no_leidas: number }>("/api/notificaciones/leer-todas");

// ---------- Sprint 8: tutor IA, calidad, banco y accesibilidad ----------

export const estadoTutor = (cuestionarioId: number) => peticion<EstadoTutor>(`/api/cuestionarios/${cuestionarioId}/tutor`);

export const preguntarAlTutor = (cuestionarioId: number, pregunta: string) =>
  post<RespuestaTutor>(`/api/cuestionarios/${cuestionarioId}/tutor`, { pregunta });

export const nuevaConversacionTutor = (cuestionarioId: number) =>
  post<EstadoTutor>(`/api/cuestionarios/${cuestionarioId}/tutor/nueva`);

export const verificarCalidad = (cuestionarioId: number) =>
  post<{ verificadas: number; total: number }>(`/api/cuestionarios/${cuestionarioId}/verificar`);

export const calificarAbierta = (intentoId: number, preguntaId: number, nota: number) =>
  enviar<IntentoResumen>("PUT", `/api/intentos/${intentoId}/abiertas/${preguntaId}/nota`, { nota });

export const guardarEnBanco = (
  preguntaId: number,
  datos: { visibilidad: "institucional" | "privada"; etiquetas: string[]; asignatura_nombre?: string },
) => post<PreguntaBanco>(`/api/preguntas/${preguntaId}/banco`, datos);

export interface FiltroBanco {
  q?: string;
  asignatura?: string;
  ra?: string;
  bloom?: string;
  tipo?: string;
  verificacion?: string;
  solo_mias?: boolean;
  pagina?: number;
}

export function buscarBanco(f: FiltroBanco) {
  const q = new URLSearchParams();
  for (const [clave, valor] of Object.entries(f)) if (valor !== undefined && valor !== "" && valor !== false) q.set(clave, String(valor));
  return peticion<PaginaBanco>(`/api/banco${q.size ? `?${q}` : ""}`);
}

export const filtrosBanco = () => peticion<FiltrosBanco>("/api/banco/filtros");

export const editarBanco = (id: number, datos: { visibilidad?: "institucional" | "privada"; etiquetas?: string[] }) =>
  enviar<PreguntaBanco>("PATCH", `/api/banco/${id}`, datos);

export const eliminarDelBanco = (id: number) => borrar(`/api/banco/${id}`);

export const agregarDesdeBanco = (bancoId: number, cuestionarioId: number) =>
  post<{ pregunta_id: number; cuestionario_id: number; num_preguntas: number }>(`/api/banco/${bancoId}/agregar`, {
    cuestionario_id: cuestionarioId,
  });

export const obtenerTranscripcion = (videoId: number) => peticion<TranscripcionVideo>(`/api/videos/${videoId}/transcripcion`);

/** Descarga los subtítulos WebVTT con el token y devuelve una URL de objeto para usarla en <track>. */
export async function urlSubtitulos(videoId: number): Promise<string> {
  const token = leerToken();
  const resp = await fetch(`${API_URL}/api/videos/${videoId}/subtitulos.vtt`, { headers: token ? { Authorization: `Bearer ${token}` } : {} });
  if (!resp.ok) throw new Error("No se pudieron cargar los subtítulos.");
  return URL.createObjectURL(await resp.blob());
}

export const descargarTranscripcion = (videoId: number) => descargarArchivo(`/api/videos/${videoId}/transcripcion.txt`, `transcripcion_${videoId}.txt`);

export const descargarSubtitulos = (videoId: number) => descargarArchivo(`/api/videos/${videoId}/subtitulos.vtt`, `subtitulos_${videoId}.vtt`);
