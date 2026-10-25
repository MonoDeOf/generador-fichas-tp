import { useEffect } from 'react'

export default function Modal({ titulo, alCerrar, children }) {
  useEffect(() => {
    const alPresionar = (e) => e.key === 'Escape' && alCerrar()
    window.addEventListener('keydown', alPresionar)
    return () => window.removeEventListener('keydown', alPresionar)
  }, [alCerrar])

  return (
    <div className="modal-fondo" onClick={alCerrar}>
      <div className="modal-caja" role="dialog" aria-modal="true" aria-label={titulo} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header p-3 border-bottom">
          <h2 className="h5 modal-title">{titulo}</h2>
          <button type="button" className="btn-close" aria-label="Cerrar" onClick={alCerrar} />
        </div>
        <div className="p-3">{children}</div>
      </div>
    </div>
  )
}
