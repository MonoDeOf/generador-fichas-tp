import { useState } from 'react'
import { api } from '../../api/cliente'
import { ConDatos } from '../../componentes/Estado'
import GraficoBarras from '../../componentes/GraficoBarras'
import { useDatos } from '../../hooks/useDatos'

const DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes']
const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

// HU 2.3: calendario mensual (lunes a viernes) con ausencias en rojo y atrasos en amarillo.
function Calendario({ mes, registros }) {
  const [anio, numMes] = mes.split('-').map(Number)
  const porFecha = Object.fromEntries(registros.map((r) => [r.fecha, r.estado]))
  const celdas = []
  const ultimo = new Date(anio, numMes, 0).getDate()
  for (let dia = 1; dia <= ultimo; dia++) {
    const fecha = new Date(anio, numMes - 1, dia)
    const semana = (fecha.getDay() + 6) % 7
    if (semana > 4) continue
    if (celdas.length === 0) for (let i = 0; i < semana; i++) celdas.push(null)
    const clave = `${mes}-${String(dia).padStart(2, '0')}`
    celdas.push({ dia, estado: porFecha[clave] })
  }
  return (
    <div className="calendario">
      {DIAS.map((d) => <div className="cabecera" key={d}>{d}</div>)}
      {celdas.map((c, i) => c ? (
        <div key={i} className={`dia ${c.estado || ''}`} title={c.estado || 'sin registro'}>
          <div className="fw-semibold">{c.dia}</div>
          <div>{c.estado === 'ausente' ? 'Ausente' : c.estado === 'atraso' ? 'Atraso' : c.estado === 'presente' ? 'Presente' : 'Sin registro'}</div>
        </div>
      ) : <div key={i} />)}
    </div>
  )
}

export default function TabAsistencia({ rut }) {
  const estado = useDatos(() => api.asistencia(rut), [rut])
  const [mes, setMes] = useState(null)
  return (
    <ConDatos estado={estado}>
      {(d) => {
        const meses = d.por_mes.map((m) => m.mes)
        const actual = mes || meses[meses.length - 1]
        const ausenciasPorDia = DIAS.map((nombre, i) => ({
          etiqueta: nombre, valor: d.registros.filter((r) => r.dia_semana === i && r.estado === 'ausente').length,
        }))
        return (
          <div className="row g-4">
            <div className="col-lg-7">
              <div className="card card-body">
                <div className="d-flex align-items-center gap-2 mb-3">
                  <label htmlFor="mes" className="form-label mb-0">Mes</label>
                  <select id="mes" className="form-select w-auto" value={actual} onChange={(e) => setMes(e.target.value)}>
                    {meses.map((m) => <option key={m} value={m}>{MESES[Number(m.slice(5)) - 1]} {m.slice(0, 4)}</option>)}
                  </select>
                </div>
                {actual && <Calendario mes={actual} registros={d.registros} />}
                <div className="small mt-2"><span className="badge bg-danger">Ausente</span> <span className="badge bg-warning text-dark">Atraso</span></div>
              </div>
            </div>
            <div className="col-lg-5">
              <div className="card card-body mb-4">
                <h2 className="h6">Asistencia por mes</h2>
                <GraficoBarras datos={d.por_mes.map((m) => ({ etiqueta: `${MESES[Number(m.mes.slice(5)) - 1]}`, valor: m.porcentaje_asistencia }))} />
              </div>
              <div className="card card-body mb-4">
                <h2 className="h6">Ausencias por día de la semana</h2>
                <GraficoBarras sufijo="" color="#dc3545" maximo={Math.max(1, ...ausenciasPorDia.map((a) => a.valor))} datos={ausenciasPorDia} />
              </div>
              {d.rachas_ausencia.length > 0 && (
                <div className="card card-body">
                  <h2 className="h6">Ausencias consecutivas</h2>
                  <ul className="mb-0">{d.rachas_ausencia.map((r) => <li key={r.inicio}>{r.dias} días: {r.inicio} a {r.fin}</li>)}</ul>
                </div>
              )}
            </div>
          </div>
        )
      }}
    </ConDatos>
  )
}
