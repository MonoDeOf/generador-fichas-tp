import { useEffect, useState } from 'react'

// Navegación simple basada en el hash de la URL (#/estudiantes/RUT).
function leerRuta() {
  const partes = window.location.hash.replace(/^#\/?/, '').split('/').filter(Boolean).map(decodeURIComponent)
  return { pagina: partes[0] || '', parametros: partes.slice(1) }
}

export function useRuta() {
  const [ruta, setRuta] = useState(leerRuta)
  useEffect(() => {
    const alCambiar = () => setRuta(leerRuta())
    window.addEventListener('hashchange', alCambiar)
    return () => window.removeEventListener('hashchange', alCambiar)
  }, [])
  return ruta
}

export const enlace = (...partes) => '#/' + partes.map(encodeURIComponent).join('/')
