import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test, vi } from 'vitest'
import { ConDatos, MensajeError, MensajeExito } from '../componentes/Estado'

describe('Componentes de estado', () => {
  test('MensajeError muestra el mensaje y los detalles de la API', () => {
    const error = { message: 'La configuración no fue guardada', detalles: ['El porcentaje de asistencia debe encontrarse entre 0 y 100'] }
    render(<MensajeError error={error} />)
    expect(screen.getByRole('alert')).toHaveTextContent('La configuración no fue guardada')
    expect(screen.getByText(/entre 0 y 100/)).toBeInTheDocument()
  })

  test('MensajeError ejecuta la función de reintento', async () => {
    const reintentar = vi.fn()
    render(<MensajeError error={{ message: 'Sin conexión' }} alReintentar={reintentar} />)
    await userEvent.click(screen.getByRole('button', { name: 'Reintentar' }))
    expect(reintentar).toHaveBeenCalledTimes(1)
  })

  test('sin error ni texto no se muestra nada', () => {
    const { container } = render(<><MensajeError error={null} /><MensajeExito texto="" /></>)
    expect(container).toBeEmptyDOMElement()
  })

  test('ConDatos muestra cargando, error o el contenido', () => {
    const hijo = (d) => <p>{d.total} estudiantes</p>
    const { rerender } = render(<ConDatos estado={{ cargando: true, datos: null }}>{hijo}</ConDatos>)
    expect(screen.getByRole('status')).toHaveTextContent('Cargando...')
    rerender(<ConDatos estado={{ cargando: false, error: { message: 'Error 500' } }}>{hijo}</ConDatos>)
    expect(screen.getByRole('alert')).toHaveTextContent('Error 500')
    rerender(<ConDatos estado={{ cargando: false, datos: { total: 90 } }}>{hijo}</ConDatos>)
    expect(screen.getByText('90 estudiantes')).toBeInTheDocument()
  })
})
