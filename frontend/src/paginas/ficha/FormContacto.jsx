import { useState } from 'react'
import { api } from '../../api/cliente'
import { MensajeError } from '../../componentes/Estado'

// RF06 / HU 2.2: actualización del apoderado titular. El teléfono debe tener 9 dígitos.
export default function FormContacto({ rut, apoderado, alGuardar, alCancelar }) {
  const [datos, setDatos] = useState({ nombre: apoderado.nombre, apellido_apoderado: apoderado.apellido_apoderado, telefono: apoderado.telefono })
  const [error, setError] = useState(null)
  const [aviso, setAviso] = useState(null)
  const [guardando, setGuardando] = useState(false)
  const telefonoValido = /^\d{9}$/.test(datos.telefono)
  const cambiar = (campo) => (e) => setDatos({ ...datos, [campo]: e.target.value })

  async function guardar(e) {
    e.preventDefault()
    setGuardando(true)
    setError(null)
    try {
      const r = await api.actualizarApoderado(rut, datos)
      if (r.otros_estudiantes_afectados.length) {
        setAviso(`Este apoderado también está registrado para ${r.otros_estudiantes_afectados.length} estudiante(s) más; el cambio se aplica a todos.`)
        setTimeout(alGuardar, 2500)
      } else alGuardar()
    } catch (err) { setError(err) } finally { setGuardando(false) }
  }

  return (
    <form onSubmit={guardar} noValidate>
      <MensajeError error={error} />
      {aviso && <div className="alert alert-info">{aviso}</div>}
      <div className="row g-2">
        <div className="col-sm-6">
          <label className="form-label small" htmlFor="ap-nombre">Nombre</label>
          <input id="ap-nombre" className="form-control" required maxLength={50} value={datos.nombre} onChange={cambiar('nombre')} />
        </div>
        <div className="col-sm-6">
          <label className="form-label small" htmlFor="ap-apellido">Apellido</label>
          <input id="ap-apellido" className="form-control" required maxLength={50} value={datos.apellido_apoderado} onChange={cambiar('apellido_apoderado')} />
        </div>
        <div className="col-sm-6">
          <label className="form-label small" htmlFor="ap-telefono">Teléfono (9 dígitos)</label>
          <input id="ap-telefono" className={`form-control ${telefonoValido ? '' : 'is-invalid'}`} inputMode="numeric" maxLength={9}
            value={datos.telefono} onChange={cambiar('telefono')} />
          <div className="invalid-feedback">Debe tener exactamente 9 dígitos numéricos.</div>
        </div>
      </div>
      <div className="mt-3 d-flex gap-2">
        <button className="btn btn-primary btn-sm" disabled={guardando || !telefonoValido || !datos.nombre.trim() || !datos.apellido_apoderado.trim()}>
          {guardando ? 'Guardando...' : 'Guardar cambios'}
        </button>
        <button type="button" className="btn btn-outline-secondary btn-sm" onClick={alCancelar}>Cancelar</button>
      </div>
    </form>
  )
}
