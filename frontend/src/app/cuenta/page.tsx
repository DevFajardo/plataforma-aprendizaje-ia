"use client";

import { useState } from "react";
import BotonInstalarApp from "@/components/BotonInstalarApp";
import { useTutorial } from "@/components/Tutorial";
import {
  Aviso,
  Boton,
  Casilla,
  ConfirmacionEnLinea,
  EncabezadoPagina,
  Enlace,
  EsqueletoPagina,
  Icono,
  Input,
  Insignia,
  Pagina,
  Tarjeta,
  type MensajeForm,
  type NombreIcono,
} from "@/components/ui";
import { editarCuenta, eliminarCuenta, obtenerMisDatos } from "@/lib/api";
import { useRequiereLogin } from "@/lib/auth";

function Seccion({ icono, titulo, children, peligro, ...resto }: { icono: NombreIcono; titulo: string; children: React.ReactNode; peligro?: boolean } & React.HTMLAttributes<HTMLElement>) {
  return (
    <Tarjeta as="section" className={"flex flex-col gap-4 " + (peligro ? "border-error-borde" : "")} {...resto}>
      <h2 className={"flex items-center gap-3 text-lg font-bold " + (peligro ? "text-error-texto" : "")}>
        <span
          className={
            "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg " + (peligro ? "bg-error-fondo text-error-texto" : "bg-info-fondo text-info-texto")
          }
        >
          <Icono nombre={icono} tamano={20} />
        </span>
        {titulo}
      </h2>
      {children}
    </Tarjeta>
  );
}

const ROLES: Record<string, string> = { docente: "Docente", estudiante: "Estudiante", coordinador: "Coordinador", admin: "Administrador" };

export default function CuentaPage() {
  const { usuario, cargando, actualizarUsuario, logout } = useRequiereLogin();
  const tutorial = useTutorial();

  const [nombre, setNombre] = useState<string | null>(null); // null = sin editar (se muestra el actual)
  const [msgNombre, setMsgNombre] = useState<MensajeForm>(null);
  const [actual, setActual] = useState("");
  const [nueva, setNueva] = useState("");
  const [msgClave, setMsgClave] = useState<MensajeForm>(null);
  const [msgPrivacidad, setMsgPrivacidad] = useState<MensajeForm>(null);
  const [msgDatos, setMsgDatos] = useState<MensajeForm>(null);
  const [confirmando, setConfirmando] = useState(false);
  const [claveBorrar, setClaveBorrar] = useState("");
  const [msgBorrar, setMsgBorrar] = useState<MensajeForm>(null);
  const [ocupado, setOcupado] = useState(false);

  if (cargando || !usuario) {
    return (
      <Pagina ancho="md">
        <EsqueletoPagina />
      </Pagina>
    );
  }

  const mensajeError = (e: unknown): MensajeForm => ({ tipo: "error", texto: e instanceof Error ? e.message : "Error desconocido" });

  async function guardarNombre(e: React.FormEvent) {
    e.preventDefault();
    setMsgNombre(null);
    setOcupado(true);
    try {
      actualizarUsuario(await editarCuenta({ nombre: (nombre ?? "").trim() }));
      setNombre(null);
      setMsgNombre({ tipo: "ok", texto: "Nombre actualizado." });
    } catch (err) {
      setMsgNombre(mensajeError(err));
    } finally {
      setOcupado(false);
    }
  }

  async function cambiarClave(e: React.FormEvent) {
    e.preventDefault();
    setMsgClave(null);
    setOcupado(true);
    try {
      await editarCuenta({ password_actual: actual, password_nueva: nueva });
      setActual("");
      setNueva("");
      setMsgClave({ tipo: "ok", texto: "Contraseña actualizada." });
    } catch (err) {
      setMsgClave(mensajeError(err));
    } finally {
      setOcupado(false);
    }
  }

  async function cambiarInvestigacion(valor: boolean) {
    setMsgPrivacidad(null);
    try {
      actualizarUsuario(await editarCuenta({ consentimiento_investigacion: valor }));
      setMsgPrivacidad({ tipo: "ok", texto: valor ? "Gracias por participar en el estudio." : "Participación en el estudio revocada." });
    } catch (err) {
      setMsgPrivacidad(mensajeError(err));
    }
  }

  async function aceptarPolitica() {
    setMsgPrivacidad(null);
    try {
      actualizarUsuario(await editarCuenta({ acepta_tratamiento_datos: true }));
      setMsgPrivacidad({ tipo: "ok", texto: "Política aceptada." });
    } catch (err) {
      setMsgPrivacidad(mensajeError(err));
    }
  }

  async function descargarDatos() {
    setMsgDatos(null);
    setOcupado(true);
    try {
      const datos = await obtenerMisDatos();
      const url = URL.createObjectURL(new Blob([JSON.stringify(datos, null, 2)], { type: "application/json" }));
      const a = document.createElement("a");
      a.href = url;
      a.download = "mis_datos.json";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setMsgDatos({ tipo: "ok", texto: "Descarga lista (mis_datos.json)." });
    } catch (err) {
      setMsgDatos(mensajeError(err));
    } finally {
      setOcupado(false);
    }
  }

  async function borrarCuenta(e: React.FormEvent) {
    e.preventDefault();
    setMsgBorrar(null);
    setOcupado(true);
    try {
      await eliminarCuenta(claveBorrar);
      logout("/");
    } catch (err) {
      setMsgBorrar(mensajeError(err));
      setOcupado(false);
    }
  }

  return (
    <Pagina ancho="md">
      <EncabezadoPagina
        titulo="Mi cuenta"
        descripcion={usuario.email}
        etiquetas={<Insignia tono="azul">{ROLES[usuario.rol] ?? usuario.rol}</Insignia>}
      />

      <div className="flex flex-col gap-5 sm:gap-6">
        <form onSubmit={guardarNombre}>
          <Seccion icono="usuario" titulo="Datos personales">
            <Input etiqueta="Nombre" required maxLength={100} value={nombre ?? usuario.nombre} onChange={(e) => setNombre(e.target.value)} />
            <Boton type="submit" cargando={ocupado} disabled={nombre === null} className="sm:self-start">
              Guardar nombre
            </Boton>
            <Aviso mensaje={msgNombre} />
          </Seccion>
        </form>

        <form onSubmit={cambiarClave}>
          <Seccion icono="escudo" titulo="Cambiar contraseña">
            <Input
              etiqueta="Contraseña actual"
              type="password"
              required
              value={actual}
              onChange={(e) => setActual(e.target.value)}
              autoComplete="current-password"
            />
            <Input
              etiqueta="Contraseña nueva (mínimo 8 caracteres)"
              type="password"
              required
              minLength={8}
              value={nueva}
              onChange={(e) => setNueva(e.target.value)}
              autoComplete="new-password"
            />
            <Boton type="submit" cargando={ocupado} className="sm:self-start">
              Cambiar contraseña
            </Boton>
            <Aviso mensaje={msgClave} />
          </Seccion>
        </form>

        <Seccion icono="ayuda" titulo="Ayuda y aplicación" data-tutorial="ayuda">
          {tutorial.disponible && (
            <div className="flex flex-col gap-2">
              <p className="text-sm text-suave">Repasa en pocos pasos cómo se usa la plataforma según tu rol.</p>
              <Boton variante="secundario" onClick={() => tutorial.abrir()} className="sm:self-start">
                <Icono nombre="play" tamano={18} /> Ver tutorial
              </Boton>
            </div>
          )}
          <div className="flex flex-col gap-2">
            <p className="text-sm text-suave">Instala la plataforma en tu celular o computador para abrirla como una app.</p>
            <BotonInstalarApp variante="completa" />
          </div>
        </Seccion>

        <Seccion icono="escudo" titulo="Privacidad y consentimiento">
          {usuario.acepta_tratamiento_datos ? (
            <p className="flex items-start gap-2 text-sm">
              <Icono nombre="check" className="mt-0.5 text-exito-texto" tamano={18} />
              <span>
                Aceptaste la <Enlace href="/privacidad">política de tratamiento de datos personales</Enlace>.
              </span>
            </p>
          ) : (
            <div className="flex flex-col gap-3 text-sm">
              <p>
                Tu cuenta es anterior a la política de datos. Léela en <Enlace href="/privacidad">Política de tratamiento de datos personales</Enlace> y
                acéptala para continuar usando la plataforma con tranquilidad.
              </p>
              <Boton onClick={aceptarPolitica} className="sm:self-start">
                Acepto la política
              </Boton>
            </div>
          )}
          <Casilla checked={usuario.consentimiento_investigacion} onChange={(e) => cambiarInvestigacion(e.target.checked)}>
            Participo en el estudio de evaluación de la plataforma (mis resultados se usarán de forma anónima). Puedes revocarlo cuando quieras.
          </Casilla>
          <Aviso mensaje={msgPrivacidad} />
        </Seccion>

        <Seccion icono="descargar" titulo="Descargar mis datos">
          <p className="text-sm text-suave">Obtén un archivo JSON con tu información: cuenta, cuestionarios, intentos, repasos y encuesta.</p>
          <Boton variante="secundario" onClick={descargarDatos} cargando={ocupado} className="sm:self-start">
            <Icono nombre="descargar" /> Descargar mis datos
          </Boton>
          <Aviso mensaje={msgDatos} />
        </Seccion>

        <Seccion icono="basura" titulo="Eliminar mi cuenta" peligro>
          <p className="text-sm text-suave">
            Se borrarán de forma definitiva tu cuenta, tus intentos, repasos, encuesta, tareas, los cuestionarios que creaste (con sus preguntas) y los
            archivos que subiste. Esta acción no se puede deshacer.
          </p>
          {!confirmando ? (
            <Boton variante="peligroSuave" onClick={() => setConfirmando(true)} className="sm:self-start">
              Eliminar mi cuenta
            </Boton>
          ) : (
            <ConfirmacionEnLinea
              mensaje="Confirma que quieres eliminar tu cuenta definitivamente."
              textoConfirmar="Sí, eliminar definitivamente"
              textoOcupado="Eliminando…"
              ocupado={ocupado}
              alEnviar={borrarCuenta}
              onCancelar={() => {
                setConfirmando(false);
                setClaveBorrar("");
                setMsgBorrar(null);
              }}
            >
              <Input
                etiqueta="Escribe tu contraseña para confirmar"
                type="password"
                required
                value={claveBorrar}
                onChange={(e) => setClaveBorrar(e.target.value)}
                autoComplete="current-password"
              />
              <Aviso mensaje={msgBorrar} />
            </ConfirmacionEnLinea>
          )}
        </Seccion>
      </div>
    </Pagina>
  );
}
