import { api } from '../api/cliente'
import { ConDatos } from '../componentes/Estado'
import { useDatos } from '../hooks/useDatos'
import { enlace } from '../hooks/useRuta'

// HU 3.4: los casos derivados aparecen destacados en el panel del profesional asignado.
export default function MisCasos() {
  const estado = useDatos(() => api.casosAsignados())
  return (
    <>
      <h1 className="h3">Mis casos</h1>
      <ConDatos estado={estado}>
        {(casos) => casos.length === 0 ? <p className="text-secondary">No tiene casos abiertos a su cargo.</p> : (
          <div className="list-group">
            {casos.map((c) => (
              <a key={c.id_caso} href={enlace('estudiante', c.rut_estudiante)}
                className={`list-group-item list-group-item-action ${c.estado === 'derivado' ? 'list-group-item-warning' : ''}`}>
                <div className="d-flex justify-content-between flex-wrap">
                  <strong>{c.nombre_estudiante} · {c.nombre_nivel}</strong>
                  <span className="badge bg-secondary">{c.estado}</span>
                </div>
                <small className="text-secondary">Actualizado: {c.fecha_actualizacion.replace('T', ' ')}</small>
              </a>
            ))}
          </div>
        )}
      </ConDatos>
    </>
  )
}
