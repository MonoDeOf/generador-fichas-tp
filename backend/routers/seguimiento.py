from fastapi import APIRouter, Depends

from permisos import DERIVAR_CASOS, RECIBIR_DERIVACIONES, REGISTRAR_INTERVENCION, VER_SEGUIMIENTO
from routers.dependencias import requiere, usuario_actual
from schemas.modelos import DerivacionEntrada, EstadoCasoEntrada, IntervencionEntrada
from services import estudiante_service, seguimiento_service
from services.errores import ErrorNegocio
from permisos import tiene_permiso

router = APIRouter(tags=["Seguimiento de casos"])


@router.get("/estudiantes/{rut}/seguimiento")
def linea_de_tiempo(rut: str, usuario: dict = Depends(requiere(VER_SEGUIMIENTO))):
    """RF11 / HU 3.3: línea de tiempo del más reciente al más antiguo, con el estado del caso."""
    estudiante_service.obtener_visible(usuario, rut)
    return {"caso": seguimiento_service.caso_de(rut), "eventos": seguimiento_service.linea_de_tiempo(rut)}


@router.post("/estudiantes/{rut}/intervenciones", status_code=201)
def registrar_intervencion(rut: str, datos: IntervencionEntrada,
                           usuario: dict = Depends(requiere(REGISTRAR_INTERVENCION))):
    """RF09 / HU 3.1: registro en la bitácora con fecha, tipo, descripción y responsable."""
    estudiante_service.obtener_visible(usuario, rut)
    return seguimiento_service.registrar_intervencion(usuario, rut, datos.model_dump())


@router.post("/estudiantes/{rut}/caso/derivar")
def derivar_caso(rut: str, datos: DerivacionEntrada, usuario: dict = Depends(requiere(DERIVAR_CASOS))):
    """RF12 / HU 3.4: deriva el caso a otro profesional (estado 'derivado')."""
    estudiante_service.obtener_visible(usuario, rut)
    return seguimiento_service.derivar(usuario, rut, datos.id_usuario_destino, datos.motivo)


@router.patch("/estudiantes/{rut}/caso/estado")
def cambiar_estado_caso(rut: str, datos: EstadoCasoEntrada, usuario: dict = Depends(usuario_actual)):
    """Abre o cierra el caso (estados abierto, derivado, cerrado)."""
    if not (tiene_permiso(usuario["rol"], DERIVAR_CASOS) or tiene_permiso(usuario["rol"], RECIBIR_DERIVACIONES)):
        raise ErrorNegocio(403, "Su rol no tiene permiso para esta operación")
    estudiante_service.obtener_visible(usuario, rut)
    return seguimiento_service.cambiar_estado(usuario, rut, datos.estado, datos.motivo)


@router.get("/casos/asignados")
def mis_casos(usuario: dict = Depends(requiere(VER_SEGUIMIENTO))):
    """Panel del profesional: casos a su cargo, con los derivados destacados primero."""
    return seguimiento_service.casos_asignados(usuario)


@router.get("/casos/profesionales")
def profesionales(_: dict = Depends(requiere(DERIVAR_CASOS))):
    return seguimiento_service.profesionales_derivacion()
