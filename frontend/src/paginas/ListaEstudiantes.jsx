import { useState } from 'react'
import { api } from '../api/cliente'
import { ConDatos } from '../componentes/Estado'
import Semaforo from '../componentes/Semaforo'
import { useDatos } from '../hooks/useDatos'
import { enlace } from '../hooks/useRuta'
import { useSesion } from '../hooks/useSesion'

const nombreCompleto = (e) => `${e.nombre} ${e.apellido_paterno} ${e.apellido_materno}`

// RF04 / HU 1.4 / HU 4.1: lista de estudiantes con filtros y semáforo de riesgo.
export default function ListaEstudiantes() {
  const { catalogos, puede, usuario } = useSesion()
  const verRiesgo = puede('ver_riesgo')
  const [filtros, setFiltros] = useState({ id_nivel: '', id_especialidad: '', nivel_riesgo: '', busqueda: '' })
  const [busqueda, setBusqueda] = useState('')
  const estado = useDatos(() => api.estudiantes(filtros), [JSON.stringify(filtros)])
  const cambiar = (campo) => (e) => setFiltros({ ...filtros, [campo]: e.target.value })

  return (
    <>
      <h1 className="h3">Estudiantes{usuario.rol === 'profesor_jefe' ? ' de mi curso' : ''}</h1>
      <form className="row g-2 mb-3" onSubmit={(e) => { e.preventDefault(); setFiltros({ ...filtros, busqueda }) }}>
        <div className="col-md-3">
          <label className="form-label small" htmlFor="busqueda">Buscar por nombre o RUT</label>
          <div className="input-group">
            <input id="busqueda" className="form-control" value={busqueda} onChange={(e) => setBusqueda(e.target.value)} />
            <button className="btn btn-outline-primary">Buscar</button>
          </div>
        </div>
        {usuario.rol !== 'profesor_jefe' && (
          <div className="col-md-2">
            <label className="form-label small" htmlFor="nivel">Nivel</label>
            <select id="nivel" className="form-select" value={filtros.id_nivel} onChange={cambiar('id_nivel')}>
              <option value="">Todos</option>
              {catalogos?.niveles.map((n) => <option key={n.id_nivel} value={n.id_nivel}>{n.nombre_nivel}</option>)}
            </select>
          </div>
        )}
        <div className="col-md-3">
          <label className="form-label small" htmlFor="especialidad">Especialidad</label>
          <select id="especialidad" className="form-select" value={filtros.id_especialidad} onChange={cambiar('id_especialidad')}>
            <option value="">Todas</option>
            {catalogos?.especialidades.map((e) => <option key={e.id_especialidad} value={e.id_especialidad}>{e.nombre_especialidad}</option>)}
          </select>
        </div>
        {verRiesgo && (
          <div className="col-md-2">
            <label className="form-label small" htmlFor="riesgo">Nivel de riesgo</label>
            <select id="riesgo" className="form-select" value={filtros.nivel_riesgo} onChange={cambiar('nivel_riesgo')}>
              <option value="">Todos</option>
              {catalogos?.niveles_riesgo.map((n) => <option key={n}>{n}</option>)}
            </select>
          </div>
        )}
      </form>
      <ConDatos estado={estado}>
        {(lista) => (
          <div className="card">
            <div className="table-responsive">
              <table className="table table-hover align-middle mb-0">
                <thead>
                  <tr>{verRiesgo && <th>Riesgo</th>}<th>Estudiante</th><th>RUT</th><th>Nivel</th><th>Especialidad</th>
                    {verRiesgo && <th>Asistencia</th>}</tr>
                </thead>
                <tbody>
                  {lista.length === 0 && <tr><td colSpan="6" className="text-secondary">No hay estudiantes para mostrar (con estos filtros o porque aún no se cargan los datos).</td></tr>}
                  {lista.map((e) => (
                    <tr key={e.rut_estudiante}>
                      {verRiesgo && <td><Semaforo nivel={e.nivel_riesgo} factores={e.factores} nombre={nombreCompleto(e)} /></td>}
                      <td><a href={enlace('estudiante', e.rut_estudiante)}>{nombreCompleto(e)}</a></td>
                      <td>{e.rut_estudiante}</td><td>{e.nombre_nivel}</td><td>{e.nombre_especialidad || '-'}</td>
                      {verRiesgo && <td>{e.porcentaje_asistencia}%</td>}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="card-footer small text-secondary">{lista.length} estudiantes</div>
          </div>
        )}
      </ConDatos>
    </>
  )
}
