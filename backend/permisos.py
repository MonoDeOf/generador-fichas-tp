"""Roles y permisos (RNF04, RNF05, RNF07).

Los roles son los actores del Hito 1. La asignación de permisos se basa en el
diagrama de casos de uso, las historias de usuario y las entrevistas (por ejemplo:
"un profesor solo ve a su curso, pero Convivencia y Dirección ven el panorama completo").
"""

ROLES = {
    "administrador": "Administrador del sistema",
    "director": "Director",
    "jefe_utp": "Jefe de UTP",
    "profesor_jefe": "Profesor jefe",
    "profesor": "Profesor",
    "inspector": "Inspector",
    "dupla_psicosocial": "Dupla psicosocial",
    "encargado_convivencia": "Encargado de convivencia",
    "profesional_convivencia": "Profesional de convivencia escolar",
    "miembro_convivencia": "Miembro de convivencia",
}

VER_ESTUDIANTES = "ver_estudiantes"          # lista, búsqueda y filtros (RF04)
VER_FICHA = "ver_ficha"                      # ficha integral, asistencia, notas (RF05, RF07)
VER_RIESGO = "ver_riesgo"                    # semáforo y factores (RF13, RF15, RNF07)
VER_CONVIVENCIA = "ver_convivencia"          # anotaciones (RF08)
EDITAR_CONTACTO = "editar_contacto"          # RF06
CONTACTAR_APODERADO = "contactar_apoderado"  # RF10
REGISTRAR_INTERVENCION = "registrar_intervencion"  # RF09
VER_SEGUIMIENTO = "ver_seguimiento"          # RF11
DERIVAR_CASOS = "derivar_casos"              # RF12
RECIBIR_DERIVACIONES = "recibir_derivaciones"
RECIBIR_ALERTAS = "recibir_alertas"          # RF16
VER_DASHBOARD = "ver_dashboard"              # RF02
VER_REPORTES = "ver_reportes"                # RF03
IMPORTAR_DATOS = "importar_datos"            # RF01
CONFIGURAR_REGLAS = "configurar_reglas"      # RF14
GESTIONAR_USUARIOS = "gestionar_usuarios"    # gestión de usuarios y roles (Hito 1, ERS 2.2)
GENERAR_REPORTES = "generar_reportes"        # ejecución manual de la tarea del reporte semanal

_EQUIPO_CONVIVENCIA = {
    VER_ESTUDIANTES, VER_FICHA, VER_RIESGO, VER_CONVIVENCIA, VER_SEGUIMIENTO,
    REGISTRAR_INTERVENCION, CONTACTAR_APODERADO, RECIBIR_DERIVACIONES,
}

PERMISOS = {
    "administrador": {VER_DASHBOARD, IMPORTAR_DATOS, CONFIGURAR_REGLAS, GESTIONAR_USUARIOS, GENERAR_REPORTES},
    "director": {VER_DASHBOARD, VER_ESTUDIANTES, VER_FICHA, VER_RIESGO, VER_CONVIVENCIA,
                 VER_SEGUIMIENTO, VER_REPORTES},
    "jefe_utp": {VER_DASHBOARD, VER_ESTUDIANTES, VER_FICHA, VER_RIESGO, VER_CONVIVENCIA,
                 VER_SEGUIMIENTO},
    "profesor_jefe": {VER_ESTUDIANTES, VER_FICHA, VER_RIESGO, VER_CONVIVENCIA, VER_SEGUIMIENTO,
                      REGISTRAR_INTERVENCION, CONTACTAR_APODERADO, DERIVAR_CASOS,
                      RECIBIR_ALERTAS, VER_REPORTES},
    "profesor": {VER_ESTUDIANTES, VER_FICHA, VER_SEGUIMIENTO, REGISTRAR_INTERVENCION},
    "inspector": {VER_ESTUDIANTES, VER_FICHA, VER_CONVIVENCIA, EDITAR_CONTACTO},
    "dupla_psicosocial": _EQUIPO_CONVIVENCIA | {DERIVAR_CASOS},
    "encargado_convivencia": _EQUIPO_CONVIVENCIA | {DERIVAR_CASOS, RECIBIR_ALERTAS},
    "profesional_convivencia": set(_EQUIPO_CONVIVENCIA),
    "miembro_convivencia": set(_EQUIPO_CONVIVENCIA),
}

# Roles que solo pueden ver a los estudiantes de su curso (jefatura).
ROLES_CON_CURSO = {"profesor_jefe"}


def tiene_permiso(rol: str, permiso: str) -> bool:
    return permiso in PERMISOS.get(rol, set())


def permisos_de(rol: str) -> list[str]:
    return sorted(PERMISOS.get(rol, set()))
