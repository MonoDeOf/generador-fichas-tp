"""Modelos Pydantic de entrada (JSON) con los campos reales del proyecto."""
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class LoginEntrada(BaseModel):
    nombre_usuario: str = Field(min_length=1)
    contrasena: str = Field(min_length=1)


class ApoderadoEntrada(BaseModel):
    nombre: str = Field(min_length=1, max_length=50)
    apellido_apoderado: str = Field(min_length=1, max_length=50)
    telefono: str = Field(pattern=r"^[0-9]{9}$", description="9 dígitos numéricos (HU 2.2)")


class IntervencionEntrada(BaseModel):
    fecha: date
    tipo_intervencion: str = Field(min_length=1)
    descripcion: str = Field(min_length=1, max_length=2000)


class DerivacionEntrada(BaseModel):
    id_usuario_destino: int
    motivo: str = Field(min_length=1, max_length=500)


class EstadoCasoEntrada(BaseModel):
    estado: Literal["abierto", "cerrado"]
    motivo: str = Field(default="", max_length=500)


class ReglasEntrada(BaseModel):
    umbral_asistencia: float
    nota_deficiente: float
    min_notas_deficientes: int
    operador: Literal["Y", "O"]
    ausencias_consecutivas: int
    min_anotaciones_negativas: int


class ArchivoCsv(BaseModel):
    nombre_archivo: str = Field(min_length=1)
    contenido: str = Field(description="Texto completo del archivo CSV")


class ImportacionEntrada(BaseModel):
    archivos: list[ArchivoCsv] = Field(min_length=1)
