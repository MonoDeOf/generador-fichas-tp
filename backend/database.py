"""Acceso a los archivos CSV que actúan como base de datos.

Cada archivo CSV es una tabla. Las lecturas se guardan en memoria y se recargan si
el archivo cambia en disco. Las escrituras reemplazan el archivo completo de forma
atómica (archivo temporal + os.replace) para no dejar datos a medias, conservando
la codificación UTF-8 con BOM, el separador y el fin de línea originales.
"""
import csv
import io
import os
import threading
from pathlib import Path

from config import DATA_DIR

# Tablas del esquema relacional (DSoftware_schema.sql). El sistema parte con ellas
# vacías (solo encabezados); el administrador las carga manualmente desde los CSV.
TABLAS_BASE = {
    "NIVEL": ["id_nivel", "nombre_nivel"],
    "ESPECIALIDAD": ["id_especialidad", "nombre_especialidad"],
    "APODERADO": ["rut_apoderado", "nombre", "apellido_apoderado", "telefono"],
    "ASIGNATURA": ["id_asignatura", "nombre_asignatura", "horas"],
    "COMBO": ["id_combo", "numero_combo"],
    "ESTUDIANTE": ["rut_estudiante", "nombre", "apellido_paterno", "apellido_materno", "rut_apoderado",
                   "id_nivel", "id_especialidad"],
    "ELECTIVO": ["id_combo", "id_asignatura"],
    "PLAN_COMUN": ["id_nivel", "id_asignatura"],
    "MODULO": ["id_especialidad", "id_nivel", "id_asignatura"],
    "OFRECE": ["id_nivel", "id_combo"],
    "ELIGE": ["rut_estudiante", "id_asignatura"],
    "CALIFICACION": ["id_calificacion", "numero_evaluacion", "nota", "semestre", "rut_estudiante", "id_asignatura"],
    "ASISTENCIA": ["id_asistencia", "fecha", "estado", "rut_estudiante"],
    "ANOTACION": ["id_anotacion", "descripcion_anotacion", "tipo_anotacion", "rut_estudiante"],
    "ANOTACION_AULA": ["id_asignatura", "id_anotacion"],
    "ANOTACION_FUERA_AULA": ["id_anotacion"],
}

# Tablas agregadas por la plataforma. No existen en BD_organizada porque el material
# no entrega datos de usuarios ni reglas, pero los requisitos RF14 y RNF04/RNF05
# necesitan persistirlos.
TABLAS_NUEVAS = {
    "USUARIO": ["id_usuario", "nombre_usuario", "nombre", "rol", "id_nivel", "correo",
                "contrasena_hash", "activo"],
    "REGLA_RIESGO": ["parametro", "valor", "fecha_actualizacion", "id_usuario"],
}


class TablaCsv:
    def __init__(self, nombre: str, columnas: list[str] | None = None):
        self.nombre = nombre
        self.ruta: Path = DATA_DIR / f"{nombre}.csv"
        self._lock = threading.RLock()
        self._filas: list[dict] | None = None
        self._mtime: float | None = None
        self._columnas = columnas
        self._fin_linea = "\n"
        self._delimitador = ","
        if not self.ruta.exists():
            if columnas is None:
                raise FileNotFoundError(f"No existe el archivo {self.ruta}")
            self._escribir_archivo([])

    @property
    def columnas(self) -> list[str]:
        self._cargar()
        return list(self._columnas or [])

    def _cargar(self) -> None:
        mtime = self.ruta.stat().st_mtime
        if self._filas is not None and mtime == self._mtime:
            return
        crudo = self.ruta.read_bytes().decode("utf-8-sig")
        self._fin_linea = "\r\n" if "\r\n" in crudo[:2000] else "\n"
        lector = csv.DictReader(io.StringIO(crudo, newline=""), delimiter=self._delimitador)
        self._columnas = list(lector.fieldnames or self._columnas or [])
        self._filas = [dict(f) for f in lector]
        self._mtime = mtime

    def todos(self) -> list[dict]:
        with self._lock:
            self._cargar()
            return [dict(f) for f in self._filas]

    def _escribir_archivo(self, filas: list[dict]) -> None:
        buffer = io.StringIO(newline="")
        escritor = csv.DictWriter(buffer, fieldnames=self._columnas, delimiter=self._delimitador,
                                  lineterminator=self._fin_linea, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(filas)
        temporal = self.ruta.with_suffix(".csv.tmp")
        temporal.write_bytes(buffer.getvalue().encode("utf-8-sig"))
        os.replace(temporal, self.ruta)
        self._filas = [dict(f) for f in filas]
        self._mtime = self.ruta.stat().st_mtime

    def reemplazar_todo(self, filas: list[dict]) -> None:
        with self._lock:
            self._cargar()
            self._escribir_archivo(filas)

    def agregar(self, fila: dict) -> dict:
        with self._lock:
            filas = self.todos()
            filas.append({c: _texto(fila.get(c)) for c in self._columnas})
            self._escribir_archivo(filas)
            return filas[-1]

    def actualizar(self, condicion, cambios: dict) -> int:
        """Actualiza las filas que cumplen la condición. Devuelve cuántas cambiaron."""
        with self._lock:
            filas = self.todos()
            n = 0
            for f in filas:
                if condicion(f):
                    f.update({k: _texto(v) for k, v in cambios.items()})
                    n += 1
            if n:
                self._escribir_archivo(filas)
            return n

    def siguiente_id(self, campo: str) -> int:
        valores = [int(f[campo]) for f in self.todos() if str(f.get(campo, "")).isdigit()]
        return max(valores, default=0) + 1


def _texto(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "1" if valor else "0"
    return str(valor)


_tablas: dict[str, TablaCsv] = {}


def tabla(nombre: str) -> TablaCsv:
    if nombre not in _tablas:
        _tablas[nombre] = TablaCsv(nombre, TABLAS_BASE.get(nombre) or TABLAS_NUEVAS.get(nombre))
    return _tablas[nombre]


def inicializar() -> None:
    """Crea vacías (solo encabezados) las tablas que aún no existen."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    for nombre in [*TABLAS_BASE, *TABLAS_NUEVAS]:
        tabla(nombre)
