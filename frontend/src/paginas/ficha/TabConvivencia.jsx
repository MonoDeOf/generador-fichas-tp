import { api } from '../../api/cliente'
import { ConDatos } from '../../componentes/Estado'
import { useDatos } from '../../hooks/useDatos'

const COLOR = { Negativa: 'bg-danger', Neutra: 'bg-secondary', Positiva: 'bg-success' }

// RF08 / HU 2.4: listado de anotaciones. El CSV no tiene fecha: se ordenan por orden de registro.
export default function TabConvivencia({ rut }) {
  const estado = useDatos(() => api.anotaciones(rut), [rut])
  return (
    <ConDatos estado={estado}>
      {(anotaciones) => (
        <div className="card">
          <div className="table-responsive">
            <table className="table table-sm align-middle mb-0">
              <thead><tr><th>N°</th><th>Tipo</th><th>Ámbito</th><th>Descripción</th></tr></thead>
              <tbody>
                {anotaciones.length === 0 && <tr><td colSpan="4" className="text-secondary">Sin anotaciones registradas.</td></tr>}
                {anotaciones.map((a) => (
                  <tr key={a.id_anotacion}>
                    <td>{a.id_anotacion}</td>
                    <td><span className={`badge ${COLOR[a.tipo_anotacion]}`}>{a.tipo_anotacion}</span></td>
                    <td>{a.ambito}{a.nombre_asignatura ? `: ${a.nombre_asignatura}` : ''}</td>
                    <td>{a.descripcion_anotacion}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <div className="card-footer small text-secondary">Ordenadas por número de registro (el archivo de anotaciones no incluye fecha).</div>
        </div>
      )}
    </ConDatos>
  )
}
