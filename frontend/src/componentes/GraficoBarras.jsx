// Gráfico de barras horizontal simple. El título de cada barra muestra el valor al pasar el cursor.
export default function GraficoBarras({ datos, maximo = 100, sufijo = '%', color }) {
  return (
    <div>
      {datos.map((d) => (
        <div className="barra-grafico" key={d.etiqueta} title={`${d.etiqueta}: ${d.valor ?? '-'}${sufijo}`}>
          <span className="etiqueta">{d.etiqueta}</span>
          <div className="pista" role="img" aria-label={`${d.etiqueta}: ${d.valor ?? 'sin datos'}${sufijo}`}>
            <div className="relleno" style={{ width: `${Math.min(100, (100 * (d.valor || 0)) / maximo)}%`, background: d.color || color }} />
          </div>
          <span className="valor">{d.valor ?? '-'}{sufijo}</span>
        </div>
      ))}
    </div>
  )
}
