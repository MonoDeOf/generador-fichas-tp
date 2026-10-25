import { useState } from 'react'
import { useSesion } from '../hooks/useSesion'

// Menú según rol (ERS 3.1.1). Cada opción exige el permiso que valida también el backend.
export const MENU = [
  { pagina: 'dashboard', texto: 'Dashboard', permiso: 'ver_dashboard' },
  { pagina: 'estudiantes', texto: 'Estudiantes', permiso: 'ver_estudiantes' },
  { pagina: 'casos', texto: 'Mis casos', permiso: 'ver_seguimiento' },
  { pagina: 'importar', texto: 'Importar datos', permiso: 'importar_datos' },
  { pagina: 'reglas', texto: 'Reglas de riesgo', permiso: 'configurar_reglas' },
]

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
            <span className="text-white small">{usuario.nombre} · {usuario.nombre_rol}</span>
            <button className="btn btn-sm btn-light" onClick={cerrarSesion}>Cerrar sesión</button>
          </div>
        </div>
      </div>
    </nav>
  )
}
