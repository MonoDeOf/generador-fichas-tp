import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest'
import { api, configurarExpiracion, ErrorApi, sesionGuardada } from '../api/cliente'

function respuesta(status, cuerpo) {
  return Promise.resolve({ ok: status < 400, status, json: () => Promise.resolve(cuerpo) })
}

describe('Cliente de la API (integración frontend → FastAPI)', () => {
  beforeEach(() => { globalThis.fetch = vi.fn(); sessionStorage.clear() })
  afterEach(() => vi.restoreAllMocks())

  test('envía el token Bearer y omite los filtros vacíos (HU 1.4)', async () => {
    sesionGuardada.guardar('abc')
    fetch.mockReturnValue(respuesta(200, []))
    await api.estudiantes({ id_especialidad: 3, id_nivel: '', busqueda: null })
    const [url, opciones] = fetch.mock.calls[0]
    expect(url).toMatch(/\/estudiantes\?id_especialidad=3$/)
    expect(opciones.headers.Authorization).toBe('Bearer abc')
  })

  test('envía el cuerpo como JSON', async () => {
    fetch.mockReturnValue(respuesta(200, {}))
    await api.guardarReglas({ umbral_asistencia: 85 })
    const [, opciones] = fetch.mock.calls[0]
    expect(opciones.method).toBe('PUT')
    expect(JSON.parse(opciones.body)).toEqual({ umbral_asistencia: 85 })
  })

  test('convierte un error de la API en ErrorApi con sus detalles', async () => {
    fetch.mockReturnValue(respuesta(400, { detail: 'La configuración no fue guardada', detalles: ['entre 0 y 100'] }))
    const error = await api.guardarReglas({}).catch((e) => e)
    expect(error).toBeInstanceOf(ErrorApi)
    expect(error.estado).toBe(400)
    expect(error.detalles).toEqual(['entre 0 y 100'])
  })

  test('un 401 cierra la sesión, salvo en el login', async () => {
    const alExpirar = vi.fn()
    configurarExpiracion(alExpirar)
    fetch.mockReturnValue(respuesta(401, { detail: 'Sesión no válida o expirada' }))
    await api.dashboard().catch(() => {})
    expect(alExpirar).toHaveBeenCalledTimes(1)
    await api.login('x', 'y').catch(() => {})
    expect(alExpirar).toHaveBeenCalledTimes(1)
  })

  test('sin conexión informa un mensaje claro', async () => {
    fetch.mockRejectedValue(new TypeError('Failed to fetch'))
    const error = await api.dashboard().catch((e) => e)
    expect(error.estado).toBe(0)
    expect(error.message).toMatch(/No se pudo conectar/)
  })
})
