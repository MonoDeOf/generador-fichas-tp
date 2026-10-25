import { useState } from 'react'
import { MensajeError } from '../componentes/Estado'
import { useSesion } from '../hooks/useSesion'

export default function Login() {
  const { iniciarSesion } = useSesion()
  const [nombreUsuario, setNombreUsuario] = useState('')
  const [contrasena, setContrasena] = useState('')
  const [error, setError] = useState(null)
  const [enviando, setEnviando] = useState(false)

  async function enviar(e) {
    e.preventDefault()
    setEnviando(true)
    setError(null)
    try {
      await iniciarSesion(nombreUsuario, contrasena)
    } catch (err) {
      setError(err)
    } finally {
      setEnviando(false)
    }
  }

  return (
    <main className="container" style={{ maxWidth: 420 }}>
      <h1 className="h3 mt-5 mb-1">Seguimiento de trayectorias escolares</h1>
      <p className="text-secondary">Ingrese con su cuenta del establecimiento.</p>
      <form className="card card-body" onSubmit={enviar}>
        <MensajeError error={error} />
        <label className="form-label" htmlFor="usuario">Usuario</label>
        <input id="usuario" className="form-control mb-3" value={nombreUsuario} required autoComplete="username"
          onChange={(e) => setNombreUsuario(e.target.value)} />
        <label className="form-label" htmlFor="contrasena">Contraseña</label>
        <input id="contrasena" type="password" className="form-control mb-3" value={contrasena} required
          autoComplete="current-password" onChange={(e) => setContrasena(e.target.value)} />
        <button className="btn btn-primary" disabled={enviando}>{enviando ? 'Ingresando...' : 'Ingresar'}</button>
      </form>
    </main>
  )
}
