import { api } from '../api/cliente'
import { ConDatos } from '../componentes/Estado'
import { useDatos } from '../hooks/useDatos'
import { enlace } from '../hooks/useRuta'
import { useSesion } from '../hooks/useSesion'

const TITULO = { alerta_critica: 'Alerta crítica', derivacion: 'Caso derivado', reporte_semanal: 'Reporte semanal' }

// RF16 / HU 4.4: bandeja de notificaciones internas.
export default function Notificaciones() {
  const { puede } = useSesion()
  const estado = useDatos(() => api.notificaciones())
  const avisar = () => window.dispatchEvent(new Event('notificaciones-cambiaron'))

  async function marcar(n) {
    if (!n.leida) {
      await api.marcarLeida(n.id_notificacion).catch(() => {})
      avisar()
      estado.recargar()
    }
  }

  async function marcarTodas() {
    await api.marcarTodasLeidas().catch(() => {})
    avisar()
    estado.recargar()
  }

  return (
    <>
      <div className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
        <h1 className="h3 mb-0">Notificaciones</h1>
        <button className="btn btn-outline-primary btn-sm" onClick={marcarTodas}>Marcar todas como leídas</button>
      </div>
      <ConDatos estado={estado}>
        {(lista) => lista.length === 0 ? <p className="text-secondary">No tiene notificaciones.</p> : (
          <div className="list-group">
            {lista.map((n) => (
              <div key={n.id_notificacion} className={`list-group-item ${n.leida ? '' : 'list-group-item-light border-start border-4 border-danger'}`}>
                <div className="d-flex justify-content-between flex-wrap gap-2">
                  <strong>{TITULO[n.tipo] || n.tipo}{!n.leida && <span className="badge bg-danger ms-2">Nueva</span>}</strong>
                  <small className="text-secondary">{n.fecha.replace('T', ' ')}</small>
                </div>
                <p className="mb-1">{n.mensaje}</p>
                <div className="d-flex gap-3">
                  {n.rut_estudiante && puede('ver_ficha') && (
                    <a href={enlace('estudiante', n.rut_estudiante)} onClick={() => marcar(n)}>Ver ficha</a>
                  )}
                  {n.tipo === 'reporte_semanal' && <a href="#/reportes" onClick={() => marcar(n)}>Ver reporte</a>}
                  {!n.leida && <button className="btn btn-link btn-sm p-0" onClick={() => marcar(n)}>Marcar como leída</button>}
                </div>
              </div>
            ))}
          </div>
        )}
      </ConDatos>
    </>
  )
}
