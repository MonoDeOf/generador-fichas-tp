import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, test, vi } from 'vitest'
import { api } from '../api/cliente'
import FormContacto from '../paginas/ficha/FormContacto'

vi.mock('../api/cliente', () => ({ api: { actualizarApoderado: vi.fn() } }))

const APODERADO = { nombre: 'Ana', apellido_apoderado: 'Rojas', telefono: '912345678' }

describe('FormContacto (HU 2.2)', () => {
  beforeEach(() => vi.clearAllMocks())

  test('con un teléfono de 8 dígitos marca el error y deshabilita Guardar', async () => {
    render(<FormContacto rut="1-1" apoderado={APODERADO} alGuardar={vi.fn()} alCancelar={vi.fn()} />)
    const telefono = screen.getByLabelText('Teléfono (9 dígitos)')
    await userEvent.clear(telefono)
    await userEvent.type(telefono, '98765432')
    expect(telefono).toHaveClass('is-invalid')
    expect(screen.getByRole('button', { name: 'Guardar cambios' })).toBeDisabled()
  })

  test('con datos válidos envía el cambio a la API y avisa al guardar', async () => {
    api.actualizarApoderado.mockResolvedValue({ otros_estudiantes_afectados: [] })
    const alGuardar = vi.fn()
    render(<FormContacto rut="1-1" apoderado={APODERADO} alGuardar={alGuardar} alCancelar={vi.fn()} />)
    const telefono = screen.getByLabelText('Teléfono (9 dígitos)')
    await userEvent.clear(telefono)
    await userEvent.type(telefono, '987654321')
    await userEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    expect(api.actualizarApoderado).toHaveBeenCalledWith('1-1', { ...APODERADO, telefono: '987654321' })
    expect(alGuardar).toHaveBeenCalled()
  })

  test('muestra el error que devuelve el backend', async () => {
    api.actualizarApoderado.mockRejectedValue(Object.assign(new Error('Datos inválidos'), { detalles: ['telefono: formato'] }))
    render(<FormContacto rut="1-1" apoderado={APODERADO} alGuardar={vi.fn()} alCancelar={vi.fn()} />)
    await userEvent.click(screen.getByRole('button', { name: 'Guardar cambios' }))
    expect(await screen.findByRole('alert')).toHaveTextContent('Datos inválidos')
  })

  test('Cancelar no llama a la API', async () => {
    const alCancelar = vi.fn()
    render(<FormContacto rut="1-1" apoderado={APODERADO} alGuardar={vi.fn()} alCancelar={alCancelar} />)
    await userEvent.click(screen.getByRole('button', { name: 'Cancelar' }))
    expect(alCancelar).toHaveBeenCalled()
    expect(api.actualizarApoderado).not.toHaveBeenCalled()
  })
})
