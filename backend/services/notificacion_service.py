"""Notificaciones internas tipo campana (RF16, HU 3.4, HU 4.4) y contacto por WhatsApp (RF10)."""
from datetime import datetime
from urllib.parse import quote

from config import CODIGO_PAIS_WHATSAPP
from database import tabla
from permisos import RECIBIR_ALERTAS, tiene_permiso
from services import academico_service as acad
from services.errores import ErrorNegocio


def crear(id_usuario: int | str, rut: str, tipo: str, mensaje: str, clave_evento: str = "") -> bool:
    """Crea una notificación salvo que ya exista una con la misma clave para ese usuario."""
    t = tabla("NOTIFICACION")
    if clave_evento and any(n["clave_evento"] == clave_evento and n["id_usuario"] == str(id_usuario)
                            for n in t.todos()):
        return False
    t.agregar({"id_notificacion": t.siguiente_id("id_notificacion"), "id_usuario": id_usuario,
               "rut_estudiante": rut, "tipo": tipo, "mensaje": mensaje,
               "fecha": datetime.now().isoformat(timespec="seconds"), "leida": "0",
               "clave_evento": clave_evento})
    return True


def destinatarios_alerta(e: dict) -> list[dict]:
    """Usuarios activos que reciben alertas; el profesor jefe solo las de su curso."""
    return [u for u in tabla("USUARIO").todos()
            if u["activo"] == "1" and tiene_permiso(u["rol"], RECIBIR_ALERTAS)
            and (u["rol"] != "profesor_jefe" or u["id_nivel"] == str(e["id_nivel"]))]


def alertar_equipo(e: dict, tipo: str, clave: str, mensaje: str) -> int:
    return sum(crear(u["id_usuario"], e["rut_estudiante"], tipo, mensaje, clave) for u in destinatarios_alerta(e))


def listar(id_usuario: int, solo_no_leidas: bool = False) -> list[dict]:
    filas = [n for n in tabla("NOTIFICACION").todos() if n["id_usuario"] == str(id_usuario)
             and (not solo_no_leidas or n["leida"] == "0")]
    return [{"id_notificacion": int(n["id_notificacion"]), "rut_estudiante": n["rut_estudiante"] or None,
             "tipo": n["tipo"], "mensaje": n["mensaje"], "fecha": n["fecha"], "leida": n["leida"] == "1"}
            for n in sorted(filas, key=lambda n: (n["fecha"], int(n["id_notificacion"])), reverse=True)]


def cantidad_no_leidas(id_usuario: int) -> int:
    return sum(1 for n in tabla("NOTIFICACION").todos() if n["id_usuario"] == str(id_usuario) and n["leida"] == "0")


def marcar_leida(id_notificacion: int, id_usuario: int) -> None:
    n = tabla("NOTIFICACION").actualizar(
        lambda f: f["id_notificacion"] == str(id_notificacion) and f["id_usuario"] == str(id_usuario),
        {"leida": "1"})
    if not n:
        raise ErrorNegocio(404, "Notificación no encontrada")


def marcar_todas_leidas(id_usuario: int) -> int:
    return tabla("NOTIFICACION").actualizar(
        lambda f: f["id_usuario"] == str(id_usuario) and f["leida"] == "0", {"leida": "1"})


MENSAJE_WHATSAPP = ("Hola {apoderado}, le saluda {usuario} del liceo. Quisiera conversar con usted "
                    "sobre {estudiante}. ¿Cuándo podríamos hablar? Muchas gracias.")


def enlace_whatsapp(rut: str, nombre_usuario: str) -> dict:
    """Enlace wa.me con un mensaje predefinido que no menciona el nivel de riesgo (sin etiquetas)."""
    e = acad.estudiante(rut)
    apoderado = acad.apoderados().get(e["rut_apoderado"])
    if not apoderado or not apoderado["telefono"]:
        raise ErrorNegocio(404, "El estudiante no tiene un teléfono de apoderado registrado")
    mensaje = MENSAJE_WHATSAPP.format(apoderado=apoderado["nombre"], usuario=nombre_usuario,
                                      estudiante=e["nombre"])
    numero = f"{CODIGO_PAIS_WHATSAPP}{apoderado['telefono']}"
    return {"telefono": apoderado["telefono"], "mensaje": mensaje,
            "url": f"https://wa.me/{numero}?text={quote(mensaje)}"}
