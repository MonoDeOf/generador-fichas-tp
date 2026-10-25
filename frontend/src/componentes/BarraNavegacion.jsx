import { useEffect, useState } from 'react'
import { api } from '../api/cliente'
import { useSesion } from '../hooks/useSesion'

// Menú según rol (ERS 3.1.1). Cada opción exige el permiso que valida también el backend.
export const MENU = [
  { pagina: 'dashboard', texto: 'Dashboard', permiso: 'ver_dashboard' },
  { pagina: 'estudiantes', texto: 'Estudiantes', permiso: 'ver_estudiantes' },
  { pagina: 'casos', texto: 'Mis casos', permiso: 'ver_seguimiento' },
  { pagina: 'reportes', texto: 'Reportes semanales', permiso: 'ver_reportes' },
  { pagina: 'importar', texto: 'Importar datos', permiso: 'importar_datos' },
  { pagina: 'reglas', texto: 'Reglas de riesgo', permiso: 'configurar_reglas' },
  { pagina: 'usuarios', texto: 'Usuarios', permiso: 'gestionar_usuarios' },
]

const INTERVALO_CONSULTA_MS = 30000

// HU 4.4: campana con contador rojo, actualizada por consulta periódica (polling).
function Campana({ pagina }) {
  const [cantidad, setCantidad] = useState(0)
  useEffect(() => {
    let activo = true
    const consultar = () => api.noLeidas().then((r) => activo && setCantidad(r.cantidad)).catch(() => {})
    consultar()
    const id = setInterval(consultar, INTERVALO_CONSULTA_MS)
    window.addEventListener('notificaciones-cambiaron', consultar)
    return () => { activo = false; clearInterval(id); window.removeEventListener('notificaciones-cambiaron', consultar) }
  }, [])
  return (
    <a href="#/notificaciones" className={`btn btn-sm position-relative ${pagina === 'notificaciones' ? 'btn-light' : 'btn-outline-light'}`}
      aria-label={`Notificaciones: ${cantidad} sin leer`}>
      <span aria-hidden="true">🔔</span> Notificaciones
      {cantidad > 0 && (
        <span className="position-absolute top-0 start-100 translate-middle badge rounded-pill bg-danger">{cantidad}</span>
      )}
    </a>
  )
}

export default function BarraNavegacion({ pagina }) {
  const { usuario, cerrarSesion, puede } = useSesion()
  const [abierto, setAbierto] = useState(false)
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary mb-4">
      <div className="container-fluid">
        <span className="navbar-brand">Seguimiento escolar</span>
        <button className="navbar-toggler" type="button" aria-label="Abrir menú" onClick={() => setAbierto(!abierto)}>
          <span className="navbar-toggler-icon" />
        </button>
        <div className={`collapse navbar-collapse ${abierto ? 'show' : ''}`}>
          <ul className="navbar-nav me-auto">
            {MENU.filter((m) => puede(m.permiso)).map((m) => (
              <li className="nav-item" key={m.pagina}>
                <a className={`nav-link ${pagina === m.pagina ? 'active' : ''}`} href={`#/${m.pagina}`}
                  onClick={() => setAbierto(false)}>{m.texto}</a>
              </li>
            ))}
          </ul>
          <div className="d-flex align-items-center gap-2 flex-wrap">
            <Campana pagina={pagina} />
            <span className="text-white small">{usuario.nombre} · {usuario.nombre_rol}</span>
            <button className="btn btn-sm btn-light" onClick={cerrarSesion}>Cerrar sesión</button>
          </div>
        </div>
      </div>
    </nav>
  )
}
