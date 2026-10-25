import { useState } from 'react'
import { api } from '../../api/cliente'
import { MensajeError } from '../../componentes/Estado'
import { useSesion } from '../../hooks/useSesion'

const hoy = () => new Date().toLocaleDateString('sv-SE')

// RF09 / HU 3.1: fecha, tipo de acción y notas. El responsable es el usuario de la sesión.
export default function FormIntervencion({ rut, alGuardar, alCancelar }) {
  const { catalogos } = useSesion()
  const [datos, setDatos] = useState({ fecha: hoy(), tipo_intervencion: '', descripcion: '' })
  const [error, setError] = useState(null)
  const [guardando, setGuardando] = useState(false)
  const cambiar = (campo) => (e) => setDatos({ ...datos, [campo]: e.target.value })

  async function guardar(e) {
    e.preventDefault()
    setGuardando(true)
    setError(null)
    try { await api.registrarIntervencion(rut, datos); alGuardar() } catch (err) { setError(err) } finally { setGuardando(false) }
  }

  return (
    <form className="card card-body" onSubmit={guardar}>
      <h3 className="h6">Nueva intervención</h3>
      <MensajeError error={error} />
      <label className="form-label small" htmlFor="int-fecha">Fecha</label>
      <input id="int-fecha" type="date" className="form-control mb-2" required max={hoy()} value={datos.fecha} onChange={cambiar('fecha')} />
      <label className="form-label small" htmlFor="int-tipo">Tipo de acción</label>
      <select id="int-tipo" className="form-select mb-2" required value={datos.tipo_intervencion} onChange={cambiar('tipo_intervencion')}>
        <option value="">Seleccione...</option>
        {catalogos?.tipos_intervencion.map((t) => <option key={t}>{t}</option>)}
      </select>
      <label className="form-label small" htmlFor="int-desc">Notas / descripción</label>
      <textarea id="int-desc" className="form-control mb-3" rows="4" required maxLength={2000} value={datos.descripcion} onChange={cambiar('descripcion')} />
      <div className="d-flex gap-2">
        <button className="btn btn-primary btn-sm" disabled={guardando || !datos.descripcion.trim()}>{guardando ? 'Guardando...' : 'Guardar'}</button>
        <button type="button" className="btn btn-outline-secondary btn-sm" onClick={alCancelar}>Cancelar</button>
      </div>
    </form>
  )
}
