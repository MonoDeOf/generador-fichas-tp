import { useState } from 'react'
import GraficoBarras from '../../componentes/GraficoBarras'
import { ListaFactores } from '../../componentes/Semaforo'
import { useSesion } from '../../hooks/useSesion'
import FormContacto from './FormContacto'

export default function TabResumen({ rut, ficha, alCambiar }) {
  const { puede } = useSesion()
  const [editando, setEditando] = useState(false)
  const { apoderado, asistencia, riesgo } = ficha

  return (
    <div className="row g-4">
      <div className="col-lg-6">
        {riesgo && (
          <div className="card card-body mb-4">
            <h2 className="h5"><span className={`semaforo semaforo-${riesgo.nivel_riesgo} me-2`} />Nivel de riesgo: {riesgo.nivel_riesgo}</h2>
            <p className="small text-secondary mb-1">Factores que provocan la clasificación:</p>
            <ListaFactores factores={riesgo.factores} />
          </div>
        )}
        <div className="card card-body mb-4">
          <h2 className="h5">Red de apoyo (apoderado titular)</h2>
          {apoderado ? (
            editando ? (
              <FormContacto rut={rut} apoderado={apoderado} alCancelar={() => setEditando(false)}
                alGuardar={() => { setEditando(false); alCambiar() }} />
            ) : (
              <>
                <dl className="row mb-2">
                  <dt className="col-4">Nombre</dt><dd className="col-8">{apoderado.nombre} {apoderado.apellido_apoderado}</dd>
                  <dt className="col-4">RUT</dt><dd className="col-8">{apoderado.rut_apoderado}</dd>
                  <dt className="col-4">Teléfono</dt><dd className="col-8">{apoderado.telefono}</dd>
                </dl>
                <div className="d-flex gap-2 flex-wrap">
                  {puede('editar_contacto') && <button className="btn btn-outline-primary btn-sm" onClick={() => setEditando(true)}>Editar contacto</button>}
                </div>
              </>
            )
          ) : <p className="text-secondary">Sin apoderado registrado.</p>}
        </div>
        {ficha.electivos.length > 0 && (
          <div className="card card-body mb-4">
            <h2 className="h5">Electivos</h2>
            <ul className="mb-0">{ficha.electivos.map((e) => <li key={e.id_asignatura}>Combo {e.numero_combo}: {e.nombre_asignatura}</li>)}</ul>
          </div>
        )}
      </div>
      <div className="col-lg-6">
        <div className="card card-body mb-4">
          <h2 className="h5">Asistencia</h2>
          <p className="mb-2">{asistencia.porcentaje_asistencia}% de asistencia en {asistencia.total_dias} días registrados</p>
          <GraficoBarras sufijo="" maximo={asistencia.total_dias} datos={[
            { etiqueta: 'Presente', valor: asistencia.presentes, color: '#198754' },
            { etiqueta: 'Atraso', valor: asistencia.atrasos, color: '#ffc107' },
            { etiqueta: 'Ausente', valor: asistencia.ausentes, color: '#dc3545' },
          ]} />
        </div>
        {ficha.resumen_convivencia && (
          <div className="card card-body mb-4">
            <h2 className="h5">Anotaciones</h2>
            <p className="mb-0">Negativas: {ficha.resumen_convivencia.Negativa} · Neutras: {ficha.resumen_convivencia.Neutra} · Positivas: {ficha.resumen_convivencia.Positiva}</p>
          </div>
        )}
        <div className="card card-body">
          <h2 className="h5">Promedios por asignatura</h2>
          <GraficoBarras sufijo="" maximo={7} datos={ficha.promedios.map((p) => {
            const promedio = p.promedio_s2 ?? p.promedio_s1
            return { etiqueta: p.nombre_asignatura, valor: promedio, color: promedio < 4 ? '#dc3545' : '#0d6efd' }
          })} />
          <p className="small text-secondary mb-0">Se muestra el promedio del último semestre con notas.</p>
        </div>
      </div>
    </div>
  )
}
