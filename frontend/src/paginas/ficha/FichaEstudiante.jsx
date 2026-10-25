import { useState } from 'react'
import { api } from '../../api/cliente'
import { ConDatos } from '../../componentes/Estado'
import { useDatos } from '../../hooks/useDatos'
import { useSesion } from '../../hooks/useSesion'
import TabAsistencia from './TabAsistencia'
import TabCalificaciones from './TabCalificaciones'
import TabConvivencia from './TabConvivencia'
import TabResumen from './TabResumen'

const PESTANAS = [
  { id: 'resumen', texto: 'Ficha', componente: TabResumen },
  { id: 'asistencia', texto: 'Asistencia', componente: TabAsistencia },
  { id: 'calificaciones', texto: 'Calificaciones', componente: TabCalificaciones },
  { id: 'convivencia', texto: 'Convivencia', componente: TabConvivencia, permiso: 'ver_convivencia' },
]

// RF05 / HU 2.1: ficha integral con pestañas.
export default function FichaEstudiante({ parametros }) {
  const rut = parametros[0]
  const { puede } = useSesion()
  const [pestana, setPestana] = useState('resumen')
  const estado = useDatos(() => api.ficha(rut), [rut])
  const visibles = PESTANAS.filter((p) => !p.permiso || puede(p.permiso))
  const Actual = visibles.find((p) => p.id === pestana)?.componente || TabResumen

  return (
    <>
      <a href="#/estudiantes" className="small">&larr; Volver a la lista</a>
      <ConDatos estado={estado}>
        {(ficha) => (
          <>
            <h1 className="h3 mt-2">
              {ficha.estudiante.nombre} {ficha.estudiante.apellido_paterno} {ficha.estudiante.apellido_materno}
            </h1>
            <p className="text-secondary">
              {ficha.estudiante.rut_estudiante} · {ficha.estudiante.nombre_nivel}
              {ficha.estudiante.nombre_especialidad ? ` · ${ficha.estudiante.nombre_especialidad}` : ''}
            </p>
            <ul className="nav nav-tabs mb-3">
              {visibles.map((p) => (
                <li className="nav-item" key={p.id}>
                  <button className={`nav-link ${p.id === pestana ? 'active' : ''}`} onClick={() => setPestana(p.id)}>{p.texto}</button>
                </li>
              ))}
            </ul>
            <Actual rut={rut} ficha={ficha} alCambiar={estado.recargar} />
          </>
        )}
      </ConDatos>
    </>
  )
}
