import { render, screen } from '@testing-library/react'
import { describe, expect, test } from 'vitest'
import GraficoBarras from '../componentes/GraficoBarras'

describe('GraficoBarras (HU 1.2)', () => {
  test('dibuja una barra por nivel con su valor', () => {
    render(<GraficoBarras datos={[{ etiqueta: '1M', valor: 91.5 }, { etiqueta: '2M', valor: 84 }]} />)
    expect(screen.getByRole('img', { name: '1M: 91.5%' })).toBeInTheDocument()
    expect(screen.getByText('84%')).toBeInTheDocument()
  })

  test('el ancho es proporcional al máximo y no supera el 100 %', () => {
    const { container } = render(<GraficoBarras datos={[{ etiqueta: 'A', valor: 10 }, { etiqueta: 'B', valor: 30 }]} maximo={20} sufijo="" />)
    const rellenos = container.querySelectorAll('.relleno')
    expect(rellenos[0]).toHaveStyle({ width: '50%' })
    expect(rellenos[1]).toHaveStyle({ width: '100%' })
  })

  test('un nivel sin datos se muestra con guion', () => {
    render(<GraficoBarras datos={[{ etiqueta: '4M', valor: null }]} />)
    expect(screen.getByRole('img', { name: '4M: sin datos%' })).toBeInTheDocument()
    expect(screen.getByText('-%')).toBeInTheDocument()
  })
})
