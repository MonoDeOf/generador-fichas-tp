"""Pruebas de aceptación de la API contra un servidor en ejecución.

Uso: levante el servidor con una carpeta de datos VACÍA (las pruebas escriben) y pase la
carpeta con los CSV originales, que se cargan primero mediante la importación manual:
    DATA_DIR=/tmp/datos_prueba uvicorn main:app --port 8001
    python pruebas/prueba_api.py http://127.0.0.1:8001 ../ruta/a/BD_organizada

Solo usa la biblioteca estándar. Cada prueba imprime PASS o FAIL.
"""
import glob
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000"
CARPETA_CSV = sys.argv[2] if len(sys.argv) > 2 else "BD_organizada"
resultados = []


def pedir(metodo, ruta, cuerpo=None, token=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(BASE + ruta, data=datos, method=metodo)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or "null")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or "null")


def prueba(nombre, condicion, detalle=""):
    condicion = bool(condicion)
    resultados.append(condicion)
    print(f"{'PASS' if condicion else 'FAIL'}  {nombre}" + (f"  -> {detalle}" if not condicion and detalle else ""))


def login(usuario):
    codigo, r = pedir("POST", "/auth/login", {"nombre_usuario": usuario, "contrasena": "demo1234"})
    return r["token"] if codigo == 200 else None


# --- Autenticación y roles (RNF04, RNF05, RNF07)
c, _ = pedir("GET", "/estudiantes")
prueba("RNF04 sin sesión no hay acceso a estudiantes (401)", c == 401, c)
c, _ = pedir("POST", "/auth/login", {"nombre_usuario": "director", "contrasena": "mala"})
prueba("Login con contraseña incorrecta rechazado (401)", c == 401, c)
tk_admin = login("administrador")
c, est = pedir("GET", "/importaciones/estado", token=tk_admin)
prueba("El sistema parte con la base de datos vacía", c == 200 and all(t["registros"] == 0 for t in est), est)
c, r = pedir("GET", "/estudiantes", token=login("director"))
prueba("Sin carga no hay estudiantes", c == 200 and r == [], r)
archivos = [{"nombre_archivo": os.path.basename(f), "contenido": open(f, encoding="utf-8-sig").read()}
            for f in sorted(glob.glob(os.path.join(CARPETA_CSV, "*.csv")))]
c, r = pedir("POST", "/importaciones", {"archivos": [a for a in archivos if a["nombre_archivo"] == "ESTUDIANTE.csv"]}, tk_admin)
prueba("Cargar ESTUDIANTE sin APODERADO ni NIVEL falla por claves foráneas", c == 400 and "no existe en" in " ".join(r["detalles"]), r)
c, r = pedir("POST", "/importaciones", {"archivos": archivos}, tk_admin)
prueba("Carga manual de los 16 CSV en un solo lote", c == 200 and len(r["archivos"]) == 16, r.get("detalles") if c != 200 else "")
c, est = pedir("GET", "/importaciones/estado", token=tk_admin)
prueba("Tablas con los registros de los CSV (90 estudiantes, 12690 asistencias)",
       {t["tabla"]: t["registros"] for t in est}.get("ESTUDIANTE") == 90 and {t["tabla"]: t["registros"] for t in est}.get("ASISTENCIA") == 12690)
time.sleep(2)

tk = {u: login(u) for u in ["administrador", "director", "jefeutp", "profejefe3m", "profesor", "inspector",
                            "duplapsicosocial", "encargadoconvivencia"]}
prueba("Login de cuentas de demostración", all(tk.values()))

c, lista_prof = pedir("GET", "/estudiantes", token=tk["profesor"])
prueba("RNF07 el profesor no recibe el nivel de riesgo", c == 200 and "nivel_riesgo" not in lista_prof[0], lista_prof[:1])
c, _ = pedir("GET", "/dashboard", token=tk["profejefe3m"])
prueba("RNF05 profesor jefe sin acceso al dashboard directivo (403)", c == 403, c)

# --- Dashboard (HU 1.2)
c, d = pedir("GET", "/dashboard", token=tk["director"])
prueba("HU 1.2 dashboard con asistencia promedio por nivel", c == 200 and len(d["por_nivel"]) == 4
       and all(n["asistencia_promedio"] is not None for n in d["por_nivel"]), d.get("por_nivel") if c == 200 else c)
prueba("Dashboard: 90 estudiantes leídos desde ESTUDIANTE.csv", d["total_estudiantes"] == 90, d["total_estudiantes"])

# --- Filtro por especialidad (HU 1.4)
c, lst = pedir("GET", "/estudiantes?id_especialidad=29", token=tk["jefeutp"])
prueba("HU 1.4 filtro por especialidad devuelve solo Turismo", c == 200 and lst and
       all(e["nombre_especialidad"] == "Turismo" for e in lst), len(lst))

# --- Profesor jefe solo ve su curso
c, lst = pedir("GET", "/estudiantes", token=tk["profejefe3m"])
prueba("Profesor jefe 3M solo ve estudiantes de 3M", c == 200 and lst and all(e["nombre_nivel"] == "3M" for e in lst))
otro = next(e for e in pedir("GET", "/estudiantes?id_nivel=1", token=tk["director"])[1])
c, _ = pedir("GET", f"/estudiantes/{otro['rut_estudiante']}", token=tk["profejefe3m"])
prueba("Profesor jefe 3M no accede a ficha de 1M (403)", c == 403, c)

# --- Ficha integral (HU 2.1), asistencia (HU 2.3), convivencia (HU 2.4)
rut = lst[0]["rut_estudiante"]
c, ficha = pedir("GET", f"/estudiantes/{rut}", token=tk["profejefe3m"])
prueba("HU 2.1 ficha con datos personales, apoderado, asistencia y riesgo",
       c == 200 and ficha["apoderado"] and ficha["asistencia"]["total_dias"] > 0 and "riesgo" in ficha)
c, asis = pedir("GET", f"/estudiantes/{rut}/asistencia", token=tk["profejefe3m"])
prueba("HU 2.3 historial de asistencia con 141 registros", c == 200 and len(asis["registros"]) == 141, len(asis.get("registros", [])))
c, an = pedir("GET", f"/estudiantes/{rut}/anotaciones", token=tk["duplapsicosocial"])
prueba("HU 2.4 anotaciones ordenadas", c == 200 and [a["id_anotacion"] for a in an] == sorted(a["id_anotacion"] for a in an))
c, _ = pedir("GET", f"/estudiantes/{rut}/anotaciones", token=tk["profesor"])
prueba("Profesor sin permiso de convivencia (403)", c == 403, c)
c, _ = pedir("GET", "/estudiantes/99.999.999-9", token=tk["director"])
prueba("Estudiante inexistente (404)", c == 404, c)

# --- Contacto (HU 2.2) y WhatsApp (HU 3.2)
apod = ficha["apoderado"]
c, r = pedir("PUT", f"/estudiantes/{rut}/apoderado", {"nombre": apod["nombre"], "apellido_apoderado": apod["apellido_apoderado"], "telefono": "12345"}, tk["inspector"])
prueba("HU 2.2 teléfono con formato inválido rechazado", c in (400, 422), c)
c, r = pedir("PUT", f"/estudiantes/{rut}/apoderado", {"nombre": apod["nombre"], "apellido_apoderado": apod["apellido_apoderado"], "telefono": "987654321"}, tk["inspector"])
c2, ficha2 = pedir("GET", f"/estudiantes/{rut}", token=tk["inspector"])
prueba("HU 2.2 teléfono válido se guarda y se muestra", c == 200 and ficha2["apoderado"]["telefono"] == "987654321", r)
c, _ = pedir("PUT", f"/estudiantes/{rut}/apoderado", {"nombre": "X", "apellido_apoderado": "Y", "telefono": "987654321"}, tk["profesor"])
prueba("Profesor no puede editar contacto (403)", c == 403, c)
c, wa = pedir("GET", f"/estudiantes/{rut}/contacto-whatsapp", token=tk["profejefe3m"])
prueba("HU 3.2 enlace wa.me con mensaje predefinido", c == 200 and wa["url"].startswith("https://wa.me/56987654321?text="), wa)

# --- Bitácora (HU 3.1), línea de tiempo (HU 3.3), derivación (HU 3.4)
c, _ = pedir("POST", f"/estudiantes/{rut}/intervenciones", {"fecha": "2026-10-01", "tipo_intervencion": "Llamada telefónica", "descripcion": "   "}, tk["profejefe3m"])
prueba("HU 3.1 descripción vacía rechazada", c == 400, c)
c, i1 = pedir("POST", f"/estudiantes/{rut}/intervenciones", {"fecha": "2026-10-01", "tipo_intervencion": "Llamada telefónica", "descripcion": "Llamada con la apoderada"}, tk["profejefe3m"])
prueba("HU 3.1 intervención registrada con el nombre de quien la registró", c == 201 and i1["responsable"].startswith("Profesor jefe 3M"), i1)
c, i2 = pedir("POST", f"/estudiantes/{rut}/intervenciones", {"fecha": "2026-10-03", "tipo_intervencion": "Entrevista", "descripcion": "Entrevista con el estudiante"}, tk["profesor"])
c, _ = pedir("POST", f"/estudiantes/{rut}/intervenciones", {"fecha": "2099-01-01", "tipo_intervencion": "Entrevista", "descripcion": "x"}, tk["profesor"])
prueba("Intervención con fecha futura rechazada", c == 400, c)
c, seg = pedir("GET", f"/estudiantes/{rut}/seguimiento", token=tk["director"])
fechas = [e["fecha"][:10] for e in seg["eventos"]]
prueba("HU 3.3 línea de tiempo de la más reciente a la más antigua", c == 200 and fechas == sorted(fechas, reverse=True) and seg["caso"]["estado"] == "abierto", fechas)
c, prof = pedir("GET", "/casos/profesionales", token=tk["profejefe3m"])
dupla = next(p for p in prof if p["rol"] == "dupla_psicosocial")
c, caso = pedir("POST", f"/estudiantes/{rut}/caso/derivar", {"id_usuario_destino": dupla["id_usuario"], "motivo": "Supera el ámbito académico"}, tk["profejefe3m"])
prueba("HU 3.4 caso derivado a la dupla psicosocial", c == 200 and caso["estado"] == "derivado", caso)
c, mis = pedir("GET", "/casos/asignados", token=tk["duplapsicosocial"])
prueba("HU 3.4 el caso aparece destacado en el panel de la dupla", c == 200 and mis and mis[0]["rut_estudiante"] == rut and mis[0]["estado"] == "derivado")
c, notis = pedir("GET", "/notificaciones", token=tk["duplapsicosocial"])
prueba("HU 3.4 la dupla recibe la notificación de derivación", any(n["tipo"] == "derivacion" for n in notis))
c, _ = pedir("POST", f"/estudiantes/{rut}/caso/derivar", {"id_usuario_destino": dupla["id_usuario"], "motivo": "otra vez"}, tk["profejefe3m"])
prueba("Derivar al mismo responsable es un conflicto (409)", c == 409, c)
c, cerrado = pedir("PATCH", f"/estudiantes/{rut}/caso/estado", {"estado": "cerrado", "motivo": "Situación resuelta"}, tk["duplapsicosocial"])
prueba("El responsable cierra el caso", c == 200 and cerrado["estado"] == "cerrado", cerrado)
c, _ = pedir("POST", f"/estudiantes/{rut}/caso/derivar", {"id_usuario_destino": dupla["id_usuario"] + 1, "motivo": "x"}, tk["profejefe3m"])
prueba("No se deriva un caso cerrado (409)", c == 409, c)

# --- Riesgo (HU 4.1, 4.3) y reglas (HU 4.2)
c, lst = pedir("GET", "/estudiantes", token=tk["duplapsicosocial"])
prueba("HU 4.1 cada estudiante tiene semáforo Rojo/Amarillo/Verde", c == 200 and all(e["nivel_riesgo"] in ("Rojo", "Amarillo", "Verde") for e in lst))
rojo = next((e for e in lst if e["nivel_riesgo"] == "Rojo"), None)
prueba("HU 4.3 un estudiante en rojo tiene factores explicados", rojo is not None and len(rojo["factores"]) > 0, rojo)
c, cfg = pedir("GET", "/config/reglas", token=tk["administrador"])
prueba("HU 4.2 E1 consulta de configuración vigente (85 %)", c == 200 and cfg["reglas"]["umbral_asistencia"] == 85, cfg)
reglas = dict(cfg["reglas"])
c, r = pedir("PUT", "/config/reglas", {**reglas, "umbral_asistencia": 120}, tk["administrador"])
c2, cfg2 = pedir("GET", "/config/reglas", token=tk["administrador"])
prueba("HU 4.2 E4 120 % rechazado y se conserva la configuración", c == 400 and cfg2["reglas"]["umbral_asistencia"] == 85, r)
c, r = pedir("PUT", "/config/reglas", {**reglas, "umbral_asistencia": "abc"}, tk["administrador"])
prueba("HU 4.2 E5 valor incompatible rechazado", c == 422, c)
c, _ = pedir("PUT", "/config/reglas", {**reglas, "umbral_asistencia": 85}, tk["director"])
prueba("HU 4.2 E6 usuario no administrador rechazado (403)", c == 403, c)
antes = sum(1 for e in lst if e["nivel_riesgo"] != "Verde")
c, r = pedir("PUT", "/config/reglas", {**reglas, "umbral_asistencia": 95}, tk["administrador"])
prueba("HU 4.2 E2 modificación válida guardada", c == 200 and r["reglas"]["umbral_asistencia"] == 95, r)
c, lst2 = pedir("GET", "/estudiantes", token=tk["duplapsicosocial"])
despues = sum(1 for e in lst2 if e["nivel_riesgo"] != "Verde")
prueba("HU 4.2 E3 el motor usa el nuevo umbral (más estudiantes en riesgo)", despues > antes, (antes, despues))
pedir("PUT", "/config/reglas", reglas, tk["administrador"])

# --- Alertas críticas (HU 4.4)
c, n = pedir("GET", "/notificaciones/no-leidas", token=tk["encargadoconvivencia"])
prueba("HU 4.4 el encargado de convivencia tiene alertas críticas sin leer", c == 200 and n["cantidad"] > 0, n)

# --- Importación (HU 1.1)
c, r = pedir("POST", "/importaciones", {"archivos": [{"nombre_archivo": "ASISTENCIA.csv", "contenido": "fecha,estado\n2026-10-06,presente\n"}]}, tk["administrador"])
prueba("HU 1.1 E2 archivo sin columna RUT abortado con error de estructura", c == 400 and "rut_estudiante" in " ".join(r["detalles"]), r)
c, r = pedir("POST", "/importaciones", {"archivos": [{"nombre_archivo": "otro.csv", "contenido": "a,b\n1,2\n"}]}, tk["administrador"])
prueba("Archivo que no corresponde a ninguna tabla rechazado", c == 400, r)
contenido = "fecha,estado,rut_estudiante\n" + "\n".join(f"{f},ausente,{rut}" for f in ["2026-10-06", "2026-10-07", "2026-10-08"])
c, r = pedir("POST", "/importaciones", {"archivos": [{"nombre_archivo": "ASISTENCIA.csv", "contenido": contenido + "\n2026-10-09,vacaciones," + rut}]}, tk["administrador"])
prueba("Importación con un estado inválido no guarda nada (RNF10)", c == 400, r)
_, previas = pedir("GET", "/notificaciones", token=tk["encargadoconvivencia"])
c, r = pedir("POST", "/importaciones", {"archivos": [{"nombre_archivo": "ASISTENCIA.csv", "contenido": contenido}]}, tk["administrador"])
prueba("HU 1.1 E1 carga válida procesada", c == 200 and r["archivos"][0]["insertados"] == 3, r)
time.sleep(2)
c, notis = pedir("GET", "/notificaciones", token=tk["encargadoconvivencia"])
prueba("HU 4.4 3 ausencias seguidas importadas generan alerta crítica", len([n for n in notis if n["rut_estudiante"] == rut]) > len([n for n in previas if n["rut_estudiante"] == rut]))
c, r = pedir("POST", "/importaciones", {"archivos": [{"nombre_archivo": "notas.csv", "contenido": f"numero_evaluacion;nota;semestre;rut_estudiante;id_asignatura\n9;5,0;2;{rut};1_3M\n"}]}, tk["administrador"])
prueba("Importación de notas valida R7 (máximo de evaluaciones)", c == 400, r)
c, r = pedir("POST", "/importaciones", {"archivos": [{"nombre_archivo": "ASISTENCIA.csv", "contenido": contenido}]}, tk["director"])
prueba("Solo el administrador importa (403)", c == 403, c)

# --- Reporte semanal (HU 1.3)
c, r = pedir("POST", "/reportes/semanales/generar", token=tk["administrador"])
prueba("HU 1.3 reporte semanal generado para los profesores jefes", c == 200 and len(r["destinatarios"]) == 4, r)
c, reps = pedir("GET", "/reportes/semanales", token=tk["profejefe3m"])
prueba("HU 1.3 el profesor jefe ve su reporte con estudiantes de su curso", c == 200 and len(reps) == 1 and reps[0]["estudiantes"], reps[:1])

# --- Usuarios
c, u = pedir("POST", "/usuarios", {"nombre_usuario": "nuevo.prof", "nombre": "Nuevo Profesor", "rol": "profesor_jefe", "contrasena": "clave12345"}, tk["administrador"])
prueba("Profesor jefe sin curso rechazado", c == 400, u)
c, u = pedir("POST", "/usuarios", {"nombre_usuario": "nuevo.prof", "nombre": "Nuevo Profesor", "rol": "profesor_jefe", "id_nivel": 2, "contrasena": "clave12345"}, tk["administrador"])
prueba("Administrador crea usuario", c == 201, u)
c, _ = pedir("POST", "/usuarios", {"nombre_usuario": "nuevo.prof", "nombre": "Otro", "rol": "profesor", "contrasena": "clave12345"}, tk["administrador"])
prueba("Usuario duplicado (409)", c == 409, c)

print(f"\n{sum(resultados)}/{len(resultados)} pruebas PASS")
sys.exit(0 if all(resultados) else 1)
