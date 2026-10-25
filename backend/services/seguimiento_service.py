"""Seguimiento de casos: bitácora (RF09), línea de tiempo (RF11) y derivación (RF12)."""
from datetime import date, datetime

from database import tabla
from permisos import DERIVAR_CASOS, RECIBIR_DERIVACIONES, ROLES, tiene_permiso
from services import academico_service as acad
from services import notificacion_service
from services.errores import ErrorNegocio

# Tipos de acción mencionados en las HU y entrevistas (llamada, entrevista, tutoría,
# visita domiciliaria, contención y contacto por WhatsApp con el apoderado).
TIPOS_INTERVENCION = ["Llamada telefónica", "Entrevista", "Entrevista de tutoría", "Visita domiciliaria",
                      "Contención", "Mensaje WhatsApp al apoderado", "Otra"]
ESTADOS_CASO = ["abierto", "derivado", "cerrado"]


def _ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _usuarios() -> dict[str, dict]:
    return {u["id_usuario"]: u for u in tabla("USUARIO").todos()}


def _nombre_usuario(usuarios: dict, id_usuario: str) -> str | None:
    u = usuarios.get(str(id_usuario))
    return f"{u['nombre']} ({ROLES.get(u['rol'], u['rol'])})" if u else None


def registrar_intervencion(usuario: dict, rut: str, datos: dict) -> dict:
    if datos["tipo_intervencion"] not in TIPOS_INTERVENCION:
        raise ErrorNegocio(400, "Tipo de intervención no válido")
    if datos["fecha"] > date.today():
        raise ErrorNegocio(400, "La fecha de la intervención no puede ser futura")
    descripcion = datos["descripcion"].strip()
    if not descripcion:
        raise ErrorNegocio(400, "La descripción es obligatoria")
    t = tabla("INTERVENCION")
    fila = t.agregar({"id_intervencion": t.siguiente_id("id_intervencion"), "rut_estudiante": rut,
                      "fecha": datos["fecha"].isoformat(), "tipo_intervencion": datos["tipo_intervencion"],
                      "descripcion": descripcion, "id_usuario": usuario["id_usuario"],
                      "fecha_registro": _ahora()})
    if not _caso(rut):
        _crear_caso(rut, usuario["id_usuario"], usuario["id_usuario"], "Caso abierto al registrar la primera intervención")
    return _intervencion_publica(fila, _usuarios())


def _intervencion_publica(f: dict, usuarios: dict) -> dict:
    return {"id_intervencion": int(f["id_intervencion"]), "rut_estudiante": f["rut_estudiante"],
            "fecha": f["fecha"], "tipo_intervencion": f["tipo_intervencion"], "descripcion": f["descripcion"],
            "id_usuario": int(f["id_usuario"]), "responsable": _nombre_usuario(usuarios, f["id_usuario"]),
            "fecha_registro": f["fecha_registro"]}


def _caso(rut: str) -> dict | None:
    return next((c for c in tabla("CASO").todos() if c["rut_estudiante"] == rut), None)


def _crear_caso(rut: str, id_responsable, id_accion, motivo: str) -> dict:
    t = tabla("CASO")
    fecha = _ahora()
    caso = t.agregar({"id_caso": t.siguiente_id("id_caso"), "rut_estudiante": rut, "estado": "abierto",
                      "id_usuario_responsable": id_responsable, "fecha_actualizacion": fecha})
    _agregar_historial(caso["id_caso"], "abierto", id_responsable, id_accion, motivo, fecha)
    return caso


def _agregar_historial(id_caso, estado, id_responsable, id_accion, motivo, fecha) -> None:
    t = tabla("HISTORIAL_CASO")
    t.agregar({"id_historial": t.siguiente_id("id_historial"), "id_caso": id_caso, "estado": estado,
               "id_usuario_responsable": id_responsable, "id_usuario_accion": id_accion,
               "motivo": motivo, "fecha": fecha})


def caso_de(rut: str) -> dict | None:
    c = _caso(rut)
    if not c:
        return None
    usuarios = _usuarios()
    return {"id_caso": int(c["id_caso"]), "rut_estudiante": rut, "estado": c["estado"],
            "id_usuario_responsable": int(c["id_usuario_responsable"]),
            "responsable": _nombre_usuario(usuarios, c["id_usuario_responsable"]),
            "fecha_actualizacion": c["fecha_actualizacion"]}


def derivar(usuario: dict, rut: str, id_destino: int, motivo: str) -> dict:
    destino = _usuarios().get(str(id_destino))
    if not destino or destino["activo"] != "1" or not tiene_permiso(destino["rol"], RECIBIR_DERIVACIONES):
        raise ErrorNegocio(400, "El profesional de destino no es válido para recibir derivaciones")
    motivo = motivo.strip()
    if not motivo:
        raise ErrorNegocio(400, "El motivo de la derivación es obligatorio")
    caso = _caso(rut) or _crear_caso(rut, usuario["id_usuario"], usuario["id_usuario"], "Caso abierto para derivación")
    if caso["estado"] == "cerrado":
        raise ErrorNegocio(409, "El caso está cerrado; debe reabrirse antes de derivarlo")
    if caso["id_usuario_responsable"] == str(id_destino):
        raise ErrorNegocio(409, "El caso ya está asignado a ese profesional")
    fecha = _ahora()
    tabla("CASO").actualizar(lambda c: c["id_caso"] == caso["id_caso"],
                             {"estado": "derivado", "id_usuario_responsable": id_destino, "fecha_actualizacion": fecha})
    _agregar_historial(caso["id_caso"], "derivado", id_destino, usuario["id_usuario"], motivo, fecha)
    e = acad.estudiante(rut)
    notificacion_service.crear(id_destino, rut, "derivacion",
                               f"{usuario['nombre']} le derivó el caso de {e['nombre']} {e['apellido_paterno']} "
                               f"({e['nombre_nivel']}): {motivo}", f"derivacion:{caso['id_caso']}:{fecha}")
    return caso_de(rut)


def cambiar_estado(usuario: dict, rut: str, estado: str, motivo: str) -> dict:
    """Abre o cierra un caso. Para derivar se usa derivar()."""
    if estado not in ("abierto", "cerrado"):
        raise ErrorNegocio(400, "El estado debe ser 'abierto' o 'cerrado' (para derivar use la derivación)")
    caso = _caso(rut)
    if not caso:
        raise ErrorNegocio(404, "El estudiante no tiene un caso registrado")
    es_responsable = caso["id_usuario_responsable"] == str(usuario["id_usuario"])
    if not es_responsable and not tiene_permiso(usuario["rol"], DERIVAR_CASOS):
        raise ErrorNegocio(403, "Solo el responsable del caso o un usuario autorizado puede cambiar su estado")
    if caso["estado"] == estado:
        raise ErrorNegocio(409, f"El caso ya se encuentra {estado}")
    fecha = _ahora()
    tabla("CASO").actualizar(lambda c: c["id_caso"] == caso["id_caso"], {"estado": estado, "fecha_actualizacion": fecha})
    _agregar_historial(caso["id_caso"], estado, caso["id_usuario_responsable"], usuario["id_usuario"],
                       motivo.strip() or f"Caso {estado}", fecha)
    return caso_de(rut)


def linea_de_tiempo(rut: str) -> list[dict]:
    """Intervenciones y movimientos del caso, desde el más reciente al más antiguo (HU 3.3)."""
    usuarios = _usuarios()
    eventos = [{"clase": "intervencion", "orden": (f["fecha"], f["fecha_registro"]), **_intervencion_publica(f, usuarios)}
               for f in tabla("INTERVENCION").todos() if f["rut_estudiante"] == rut]
    caso = _caso(rut)
    if caso:
        for h in tabla("HISTORIAL_CASO").todos():
            if h["id_caso"] == caso["id_caso"]:
                eventos.append({"clase": "caso", "orden": (h["fecha"][:10], h["fecha"]),
                                "id_historial": int(h["id_historial"]), "fecha": h["fecha"], "estado": h["estado"],
                                "motivo": h["motivo"],
                                "responsable": _nombre_usuario(usuarios, h["id_usuario_responsable"]),
                                "realizado_por": _nombre_usuario(usuarios, h["id_usuario_accion"])})
    eventos.sort(key=lambda ev: ev["orden"], reverse=True)
    for ev in eventos:
        ev.pop("orden")
    return eventos


def casos_asignados(usuario: dict) -> list[dict]:
    estudiantes = {e["rut_estudiante"]: e for e in acad.estudiantes()}
    filas = []
    for c in tabla("CASO").todos():
        if c["id_usuario_responsable"] == str(usuario["id_usuario"]) and c["estado"] != "cerrado":
            e = estudiantes.get(c["rut_estudiante"], {})
            filas.append({**caso_de(c["rut_estudiante"]), "nombre_estudiante":
                          f"{e.get('nombre', '')} {e.get('apellido_paterno', '')} {e.get('apellido_materno', '')}".strip(),
                          "nombre_nivel": e.get("nombre_nivel")})
    filas.sort(key=lambda f: f["fecha_actualizacion"], reverse=True)
    return sorted(filas, key=lambda f: f["estado"] != "derivado")  # derivados primero (destacados)


def profesionales_derivacion() -> list[dict]:
    return [{"id_usuario": int(u["id_usuario"]), "nombre": u["nombre"], "rol": u["rol"],
             "nombre_rol": ROLES.get(u["rol"], u["rol"])}
            for u in tabla("USUARIO").todos() if u["activo"] == "1" and tiene_permiso(u["rol"], RECIBIR_DERIVACIONES)]
