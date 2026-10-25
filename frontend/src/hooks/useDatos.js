import { useCallback, useEffect, useRef, useState } from 'react'

// Carga datos de la API y expone su estado de carga y error.
// Si llega una respuesta de una petición anterior (por ejemplo, tras cambiar un filtro), se descarta.
export function useDatos(cargar, dependencias = []) {
  const [datos, setDatos] = useState(null)
  const [cargando, setCargando] = useState(true)
  const [error, setError] = useState(null)
  const ultimaPeticion = useRef(0)

  // eslint-disable-next-line react-hooks/exhaustive-deps
  const recargar = useCallback(() => {
    const numero = ++ultimaPeticion.current
    const vigente = () => numero === ultimaPeticion.current
    setCargando(true)
    setError(null)
    return cargar()
      .then((d) => vigente() && setDatos(d))
      .catch((e) => vigente() && setError(e))
      .finally(() => vigente() && setCargando(false))
  }, dependencias)

  useEffect(() => { recargar() }, [recargar])

  return { datos, cargando, error, recargar, setDatos }
}
