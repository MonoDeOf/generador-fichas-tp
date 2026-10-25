import { useState } from 'react'
import { api } from '../api/cliente'
import { ConDatos, MensajeError, MensajeExito } from '../componentes/Estado'
import Modal from '../componentes/Modal'
import { useDatos } from '../hooks/useDatos'
import { useSesion } from '../hooks/useSesion'

const VACIO = { nombre_usuario: '', nombre: '', rol: '', id_nivel: '', correo: '', contrasena: '', activo: true }

function FormUsuario({ inicial, alGuardar, alCerrar }) {
  const { catalogos } = useSesion()
  const nuevo = !inicial.id_usuario
  const [datos, setDatos] = useState({ ...VACIO, ...inicial, id_nivel: inicial.id_nivel ?? '', correo: inicial.correo ?? '', contrasena: '' })
  const [error, setError] = useState(null)
  const cambiar = (campo) => (e) => setDatos({ ...datos, [campo]: e.target.type === 'checkbox' ? e.target.checked : e.target.value })

  async function guardar(e) {
    e.preventDefault()
    setError(null)
    const cuerpo = { nombre: datos.nombre, rol: datos.rol, id_nivel: datos.id_nivel ? Number(datos.id_nivel) : null, correo: datos.correo || null }
    try {
      if (nuevo) await api.crearUsuario({ ...cuerpo, nombre_usuario: datos.nombre_usuario, contrasena: datos.contrasena })
      else await api.actualizarUsuario(inicial.id_usuario, { ...cuerpo, activo: datos.activo, contrasena: datos.contrasena || null })
      alGuardar()
    } catch (err) { setError(err) }
  }

  return (
    <Modal titulo={nuevo ? 'Nuevo usuario' : `Editar ${inicial.nombre_usuario}`} alCerrar={alCerrar}>
      <form onSubmit={guardar}>
        <MensajeError error={error} />
        {nuevo && (<>
          <label className="form-label small" htmlFor="u-usuario">Nombre de usuario</label>
          <input id="u-usuario" className="form-control mb-2" required minLength={3} maxLength={30} value={datos.nombre_usuario} onChange={cambiar('nombre_usuario')} />
        </>)}
        <label className="form-label small" htmlFor="u-nombre">Nombre</label>
        <input id="u-nombre" className="form-control mb-2" required maxLength={80} value={datos.nombre} onChange={cambiar('nombre')} />
        <label className="form-label small" htmlFor="u-rol">Rol</label>
        <select id="u-rol" className="form-select mb-2" required value={datos.rol} onChange={cambiar('rol')}>
          <option value="">Seleccione...</option>
          {catalogos?.roles.map((r) => <option key={r.rol} value={r.rol}>{r.nombre}</option>)}
        </select>
        {datos.rol === 'profesor_jefe' && (<>
          <label className="form-label small" htmlFor="u-nivel">Curso (jefatura)</label>
          <select id="u-nivel" className="form-select mb-2" required value={datos.id_nivel} onChange={cambiar('id_nivel')}>
            <option value="">Seleccione...</option>
            {catalogos?.niveles.map((n) => <option key={n.id_nivel} value={n.id_nivel}>{n.nombre_nivel}</option>)}
          </select>
        </>)}
        <label className="form-label small" htmlFor="u-correo">Correo (para el reporte semanal)</label>
        <input id="u-correo" type="email" className="form-control mb-2" value={datos.correo} onChange={cambiar('correo')} />
        <label className="form-label small" htmlFor="u-clave">{nuevo ? 'Contraseña' : 'Nueva contraseña (opcional)'}</label>
        <input id="u-clave" type="password" className="form-control mb-2" required={nuevo} minLength={8} value={datos.contrasena} onChange={cambiar('contrasena')} />
        {!nuevo && (
          <div className="form-check mb-2">
            <input id="u-activo" type="checkbox" className="form-check-input" checked={datos.activo} onChange={cambiar('activo')} />
            <label className="form-check-label" htmlFor="u-activo">Activo</label>
          </div>
        )}
        <button className="btn btn-primary mt-2">Guardar</button>
      </form>
    </Modal>
  )
}

// Gestión de usuarios, roles y permisos (administrador).
export default function Usuarios() {
  const { catalogos } = useSesion()
  const estado = useDatos(() => api.usuarios())
  const [editando, setEditando] = useState(null)
  const [exito, setExito] = useState(null)
  const nivel = (id) => catalogos?.niveles.find((n) => n.id_nivel === id)?.nombre_nivel

  return (
    <>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <h1 className="h3 mb-0">Usuarios</h1>
        <button className="btn btn-primary btn-sm" onClick={() => setEditando({})}>Nuevo usuario</button>
      </div>
      <MensajeExito texto={exito} />
      <ConDatos estado={estado}>
        {(lista) => (
          <div className="card table-responsive">
            <table className="table table-sm align-middle mb-0">
              <thead><tr><th>Usuario</th><th>Nombre</th><th>Rol</th><th>Curso</th><th>Correo</th><th>Estado</th><th /></tr></thead>
              <tbody>
                {lista.map((u) => (
                  <tr key={u.id_usuario}>
                    <td>{u.nombre_usuario}</td><td>{u.nombre}</td><td>{u.nombre_rol}</td><td>{nivel(u.id_nivel) || '-'}</td>
                    <td>{u.correo || '-'}</td><td>{u.activo ? 'Activo' : 'Inactivo'}</td>
                    <td><button className="btn btn-outline-primary btn-sm" onClick={() => setEditando(u)}>Editar</button></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </ConDatos>
      {editando && (
        <FormUsuario inicial={editando} alCerrar={() => setEditando(null)}
          alGuardar={() => { setEditando(null); setExito('Usuario guardado.'); estado.recargar() }} />
      )}
    </>
  )
}
