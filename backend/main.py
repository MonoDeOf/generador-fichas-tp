"""API FastAPI de la plataforma de seguimiento de trayectorias y riesgo de deserción escolar.

Ejecutar desde esta carpeta:  uvicorn main:app --reload
Documentación interactiva:    http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

import config
import database
from routers import auth, catalogos, estudiantes, importaciones, reportes, riesgo, seguimiento
from services import auth_service, riesgo_service
from services.errores import ErrorNegocio


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    database.inicializar()
    auth_service.crear_usuarios_iniciales()
    riesgo_service.inicializar_reglas()
    yield


app = FastAPI(title="API Seguimiento de trayectorias y riesgo de deserción escolar", lifespan=ciclo_de_vida)

app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ErrorNegocio)
def manejar_error_negocio(_: Request, error: ErrorNegocio):
    return JSONResponse(status_code=error.codigo, content={"detail": error.mensaje, "detalles": error.detalles})


@app.exception_handler(RequestValidationError)
def manejar_error_validacion(_: Request, error: RequestValidationError):
    detalles = [f"{'.'.join(str(p) for p in e['loc'] if p != 'body')}: {e['msg']}" for e in error.errors()]
    return JSONResponse(status_code=422, content={"detail": "Datos inválidos", "detalles": detalles})


@app.get("/")
def inicio():
    return {"mensaje": "API de seguimiento de trayectorias escolares funcionando"}


for modulo in (auth, catalogos, estudiantes, seguimiento, riesgo, importaciones, reportes):
    app.include_router(modulo.router)
