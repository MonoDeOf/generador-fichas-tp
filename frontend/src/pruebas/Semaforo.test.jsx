import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, test } from 'vitest'
import Semaforo from '../componentes/Semaforo'

const FACTORES = [
  { tipo: 'regla_combinada', critico: true, descripcion: 'Cumple la regla combinada' },
  { tipo: 'asistencia', descripcion: 'Asistencia de 80% bajo el umbral de 85%' },
]

describe('Semaforo (HU 4.1 y 4.3)', () => {
  test('no muestra nada si el rol no recibe nivel de riesgo', () => {
    const { container } = render(<Semaforo nivel={null} factores={[]} />)
    expect(container).toBeEmptyDOMElement()
  })

  test('muestra el color según el nivel', () => {
    const { container } = render(<Semaforo nivel="Rojo" factores={FACTORES} />)
    expect(container.querySelector('.semaforo-Rojo')).toBeInTheDocument()
    expect(screen.getByText('Riesgo alto, ver motivos')).toBeInTheDocument()
  })

  test('al hacer clic abre el modal con los motivos y destaca los críticos', async () => {
    render(<Semaforo nivel="Rojo" factores={FACTORES} nombre="Luis Soto" />)
    await userEvent.click(screen.getByRole('button'))
    expect(screen.getByRole('dialog', { name: 'Motivos de la alerta - Luis Soto' })).toBeInTheDocument()
    expect(screen.getByText('Cumple la regla combinada')).toHaveClass('text-danger')
    expect(screen.getByText('Asistencia de 80% bajo el umbral de 85%')).not.toHaveClass('text-danger')
  })

  test('el modal se cierra con Escape', async () => {
    render(<Semaforo nivel="Amarillo" factores={FACTORES.slice(1)} />)
    await userEvent.click(screen.getByRole('button'))
    await userEvent.keyboard('{Escape}')
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  test('nivel verde informa que no hay factores', async () => {
    render(<Semaforo nivel="Verde" factores={[]} />)
    await userEvent.click(screen.getByRole('button'))
    expect(screen.getByText('No se detectaron factores de riesgo.')).toBeInTheDocument()
  })
})
