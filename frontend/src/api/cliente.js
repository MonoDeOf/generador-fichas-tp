// Comunicación con la API FastAPI. Todas las peticiones intercambian JSON.
const URL_API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'
const CLAVE_TOKEN = 'token_sesion'

export class ErrorApi extends Error {
  constructor(estado, mensaje, detalles = []) {
    super(mensaje)
    this.estado = estado
    this.detalles = detalles
  }
}

export const sesionGuardada = {
  obtener: () => sessionStorage.getItem(CLAVE_TOKEN),
  guardar: (token) => sessionStorage.setItem(CLAVE_TOKEN, token),
  borrar: () => sessionStorage.removeItem(CLAVE_TOKEN),
}

let alExpirarSesion = () => {}
export function configurarExpiracion(funcion) { alExpirarSesion = funcion }

async function pedir(metodo, ruta, cuerpo) {
  const token = sesionGuardada.obtener()
  let respuesta
  try {
    respuesta = await fetch(URL_API + ruta, {
      method: metodo,
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
    })
  } catch {
    throw new ErrorApi(0, 'No se pudo conectar con el servidor. Revise su conexión e intente nuevamente.')
  }
  const datos = await respuesta.json().catch(() => null)
  if (!respuesta.ok) {
    if (respuesta.status === 401 && ruta !== '/auth/login') alExpirarSesion()
    throw new ErrorApi(respuesta.status, datos?.detail || `Error ${respuesta.status}`, datos?.detalles || [])
  }
  return datos
}

function consulta(parametros) {
  const limpio = Object.entries(parametros).filter(([, v]) => v !== '' && v !== null && v !== undefined)
  return limpio.length ? '?' + new URLSearchParams(limpio).toString() : ''
}

const r = encodeURIComponent

export const api = {
  login: (nombre_usuario, contrasena) => pedir('POST', '/auth/login', { nombre_usuario, contrasena }),
  sesion: () => pedir('GET', '/auth/me'),
  catalogos: () => pedir('GET', '/catalogos'),

  estudiantes: (filtros = {}) => pedir('GET', '/estudiantes' + consulta(filtros)),
  ficha: (rut) => pedir('GET', `/estudiantes/${r(rut)}`),
  asistencia: (rut) => pedir('GET', `/estudiantes/${r(rut)}/asistencia`),
  calificaciones: (rut) => pedir('GET', `/estudiantes/${r(rut)}/calificaciones`),
  anotaciones: (rut) => pedir('GET', `/estudiantes/${r(rut)}/anotaciones`),
  riesgo: (rut) => pedir('GET', `/estudiantes/${r(rut)}/riesgo`),
  actualizarApoderado: (rut, datos) => pedir('PUT', `/estudiantes/${r(rut)}/apoderado`, datos),
  whatsapp: (rut) => pedir('GET', `/estudiantes/${r(rut)}/contacto-whatsapp`),

  seguimiento: (rut) => pedir('GET', `/estudiantes/${r(rut)}/seguimiento`),
  registrarIntervencion: (rut, datos) => pedir('POST', `/estudiantes/${r(rut)}/intervenciones`, datos),
  derivarCaso: (rut, datos) => pedir('POST', `/estudiantes/${r(rut)}/caso/derivar`, datos),
  cambiarEstadoCaso: (rut, datos) => pedir('PATCH', `/estudiantes/${r(rut)}/caso/estado`, datos),
  casosAsignados: () => pedir('GET', '/casos/asignados'),
  profesionales: () => pedir('GET', '/casos/profesionales'),

  reglas: () => pedir('GET', '/config/reglas'),
  guardarReglas: (datos) => pedir('PUT', '/config/reglas', datos),
  importar: (datos) => pedir('POST', '/importaciones', datos),
  estadoTablas: () => pedir('GET', '/importaciones/estado'),

  dashboard: () => pedir('GET', '/dashboard'),
}
