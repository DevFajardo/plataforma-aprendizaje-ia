// Tipos que reflejan backend/app/schemas_api.py

export type TipoPregunta = "opcion_multiple" | "verdadero_falso" | "abierta";

export interface Usuario {
  id: number;
  nombre: string;
  email: string;
  rol: "estudiante" | "docente";
  acepta_tratamiento_datos: boolean;
  consentimiento_investigacion: boolean;
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
}

export interface CuestionarioDetalle {
  id: number;
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
  respuestas_abiertas: { nombre: string; respuesta: string }[];
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
}

export interface RespuestaServidor {
  registrada: boolean;
  con_feedback: boolean; // false en repasos diferidos y en el grupo control
  correcta: boolean | null; // null = pregunta abierta o sin retroalimentación
  respuesta_correcta: string;
  explicacion: string;
  marca_tiempo: string;
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
