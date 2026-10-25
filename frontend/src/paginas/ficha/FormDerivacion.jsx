import { useState } from 'react'
import { api } from '../../api/cliente'
import { ConDatos, MensajeError } from '../../componentes/Estado'
import { useDatos } from '../../hooks/useDatos'

// RF12 / HU 3.4: elegir al profesional de convivencia que continúa el caso.
export default function FormDerivacion({ rut, alGuardar, alCancelar }) {
  const profesionales = useDatos(() => api.profesionales())
  const [datos, setDatos] = useState({ id_usuario_destino: '', motivo: '' })
  const [error, setError] = useState(null)
  const [guardando, setGuardando] = useState(false)

  async function guardar(e) {
    e.preventDefault()
    setGuardando(true)
    setError(null)
    try {
      await api.derivarCaso(rut, { ...datos, id_usuario_destino: Number(datos.id_usuario_destino) })
      alGuardar()
    } catch (err) { setError(err) } finally { setGuardando(false) }
  }

  return (
    <form className="card card-body" onSubmit={guardar}>
      <h3 className="h6">Derivar caso</h3>
      <MensajeError error={error} />
      <ConDatos estado={profesionales}>
        {(lista) => (
          <>
            <label className="form-label small" htmlFor="der-dest">Profesional</label>
            <select id="der-dest" className="form-select mb-2" required value={datos.id_usuario_destino}
              onChange={(e) => setDatos({ ...datos, id_usuario_destino: e.target.value })}>
              <option value="">Seleccione...</option>
              {lista.map((p) => <option key={p.id_usuario} value={p.id_usuario}>{p.nombre} ({p.nombre_rol})</option>)}
            </select>
          </>
        )}
      </ConDatos>
      <label className="form-label small" htmlFor="der-motivo">Motivo</label>
      <textarea id="der-motivo" className="form-control mb-3" rows="3" required maxLength={500} value={datos.motivo}
        onChange={(e) => setDatos({ ...datos, motivo: e.target.value })} />
      <div className="d-flex gap-2">
        <button className="btn btn-warning btn-sm" disabled={guardando || !datos.id_usuario_destino || !datos.motivo.trim()}>
          {guardando ? 'Derivando...' : 'Confirmar derivación'}
        </button>
        <button type="button" className="btn btn-outline-secondary btn-sm" onClick={alCancelar}>Cancelar</button>
      </div>
    </form>
  )
}
