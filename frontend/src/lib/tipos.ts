// Tipos que reflejan backend/app/schemas_api.py

export type TipoPregunta = "opcion_multiple" | "verdadero_falso" | "abierta";

export type Rol = "estudiante" | "docente" | "coordinador" | "admin";

export interface Usuario {
  id: number;
  nombre: string;
  email: string;
  rol: Rol;
  programa_id?: number | null;
  acepta_tratamiento_datos: boolean;
  consentimiento_investigacion: boolean;
  /** Roles cuyo tutorial de primer uso ya vio el usuario. */
  tutorial_visto?: string[];
}

export interface RespuestaAuth {
  token: string;
  usuario: Usuario;
}

export type EstadoTarea =
  | "pendiente"
  | "transcribiendo"
  | "generando"
  | "listo"
  | "error";

export interface Tarea {
  id: string;
  url: string;
  estado: EstadoTarea;
  mensaje: string;
  fuente_transcripcion: string | null;
  proveedor_ia: string | null;
  cuestionario_id: number | null;
}

export interface Pregunta {
  id: number;
  orden: number;
  tipo: TipoPregunta;
  enunciado: string;
  opciones: string[];
  marca_tiempo: string; // mm:ss
  // Solo vienen para el creador; el feedback oficial lo da el servidor al responder
  respuesta_correcta: string | null;
  explicacion: string | null;
  // Sprint 6 (solo el creador): resultado de aprendizaje y nivel de Bloom
  ra_id?: number | null;
  nivel_bloom?: NivelBloom | null;
  // Sprint 8 (solo el creador): verificación de calidad con IA (null/ausente = sin verificar) y vínculo con el banco
  verificacion?: Verificacion | null;
  banco_id?: number | null;
}

export interface Verificacion {
  estado: "verificada" | "revisar";
  respaldo: "si" | "parcial" | "no";
  cita: string;
  marca_tiempo: string;
  inequivoca: boolean;
  problemas: string[];
}

export type NivelBloom = "recordar" | "comprender" | "aplicar" | "analizar" | "evaluar" | "crear";
export const NIVELES_BLOOM: NivelBloom[] = ["recordar", "comprender", "aplicar", "analizar", "evaluar", "crear"];

export interface CuestionarioDetalle {
  id: number;
  video_id: number;
  titulo: string;
  resumen: string;
  ideas_clave: string[];
  proveedor_ia: string;
  num_preguntas: number;
  publicado: boolean;
  codigo_compartir: string | null;
  es_creador: boolean;
  youtube_id: string | null;
  medio: "youtube" | "vimeo" | "video" | "audio";
  video_externo_id: string | null;
  vimeo_hash: string | null;
  archivo_url: string | null;
  url: string;
  creado_en: string;
  modo: ModoCuestionario;
  repaso_dias: number | null;
  repaso: { disponible_desde: string; vencido: boolean } | null;
  // Solo el creador
  segundos_edicion: number | null;
  estimacion_manual_min: number | null;
  publicado_en: string | null;
  grupo_id?: number | null;
  grupo_nombre?: string | null;
  asignatura_nombre?: string | null;
  preguntas: Pregunta[];
}

export type ModoCuestionario = "aprendizaje" | "control";
export type TipoIntento = "inicial" | "practica" | "diferido";

export interface CuestionarioResumen {
  id: number;
  titulo: string;
  creado_en: string;
  num_preguntas: number;
  youtube_id: string | null;
  plataforma: string;
  modo: ModoCuestionario;
  publicado: boolean;
  mejor_puntaje: number | null;
  mejor_total: number | null;
  propio: boolean; // false = cuestionario ajeno al que me uní
  creador: string | null;
}

export interface Compartido {
  cuestionario_id: number;
  titulo: string;
  creador: string;
}

/** Datos que se envían al crear/editar una pregunta. */
export interface EntradaPregunta {
  tipo: TipoPregunta;
  enunciado: string;
  opciones: string[];
  respuesta_correcta: string;
  explicacion: string;
  marca_tiempo: string;
  ra_id?: number | null;
  nivel_bloom?: NivelBloom | null;
}

export interface IntentoResultado {
  intento_id: number;
  nombre: string;
  email: string;
  puntaje: number;
  total: number;
  porcentaje: number;
  fecha: string;
  tipo: TipoIntento;
  consentimiento_investigacion: boolean;
}

export interface PreguntaResultado {
  pregunta_id: number;
  orden: number;
  tipo: TipoPregunta;
  enunciado: string;
  num_respuestas: number;
  porcentaje_acierto: number | null;
  respuestas_abiertas: RespuestaAbierta[];
}

export type NivelCalificacion = "insuficiente" | "basico" | "bueno" | "excelente";

export interface CalificacionIA {
  puntaje: number;
  nivel: NivelCalificacion;
  retroalimentacion: string;
  falto: string;
}

export interface RespuestaAbierta {
  intento_id: number | null;
  nombre: string;
  respuesta: string;
  sugerida: CalificacionIA | null;
  nota_final: number | null; // aprobada o ajustada por el docente
}

export interface Distractor {
  opcion: string;
  letra: string;
  correcta: boolean;
  porcentaje: number;
  porcentaje_superior: number | null;
  porcentaje_inferior: number | null;
  funcional: boolean | null;
  confunde_mejores: boolean;
}

export interface ItemAnalisis {
  pregunta_id: number;
  orden: number;
  enunciado: string;
  n: number;
  suficiente: boolean;
  p: number | null;
  d: number | null;
  r_pb: number | null;
  dificultad: string;
  discriminacion: string;
  distractores: Distractor[];
  observaciones: string[];
  revisar: boolean;
}

export interface Resultados {
  titulo: string;
  total_intentos: number;
  estudiantes_unicos: number;
  promedio_porcentaje: number;
  intentos: IntentoResultado[];
  preguntas: PreguntaResultado[];
  ganancia: GananciaAprendizaje;
  retencion: Retencion;
  modo: ModoCuestionario;
  items: ItemAnalisis[];
  items_minimo: number;
  items_intentos: number;
}

export interface RespuestaServidor {
  registrada: boolean;
  con_feedback: boolean; // false en repasos diferidos y en el grupo control
  correcta: boolean | null; // null = pregunta abierta o sin retroalimentación
  respuesta_correcta: string;
  explicacion: string;
  marca_tiempo: string;
  calificacion_ia?: CalificacionIA | null; // solo preguntas abiertas con retroalimentación
}

export interface IntentoCreado {
  id: number;
  cuestionario_id: number;
  tipo: TipoIntento;
  con_feedback: boolean;
}

export interface RevisionPregunta {
  pregunta_id: number;
  enunciado: string;
  respuesta: string;
  correcta: boolean | null;
  respuesta_correcta: string;
  explicacion: string;
  marca_tiempo: string;
}

export interface Repaso {
  id: number;
  cuestionario_id: number;
  cuestionario_titulo: string;
  disponible_desde: string;
  vencido: boolean;
}

export interface IntentoResumen {
  id: number;
  cuestionario_id: number;
  puntaje: number;
  total: number;
  porcentaje: number;
  finalizado: boolean;
  creado_en: string;
  tipo: TipoIntento;
  revision: RevisionPregunta[] | null; // respuestas correctas al terminar un repaso diferido
  repaso_disponible_desde: string | null;
}

export interface IntentoHistorial extends IntentoResumen {
  cuestionario_titulo: string;
}

// ---------- Ganancia de aprendizaje (resultados del docente) ----------

export interface EstudianteGanancia {
  nombre: string;
  email: string;
  intentos: number;
  primer_porcentaje: number;
  ultimo_porcentaje: number;
  diferencia: number;
}

export interface GananciaAprendizaje {
  estudiantes: number;
  promedio_primer_intento: number | null;
  promedio_ultimo_intento: number | null;
  diferencia_puntos: number | null;
  detalle: EstudianteGanancia[];
}

// ---------- Retención (post-test diferido) ----------

export interface EstudianteRetencion {
  nombre: string;
  email: string;
  inicial: number;
  diferido: number;
  retencion: number | null;
  diferencia: number;
}

export interface Retencion {
  repaso_dias: number | null;
  estudiantes: number;
  promedio_inicial: number | null;
  promedio_diferido: number | null;
  retencion_pct: number | null;
  diferencia_puntos: number | null;
  detalle: EstudianteRetencion[];
}

// ---------- Comparación de grupos ----------

export interface MetricaGrupo {
  n: number;
  media: number | null;
  desviacion: number | null;
}

export interface Efecto {
  diferencia_medias: number | null;
  d_cohen: number | null;
  interpretacion: string;
}

export interface GrupoComparacion {
  id: number;
  titulo: string;
  modo: ModoCuestionario;
  inicial: MetricaGrupo;
  diferido: MetricaGrupo;
  retencion: MetricaGrupo;
}

export interface Comparacion {
  a: GrupoComparacion;
  b: GrupoComparacion;
  efecto_inicial: Efecto;
  efecto_diferido: Efecto;
  efecto_retencion: Efecto;
  nota: string;
}

// ---------- Estadísticas (panel) ----------

export interface PuntoEvolucion {
  fecha: string;
  porcentaje: number;
  cuestionario_titulo: string;
}

export interface TemaReforzar {
  pregunta_id: number;
  enunciado: string;
  cuestionario_id: number;
  cuestionario_titulo: string;
  fallos: number;
}

export interface ResumenCuestionarioDocente {
  id: number;
  titulo: string;
  intentos: number;
  promedio: number | null;
  codigo_compartir: string;
}

export interface EstadisticasDocente {
  cuestionarios_publicados: number;
  estudiantes_unicos: number;
  intentos_recibidos: number;
  promedio_general: number | null;
  por_cuestionario: ResumenCuestionarioDocente[];
  tiempo: TiempoDocente;
}

export interface TiempoDocente {
  cuestionarios_con_estimacion: number;
  promedio_herramienta_min: number | null;
  promedio_manual_min: number | null;
  ahorro_pct: number | null;
}

export interface Estadisticas {
  rol: "estudiante" | "docente";
  intentos_finalizados: number;
  promedio_porcentaje: number | null;
  mejor_porcentaje: number | null;
  retencion_promedio: number | null;
  cuestionarios_generados: number;
  cuestionarios_unidos: number;
  evolucion: PuntoEvolucion[];
  temas_a_reforzar: TemaReforzar[];
  docente: EstadisticasDocente | null;
}

// ---------- Encuesta SUS ----------

export interface RespuestaSus {
  respuestas: number[];
  puntaje: number;
  interpretacion: string;
  comentario: string | null;
  creado_en: string;
}

export interface ResumenSus {
  n: number;
  promedio: number | null;
  desviacion: number | null;
  minimo: number | null;
  maximo: number | null;
  interpretacion_promedio: string | null;
  distribucion: Record<string, number>;
  promedio_por_item: number[];
}


// ---------- Sprint 6: estructura académica, cursos, coordinación y alertas ----------

export interface Facultad {
  id: number;
  nombre: string;
  num_programas: number;
}
export interface Programa {
  id: number;
  facultad_id: number;
  facultad: string;
  nombre: string;
  codigo: string;
}
export interface Asignatura {
  id: number;
  programa_id: number;
  programa: string;
  nombre: string;
  codigo: string;
  semestre: number;
  ra_ids: number[];
}
export interface ResultadoAprendizaje {
  id: number;
  programa_id: number;
  programa: string;
  codigo: string;
  descripcion: string;
}
export interface UsuarioAdmin {
  id: number;
  nombre: string;
  email: string;
  rol: Rol;
  programa_id: number | null;
  programa: string | null;
}
export interface Grupo {
  id: number;
  nombre: string;
  periodo: string;
  codigo_ingreso: string;
  asignatura_id: number;
  asignatura: string;
  programa: string;
  docente: string;
  num_matriculados: number;
  num_cuestionarios: number;
}
export interface Matriculado {
  estudiante_id: number;
  nombre: string;
  email: string;
  desde: string;
}
export interface MiCurso {
  grupo_id: number;
  nombre: string;
  periodo: string;
  asignatura: string;
  programa: string;
  docente: string;
  cuestionarios: { id: number; titulo: string; num_preguntas: number; mejor_puntaje: number | null; mejor_total: number | null }[];
}
export type Semaforo = "verde" | "amarillo" | "rojo" | "sin_datos";
export interface LogroRa {
  ra_id: number;
  codigo: string;
  descripcion: string;
  programa: string;
  logro: number | null;
  respuestas: number;
  estudiantes: number;
  semaforo: Semaforo;
}
export interface LogroGrupo {
  grupo_id: number;
  nombre: string;
  periodo: string;
  docente: string;
  logro: number | null;
  respuestas: number;
  estudiantes: number;
  semaforo: Semaforo;
}
export interface LogroAsignatura {
  asignatura_id: number;
  nombre: string;
  codigo: string;
  logro: number | null;
  respuestas: number;
  estudiantes: number;
  semaforo: Semaforo;
  grupos: LogroGrupo[];
}
export interface Coordinacion {
  programas: { id: number; nombre: string }[];
  programa_id: number | null;
  programa_nombre: string;
  periodo: string | null;
  periodos: string[];
  logro_global: number | null;
  respuestas: number;
  estudiantes: number;
  ras: LogroRa[];
  bloom: { nivel: NivelBloom; preguntas: number; respuestas: number; logro: number | null }[];
  asignaturas: LogroAsignatura[];
  tendencia: { semana: string; logro: number; respuestas: number }[];
}
export interface Alerta {
  grupo_id: number;
  grupo: string;
  asignatura: string;
  estudiante_id: number;
  nombre: string;
  email: string;
  nivel: "alto" | "medio";
  motivos: { codigo: string; texto: string }[];
}

// ---------- Clase en vivo (Sprint 7) ----------

export type EstadoSesionVivo = "lobby" | "pregunta" | "resultados_pregunta" | "finalizada";

export interface SesionVivoInfo {
  id: number;
  cuestionario_id: number;
  titulo: string;
  pin: string;
  estado: EstadoSesionVivo;
  segundos_por_pregunta: number;
  total_preguntas: number;
}

export interface UnidoVivo {
  pin: string;
  apodo: string;
  token: string;
}

export interface PuestoVivo {
  apodo: string;
  puntos: number;
  posicion: number;
}

export interface ResultadosPreguntaVivo {
  distribucion: { opcion: string; cantidad: number; correcta: boolean }[];
  correcta: string | null;
  explicacion: string;
  respondieron: number;
  abiertas: string[];
}

/** Foto del estado de la sesión que el servidor envía por WebSocket (o por sondeo HTTP). */
export interface EstadoVivo {
  tipo: "estado";
  rol: "presentador" | "participante" | "publico";
  pin: string;
  titulo: string;
  estado: EstadoSesionVivo;
  indice: number;
  total_preguntas: number;
  segundos: number;
  restante_ms: number;
  num_participantes: number;
  participantes: string[];
  respondieron: number;
  pregunta: { id: number; tipo: string; enunciado: string; opciones: string[] } | null;
  resultados: ResultadosPreguntaVivo | null;
  ranking: PuestoVivo[];
  yo?: {
    apodo: string;
    puntos: number;
    posicion: number;
    respondio: boolean;
    mi_respuesta: string | null;
    correcta: boolean | null;
    puntos_ganados: number | null;
  };
  /** Marca de tiempo local (performance.now) en que llegó este estado; sirve para la cuenta regresiva. */
  _t?: number;
}

export interface HistorialVivo {
  id: number;
  creada_en: string;
  finalizada_en: string | null;
  estado: EstadoSesionVivo;
  pin: string;
  participantes: number;
  promedio_acierto: number | null;
  preguntas: { pregunta_id: number; orden: number; enunciado: string; tipo: string; respuestas: number; porcentaje_acierto: number | null }[];
}

// ---------- Notificaciones (Sprint 7) ----------

export interface Notificacion {
  id: number;
  tipo: "publicado" | "repaso" | "alerta" | "clase_vivo" | string;
  titulo: string;
  mensaje: string;
  enlace: string;
  leida: boolean;
  creada_en: string;
}

export interface PaginaNotificaciones {
  items: Notificacion[];
  total: number;
  pagina: number;
  por_pagina: number;
  no_leidas: number;
}

// ---------- Sprint 8: tutor IA, banco y transcripción ----------

export interface CitaTutor {
  marca_tiempo: string;
  fragmento: string;
}

export interface MensajeTutor {
  id: number;
  rol: "usuario" | "tutor";
  texto: string;
  citas: CitaTutor[];
  creado_en: string;
}

export interface EstadoTutor {
  habilitado: boolean;
  motivo: string;
  conversacion_id: number | null;
  mensajes: MensajeTutor[];
  restantes: number;
  limite: number;
  sugerencias: string[];
}

export interface RespuestaTutor {
  usuario: MensajeTutor;
  tutor: MensajeTutor;
  restantes: number;
}

export interface SegmentoTranscripcion {
  inicio: number;
  texto: string;
}

export interface TranscripcionVideo {
  idioma: string;
  fuente: string;
  segmentos: SegmentoTranscripcion[];
}

export type EstadoVerificacion = "verificada" | "revisar" | "sin_verificar";

export interface PreguntaBanco {
  id: number;
  autor: string;
  es_mia: boolean;
  visibilidad: "institucional" | "privada";
  tipo: TipoPregunta;
  enunciado: string;
  opciones: string[];
  respuesta_correcta: string;
  explicacion: string;
  nivel_bloom: NivelBloom | null;
  ra_codigo: string | null;
  ra_descripcion: string | null;
  asignatura_nombre: string | null;
  etiquetas: string[];
  verificacion: Verificacion | null;
  estado_verificacion: EstadoVerificacion;
  estadisticas: { respuestas: number; porcentaje_acierto: number | null; usos: number } | null;
  creado_en: string;
}

export interface PaginaBanco {
  total: number;
  pagina: number;
  por_pagina: number;
  items: PreguntaBanco[];
}

export interface FiltrosBanco {
  asignaturas: string[];
  ras: string[];
}
