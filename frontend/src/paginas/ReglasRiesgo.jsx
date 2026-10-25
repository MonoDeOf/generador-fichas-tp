import { useState } from 'react'
import { api } from '../api/cliente'
import { ConDatos, MensajeError, MensajeExito } from '../componentes/Estado'
import { useDatos } from '../hooks/useDatos'

const CAMPOS = [
  { id: 'umbral_asistencia', min: 0, max: 100, paso: 'any', unidad: '%' },
  { id: 'nota_deficiente', min: 1, max: 7, paso: 0.1 },
  { id: 'min_notas_deficientes', min: 1, paso: 1 },
  { id: 'ausencias_consecutivas', min: 1, paso: 1 },
  { id: 'min_anotaciones_negativas', min: 0, paso: 1 },
]

// RF14 / HU 4.2: configuración de umbrales y reglas del motor de riesgo.
export default function ReglasRiesgo() {
  const estado = useDatos(() => api.reglas())
  return (
    <>
      <h1 className="h3">Reglas de riesgo</h1>
      <ConDatos estado={estado}>
        {(d) => <FormReglas key={d.ultima_actualizacion} d={d} />}
      </ConDatos>
    </>
  )
}

const comoTexto = (reglas) => Object.fromEntries(Object.entries(reglas).map(([k, v]) => [k, String(v)]))

function FormReglas({ d }) {
  const [form, setForm] = useState(() => comoTexto(d.reglas))
  const [error, setError] = useState(null)
  const [exito, setExito] = useState(null)
  const [guardando, setGuardando] = useState(false)

  async function guardar(e) {
    e.preventDefault()
    setError(null)
    setExito(null)
    const vacios = Object.entries(form).filter(([, v]) => v.trim() === '').map(([k]) => d.descripciones[k])
    if (vacios.length) { setError({ message: 'Complete los valores obligatorios', detalles: vacios }); return }
    setGuardando(true)
    try {
      const datos = Object.fromEntries(Object.entries(form).map(([k, v]) => [k, k === 'operador' ? v : Number(v)]))
      const r = await api.guardarReglas(datos)
      setExito(`${r.mensaje}. Los niveles de riesgo se recalculan con los nuevos parámetros.`)
      setForm(comoTexto(r.reglas))
    } catch (err) {
      setError(err)
      setForm(comoTexto(d.reglas))
    } finally {
      setGuardando(false)
    }
  }

  return (
          <form className="card card-body" style={{ maxWidth: 720 }} onSubmit={guardar} noValidate>
            <MensajeError error={error} />
            <MensajeExito texto={exito} />
            {CAMPOS.map((c) => (
              <div className="row mb-2 align-items-center" key={c.id}>
                <label className="col-sm-7 col-form-label" htmlFor={c.id}>{d.descripciones[c.id]}</label>
                <div className="col-sm-5">
                  <div className="input-group">
                    <input id={c.id} type="number" className="form-control" min={c.min} max={c.max} step={c.paso}
                      value={form[c.id]} onChange={(e) => setForm({ ...form, [c.id]: e.target.value })} />
                    {c.unidad && <span className="input-group-text">{c.unidad}</span>}
                  </div>
                </div>
              </div>
            ))}
            <div className="row mb-3 align-items-center">
              <label className="col-sm-7 col-form-label" htmlFor="operador">{d.descripciones.operador}</label>
              <div className="col-sm-5">
                <select id="operador" className="form-select" value={form.operador} onChange={(e) => setForm({ ...form, operador: e.target.value })}>
                  <option value="Y">Y (se deben cumplir ambas condiciones)</option>
                  <option value="O">O (basta con una condición)</option>
                </select>
              </div>
            </div>
            <div className="alert alert-secondary small">
              Rojo: se cumple la regla combinada, hay ausencias consecutivas críticas o 2 o más factores.
              Amarillo: un factor. Verde: ningún factor.
            </div>
            <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
              <small className="text-secondary">Última actualización: {d.ultima_actualizacion?.replace('T', ' ')}</small>
              <button className="btn btn-primary" disabled={guardando}>{guardando ? 'Guardando...' : 'Guardar cambios'}</button>
            </div>
          </form>
  )
}
