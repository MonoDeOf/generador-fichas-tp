import { createContext, useCallback, useContext, useEffect, useState } from 'react'
import { api, configurarExpiracion, sesionGuardada } from '../api/cliente'

const ContextoSesion = createContext(null)

export function ProveedorSesion({ children }) {
  const [usuario, setUsuario] = useState(null)
  const [catalogos, setCatalogos] = useState(null)
  const [verificando, setVerificando] = useState(Boolean(sesionGuardada.obtener()))

  const cerrarSesion = useCallback(() => {
    sesionGuardada.borrar()
    setUsuario(null)
    window.location.hash = ''
  }, [])

  useEffect(() => { configurarExpiracion(cerrarSesion) }, [cerrarSesion])

  useEffect(() => {
    if (!sesionGuardada.obtener()) return
    api.sesion().then(setUsuario).catch(() => sesionGuardada.borrar()).finally(() => setVerificando(false))
  }, [])

  useEffect(() => {
    if (usuario) api.catalogos().then(setCatalogos).catch(() => setCatalogos(null))
  }, [usuario])

  async function iniciarSesion(nombreUsuario, contrasena) {
    const { token, usuario } = await api.login(nombreUsuario, contrasena)
    sesionGuardada.guardar(token)
    setUsuario(usuario)
  }

  const puede = useCallback((permiso) => Boolean(usuario?.permisos.includes(permiso)), [usuario])

  return (
    <ContextoSesion.Provider value={{ usuario, catalogos, verificando, iniciarSesion, cerrarSesion, puede }}>
      {children}
    </ContextoSesion.Provider>
  )
}

export const useSesion = () => useContext(ContextoSesion)
