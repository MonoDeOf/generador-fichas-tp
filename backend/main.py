"""
Backend FastAPI para el sistema de alerta de riesgo estudiantil.

Flujo:
  1. El usuario sube los CSV (o un ZIP con ellos) en POST /api/upload-db.
  2. Se crea una base SQLite nueva con una tabla por archivo.
  3. Recién entonces se pueden leer/guardar umbrales y calcular el riesgo.

Ejecutar:
  pip install -r requirements.txt
  python main.py        (abre http://127.0.0.1:8000)
"""

from __future__ import annotations

import csv
import io
import json
import re
import sqlite3
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "escuela.db"
CONFIG_PATH = BASE_DIR / "risk_config.json"

# Tablas mínimas para poder calcular el riesgo y las columnas que deben traer.
REQUIRED_TABLES: dict[str, set[str]] = {
    "ESTUDIANTE": {"rut_estudiante", "nombre", "apellido_paterno"},
    "ASISTENCIA": {"rut_estudiante", "estado"},
    "CALIFICACION": {"rut_estudiante", "nota"},
}

IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

app = FastAPI(title="Riesgo estudiantil")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------------------------------- #
# Configuración de riesgo
# --------------------------------------------------------------------------- #
class RiskConfig(BaseModel):
    umbral_asistencia: float = Field(75, ge=0, le=100)
    minimo_notas_deficientes: int = Field(2, ge=0)
    nota_deficiente: float = Field(4.0, ge=1, le=7)
    atraso_cuenta_como_asistencia: bool = True
    operador_logico: Literal["AND", "OR"] = "AND"


def leer_config() -> RiskConfig:
    if CONFIG_PATH.exists():
        try:
            return RiskConfig(**json.loads(CONFIG_PATH.read_text("utf-8")))
        except Exception:
            pass
    return RiskConfig()


def guardar_config(cfg: RiskConfig) -> None:
    CONFIG_PATH.write_text(cfg.model_dump_json(indent=2), "utf-8")


# --------------------------------------------------------------------------- #
# Base de datos
# --------------------------------------------------------------------------- #
def db_cargada() -> bool:
    if not DB_PATH.exists():
        return False
    with sqlite3.connect(DB_PATH) as con:
        tablas = {r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table'")}
    return set(REQUIRED_TABLES) <= tablas


def exigir_db() -> None:
    if not db_cargada():
        raise HTTPException(
            status_code=409,
            detail="Primero debes cargar la base de datos (CSV).",
        )


def parsear_csv(nombre: str, contenido: bytes) -> tuple[list[str], list[list[str]]]:
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = contenido.decode("latin-1")

    # Detecta separador , o ;
    muestra = texto[:4096]
    try:
        dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t")
    except csv.Error:
        dialecto = csv.excel

    filas = list(csv.reader(io.StringIO(texto), dialecto))
    filas = [f for f in filas if any(c.strip() for c in f)]
    if not filas:
        raise HTTPException(400, f"El archivo {nombre} está vacío.")

    columnas = [c.strip() for c in filas[0]]
    for c in columnas:
        if not IDENT_RE.match(c):
            raise HTTPException(
                400, f"Nombre de columna inválido en {nombre}: '{c}'")
    if len(set(columnas)) != len(columnas):
        raise HTTPException(400, f"Columnas duplicadas en {nombre}.")

    datos = []
    for f in filas[1:]:
        f = (f + [""] * len(columnas))[: len(columnas)]
        datos.append([v.strip() if v.strip() != "" else None for v in f])
    return columnas, datos


def extraer_archivos(uploads: list[tuple[str, bytes]]) -> dict[str, bytes]:
    """Devuelve {NOMBRE_TABLA: bytes_csv}, desempaquetando ZIPs."""
    archivos: dict[str, bytes] = {}

    def agregar(nombre: str, data: bytes) -> None:
        p = Path(nombre)
        if p.name.startswith(".") or "__MACOSX" in p.parts:
            return
        if p.suffix.lower() != ".csv":
            return
        tabla = p.stem.strip().upper()
        if not IDENT_RE.match(tabla):
            raise HTTPException(400, f"Nombre de archivo inválido: {p.name}")
        archivos[tabla] = data

    for nombre, data in uploads:
        if nombre.lower().endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    for info in z.infolist():
                        if not info.is_dir():
                            agregar(info.filename, z.read(info))
            except zipfile.BadZipFile:
                raise HTTPException(400, f"{nombre} no es un ZIP válido.")
        else:
            agregar(nombre, data)
    return archivos


@app.get("/api/db-status")
def db_status():
    if not db_cargada():
        return {"cargada": False, "tablas": {}, "cargada_en": None}
    with sqlite3.connect(DB_PATH) as con:
        tablas = [r[0] for r in con.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
        conteo = {t: con.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
                  for t in tablas}
    cargada_en = datetime.fromtimestamp(DB_PATH.stat().st_mtime).isoformat(
        timespec="seconds")
    return {"cargada": True, "tablas": conteo, "cargada_en": cargada_en}


@app.post("/api/upload-db")
async def upload_db(files: list[UploadFile] = File(...)):
    uploads = [(f.filename or "", await f.read()) for f in files]
    archivos = extraer_archivos(uploads)

    if not archivos:
        raise HTTPException(400, "No se encontraron archivos CSV.")

    faltantes = [t for t in REQUIRED_TABLES if t not in archivos]
    if faltantes:
        raise HTTPException(
            400,
            "Faltan archivos obligatorios: "
            + ", ".join(f"{t}.csv" for t in faltantes),
        )

    parseados = {t: parsear_csv(f"{t}.csv", b) for t, b in archivos.items()}

    for tabla, cols_req in REQUIRED_TABLES.items():
        faltan = cols_req - set(parseados[tabla][0])
        if faltan:
            raise HTTPException(
                400, f"{tabla}.csv no tiene las columnas: {', '.join(sorted(faltan))}")

    # Construye la base en un archivo temporal y la reemplaza al final,
    # así una carga fallida no deja la base anterior a medias.
    tmp = DB_PATH.with_suffix(".tmp")
    tmp.unlink(missing_ok=True)
    con = sqlite3.connect(tmp)
    try:
        for tabla, (cols, datos) in parseados.items():
            cols_sql = ", ".join(f'"{c}" TEXT' for c in cols)
            con.execute(f'CREATE TABLE "{tabla}" ({cols_sql})')
            ph = ", ".join("?" for _ in cols)
            con.executemany(f'INSERT INTO "{tabla}" VALUES ({ph})', datos)
        con.execute('CREATE INDEX ix_asis ON ASISTENCIA(rut_estudiante)')
        con.execute('CREATE INDEX ix_cal ON CALIFICACION(rut_estudiante)')
        con.commit()
    finally:
        con.close()
    tmp.replace(DB_PATH)

    return db_status()


@app.delete("/api/db")
def borrar_db():
    DB_PATH.unlink(missing_ok=True)
    return {"cargada": False}


# --------------------------------------------------------------------------- #
# Endpoints de riesgo
# --------------------------------------------------------------------------- #
@app.get("/api/risk-config", response_model=RiskConfig)
def get_config():
    exigir_db()
    return leer_config()


@app.put("/api/risk-config", response_model=RiskConfig)
def put_config(cfg: RiskConfig):
    exigir_db()
    guardar_config(cfg)
    return cfg


@app.get("/api/students-risk")
def students_risk():
    exigir_db()
    cfg = leer_config()

    estados_asiste = ("presente", "atraso") if cfg.atraso_cuenta_como_asistencia \
        else ("presente",)
    ph = ", ".join("?" for _ in estados_asiste)

    sql = f"""
        SELECT e.rut_estudiante, e.nombre, e.apellido_paterno,
               a.total, a.asistidas,
               COALESCE(c.deficientes, 0) AS deficientes
        FROM ESTUDIANTE e
        LEFT JOIN (
            SELECT rut_estudiante,
                   COUNT(*) AS total,
                   SUM(CASE WHEN LOWER(TRIM(estado)) IN ({ph}) THEN 1 ELSE 0 END)
                       AS asistidas
            FROM ASISTENCIA GROUP BY rut_estudiante
        ) a ON a.rut_estudiante = e.rut_estudiante
        LEFT JOIN (
            SELECT rut_estudiante, COUNT(*) AS deficientes
            FROM CALIFICACION
            WHERE nota IS NOT NULL
              AND CAST(REPLACE(nota, ',', '.') AS REAL) < ?
            GROUP BY rut_estudiante
        ) c ON c.rut_estudiante = e.rut_estudiante
    """

    with sqlite3.connect(DB_PATH) as con:
        filas = con.execute(sql, (*estados_asiste, cfg.nota_deficiente)).fetchall()

    orden = {"ALTO": 0, "MEDIO": 1, "BAJO": 2}
    resultado = []
    for rut, nombre, ap, total, asistidas, deficientes in filas:
        asistencia = round(asistidas * 100 / total, 1) if total else None

        cond_asis = asistencia is not None and asistencia < cfg.umbral_asistencia
        cond_notas = deficientes >= cfg.minimo_notas_deficientes

        disparada = (cond_asis and cond_notas) if cfg.operador_logico == "AND" \
            else (cond_asis or cond_notas)

        if disparada:
            nivel = "ALTO"
        elif cond_asis or cond_notas:
            nivel = "MEDIO"
        else:
            nivel = "BAJO"

        resultado.append({
            "rut_estudiante": rut,
            "nombre": nombre,
            "apellido_paterno": ap,
            "asistencia": asistencia,
            "cantidad_notas_deficientes": deficientes,
            "cumple_condicion_asistencia": cond_asis,
            "cumple_condicion_notas": cond_notas,
            "operador_logico": cfg.operador_logico,
            "regla_disparada": disparada,
            "nivel_riesgo": nivel,
        })

    resultado.sort(key=lambda r: (orden[r["nivel_riesgo"]],
                                  r["asistencia"] if r["asistencia"] is not None else 101))
    return resultado


# --------------------------------------------------------------------------- #
# Dashboard directivo (templates/dashboard.html, sin cambios).
# Mismos endpoints y cálculos que el app_dashboard.py original (Flask),
# pero leyendo la base de datos cargada en el Paso 1 en vez de la carpeta CSV.
# --------------------------------------------------------------------------- #
TEMPLATES_DIR = BASE_DIR / "templates"

# Igual que el original: solo "presente" cuenta como asistencia (100), el resto 0.
ASISTE_ORIGINAL = "CASE WHEN LOWER(TRIM(estado)) = 'presente' THEN 100.0 ELSE 0 END"


def tablas_existentes(con: sqlite3.Connection) -> set[str]:
    return {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


@app.get("/dashboard-original", include_in_schema=False)
def dashboard_html():
    return FileResponse(TEMPLATES_DIR / "dashboard.html")


@app.get("/api/metricas/globales")
def metricas_globales():
    vacio = {"promedio_global": 0.0, "asistencia_global": 0.0,
             "anotaciones": {"positivas": 0, "negativas": 0, "neutras": 0}}
    if not db_cargada():
        return vacio

    with sqlite3.connect(DB_PATH) as con:
        promedio = con.execute(
            "SELECT AVG(CAST(REPLACE(nota, ',', '.') AS REAL)) "
            "FROM CALIFICACION WHERE nota IS NOT NULL").fetchone()[0] or 0.0
        asistencia = con.execute(
            f"SELECT AVG({ASISTE_ORIGINAL}) FROM ASISTENCIA").fetchone()[0] or 0.0

        conteo: dict[str, int] = {}
        if "ANOTACION" in tablas_existentes(con):
            conteo = dict(con.execute(
                "SELECT tipo_anotacion, COUNT(*) FROM ANOTACION "
                "GROUP BY tipo_anotacion").fetchall())

    return {
        "promedio_global": round(promedio, 1),
        "asistencia_global": round(asistencia, 1),
        "anotaciones": {
            "positivas": int(conteo.get("Positiva", 0)),
            "negativas": int(conteo.get("Negativa", 0)),
            "neutras": int(conteo.get("Neutra", 0)),
        },
    }


@app.get("/api/asistencia/curso")
def asistencia_curso():
    if not db_cargada():
        return []
    with sqlite3.connect(DB_PATH) as con:
        if "NIVEL" not in tablas_existentes(con):
            return []
        filas = con.execute(f"""
            SELECT n.nombre_nivel, AVG({ASISTE_ORIGINAL})
            FROM ASISTENCIA a
            JOIN ESTUDIANTE e ON e.rut_estudiante = a.rut_estudiante
            JOIN NIVEL n ON n.id_nivel = e.id_nivel
            GROUP BY n.nombre_nivel
            ORDER BY n.nombre_nivel
        """).fetchall()
    return [{"nivel": nivel, "asistencia": round(v, 1)} for nivel, v in filas]


@app.get("/api/asistencia/alumno")
def asistencia_alumno():
    if not db_cargada():
        return []
    with sqlite3.connect(DB_PATH) as con:
        filas = con.execute(f"""
            SELECT e.nombre, e.apellido_paterno, AVG({ASISTE_ORIGINAL}) AS v
            FROM ASISTENCIA a
            JOIN ESTUDIANTE e ON e.rut_estudiante = a.rut_estudiante
            GROUP BY e.rut_estudiante, e.nombre, e.apellido_paterno
            ORDER BY v ASC
            LIMIT 15
        """).fetchall()
    return [{"nombre_completo": f"{n} {ap}", "asistencia": v} for n, ap, v in filas]


@app.get("/api/alumnos")
def alumnos():
    """Lista de alumnos con curso, asistencia y promedio, para el buscador
    del Dashboard. Asistencia con el mismo criterio del Dashboard
    (solo "presente" cuenta)."""
    if not db_cargada():
        return []
    with sqlite3.connect(DB_PATH) as con:
        tablas = tablas_existentes(con)
        cols_est = {r[1] for r in con.execute('PRAGMA table_info("ESTUDIANTE")')}
        materno = "e.apellido_materno" if "apellido_materno" in cols_est else "''"
        if "NIVEL" in tablas and "id_nivel" in cols_est:
            nivel_sql = "n.nombre_nivel"
            join_nivel = "LEFT JOIN NIVEL n ON n.id_nivel = e.id_nivel"
        else:
            nivel_sql, join_nivel = "NULL", ""

        filas = con.execute(f"""
            SELECT e.rut_estudiante, e.nombre, e.apellido_paterno, {materno},
                   {nivel_sql}, a.asis, c.prom
            FROM ESTUDIANTE e
            {join_nivel}
            LEFT JOIN (
                SELECT rut_estudiante, AVG({ASISTE_ORIGINAL}) AS asis
                FROM ASISTENCIA GROUP BY rut_estudiante
            ) a ON a.rut_estudiante = e.rut_estudiante
            LEFT JOIN (
                SELECT rut_estudiante,
                       AVG(CAST(REPLACE(nota, ',', '.') AS REAL)) AS prom
                FROM CALIFICACION WHERE nota IS NOT NULL GROUP BY rut_estudiante
            ) c ON c.rut_estudiante = e.rut_estudiante
            ORDER BY a.asis IS NULL, a.asis ASC, e.apellido_paterno
        """).fetchall()

    return [{
        "rut_estudiante": rut,
        "nombre_completo": " ".join(x for x in (nom, ap, am) if x),
        "nivel": nivel or "",
        "asistencia": round(asis, 1) if asis is not None else None,
        "promedio": round(prom, 1) if prom is not None else None,
    } for rut, nom, ap, am, nivel, asis, prom in filas]


# --------------------------------------------------------------------------- #
# Sitio web (frontend ya compilado en la carpeta "static")
# Debe ir al final para no tapar las rutas /api.
# --------------------------------------------------------------------------- #
STATIC_DIR = BASE_DIR / "static"
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="web")


if __name__ == "__main__":
    import threading
    import webbrowser

    import uvicorn

    import socket

    with socket.socket() as sock:
        ocupado = sock.connect_ex(("127.0.0.1", 8000)) == 0
    if ocupado:
        print("\n  [!] Ya hay otro servidor usando el puerto 8000.")
        print("      Cierra la otra ventana negra del sistema (o reinicia el")
        print("      computador) y vuelve a abrir iniciar.bat.\n")
        raise SystemExit(1)

    url = "http://127.0.0.1:8000"
    print(f"\n  Sitio disponible en {url}  (Ctrl+C para detener)\n")
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host="127.0.0.1", port=8000)
