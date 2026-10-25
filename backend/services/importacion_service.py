"""Carga manual de los CSV de la base de datos (RF01, HU 1.1, RNF09, RNF10).

El sistema parte con las tablas vacías. El administrador sube uno o varios CSV
(por ejemplo, los 16 archivos de BD_organizada). Cada archivo se asocia a su tabla
por el nombre (ESTUDIANTE.csv) o, si el nombre no coincide, por sus columnas.

Todo el lote se valida antes de guardar: columnas obligatorias, tipos, dominios del
esquema (DSoftware_schema.sql), claves foráneas y reglas R1–R16 del MER. Si hay un
solo error, no se guarda nada. Si todo es válido, cada tabla se sincroniza: un
registro con la misma clave se actualiza y uno nuevo se agrega.
"""
import csv
import io
from datetime import date

from database import TABLAS_BASE, tabla
from services import academico_service as acad
from services.errores import ErrorNegocio

MAX_ERRORES = 50

# Orden de carga según las dependencias entre tablas (claves foráneas).
ORDEN = ["NIVEL", "ESPECIALIDAD", "APODERADO", "ASIGNATURA", "COMBO", "ESTUDIANTE", "ELECTIVO", "PLAN_COMUN",
         "MODULO", "OFRECE", "ELIGE", "CALIFICACION", "ASISTENCIA", "ANOTACION", "ANOTACION_AULA",
         "ANOTACION_FUERA_AULA"]

# Clave primaria de cada tabla (DSoftware_schema.sql).
CLAVES = {
    "NIVEL": ["id_nivel"], "ESPECIALIDAD": ["id_especialidad"], "APODERADO": ["rut_apoderado"],
    "ASIGNATURA": ["id_asignatura"], "COMBO": ["id_combo"], "ESTUDIANTE": ["rut_estudiante"],
    "ELECTIVO": ["id_asignatura"], "PLAN_COMUN": ["id_asignatura"], "MODULO": ["id_asignatura"],
    "OFRECE": ["id_nivel", "id_combo"], "ELIGE": ["rut_estudiante", "id_asignatura"],
    # Asistencia y calificación se sincronizan por su clave única (R15, R12); el id es opcional
    # para poder cargar planillas exportadas de otros sistemas.
    "CALIFICACION": ["rut_estudiante", "id_asignatura", "semestre", "numero_evaluacion"],
    "ASISTENCIA": ["rut_estudiante", "fecha"],
    "ANOTACION": ["id_anotacion"], "ANOTACION_AULA": ["id_anotacion"], "ANOTACION_FUERA_AULA": ["id_anotacion"],
}
ID_OPCIONAL = {"CALIFICACION": "id_calificacion", "ASISTENCIA": "id_asistencia"}

# Claves foráneas: (columna, tabla referenciada, columna referenciada).
FORANEAS = {
    "ESTUDIANTE": [("rut_apoderado", "APODERADO", "rut_apoderado"), ("id_nivel", "NIVEL", "id_nivel"),
                   ("id_especialidad", "ESPECIALIDAD", "id_especialidad")],
    "ELECTIVO": [("id_combo", "COMBO", "id_combo"), ("id_asignatura", "ASIGNATURA", "id_asignatura")],
    "PLAN_COMUN": [("id_nivel", "NIVEL", "id_nivel"), ("id_asignatura", "ASIGNATURA", "id_asignatura")],
    "MODULO": [("id_especialidad", "ESPECIALIDAD", "id_especialidad"), ("id_nivel", "NIVEL", "id_nivel"),
               ("id_asignatura", "ASIGNATURA", "id_asignatura")],
    "OFRECE": [("id_nivel", "NIVEL", "id_nivel"), ("id_combo", "COMBO", "id_combo")],
    "ELIGE": [("rut_estudiante", "ESTUDIANTE", "rut_estudiante"), ("id_asignatura", "ELECTIVO", "id_asignatura")],
    "CALIFICACION": [("rut_estudiante", "ESTUDIANTE", "rut_estudiante"), ("id_asignatura", "ASIGNATURA", "id_asignatura")],
    "ASISTENCIA": [("rut_estudiante", "ESTUDIANTE", "rut_estudiante")],
    "ANOTACION": [("rut_estudiante", "ESTUDIANTE", "rut_estudiante")],
    "ANOTACION_AULA": [("id_asignatura", "ASIGNATURA", "id_asignatura"), ("id_anotacion", "ANOTACION", "id_anotacion")],
    "ANOTACION_FUERA_AULA": [("id_anotacion", "ANOTACION", "id_anotacion")],
}

OPCIONALES = {("ESTUDIANTE", "id_especialidad")}  # R10: 1M y 2M no tienen especialidad
ENTEROS = {"id_nivel", "id_especialidad", "horas", "id_combo", "numero_combo", "numero_evaluacion", "semestre",
           "id_calificacion", "id_asistencia", "id_anotacion"}


def _leer_csv(nombre_archivo: str, contenido: str) -> tuple[list[str], list[dict]]:
    texto = contenido.lstrip("﻿")
    if not texto.strip():
        raise ErrorNegocio(400, f"{nombre_archivo}: el archivo está vacío")
    primera = texto.splitlines()[0]
    delimitador = ";" if primera.count(";") > primera.count(",") else ","
    lector = csv.DictReader(io.StringIO(texto, newline=""), delimiter=delimitador)
    columnas = [c.strip().lower() for c in (lector.fieldnames or [])]
    filas = [{k.strip().lower(): (v or "").strip() for k, v in f.items() if k is not None} for f in lector]
    return columnas, filas


def _identificar_tabla(nombre_archivo: str, columnas: list[str]) -> str | None:
    base = nombre_archivo.rsplit("/", 1)[-1].rsplit(".", 1)[0].strip().upper()
    if base in TABLAS_BASE:
        return base
    candidatas = [t for t, cols in TABLAS_BASE.items()
                  if set(cols) - ({ID_OPCIONAL[t]} if t in ID_OPCIONAL else set()) <= set(columnas)
                  and set(columnas) <= set(cols)]
    return candidatas[0] if len(candidatas) == 1 else None


def _validar_dominio(t: str, f: dict, linea: int, estado: dict) -> list[str]:
    """Restricciones CHECK del esquema y reglas del MER que dependen solo de la fila."""
    e = []
    err = lambda m: e.append(f"Línea {linea}: {m}")
    if t == "APODERADO" and not (f["telefono"].isdigit() and len(f["telefono"]) == 9):
        err(f"teléfono '{f['telefono']}' debe tener 9 dígitos")
    if t == "NIVEL" and f["nombre_nivel"] not in ("1M", "2M", "3M", "4M"):
        err(f"nombre_nivel '{f['nombre_nivel']}' no válido (1M, 2M, 3M o 4M)")
    if t == "ASIGNATURA" and f["horas"].isdigit() and int(f["horas"]) <= 0:
        err("las horas deben ser mayores que 0")
    if t == "COMBO" and f["numero_combo"].isdigit() and not 1 <= int(f["numero_combo"]) <= 4:
        err("numero_combo debe estar entre 1 y 4")
    if t == "ASISTENCIA":
        if f["estado"] not in ("presente", "ausente", "atraso"):
            err(f"estado '{f['estado']}' no válido (presente, ausente o atraso, R16)")
        try:
            date.fromisoformat(f["fecha"])
        except ValueError:
            err(f"fecha '{f['fecha']}' no válida (formato AAAA-MM-DD)")
    if t == "ANOTACION" and f["tipo_anotacion"] not in ("Negativa", "Neutra", "Positiva"):
        err(f"tipo_anotacion '{f['tipo_anotacion']}' no válido (Negativa, Neutra o Positiva)")
    if t == "CALIFICACION":
        try:
            nota = float(f["nota"].replace(",", "."))
            if not 1.0 <= nota <= 7.0:
                raise ValueError
            f["nota"] = f"{nota:g}"
        except ValueError:
            err(f"nota '{f['nota']}' no válida (entre 1.0 y 7.0)")
        if f["semestre"] not in ("1", "2"):
            err(f"semestre '{f['semestre']}' no válido (1 o 2)")
    if t == "ESTUDIANTE":
        nivel = estado["NIVEL"].get((f["id_nivel"],), {}).get("nombre_nivel")
        if nivel in ("1M", "2M") and f["id_especialidad"]:
            err("los estudiantes de 1M y 2M no tienen especialidad (R10)")
        if nivel in ("3M", "4M") and not f["id_especialidad"]:
            err("los estudiantes de 3M y 4M deben tener especialidad (R10)")
    return e


def _validar_relaciones(t: str, f: dict, linea: int, estado: dict, cache: dict) -> list[str]:
    """Reglas del MER que cruzan varias tablas."""
    e = []
    err = lambda m: e.append(f"Línea {linea}: {m}")
    if t == "ELIGE":
        est = estado["ESTUDIANTE"].get((f["rut_estudiante"],))
        electivo = estado["ELECTIVO"].get((f["id_asignatura"],))
        if est and electivo:
            nivel = estado["NIVEL"].get((est["id_nivel"],), {}).get("nombre_nivel")
            if nivel not in ("3M", "4M"):
                err("solo los estudiantes de 3M y 4M eligen electivos (R1)")
            elif (est["id_nivel"], electivo["id_combo"]) not in estado["OFRECE"]:
                err(f"el electivo '{f['id_asignatura']}' no se ofrece en el nivel del estudiante (R3)")
    if t == "CALIFICACION":
        est = estado["ESTUDIANTE"].get((f["rut_estudiante"],))
        asig = estado["ASIGNATURA"].get((f["id_asignatura"],))
        if est and asig:
            rut = f["rut_estudiante"]
            if rut not in cache:
                cache[rut] = acad.asignaturas_permitidas(
                    {"rut_estudiante": rut, "id_nivel": est["id_nivel"], "id_especialidad": est["id_especialidad"]},
                    plan_comun=estado["PLAN_COMUN"].values(), elige=estado["ELIGE"].values(),
                    modulos=estado["MODULO"].values())
            if f["id_asignatura"] not in cache[rut]:
                err(f"el estudiante {rut} no cursa la asignatura '{f['id_asignatura']}' (R5)")
            maximo = acad.cantidad_notas(int(asig["horas"]))
            if f["numero_evaluacion"].isdigit() and not 1 <= int(f["numero_evaluacion"]) <= maximo:
                err(f"la asignatura '{f['id_asignatura']}' admite evaluaciones de 1 a {maximo} (R6/R7)")
    if t in ("ANOTACION_AULA", "ANOTACION_FUERA_AULA"):
        otra = "ANOTACION_FUERA_AULA" if t == "ANOTACION_AULA" else "ANOTACION_AULA"
        # ANOTACION_AULA se procesa antes: se compara con lo ya guardado fuera de aula; ANOTACION_FUERA_AULA
        # se compara con el estado resultante de aula (incluye el lote).
        ids_otra = estado[otra] if otra in estado else {(x["id_anotacion"],) for x in tabla(otra).todos()}
        if (f["id_anotacion"],) in ids_otra:
            err(f"la anotación {f['id_anotacion']} no puede estar en aula y fuera de aula a la vez (R14)")
    return e


def _clave(t: str, f: dict) -> tuple:
    return tuple(f[c] for c in CLAVES[t])


def importar(archivos: list[dict]) -> dict:
    if not archivos:
        raise ErrorNegocio(400, "Debe seleccionar al menos un archivo")
    errores: list[str] = []
    lote: dict[str, tuple[str, list[dict]]] = {}
    for a in archivos:
        nombre = a["nombre_archivo"]
        if not nombre.lower().endswith(".csv"):
            errores.append(f"{nombre}: el archivo debe tener formato CSV (.csv)")
            continue
        columnas, filas = _leer_csv(nombre, a["contenido"])
        t = _identificar_tabla(nombre, columnas)
        if not t:
            errores.append(f"{nombre}: no corresponde a ninguna tabla del sistema (revise el nombre o las columnas)")
            continue
        if t in lote:
            errores.append(f"{nombre}: la tabla {t} viene en más de un archivo")
            continue
        obligatorias = [c for c in TABLAS_BASE[t] if c != ID_OPCIONAL.get(t)]
        faltantes = [c for c in obligatorias if c not in columnas]
        if faltantes:
            errores.extend(f"{nombre}: error de estructura, falta la columna '{c}'" for c in faltantes)
            continue
        if not filas:
            errores.append(f"{nombre}: el archivo no contiene registros")
            continue
        lote[t] = (nombre, filas)
    if errores:
        raise ErrorNegocio(400, "Error de estructura; no se guardó ningún registro", errores)

    # Estado resultante tabla por tabla (lo existente más lo que trae el lote), en orden de dependencias.
    estado: dict[str, dict[tuple, dict]] = {}
    resumen = []
    cambios: dict[str, list[dict]] = {}
    cache_r5: dict = {}
    for t in ORDEN:
        existentes = tabla(t).todos()
        indice = {_clave(t, f): f for f in existentes}
        if t not in lote:
            estado[t] = indice
            continue
        nombre, filas = lote[t]
        vistos = set()
        for i, f in enumerate(filas, start=2):
            fila_err = []
            for c in TABLAS_BASE[t]:
                f.setdefault(c, "")
                if not f[c] and c != ID_OPCIONAL.get(t) and (t, c) not in OPCIONALES:
                    fila_err.append(f"Línea {i}: el campo '{c}' es obligatorio")
                elif f[c] and c in ENTEROS and not f[c].isdigit():
                    fila_err.append(f"Línea {i}: '{c}' debe ser un número entero (valor '{f[c]}')")
            if not fila_err:
                fila_err += _validar_dominio(t, f, i, estado)
                for col, ref, _ in FORANEAS.get(t, []):
                    # Todas las claves foráneas del esquema apuntan a la clave primaria de la tabla referenciada.
                    if f[col] and (f[col],) not in estado[ref]:
                        fila_err.append(f"Línea {i}: {col} '{f[col]}' no existe en {ref}")
                clave = _clave(t, f)
                if clave in vistos:
                    fila_err.append(f"Línea {i}: registro duplicado {dict(zip(CLAVES[t], clave))}")
                vistos.add(clave)
            if not fila_err:
                fila_err += _validar_relaciones(t, f, i, estado, cache_r5)
            errores.extend(f"{nombre}: {m}" for m in fila_err)
        if errores:
            estado[t] = indice
            continue
        estado[t], filas_tabla, conteo = _sincronizar(t, existentes, indice, filas)
        cambios[t] = filas_tabla
        resumen.append({"archivo": nombre, "tabla": t, "registros_procesados": len(filas), **conteo})
    if errores:
        extra = [f"... y {len(errores) - MAX_ERRORES} errores más"] if len(errores) > MAX_ERRORES else []
        raise ErrorNegocio(400, "Los archivos contienen errores; no se guardó ningún registro",
                           errores[:MAX_ERRORES] + extra)
    for t, filas_tabla in cambios.items():
        if any(r["insertados"] or r["actualizados"] for r in resumen if r["tabla"] == t):
            tabla(t).reemplazar_todo(filas_tabla)
    return {"archivos": [r for t in ORDEN for r in resumen if r["tabla"] == t]}


def _sincronizar(t: str, existentes: list[dict], indice: dict, filas: list[dict]):
    columnas = TABLAS_BASE[t]
    campo_id = ID_OPCIONAL.get(t)
    usados = {f[campo_id] for f in existentes} if campo_id else set()
    siguiente = max((int(x) for x in usados if x.isdigit()), default=0) + 1 if campo_id else 0
    insertados = actualizados = sin_cambios = 0
    for f in filas:
        nueva = {c: f[c] for c in columnas}
        actual = indice.get(_clave(t, nueva))
        if actual:
            nueva_sin_id = {c: v for c, v in nueva.items() if c != campo_id}
            if any(actual[c] != v for c, v in nueva_sin_id.items()):
                actual.update(nueva_sin_id)
                actualizados += 1
            else:
                sin_cambios += 1
            continue
        if campo_id and (not nueva[campo_id] or nueva[campo_id] in usados):
            while str(siguiente) in usados:
                siguiente += 1
            nueva[campo_id] = str(siguiente)
        if campo_id:
            usados.add(nueva[campo_id])
        existentes.append(nueva)
        indice[_clave(t, nueva)] = nueva
        insertados += 1
    return indice, existentes, {"insertados": insertados, "actualizados": actualizados, "sin_cambios": sin_cambios}


def estado_tablas() -> list[dict]:
    """Cantidad de registros cargados por tabla, en el orden recomendado de carga."""
    return [{"tabla": t, "registros": len(tabla(t).todos()), "columnas": TABLAS_BASE[t]} for t in ORDEN]
