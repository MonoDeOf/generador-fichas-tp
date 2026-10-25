import { useState } from 'react'
import { api } from '../../api/cliente'
import { ConDatos, MensajeError, MensajeExito } from '../../componentes/Estado'
import { useDatos } from '../../hooks/useDatos'
import { useSesion } from '../../hooks/useSesion'
import FormDerivacion from './FormDerivacion'
import FormIntervencion from './FormIntervencion'

const COLOR_ESTADO = { abierto: 'bg-primary', derivado: 'bg-warning text-dark', cerrado: 'bg-secondary' }
const fechaLegible = (f) => f.replace('T', ' ')

// HU 3.3: línea de tiempo vertical desde el registro más reciente.
function LineaTiempo({ eventos }) {
  if (!eventos.length) return <p className="text-secondary">Aún no hay registros en la bitácora.</p>
  return (
    <ul className="linea-tiempo">
      {eventos.map((ev) => ev.clase === 'intervencion' ? (
        <li key={`i${ev.id_intervencion}`}>
          <div className="small text-secondary">{ev.fecha} · {ev.responsable}</div>
          <div className="fw-semibold">{ev.tipo_intervencion}</div>
          <div style={{ whiteSpace: 'pre-wrap' }}>{ev.descripcion}</div>
        </li>
      ) : (
        <li key={`c${ev.id_historial}`} className="caso">
          <div className="small text-secondary">{fechaLegible(ev.fecha)} · {ev.realizado_por}</div>
          <div className="fw-semibold">Caso {ev.estado}{ev.estado === 'derivado' ? ` a ${ev.responsable}` : ''}</div>
          <div>{ev.motivo}</div>
        </li>
      ))}
    </ul>
  )
}

function CambioEstado({ rut, caso, alCambiar }) {
  const [error, setError] = useState(null)
  const nuevo = caso.estado === 'cerrado' ? 'abierto' : 'cerrado'
  async function cambiar() {
    const motivo = window.prompt(nuevo === 'cerrado' ? 'Motivo del cierre del caso:' : 'Motivo de la reapertura:')
    if (motivo === null) return
    setError(null)
    try { await api.cambiarEstadoCaso(rut, { estado: nuevo, motivo }); alCambiar() } catch (e) { setError(e) }
  }
  return (
    <>
      <button className="btn btn-outline-secondary btn-sm" onClick={cambiar}>{nuevo === 'cerrado' ? 'Cerrar caso' : 'Reabrir caso'}</button>
      <MensajeError error={error} />
    </>
  )
}

export default function TabSeguimiento({ rut }) {
  const { puede, usuario } = useSesion()
  const estado = useDatos(() => api.seguimiento(rut), [rut])
  const [formulario, setFormulario] = useState(null)
  const [exito, setExito] = useState(null)

  function alGuardar(mensaje) {
    setFormulario(null)
    setExito(mensaje)
    estado.recargar()
    window.dispatchEvent(new Event('notificaciones-cambiaron'))
  }

  return (
    <ConDatos estado={estado}>
      {({ caso, eventos }) => {
        const esResponsable = caso && caso.id_usuario_responsable === usuario.id_usuario
        const puedeCambiarEstado = caso && (puede('derivar_casos') || (puede('recibir_derivaciones') && esResponsable))
        return (
          <div className="row g-4">
            <div className="col-lg-5">
              <div className="card card-body mb-3">
                <h2 className="h5">Estado del caso</h2>
                {caso ? (
                  <p className="mb-2"><span className={`badge ${COLOR_ESTADO[caso.estado]}`}>{caso.estado}</span> · Responsable: {caso.responsable}</p>
                ) : <p className="text-secondary mb-2">Sin caso abierto. Se abre al registrar la primera intervención o al derivar.</p>}
                <div className="d-flex gap-2 flex-wrap">
                  {puede('registrar_intervencion') && <button className="btn btn-primary btn-sm" onClick={() => { setExito(null); setFormulario('intervencion') }}>Nueva intervención</button>}
                  {puede('derivar_casos') && caso?.estado !== 'cerrado' && <button className="btn btn-warning btn-sm" onClick={() => { setExito(null); setFormulario('derivacion') }}>Derivar caso</button>}
                  {puedeCambiarEstado && <CambioEstado rut={rut} caso={caso} alCambiar={estado.recargar} />}
                </div>
              </div>
              <MensajeExito texto={exito} />
              {formulario === 'intervencion' && (
                <FormIntervencion rut={rut} alCancelar={() => setFormulario(null)} alGuardar={() => alGuardar('Intervención registrada en la bitácora.')} />
              )}
              {formulario === 'derivacion' && (
                <FormDerivacion rut={rut} alCancelar={() => setFormulario(null)} alGuardar={() => alGuardar('Caso derivado; el profesional fue notificado.')} />
              )}
            </div>
            <div className="col-lg-7">
              <div className="card card-body">
                <h2 className="h5">Línea de tiempo de intervenciones</h2>
                <LineaTiempo eventos={eventos} />
              </div>
            </div>
          </div>
        )
      }}
    </ConDatos>
  )
}
