import { useState } from 'react'
import Modal from './Modal'

const TEXTO = { Rojo: 'Riesgo alto', Amarillo: 'Riesgo medio', Verde: 'Sin factores de riesgo' }

export function ListaFactores({ factores }) {
  if (!factores?.length) return <p className="text-secondary mb-0">No se detectaron factores de riesgo.</p>
  return (
    <ul className="mb-0">
      {factores.map((f, i) => (
        <li key={i} className={f.critico ? 'fw-semibold text-danger' : ''}>{f.descripcion}</li>
      ))}
    </ul>
  )
}

// HU 4.1: indicador de color. HU 4.3: al hacer clic muestra los factores que lo provocan.
export default function Semaforo({ nivel, factores, nombre }) {
  const [abierto, setAbierto] = useState(false)
  if (!nivel) return null
  return (
    <>
      <button type="button" className="btn btn-link p-0 text-decoration-none" title={`${TEXTO[nivel]}: ver motivos`}
        onClick={() => setAbierto(true)}>
        <span className={`semaforo semaforo-${nivel}`} aria-hidden="true" />
        <span className="visually-hidden">{TEXTO[nivel]}, ver motivos</span>
      </button>
      {abierto && (
        <Modal titulo={`Motivos de la alerta${nombre ? ` - ${nombre}` : ''}`} alCerrar={() => setAbierto(false)}>
          <p><span className={`semaforo semaforo-${nivel} me-2`} />{TEXTO[nivel]}</p>
          <ListaFactores factores={factores} />
        </Modal>
      )}
    </>
  )
}
