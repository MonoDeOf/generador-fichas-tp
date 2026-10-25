// Estados de carga, error y resultado reutilizados por todas las vistas.
export function Cargando({ texto = 'Cargando...' }) {
  return (
    <div className="d-flex align-items-center gap-2 text-secondary my-3" role="status">
      <span className="spinner-border spinner-border-sm" aria-hidden="true" /> {texto}
    </div>
  )
}

export function MensajeError({ error, alReintentar }) {
  if (!error) return null
  return (
    <div className="alert alert-danger" role="alert">
      <strong>{error.message}</strong>
      {error.detalles?.length > 0 && (
        <ul className="mb-0 mt-2 small">{error.detalles.map((d, i) => <li key={i}>{d}</li>)}</ul>
      )}
      {alReintentar && (
        <div className="mt-2"><button className="btn btn-sm btn-outline-danger" onClick={alReintentar}>Reintentar</button></div>
      )}
    </div>
  )
}

export function MensajeExito({ texto }) {
  if (!texto) return null
  return <div className="alert alert-success" role="status">{texto}</div>
}

// Envuelve una vista que depende de datos remotos.
export function ConDatos({ estado, children }) {
  if (estado.cargando && !estado.datos) return <Cargando />
  if (estado.error) return <MensajeError error={estado.error} alReintentar={estado.recargar} />
  return estado.datos ? children(estado.datos) : null
}
