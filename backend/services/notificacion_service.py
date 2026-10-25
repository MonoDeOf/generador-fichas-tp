"""Aviso interno de derivación (HU 3.4) y contacto por WhatsApp (RF10)."""
from datetime import datetime
from urllib.parse import quote

from config import CODIGO_PAIS_WHATSAPP
from database import tabla
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
