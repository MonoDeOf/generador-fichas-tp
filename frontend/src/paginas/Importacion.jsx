import { useState } from 'react'
import { api } from '../api/cliente'
import { ConDatos, MensajeError, MensajeExito } from '../componentes/Estado'
import { useDatos } from '../hooks/useDatos'

// RF01 / HU 1.1: carga manual de los CSV de la base de datos. El sistema parte vacío.
// Se pueden seleccionar varios archivos a la vez (por ejemplo, todos los de BD_organizada);
// el backend los ordena según sus dependencias y valida todo antes de guardar.
export default function Importacion() {
  const estadoTablas = useDatos(() => api.estadoTablas())
  const [archivos, setArchivos] = useState([])
  const [error, setError] = useState(null)
  const [resultado, setResultado] = useState(null)
  const [enviando, setEnviando] = useState(false)

  async function cargar(e) {
    e.preventDefault()
    setError(null)
    setResultado(null)
    setEnviando(true)
    try {
      const contenidos = await Promise.all(archivos.map(async (a) => ({ nombre_archivo: a.name, contenido: await a.text() })))
      setResultado(await api.importar({ archivos: contenidos }))
      estadoTablas.recargar()
    } catch (err) {
      setError(err)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <>
      <h1 className="h3">Importar datos</h1>
      <div className="row g-4">
        <div className="col-lg-6">
          <form className="card card-body mb-3" onSubmit={cargar}>
            <label className="form-label" htmlFor="archivo">Archivos CSV</label>
            <input id="archivo" type="file" accept=".csv,text/csv" multiple className="form-control mb-2" required
              onChange={(e) => setArchivos([...e.target.files])} />
            <p className="small text-secondary">
              Cada archivo se asocia a su tabla por el nombre (por ejemplo <code>ESTUDIANTE.csv</code>) o por sus columnas.
              Puede cargar todos a la vez o por partes, respetando las dependencias (una tabla solo puede referirse
              a datos ya cargados o incluidos en el mismo lote). Si un registro ya existe, se actualiza.
              Si hay un error, no se guarda nada.
            </p>
            {archivos.length > 0 && <p className="small mb-2">{archivos.length} archivo(s) seleccionado(s)</p>}
            <button className="btn btn-primary" disabled={!archivos.length || enviando}>{enviando ? 'Procesando...' : 'Cargar'}</button>
          </form>
          <MensajeError error={error} />
          {resultado && (
            <>
              <MensajeExito texto={resultado.mensaje} />
              <div className="table-responsive"><table className="table table-sm">
                <thead><tr><th>Archivo</th><th>Tabla</th><th>Nuevos</th><th>Actualizados</th><th>Sin cambios</th></tr></thead>
                <tbody>
                  {resultado.archivos.map((a) => (
                    <tr key={a.tabla}><td>{a.archivo}</td><td>{a.tabla}</td><td>{a.insertados}</td><td>{a.actualizados}</td><td>{a.sin_cambios}</td></tr>
                  ))}
                </tbody>
              </table></div>
              <p className="small text-secondary">Los niveles de riesgo y las alertas se recalculan en segundo plano.</p>
            </>
          )}
        </div>
        <div className="col-lg-6">
          <div className="card card-body">
            <h2 className="h5">Estado de la base de datos</h2>
            <ConDatos estado={estadoTablas}>
              {(tablas) => (
                <table className="table table-sm mb-0">
                  <thead><tr><th>Tabla (orden de carga)</th><th>Registros</th><th>Columnas</th></tr></thead>
                  <tbody>
                    {tablas.map((t) => (
                      <tr key={t.tabla} className={t.registros ? '' : 'table-warning'}>
                        <td>{t.tabla}</td><td>{t.registros}</td><td className="small"><code>{t.columnas.join(', ')}</code></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </ConDatos>
          </div>
        </div>
      </div>
    </>
  )
}
